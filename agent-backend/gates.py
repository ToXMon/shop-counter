"""Gemini Decision 1 gates (`gemini-decision-1` via v1beta Decisions API).

Follows docs/INTERFACES.md section 3 and agent-backend/AGENTS.md:
- GATE 1 (`classify_utterance`): choice question with explicit `other` key + clarification gate; branches on confidence < 0.7.
- SCORE (`score_candidates`): ordered rubric scoring (0..1) across all candidates in a single forward pass.
- GATE 2 (`self_check`): yes/no (`noul`) self-check + deterministic budget check; triggers Neon retry if no or confidence < 0.7.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

import models
from shop import redact_sensitive

logger = logging.getLogger("shop_counter.gates")

CONFIDENCE_THRESHOLD = 0.70


def _heuristic_classify(text: str, has_history: bool) -> dict[str, Any]:
    low = text.strip().lower()
    if not low or len(low) < 2:
        return {
            "kind": "other",
            "confidence": 0.9,
            "needs_clarification": True,
            "did_research": False,
        }
    buy_phrases = ("i'll take it", "i will take it", "buy it", "buy this", "want to buy", "checkout", "get this one")
    if any(p in low for p in buy_phrases) and has_history:
        return {
            "kind": "buy_intent",
            "confidence": 0.85,
            "needs_clarification": False,
            "did_research": False,
        }
    if has_history:
        return {
            "kind": "constraint_change",
            "confidence": 0.85,
            "needs_clarification": False,
            "did_research": True,
        }
    return {
        "kind": "new_search",
        "confidence": 0.85,
        "needs_clarification": False,
        "did_research": False,
    }


def _classify_sync(
    text: str,
    history: list[dict[str, Any]],
    current_constraints: dict[str, Any] | None,
) -> dict[str, Any]:
    has_history = bool(history)
    context_str = json.dumps(
        {
            "has_prior_turns": has_history,
            "prior_constraints": current_constraints or {},
            "recent_history": [h.get("text", "") for h in history[-3:]],
            "latest_utterance": text,
        }
    )
    beta_client = models.get_beta_client()
    decision = beta_client.decisions.create(
        model=models.DECISION_MODEL,
        input=f"Shopper turn context:\n{context_str}",
        questions={
            "utterance_kind": {
                "type": "choice",
                "instructions": (
                    "Classify the shopper's latest utterance in the context of the shopping session."
                ),
                "criteria": {
                    "buy_intent": "The shopper is asking to buy or check out the currently recommended pick right now.",
                    "constraint_change": "There are prior turns and the shopper is changing or adding a constraint (budget, price limit, product type, digital sticker, seller, feature) or asking to search again.",
                    "new_search": "This is the first shopping request or a brand-new product search.",
                    "question_about_pick": "There is a current pick and the shopper is only asking a factual question about it without changing constraints.",
                    "other": "Greeting, noise, or completely unintelligible/unrelated utterance with no shopping product or constraint.",
                },
            },
            "needs_clarification": {
                "type": "noul",
                "instructions": (
                    "Is the utterance completely missing both a product topic and any prior session context, "
                    "such that the assistant must ask a clarifying question before searching?"
                ),
            },
        },
    )
    kind_ans = decision.answers["utterance_kind"]
    clar_ans = decision.answers["needs_clarification"]

    choice = str(getattr(kind_ans, "choice", "other"))
    conf = float(getattr(kind_ans, "confidence", 0.0))
    clar_prob = float(getattr(clar_ans, "noul", 0.0))
    clar_conf = float(getattr(clar_ans, "confidence", 0.0))

    # Deterministic overrides for clear refinements on existing sessions
    low = text.strip().lower()
    has_constraint_change_signal = bool(
        re.search(
            r"\b(under|below|cheaper|less than|instead|switch|different|another|show me|find me|two hundred|three hundred)\b|\$\d+",
            low,
        )
    )
    has_price_or_refinement = has_constraint_change_signal or bool(
        re.search(r"\b(dollar|cents?|sticker|digital|hat|shirt|print|\d+)\b", low)
    )
    if has_history and has_constraint_change_signal and choice != "buy_intent":
        choice = "constraint_change"
        conf = max(conf, 0.85)
    elif has_history and has_price_or_refinement and choice not in ("buy_intent", "question_about_pick"):
        choice = "constraint_change"
        conf = max(conf, 0.85)
    elif not has_history and choice == "constraint_change":
        choice = "new_search"

    needs_clarification = False
    if not has_history and not has_price_or_refinement:
        if (choice == "other" and conf >= CONFIDENCE_THRESHOLD) or (
            clar_prob >= 0.70 and clar_conf >= CONFIDENCE_THRESHOLD
        ):
            needs_clarification = True
        elif conf < CONFIDENCE_THRESHOLD and len(low.split()) <= 2 and low in ("hi", "hello", "hey", "help", "um", "uh"):
            needs_clarification = True

    did_research = bool(has_history and choice in ("constraint_change", "new_search"))
    return {
        "kind": choice,
        "confidence": conf,
        "needs_clarification": needs_clarification,
        "clarification_probability": clar_prob,
        "did_research": did_research,
        "low_confidence_escalated": conf < CONFIDENCE_THRESHOLD,
    }


async def classify_utterance(
    text: str,
    history: list[dict[str, Any]],
    current_constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run GATE 1 (Decision 1) to classify the utterance and check if clarification is needed."""
    try:
        return await asyncio.to_thread(
            _classify_sync, text, history, current_constraints
        )
    except Exception as exc:
        logger.warning("GATE 1 fallback: %s", redact_sensitive(str(exc)))
        return _heuristic_classify(text, bool(history))


