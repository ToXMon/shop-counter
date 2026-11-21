"""Integration and seam tests for Shop Counter `agent-backend`.

Covers:
1. Centralized model IDs in `models.py` (no global GEMINI_MODEL).
2. Redaction helper (`shop.redact_sensitive`).
3. Typed Monday Cartoons search -> narrow to Digital Sticker (`gid://shopify/ProductVariant/68033173323939`) -> Shop MCP checkout -> `stale_pick` invalidation -> session clear.
4. Decisions API clarification gate on ambiguous initial utterance.
5. Push-to-talk voice loop: `/tts` -> `/transcribe` -> multipart WAV `/utterance` -> Transcribe -> Hydrogen -> Shopify -> Neon -> TTS.
"""
from __future__ import annotations

import base64
import json

from fastapi.testclient import TestClient
import pytest

import main
import models
import shop


client = TestClient(main.app)


def test_models_centralized() -> None:
    assert models.AGENT_MODEL == "gemini-4-neon"
    assert models.WORKER_MODEL == "gemini-4-hydrogen"
    assert models.DECISION_MODEL == "gemini-decision-1"
    assert models.TRANSCRIBE_MODEL == "gemini-3.5-transcribe"
    assert models.TTS_MODEL == "gemini-3.8-flash-tts"
    assert models.MANAGED_AGENT_ID == "antigravity-preview-09-2026"


def test_redaction_helper() -> None:
    sample = {
        "id": "gid://shopify/Checkout/abc123?key=secret999",
        "continue_url": "https://monday-cartoons.myshopify.com/46411219107/checkouts/xyz?key=secret",
        "nested": "Link: https://shop.app/checkout/46411219107/abc",
        "merchant": "Monday Cartoons",
    }
    redacted = shop.redact_sensitive(sample)
    dumped = json.dumps(redacted)
    assert "secret" not in dumped
    assert "checkouts" not in dumped
    assert "shop.app/checkout" not in dumped
    assert redacted["merchant"] == "Monday Cartoons"


def test_clarification_gate() -> None:
    client.post("/session/clear", json={})
    resp = client.post("/utterance", json={"text": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["reply"]["did_research"] is False
    assert data["reply"].get("needs_clarification") is True
    assert len(data["reply"]["speech"].split()) <= 45


def test_monday_cartoons_to_digital_sticker_and_checkout() -> None:
    client.post("/session/clear", json={})

    # Turn 1: broad Monday Cartoons search
    r1 = client.post("/utterance", json={"text": "Show me items from Monday Cartoons under one hundred dollars"})
    assert r1.status_code == 200
    d1 = r1.json()
    sid = d1["session_id"]
    assert d1["reply"]["pick_id"]
    assert len(d1["reply"]["speech"].split()) <= 45

    # Turn 2: narrow to the Digital Sticker
    r2 = client.post(
        "/utterance",
        json={"session_id": sid, "text": "Switch to the Monday Cartoons Digital Sticker under a dollar"},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["reply"]["did_research"] is True
    assert len(d2["reply"]["speech"].split()) <= 45

    st_resp = client.get(f"/state?session_id={sid}")
    st = st_resp.json()
    pick_cand = next(c for c in st["candidates"] if c["is_pick"])
    assert pick_cand["variant_id"] == "gid://shopify/ProductVariant/68033173323939"
    assert pick_cand["seller"]["domain"] == "monday-cartoons.myshopify.com"
    assert isinstance(pick_cand["price_minor"], int) and pick_cand["price_minor"] > 0

    # Stale intent check when caller supplies outdated price_minor
    r_stale = client.post(
        "/intent",
        json={
            "session_id": sid,
            "type": "buy",
            "source": "button",
            "price_minor": pick_cand["price_minor"] + 500,
        },
    )
    assert r_stale.status_code == 200
    assert r_stale.json()["handoff"]["status"] == "stale_pick"
    assert "continue_url" not in json.dumps(r_stale.json())

    # Valid intent creates real Shop MCP handoff; device never receives continue_url
    r_intent = client.post(
        "/intent",
        json={"session_id": sid, "type": "buy", "source": "button"},
    )
    assert r_intent.status_code == 200
    intent_body = r_intent.json()
    assert intent_body["handoff"]["status"] == "ready"
    assert intent_body["handoff"]["merchant"] == "Monday Cartoons"
    assert "continue_url" not in json.dumps(intent_body)

    # Companion screen loopback GET /state has continue_url
    st_handoff = client.get(f"/state?session_id={sid}").json()
    assert st_handoff["phase"] == "handoff"
    assert st_handoff["handoff"]["continue_url"].startswith("https://")

    # Clear session removes handoff and candidates
    client.post("/session/clear", json={"session_id": sid})
    st_cleared = client.get(f"/state?session_id={sid}").json()
    assert st_cleared["handoff"] is None
    assert st_cleared["candidates"] == []


def test_push_to_talk_audio_loop() -> None:
    client.post("/session/clear", json={})

    # 1. Generate spoken request WAV via /tts
    tts_resp = client.post(
        "/tts",
        json={"text": "Find me the Digital Sticker from Monday Cartoons."},
    )
    assert tts_resp.status_code == 200
    tts_data = tts_resp.json()
    assert tts_data["ok"] is True
    assert tts_data["audio_b64"]
    wav_bytes = base64.b64decode(tts_data["audio_b64"])
    assert wav_bytes[:4] == b"RIFF"

    # 2. Verify standalone /transcribe endpoint
    stt_resp = client.post(
        "/transcribe",
        files={"audio": ("utterance.wav", wav_bytes, "audio/wav")},
    )
    assert stt_resp.status_code == 200
    stt_data = stt_resp.json()
    assert stt_data["ok"] is True
    assert "sticker" in stt_data["text"].lower()

    # 3. Verify full push-to-talk loop on multipart POST /utterance:
    # recorded audio -> Transcribe -> Hydrogen constraints -> live Shopify lookup -> Neon pick -> TTS
    utt_resp = client.post(
        "/utterance",
        files={"audio": ("utterance.wav", wav_bytes, "audio/wav")},
    )
    assert utt_resp.status_code == 200
    utt_data = utt_resp.json()
    reply = utt_data["reply"]
    assert "sticker" in reply.get("transcript", "").lower()
    assert reply["pick_id"]
    assert len(reply["speech"].split()) <= 45
    assert reply.get("audio_b64")
    reply_wav = base64.b64decode(reply["audio_b64"])
    assert reply_wav[:4] == b"RIFF"
