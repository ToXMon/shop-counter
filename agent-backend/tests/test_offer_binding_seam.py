"""Seam tests for offer-bound intent, same-seller offer invalidation, and Mac-local checkout state.

Built with the red-green TDD loop at the HTTP API seam (`POST /utterance`, `GET /state`, `POST /intent`, `POST /session/clear`).
"""
from __future__ import annotations

import json
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_slice1_intent_rejects_missing_offer_reference() -> None:
    """A tap without an offer reference must be rejected even when a pick is displayed."""
    client.post("/session/clear", json={})

    r_utt = client.post(
        "/utterance",
        json={"text": "Find me the Monday Cartoons Digital Sticker under one dollar"},
    )
    assert r_utt.status_code == 200
    utt_body = r_utt.json()
    sid = utt_body["session_id"]

    # Both /utterance reply and /state pick must expose the canonical offer_id
    offer_id = utt_body["reply"].get("offer_id")
    assert (
        isinstance(offer_id, str)
        and offer_id == "monday-cartoons.myshopify.com:gid://shopify/ProductVariant/68033173323939:50"
    )

    st = client.get(f"/state?session_id={sid}").json()
    assert st["pick"]["offer_id"] == offer_id
    assert st["pick"]["variant_id"] == "gid://shopify/ProductVariant/68033173323939"
    assert st["pick"]["price_minor"] == 50

    # Tap WITHOUT offer_id / pick_id / variant_id must be rejected as stale_pick
    r_missing = client.post(
        "/intent",
        json={"session_id": sid, "type": "buy", "source": "button"},
    )
    assert r_missing.status_code == 200
    missing_body = r_missing.json()
    assert missing_body["handoff"]["status"] == "stale_pick"
    assert missing_body["handoff"]["offer_id"] == offer_id
    assert "continue_url" not in json.dumps(missing_body)

    # /state must NOT have a checkout handoff after a rejected tap
    st_after = client.get(f"/state?session_id={sid}").json()
    assert st_after["handoff"] is None


def test_slice2_same_seller_offer_change_rejects_stale_offer_and_accepts_current_offer() -> None:
    """Changing from one Monday Cartoons item to the Monday Cartoons Digital Sticker invalidates the old offer_id."""
    client.post("/session/clear", json={})

    # Turn 1: Monday Cartoons Hat (same seller: Monday Cartoons)
    r1 = client.post(
        "/utterance",
        json={"text": "Show me the Monday Cartoons Hat under fifty dollars"},
    )
    assert r1.status_code == 200
    d1 = r1.json()
    sid = d1["session_id"]
    first_offer_id = d1["reply"]["offer_id"]
    assert first_offer_id

    # Create valid handoff for the first offer
    r_intent_1 = client.post(
        "/intent",
        json={"session_id": sid, "type": "buy", "source": "button", "offer_id": first_offer_id},
    )
    assert r_intent_1.status_code == 200
    assert r_intent_1.json()["handoff"]["status"] == "ready"
    st_1 = client.get(f"/state?session_id={sid}").json()
    assert st_1["handoff"] is not None
    assert st_1["handoff"]["offer_id"] == first_offer_id
    assert st_1["handoff"]["merchant"] == "Monday Cartoons"

    # Turn 2: Switch to Digital Sticker from the SAME seller (Monday Cartoons)
    r2 = client.post(
        "/utterance",
        json={"session_id": sid, "text": "Actually, switch to the Monday Cartoons Digital Sticker under a dollar"},
    )
    assert r2.status_code == 200
    d2 = r2.json()
    sticker_offer_id = d2["reply"]["offer_id"]
    assert sticker_offer_id == "monday-cartoons.myshopify.com:gid://shopify/ProductVariant/68033173323939:50"
    assert sticker_offer_id != first_offer_id

    # Old QR handoff must be cleared immediately on offer change
    st_after_switch = client.get(f"/state?session_id={sid}").json()
    assert st_after_switch["handoff"] is None
    assert st_after_switch["pick"]["offer_id"] == sticker_offer_id

    # Device-safe pairing endpoint /session/offer returns the new offer_id without continue_url
    pair_info = client.get(f"/session/offer?session_id={sid}").json()
    assert pair_info["session_id"] == sid
    assert pair_info["offer_id"] == sticker_offer_id
    assert "continue_url" not in json.dumps(pair_info)

    # Tapping with the OLD Monday Cartoons offer_id must be rejected as stale_pick
    r_stale = client.post(
        "/intent",
        json={"session_id": sid, "type": "buy", "source": "button", "offer_id": first_offer_id},
    )
    assert r_stale.status_code == 200
    stale_body = r_stale.json()
    assert stale_body["handoff"]["status"] == "stale_pick"
    assert stale_body["handoff"]["offer_id"] == sticker_offer_id
    assert client.get(f"/state?session_id={sid}").json()["handoff"] is None

    # Tapping with the CURRENT Digital Sticker offer_id creates the Shop MCP handoff
    r_valid = client.post(
        "/intent",
        json={"session_id": sid, "type": "buy", "source": "button", "offer_id": sticker_offer_id},
    )
    assert r_valid.status_code == 200
    valid_body = r_valid.json()
    assert valid_body["handoff"]["status"] == "ready"
    assert valid_body["handoff"]["offer_id"] == sticker_offer_id
    assert "continue_url" not in json.dumps(valid_body)

    # Loopback (Mac) /state has continue_url and matching offer_id
    st_ready = client.get(f"/state?session_id={sid}").json()
    assert st_ready["handoff"]["status"] == "ready"
    assert st_ready["handoff"]["offer_id"] == sticker_offer_id
    assert st_ready["handoff"]["continue_url"].startswith("https://")

    # Non-loopback client (e.g. device on hotspot IP) never receives continue_url from public_state_view
    non_local_view = main.public_state_view(main.SESSIONS[sid], allow_continue_url=False)
    assert "continue_url" not in json.dumps(non_local_view)