def _score_candidates_sync(
    utterance: str,
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
    summaries: list[str] | None = None,
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    beta_client = models.get_beta_client()
    cand_lines = []
    questions: dict[str, Any] = {}
    for idx, c in enumerate(candidates):
        key = f"cand_{idx}"
        summary_txt = summaries[idx] if summaries and idx < len(summaries) else ""
        cand_lines.append(
            f"[{key}] title={c['title']!r}, price_minor={c['price_minor']} ({c['currency']}), "
            f"seller={c['seller']['name']!r} ({c['seller']['domain']}), "
            f"rating={c.get('rating')}, requires_shipping={c.get('requires_shipping')}, "
            f"summary={summary_txt!r}"
        )
        questions[key] = {
            "type": "score",
            "instructions": (
                f"How well does candidate [{key}] ({c['title']}) satisfy the shopper's request "
                f"and constraints ({json.dumps(constraints)})?"
            ),
            "criteria": [
                "Poor match: wrong product type or violates budget/must-have constraints.",
                "Partial match: fits the general category and budget, but misses a stated preference.",
                "Strong match: directly matches the requested product, seller/type preferences, and stays within budget.",
            ],
        }

    shared_input = (
        f"Shopper utterance: {utterance}\n"
        f"Parsed constraints: {json.dumps(constraints)}\n"
        "Candidates:\n" + "\n".join(cand_lines)
    )
    decision = beta_client.decisions.create(
        model=models.DECISION_MODEL,
        input=shared_input,
        questions=questions,
    )

    scored: list[dict[str, Any]] = []
    budget_max = constraints.get("budget_max_minor")
    for idx, c in enumerate(candidates):
        key = f"cand_{idx}"
        ans = decision.answers.get(key)
        # 3 criteria -> raw score in [0, 2]; normalize to [0, 1]
        raw_score = (float(getattr(ans, "score", 1.0)) / 2.0) if ans else 0.5
        conf = float(getattr(ans, "confidence", 0.5)) if ans else 0.5
        if budget_max is not None and c["price_minor"] > int(budget_max):
            raw_score = min(raw_score, 0.1)
        item = dict(c)
        item["decision_score"] = round(raw_score, 4)
        item["decision_confidence"] = round(conf, 4)
        if summaries and idx < len(summaries):
            item["fit_summary"] = summaries[idx]
        scored.append(item)
    return scored


async def score_candidates(
    utterance: str,
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
    summaries: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Run SCORE gate (Decision 1) across all candidates in one call."""
    if not candidates:
        return []
    try:
        return await asyncio.to_thread(
            _score_candidates_sync, utterance, constraints, candidates, summaries
        )
    except Exception as exc:
        logger.warning("SCORE gate fallback: %s", redact_sensitive(str(exc)))
        out = []
        for idx, c in enumerate(candidates):
            item = dict(c)
            item["decision_score"] = 0.75
            item["decision_confidence"] = 0.75
            if summaries and idx < len(summaries):
                item["fit_summary"] = summaries[idx]
            out.append(item)
        return out


def _self_check_sync(
    utterance: str,
    constraints: dict[str, Any],
    pick: dict[str, Any],
    reasons: list[str],
    speech: str,
) -> dict[str, Any]:
    budget_max = constraints.get("budget_max_minor")
    budget_ok = True
    if budget_max is not None and int(pick.get("price_minor", 0)) > int(budget_max):
        budget_ok = False

    beta_client = models.get_beta_client()
    check_input = (
        f"Shopper utterance: {utterance}\n"
        f"Constraints: {json.dumps(constraints)}\n"
        f"Chosen pick: {json.dumps({k: v for k, v in pick.items() if k != 'checkout_url'})}\n"
        f"Reasons: {json.dumps(reasons)}\n"
        f"Spoken reply: {speech}"
    )
    decision = beta_client.decisions.create(
        model=models.DECISION_MODEL,
        input=check_input,
        questions={
            "satisfies_constraints": {
                "type": "noul",
                "instructions": (
                    "Does the chosen pick satisfy the shopper's stated constraints and is the spoken "
                    "explanation accurate to the candidate's title, seller, and price?"
                ),
            }
        },
    )
    ans = decision.answers["satisfies_constraints"]
    prob = float(getattr(ans, "noul", 0.8))
    conf = float(getattr(ans, "confidence", 0.8))
    passed = budget_ok and prob >= 0.5 and conf >= CONFIDENCE_THRESHOLD
    reason = None
    if not budget_ok:
        reason = f"Pick price {pick.get('price_minor')} exceeds budget_max_minor {budget_max}."
    elif prob < 0.5 or conf < CONFIDENCE_THRESHOLD:
        reason = f"Decision 1 self-check flagged pick (noul={prob:.2f}, confidence={conf:.2f})."
    return {
        "passed": passed,
        "budget_ok": budget_ok,
        "probability": round(prob, 4),
        "confidence": round(conf, 4),
        "failure_reason": reason,
    }


async def self_check(
    utterance: str,
    constraints: dict[str, Any],
    pick: dict[str, Any],
    reasons: list[str],
    speech: str,
) -> dict[str, Any]:
    """Run GATE 2 (Decision 1) self-check on Neon's pick and explanation."""
    try:
        return await asyncio.to_thread(
            _self_check_sync, utterance, constraints, pick, reasons, speech
        )
    except Exception as exc:
        logger.warning("GATE 2 fallback: %s", redact_sensitive(str(exc)))
        budget_max = constraints.get("budget_max_minor")
        budget_ok = budget_max is None or int(pick.get("price_minor", 0)) <= int(budget_max)
        return {
            "passed": budget_ok,
            "budget_ok": budget_ok,
            "probability": 0.8 if budget_ok else 0.0,
            "confidence": 0.8,
            "failure_reason": None if budget_ok else "Pick exceeds stated budget.",
        }
