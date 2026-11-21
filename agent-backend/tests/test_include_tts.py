"""Regression tests for explicit `include_tts` handling on audio and text utterances.

Verifies:
- Audio input with `include_tts=false` returns `reply.speech` and never calls Gemini TTS.
- Audio input with `include_tts=true` calls Gemini TTS once and returns `audio_b64`.
- Omitting `include_tts` preserves existing defaults (True for audio, False for text).
- `GET /state` carries `reply.speech` so the Mac can speak the reply once.
"""
from __future__ import annotations

import base64
from typing import Any

from fastapi.testclient import TestClient
import pytest

import agent
import gates
import main
import shop
import speech
import workers

client = TestClient(main.app)

_FAKE_WAV = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00"


@pytest.fixture
def stubbed_pipeline(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Stub external Gemini/Shopify calls so include_tts routing is tested deterministically."""
    calls = {"tts": 0, "transcribe": 0}

    async def fake_transcribe(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        calls["transcribe"] += 1
        return "Find me the Monday Cartoons Digital Sticker under one dollar"

    async def fake_tts(text: str, voice: str = "Kore") -> dict[str, str | None]:
        calls["tts"] += 1
        return {"audio_b64": base64.b64encode(_FAKE_WAV).decode("ascii"), "mime_type": "audio/wav"}

    async def fake_classify(text: str, history: list[dict[str, Any]], current_constraints: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"kind": "new_search", "confidence": 0.95, "needs_clarification": False, "did_research": False}

    async def fake_parse(text: str, prior_constraints: dict[str, Any] | None = None, history: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return {
            "query": "Monday Cartoons Digital Sticker",
            "budget_max_minor": 100,
            "must_have": ["digital", "sticker"],
            "seller_hint": "monday-cartoons.myshopify.com",
        }

    async def fake_search(**kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "product_id": "gid://shopify/Product/15536111124643",
                "variant_id": "gid://shopify/ProductVariant/68033173323939",
                "title": "Digital Sticker",
                "price_minor": 50,
                "currency": "USD",
                "image_url": None,
                "seller": {"name": "Monday Cartoons", "domain": "monday-cartoons.myshopify.com"},
                "rating": None,
                "is_pick": False,
                "requires_shipping": False,
                "description": "Instant digital sticker download.",
                "source": "storefront",
            }
        ]

    async def fake_summaries(constraints: dict[str, Any], candidates: list[dict[str, Any]]) -> list[str]:
        return ["Digital Sticker at $0.50 from Monday Cartoons."]

    async def fake_score(utterance: str, constraints: dict[str, Any], candidates: list[dict[str, Any]], summaries: list[str] | None = None) -> list[dict[str, Any]]:
        out = [dict(c) for c in candidates]
        out[0]["decision_score"] = 0.98
        return out

    async def fake_choose(utterance: str, constraints: dict[str, Any], candidates: list[dict[str, Any]], retry_feedback: str | None = None) -> dict[str, Any]:
        return {
            "pick_id": "gid://shopify/Product/15536111124643",
            "reasons": ["Fifty cents from Monday Cartoons", "Instant digital download", "Under your one dollar budget"],
            "speech": "I found the Digital Sticker from Monday Cartoons for fifty cents.",
        }

    async def fake_self_check(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"passed": True, "budget_ok": True, "probability": 0.99, "confidence": 0.99, "failure_reason": None}

    monkeypatch.setattr(speech, "transcribe_audio", fake_transcribe)
    monkeypatch.setattr(speech, "synthesize_speech", fake_tts)
    monkeypatch.setattr(gates, "classify_utterance", fake_classify)
    monkeypatch.setattr(workers, "parse_constraints", fake_parse)
    monkeypatch.setattr(shop, "search_catalog", fake_search)
    monkeypatch.setattr(workers, "summarise_candidates", fake_summaries)
    monkeypatch.setattr(gates, "score_candidates", fake_score)
    monkeypatch.setattr(agent, "choose_pick", fake_choose)
    monkeypatch.setattr(gates, "self_check", fake_self_check)
    return calls


def test_audio_with_include_tts_false_skips_gemini_tts(stubbed_pipeline: dict[str, int]) -> None:
    client.post("/session/clear", json={})
    resp = client.post(
        "/utterance",
        data={"include_tts": "false"},
        files={"audio": ("utterance.wav", _FAKE_WAV, "audio/wav")},
    )
    assert resp.status_code == 200
    body = resp.json()
    reply = body["reply"]
    assert reply["speech"] == "I found the Digital Sticker from Monday Cartoons for fifty cents."
    assert reply["transcript"]
    assert "audio_b64" not in reply
    assert stubbed_pipeline["transcribe"] == 1
    assert stubbed_pipeline["tts"] == 0

    # Mac companion screen /state carries reply.speech so it can speak once
    st = client.get(f"/state?session_id={body['session_id']}").json()
    assert st["reply"]["speech"] == reply["speech"]


def test_audio_with_include_tts_true_calls_gemini_tts(stubbed_pipeline: dict[str, int]) -> None:
    client.post("/session/clear", json={})
    resp = client.post(
        "/utterance",
        data={"include_tts": "true"},
        files={"audio": ("utterance.wav", _FAKE_WAV, "audio/wav")},
    )
    assert resp.status_code == 200
    reply = resp.json()["reply"]
    assert reply["speech"]
    assert reply.get("audio_b64")
    assert stubbed_pipeline["tts"] == 1


def test_audio_omitting_include_tts_preserves_default_true(stubbed_pipeline: dict[str, int]) -> None:
    client.post("/session/clear", json={})
    resp = client.post(
        "/utterance",
        files={"audio": ("utterance.wav", _FAKE_WAV, "audio/wav")},
    )
    assert resp.status_code == 200
    reply = resp.json()["reply"]
    assert reply.get("audio_b64")
    assert stubbed_pipeline["tts"] == 1


def test_text_omitting_include_tts_preserves_default_false(stubbed_pipeline: dict[str, int]) -> None:
    client.post("/session/clear", json={})
    resp = client.post(
        "/utterance",
        json={"text": "Find me the Monday Cartoons Digital Sticker under one dollar"},
    )
    assert resp.status_code == 200
    reply = resp.json()["reply"]
    assert reply["speech"]
    assert "audio_b64" not in reply
    assert stubbed_pipeline["tts"] == 0
