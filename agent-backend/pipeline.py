"""End-to-end Shop Counter pipeline in the exact order of docs/INTERFACES.md section 3.

Pipeline stages:
1. [gemini-3.5-transcribe]   WAV -> text (when audio input is provided)
2. [gemini-decision-1]       GATE 1: classify utterance + clarification gate
3. [gemini-4-hydrogen]       WORKER: parse constraints (structured output)
4. shop.search_catalog       Live Shopify Global Catalog + verified Monday Cartoons storefront
5. [gemini-4-hydrogen] x N   Parallel candidate fit summaries (`asyncio.gather`)
6. [gemini-decision-1]       SCORE: ordered rubric per candidate (0..1)
7. [gemini-4-neon]           AGENT: choose pick, 3 reasons, spoken reply (<=45 words)
8. [gemini-decision-1]       GATE 2: self-check (retries Neon once if failed or confidence < 0.7)
9. [gemini-3.8-flash-tts]    TTS audio synthesis (for voice / push-to-talk requests)
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

import agent
import gates
import shop
import speech
import workers

logger = logging.getLogger("shop_counter.pipeline")


def make_offer_id(c: dict[str, Any]) -> str:
    """Build deterministic offer ID binding seller.domain, variant_id, and price_minor."""
    seller_domain = (c.get("seller") or {}).get("domain", "")
    return f"{seller_domain}:{c['variant_id']}:{int(c['price_minor'])}"


async def _attach_tts_if_needed(
    reply_obj: dict[str, Any],
    speech_text: str,
    *,
    should_tts: bool,
    timings_ms: dict[str, int] | None = None,
) -> dict[str, Any]:
    if should_tts:
        t0 = time.perf_counter()
        tts_out = await speech.synthesize_speech(speech_text)
        if timings_ms is not None:
            timings_ms["tts_ms"] = int((time.perf_counter() - t0) * 1000)
        reply_obj["audio_b64"] = tts_out["audio_b64"]
        reply_obj["audio_mime_type"] = tts_out["mime_type"]
    elif timings_ms is not None:
        timings_ms["tts_ms"] = 0
    return reply_obj


def _record_state_reply(state: dict[str, Any], reply_obj: dict[str, Any]) -> None:
    """Store latest spoken reply on session state (no audio_b64, no continue_url)."""
    state["reply"] = {
        "speech": reply_obj.get("speech", ""),
        "pick_id": reply_obj.get("pick_id"),
        "offer_id": reply_obj.get("offer_id"),
        "did_research": bool(reply_obj.get("did_research", False)),
        "updated_at": state.get("updated_at", int(time.time())),
    }


def _public_candidate(c: dict[str, Any], is_pick: bool) -> dict[str, Any]:
    return {
        "product_id": c["product_id"],
        "variant_id": c["variant_id"],
        "offer_id": make_offer_id(c),
        "title": c["title"],
        "price_minor": int(c["price_minor"]),
        "currency": c.get("currency", "USD"),
        "image_url": c.get("image_url"),
        "seller": {
            "name": c["seller"]["name"],
            "domain": c["seller"]["domain"],
        },
        "rating": c.get("rating"),
        "is_pick": is_pick,
    }


async def run_utterance_pipeline(
    state: dict[str, Any],
    *,
    text: str | None = None,
    audio_bytes: bytes | None = None,
    audio_mime_type: str = "audio/wav",
    include_tts: bool | None = None,
) -> dict[str, Any]:
    """Execute the full section 3 pipeline and mutate `state` in place."""
    t_start = time.perf_counter()
    timings_ms: dict[str, int] = {}
    should_tts = bool(audio_bytes) if include_tts is None else bool(include_tts)

    state["phase"] = "listening" if audio_bytes else "searching"
    state["updated_at"] = int(time.time())

    # 1. Transcribe if audio was uploaded
    transcript = (text or "").strip()
    if audio_bytes:
        t0 = time.perf_counter()
        transcript = await speech.transcribe_audio(audio_bytes, mime_type=audio_mime_type)
        timings_ms["transcribe_ms"] = int((time.perf_counter() - t0) * 1000)
    if not transcript:
        reply_speech = "I didn't catch that. Tell me what product and budget you're looking for."
        reply_obj: dict[str, Any] = {
            "speech": reply_speech,
            "pick_id": (state.get("pick") or {}).get("product_id"),
            "did_research": False,
            "transcript": "",
            "needs_clarification": True,
        }
        await _attach_tts_if_needed(
            reply_obj, reply_speech, should_tts=should_tts, timings_ms=timings_ms
        )
        timings_ms["total_ms"] = int((time.perf_counter() - t_start) * 1000)
        reply_obj["timings_ms"] = timings_ms
        logger.info("utterance_timings_ms=%s", timings_ms)
        state["phase"] = "pick" if state.get("pick") else "idle"
        _record_state_reply(state, reply_obj)
        return {"session_id": state["session_id"], "reply": reply_obj}

    prior_history: list[dict[str, Any]] = state.get("history") or []
    prior_constraints: dict[str, Any] = state.get("constraints") or {}

    # 2. GATE 1: Decision 1 classification + clarification gate
    t0 = time.perf_counter()
    gate1 = await gates.classify_utterance(
        transcript, prior_history, current_constraints=prior_constraints
    )
    timings_ms["gate1_ms"] = int((time.perf_counter() - t0) * 1000)

    if gate1.get("needs_clarification"):
        reply_speech = (
            "What kind of product are you shopping for today, and do you have a price limit?"
        )
        state["history"].append(
            {"t": int(time.time()), "text": transcript, "did_research": False}
        )
        state["phase"] = "pick" if state.get("pick") else "idle"
        state["updated_at"] = int(time.time())
        reply_obj = {
            "speech": reply_speech,
            "pick_id": (state.get("pick") or {}).get("product_id"),
            "did_research": False,
            "transcript": transcript,
            "needs_clarification": True,
            "gate1": gate1,
        }
        await _attach_tts_if_needed(
            reply_obj, reply_speech, should_tts=should_tts, timings_ms=timings_ms
        )
        timings_ms["total_ms"] = int((time.perf_counter() - t_start) * 1000)
        reply_obj["timings_ms"] = timings_ms
        logger.info("utterance_timings_ms=%s", timings_ms)
        _record_state_reply(state, reply_obj)
        return {"session_id": state["session_id"], "reply": reply_obj}

    # Voice alone never creates a checkout (hard rule). Record voice buy intent timestamp and prompt physical tap.
    if gate1.get("kind") == "buy_intent" and state.get("pick") and gate1.get("confidence", 0.0) >= 0.8:
        state["_last_voice_buy_ts"] = time.time()
        current_pick_id = state["pick"]["product_id"]
        pick_cand = next(
            (c for c in state.get("candidates", []) if c["product_id"] == current_pick_id),
            None,
        )
        title = pick_cand["title"] if pick_cand else "that item"
        spoken_price = (
            shop.minor_to_spoken(pick_cand["price_minor"]) if pick_cand else ""
        )
        reply_speech = agent.sanitize_speech(
            f"Ready for the {title} at {spoken_price}. Tap the button or badge on the counter to send checkout to your phone."
        )
        state["history"].append(
            {"t": int(time.time()), "text": transcript, "did_research": False}
        )
        state["updated_at"] = int(time.time())
        reply_obj = {
            "speech": reply_speech,
            "pick_id": current_pick_id,
            "offer_id": state["pick"].get("offer_id"),
            "did_research": False,
            "transcript": transcript,
            "gate1": gate1,
        }
        await _attach_tts_if_needed(
            reply_obj, reply_speech, should_tts=should_tts, timings_ms=timings_ms
        )
        timings_ms["total_ms"] = int((time.perf_counter() - t_start) * 1000)
        reply_obj["timings_ms"] = timings_ms
        logger.info("utterance_timings_ms=%s", timings_ms)
        _record_state_reply(state, reply_obj)
        return {"session_id": state["session_id"], "reply": reply_obj}

    # 3. Hydrogen worker: parse constraints
    state["phase"] = "searching"
    t0 = time.perf_counter()
    parsed_constraints = await workers.parse_constraints(
        transcript, prior_constraints=prior_constraints, history=prior_history
    )
    timings_ms["hydrogen_constraints_ms"] = int((time.perf_counter() - t0) * 1000)
    country = os.environ.get("SHOP_COUNTRY", "US")
    currency = os.environ.get("SHOP_CURRENCY", "USD")
    constraints_state = {
        "query": parsed_constraints.get("query") or "espresso machine",
        "budget_max_minor": parsed_constraints.get("budget_max_minor"),
        "currency": currency,
        "country": country,
    }

    did_research = bool(prior_history) and (
        bool(gate1.get("did_research"))
        or constraints_state.get("budget_max_minor") != prior_constraints.get("budget_max_minor")
        or constraints_state.get("query") != prior_constraints.get("query")
    )

    # 4. Live Shopify search (Global Catalog + verified Monday Cartoons storefront)
    t0 = time.perf_counter()
    raw_candidates = await shop.search_catalog(
        query=constraints_state["query"],
        budget_max_minor=constraints_state["budget_max_minor"],
        country=country,
        currency=currency,
        limit=5,
        must_have=parsed_constraints.get("must_have"),
        seller_hint=parsed_constraints.get("seller_hint"),
    )
    timings_ms["shopify_search_ms"] = int((time.perf_counter() - t0) * 1000)

    if not raw_candidates:
        reply_speech = "I couldn't find any available products matching that request and budget. Want to try a higher budget?"
        state["constraints"] = constraints_state
        state["candidates"] = []
        state["pick"] = None
        state["handoff"] = None
        state["phase"] = "idle"
        state["history"].append(
            {"t": int(time.time()), "text": transcript, "did_research": did_research}
        )
        state["updated_at"] = int(time.time())
        reply_obj = {
            "speech": reply_speech,
            "pick_id": None,
            "did_research": did_research,
            "transcript": transcript,
        }
        await _attach_tts_if_needed(
            reply_obj, reply_speech, should_tts=should_tts, timings_ms=timings_ms
        )
        timings_ms["total_ms"] = int((time.perf_counter() - t_start) * 1000)
        reply_obj["timings_ms"] = timings_ms
        logger.info("utterance_timings_ms=%s", timings_ms)
        _record_state_reply(state, reply_obj)
        return {"session_id": state["session_id"], "reply": reply_obj}

    # 5. Hydrogen parallel workers: summarise each candidate
    state["phase"] = "comparing"
    t0 = time.perf_counter()
    summaries = await workers.summarise_candidates(parsed_constraints, raw_candidates)
    timings_ms["hydrogen_summaries_ms"] = int((time.perf_counter() - t0) * 1000)

    # 6. Decision 1 SCORE gate: score all candidates
    t0 = time.perf_counter()
    scored_candidates = await gates.score_candidates(
        transcript, parsed_constraints, raw_candidates, summaries=summaries
    )
    timings_ms["decision_score_ms"] = int((time.perf_counter() - t0) * 1000)

    # 7. Neon agent: choose the pick, reasons, and spoken explanation
    t0 = time.perf_counter()
    neon_choice = await agent.choose_pick(
        transcript, parsed_constraints, scored_candidates
    )
    timings_ms["neon_pick_ms"] = int((time.perf_counter() - t0) * 1000)
    pick_id = neon_choice["pick_id"]
    pick_cand = next(
        (c for c in scored_candidates if c["product_id"] == pick_id),
        scored_candidates[0],
    )
    pick_id = pick_cand["product_id"]

    # 8. Decision 1 GATE 2: self-check; retry Neon once if failed or confidence < 0.7
    t0 = time.perf_counter()
    gate2 = await gates.self_check(
        transcript,
        parsed_constraints,
        pick_cand,
        neon_choice["reasons"],
        neon_choice["speech"],
    )
    timings_ms["gate2_self_check_ms"] = int((time.perf_counter() - t0) * 1000)
    if not gate2["passed"]:
        t0 = time.perf_counter()
        neon_choice = await agent.choose_pick(
            transcript,
            parsed_constraints,
            scored_candidates,
            retry_feedback=gate2.get("failure_reason") or "Ensure pick satisfies all constraints and budget.",
        )
        timings_ms["neon_retry_ms"] = int((time.perf_counter() - t0) * 1000)
        pick_id = neon_choice["pick_id"]
        pick_cand = next(
            (c for c in scored_candidates if c["product_id"] == pick_id),
            scored_candidates[0],
        )
        pick_id = pick_cand["product_id"]

    # Assemble public candidates (put pick or keep order with is_pick marked)
    public_cands = [
        _public_candidate(c, is_pick=(c["product_id"] == pick_id))
        for c in scored_candidates[:5]
    ]

    # Check if the offer changed compared to previously displayed offer; if so, invalidate any old handoff
    prev_sig = state.get("_offer_signature")
    new_sig = (
        pick_cand["seller"]["domain"],
        pick_cand["variant_id"],
        int(pick_cand["price_minor"]),
    )
    if prev_sig and prev_sig != new_sig and state.get("handoff") is not None:
        # Offer changed after a previous handoff -> require fresh approval
        state["_stale_pick_pending"] = False

    offer_id = make_offer_id(pick_cand)
    state["_raw_candidates"] = scored_candidates[:5]
    state["_offer_signature"] = new_sig
    state["_stale_pick_pending"] = False
    state["phase"] = "pick"
    state["constraints"] = constraints_state
    state["candidates"] = public_cands
    state["pick"] = {
        "product_id": pick_id,
        "variant_id": pick_cand["variant_id"],
        "price_minor": int(pick_cand["price_minor"]),
        "offer_id": offer_id,
        "reasons": neon_choice["reasons"][:3],
    }
    # Clear any previous checkout handoff whenever a new utterance updates the pick/constraints
    state["handoff"] = None
    state["history"].append(
        {"t": int(time.time()), "text": transcript, "did_research": did_research}
    )
    state["updated_at"] = int(time.time())

    reply_obj = {
        "speech": neon_choice["speech"],
        "pick_id": pick_id,
        "variant_id": pick_cand["variant_id"],
        "price_minor": int(pick_cand["price_minor"]),
        "offer_id": offer_id,
        "did_research": did_research,
    }
    if audio_bytes:
        reply_obj["transcript"] = transcript
    await _attach_tts_if_needed(
        reply_obj, neon_choice["speech"], should_tts=should_tts, timings_ms=timings_ms
    )
    timings_ms["total_ms"] = int((time.perf_counter() - t_start) * 1000)
    reply_obj["timings_ms"] = timings_ms
    logger.info("utterance_timings_ms=%s", timings_ms)
    _record_state_reply(state, reply_obj)

    return {"session_id": state["session_id"], "reply": reply_obj}
