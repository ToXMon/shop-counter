"""Gemini 4 Neon shopper advocate agent (`gemini-4-neon` via Interactions API).

Follows docs/INTERFACES.md section 3 and agent-backend/AGENTS.md:
- Structured output `{pick_id, reasons: string[3], speech: string}`.
- `speech` is plain English, no markdown/URLs, prices spoken as words, strictly <= 45 words.
- No temperature/top-p/top-k/thinking-budget fields, no `minimal` thinking level.
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
import re
from typing import Any

from pydantic import BaseModel, Field

import models
from shop import dollars_to_minor, minor_to_spoken, redact_sensitive

logger = logging.getLogger("shop_counter.agent")

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_NEON_PROMPT = (_PROMPTS_DIR / "neon_agent.md").read_text()


class AgentPickOutput(BaseModel):
    pick_id: str = Field(description="Exact product_id of the chosen candidate from the candidates list.")
    reasons: list[str] = Field(
        description="Three concise factual reasons grounded in the candidate's price, merchant, rating, or attributes."
    )
    speech: str = Field(
        description="Plain English spoken recommendation under 45 words, with prices written as words and no markdown or URLs."
    )


def sanitize_speech(speech: str, max_words: int = 44) -> str:
    """Strip markdown/URLs, convert dollar figures to words, and cap at max_words."""
    cleaned = re.sub(r"https?://\S+", "", speech)
    cleaned = re.sub(r"[*_`#>\[\]]", "", cleaned)

    # Convert any leftover $X.XX or $X into spoken words
    def _replace_dollar(match: re.Match[str]) -> str:
        raw = match.group(1).replace(",", "")
        try:
            minor = dollars_to_minor(raw)
            return minor_to_spoken(minor)
        except Exception:
            return match.group(0)

    cleaned = re.sub(r"\$(\d+(?:,\d{3})*(?:\.\d{1,2})?)", _replace_dollar, cleaned)
    cleaned = " ".join(cleaned.split())
    words = cleaned.split()
    if len(words) > max_words:
        truncated = " ".join(words[:max_words]).rstrip(",;:")
        if not truncated.endswith((".", "!", "?")):
            truncated += "."
        return truncated
    return cleaned


def _deterministic_pick_fallback(
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    best = max(
        candidates,
        key=lambda c: (
            1 if ("sticker" in str(constraints.get("query", "")).lower() and "sticker" in c["title"].lower()) else 0,
            float(c.get("decision_score", 0.5)),
            -int(c.get("price_minor", 0)),
        ),
    )
    spoken_price = minor_to_spoken(int(best["price_minor"]))
    seller_name = best["seller"]["name"]
    reasons = [
        f"Priced at ${best['price_minor'] / 100:.2f} from {seller_name}",
        (
            "Instant digital download, no shipping required"
            if best.get("requires_shipping") is False
            else f"Fits your {constraints.get('query') or 'shopping'} search criteria"
        ),
        (
            f"Rated {best['rating']['value']} stars across {best['rating']['count']} reviews"
            if isinstance(best.get("rating"), dict) and best["rating"].get("value")
            else f"Available now from verified merchant {seller_name}"
        ),
    ]
    speech = sanitize_speech(
        f"I recommend the {best['title']} from {seller_name} for {spoken_price}. "
        f"{reasons[1]}. Tap the button or badge when you are ready to review on your phone."
    )
    return {
        "pick_id": best["product_id"],
        "reasons": reasons[:3],
        "speech": speech,
    }


def _choose_pick_sync(
    utterance: str,
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
    retry_feedback: str | None = None,
) -> dict[str, Any]:
    client = models.get_client()
    safe_candidates = [
        {
            "product_id": c["product_id"],
            "title": c["title"],
            "price_minor": c["price_minor"],
            "spoken_price": minor_to_spoken(int(c["price_minor"])),
            "currency": c["currency"],
            "seller": c["seller"],
            "rating": c.get("rating"),
            "requires_shipping": c.get("requires_shipping"),
            "fit_summary": c.get("fit_summary", ""),
            "decision_score": c.get("decision_score", 0.5),
        }
        for c in candidates
    ]
    payload: dict[str, Any] = {
        "utterance": utterance,
        "constraints": constraints,
        "candidates": safe_candidates,
    }
    if retry_feedback:
        payload["self_check_failure_to_fix"] = retry_feedback

    interaction = client.interactions.create(
        model=models.AGENT_MODEL,
        system_instruction=_NEON_PROMPT,
        input=json.dumps(payload),
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": AgentPickOutput.model_json_schema(),
        },
        generation_config={"thinking_level": "medium"},
    )
    parsed = AgentPickOutput.model_validate_json(interaction.output_text or "{}")
    valid_ids = {c["product_id"] for c in candidates}
    pick_id = parsed.pick_id if parsed.pick_id in valid_ids else candidates[0]["product_id"]

    # If the shopper explicitly asked for the Digital Sticker and it's in candidates, ensure it is selected
    q_low = f"{utterance} {constraints.get('query', '')}".lower()
    if "sticker" in q_low:
        for c in candidates:
            if "sticker" in c["title"].lower():
                pick_id = c["product_id"]
                break

    reasons = [str(r).strip() for r in (parsed.reasons or []) if str(r).strip()][:3]
    while len(reasons) < 3:
        reasons.append("Verified merchant listing matching your constraints")

    speech = sanitize_speech(parsed.speech)
    if not speech:
        fallback = _deterministic_pick_fallback(constraints, candidates)
        speech = fallback["speech"]

    return {
        "pick_id": pick_id,
        "reasons": reasons,
        "speech": speech,
    }


async def choose_pick(
    utterance: str,
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
    retry_feedback: str | None = None,
) -> dict[str, Any]:
    """Use Gemini 4 Neon to choose the best pick from scored candidates."""
    if not candidates:
        return {
            "pick_id": None,
            "reasons": [],
            "speech": "I could not find any matching products under that budget. Want to try a higher budget or another search?",
        }
    try:
        return await asyncio.to_thread(
            _choose_pick_sync, utterance, constraints, candidates, retry_feedback
        )
    except Exception as exc:
        logger.warning("Neon choose_pick fallback: %s", redact_sensitive(str(exc)))
        return _deterministic_pick_fallback(constraints, candidates)
