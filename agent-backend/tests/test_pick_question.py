"""Tests for grounded `question_about_pick` fast-path vs live constraint-change re-search.

Verifies:
1. High-confidence factual question about the current pick answers from that pick's data without re-searching or creating checkout.
2. Factual question asking for missing details (e.g. warranty) states honestly that the listing does not mention it.
3. Changed budget/seller/product constraint still triggers live Shopify search (`did_research=True`) and never creates checkout without explicit offer-bound intent.
"""
from __future__ import annotations

import json
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_question_about_pick_grounded_and_constraint_change_researches() -> None:
    client.post("/session/clear", json={})

    # Turn 1: Establish a current pick (Monday Cartoons Digital Sticker)
    r1 = client.post(
        "/utterance",
        json={"text": "Find me the Monday Cartoons Digital Sticker under one dollar"},
    )
    assert r1.status_code == 200
    d1 = r1.json()
    sid = d1["session_id"]
    sticker_offer_id = d1["reply"]["offer_id"]
    assert sticker_offer_id == "monday-cartoons.myshopify.com:gid://shopify/ProductVariant/68033173323939:50"

    # Turn 2a: High-confidence factual question grounded in pick data (no shipping / price)
    r_qa_known = client.post(
        "/utterance",
        json={"session_id": sid, "text": "Does this item require shipping?"},
    )
    assert r_qa_known.status_code == 200
    d_known = r_qa_known.json()
    assert d_known["reply"]["did_research"] is False
    assert d_known["reply"]["offer_id"] == sticker_offer_id
    assert len(d_known["reply"]["speech"].split()) <= 45
    assert "no" in d_known["reply"]["speech"].lower() or "digital" in d_known["reply"]["speech"].lower()
    st_known = client.get(f"/state?session_id={sid}").json()
    assert st_known["handoff"] is None

    # Turn 2b: Factual question where data is missing (warranty) -> should admit missing fact, no re-search, no checkout
    r_qa_missing = client.post(
        "/utterance",
        json={"session_id": sid, "text": "Does this come with a five year warranty?"},
    )
    assert r_qa_missing.status_code == 200
    d_missing = r_qa_missing.json()
    assert d_missing["reply"]["did_research"] is False
    assert d_missing["reply"]["offer_id"] == sticker_offer_id
    assert len(d_missing["reply"]["speech"].split()) <= 45
    low_speech = d_missing["reply"]["speech"].lower()
    assert any(w in low_speech for w in ("not", "doesn't", "does not", "no mention", "listed", "state", "specify"))
    assert client.get(f"/state?session_id={sid}").json()["handoff"] is None

    # Turn 3: Changed product & budget constraint MUST still trigger live search and NEVER create checkout
    r_change = client.post(
        "/utterance",
        json={"session_id": sid, "text": "Instead, show me a Monday Cartoons hat under fifty dollars"},
    )
    assert r_change.status_code == 200
    d_change = r_change.json()
    assert d_change["reply"]["did_research"] is True
    assert d_change["reply"]["offer_id"] != sticker_offer_id
    st_change = client.get(f"/state?session_id={sid}").json()
    assert st_change["handoff"] is None
    assert "continue_url" not in json.dumps(d_change)
