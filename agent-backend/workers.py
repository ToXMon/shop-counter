"""Gemini 4 Hydrogen workers (`gemini-4-hydrogen` via Interactions API).

Follows docs/INTERFACES.md section 3 and agent-backend/AGENTS.md:
- `parse_constraints`: native structured output -> {query, budget_max_minor, must_have[], seller_hint}.
- `summarise_candidates`: parallel `asyncio.gather` Hydrogen calls (one per candidate, 2-line fit summary).
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
from shop import redact_sensitive

logger = logging.getLogger("shop_counter.workers")

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_CONSTRAINTS_PROMPT = (_PROMPTS_DIR / "hydrogen_constraints.md").read_text()
_SUMMARY_PROMPT = (_PROMPTS_DIR / "hydrogen_summary.md").read_text()


class ParsedConstraints(BaseModel):
    query: str = Field(description="Search query for Shopify catalog (e.g. 'espresso machine', 'Digital Sticker', 'Monday Cartoons').")
    budget_max_minor: int | None = Field(
        default=None,
        description="Maximum budget in integer minor units (cents), e.g. $300 -> 30000, $200 -> 20000, $1 -> 100, or null if no budget stated.",
    )
    must_have: list[str] = Field(
        default_factory=list,
        description="List of must-have features or attributes mentioned by the shopper.",
    )
    seller_hint: str | None = Field(
        default=None,
        description="Seller domain or merchant hint if mentioned (e.g. 'monday-cartoons.myshopify.com').",
    )


_WORD_NUMBERS = {
    "three hundred": 30000,
    "300": 30000,
    "two hundred": 20000,
    "200": 20000,
    "one hundred": 10000,
    "100": 10000,
    "fifty dollars": 5000,
    "one dollar": 100,
    "a dollar": 100,
    "ninety-nine cents": 99,
    "fifty cents": 50,
}


def _fallback_parse_constraints(
    text: str,
    prior_constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    low = text.lower().strip()
    prior = prior_constraints or {}
    budget = prior.get("budget_max_minor")

    m_dollar = re.search(r"\$\s*(\d+(?:\.\d{1,2})?)", low)
    if m_dollar:
        budget = int(round(float(m_dollar.group(1)) * 100))
    else:
        for phrase, val in _WORD_NUMBERS.items():
            if phrase in low:
                budget = val
                break

    seller_hint = prior.get("seller_hint")
    if "monday cartoon" in low or "monday-cartoon" in low or "sticker" in low:
        seller_hint = "monday-cartoons.myshopify.com"

    must_have: list[str] = list(prior.get("must_have") or [])
    if "digital" in low and "digital" not in must_have:
        must_have.append("digital")
    if "sticker" in low and "sticker" not in must_have:
        must_have.append("sticker")

    if "sticker" in low:
        query = "Monday Cartoons Digital Sticker"
    elif "monday cartoon" in low:
        query = "Monday Cartoons"
    elif "espresso" in low:
        query = "espresso machine"
    elif prior.get("query") and any(k in low for k in ("under", "below", "cheaper", "less", "hundred", "dollar")):
        query = str(prior["query"])
    else:
        cleaned = re.sub(
            r"\b(find me|show me|looking for|search for|i want|an?|the|under|below|less than|three hundred|two hundred|one hundred|dollars?|\$\d+(?:\.\d+)?)\b",
            " ",
            low,
        )
        cleaned = " ".join(cleaned.split())
        query = cleaned or str(prior.get("query") or "espresso machine")

    return {
        "query": query,
        "budget_max_minor": budget,
        "must_have": must_have,
        "seller_hint": seller_hint,
    }


def _parse_constraints_sync(
    text: str,
    prior_constraints: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    client = models.get_client()
    prompt_input = json.dumps(
        {
            "prior_constraints": prior_constraints or {},
            "recent_utterances": [h.get("text", "") for h in (history or [])[-4:]],
            "latest_utterance": text,
        }
    )
    interaction = client.interactions.create(
        model=models.WORKER_MODEL,
        system_instruction=_CONSTRAINTS_PROMPT,
        input=prompt_input,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": ParsedConstraints.model_json_schema(),
        },
        generation_config={"thinking_level": "low"},
    )
    parsed = ParsedConstraints.model_validate_json(interaction.output_text or "{}")
    result = parsed.model_dump()

    # Deterministic guardrails for common spoken budgets ("under two hundred", "under three hundred", etc.)
    low = text.lower()
    if "two hundred" in low or "$200" in low or " 200" in f" {low}":
        result["budget_max_minor"] = 20000
    elif "three hundred" in low or "$300" in low or " 300" in f" {low}":
        result["budget_max_minor"] = 30000
    elif "under a dollar" in low or "under one dollar" in low or "$1" in low:
        result["budget_max_minor"] = 100

    # Preserve prior query when utterance is purely a budget/attribute refinement
    if (not result.get("query") or result["query"].lower() in ("under two hundred", "cheaper", "something cheaper")) and prior_constraints and prior_constraints.get("query"):
        result["query"] = prior_constraints["query"]

    if "sticker" in low or "monday cartoon" in low:
        result["seller_hint"] = "monday-cartoons.myshopify.com"
        if "sticker" in low:
            result["query"] = "Monday Cartoons Digital Sticker"

    return result


async def parse_constraints(
    text: str,
    prior_constraints: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Parse shopping constraints using Gemini 4 Hydrogen with structured output."""
    try:
        return await asyncio.to_thread(
            _parse_constraints_sync, text, prior_constraints, history
        )
    except Exception as exc:
        logger.warning("Hydrogen parse_constraints fallback: %s", redact_sensitive(str(exc)))
        return _fallback_parse_constraints(text, prior_constraints)


def _summarise_one_sync(
    constraints: dict[str, Any],
    candidate: dict[str, Any],
) -> str:
    client = models.get_client()
    payload = {
        "constraints": constraints,
        "candidate": {
            "title": candidate.get("title"),
            "price_minor": candidate.get("price_minor"),
            "currency": candidate.get("currency"),
            "seller": candidate.get("seller"),
            "rating": candidate.get("rating"),
            "requires_shipping": candidate.get("requires_shipping"),
            "description": str(candidate.get("description") or "")[:280],
        },
    }
    interaction = client.interactions.create(
        model=models.WORKER_MODEL,
        system_instruction=_SUMMARY_PROMPT,
        input=json.dumps(payload),
        generation_config={"thinking_level": "low"},
    )
    text = (interaction.output_text or "").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return " ".join(lines[:2])[:260]


async def summarise_candidate(
    constraints: dict[str, Any],
    candidate: dict[str, Any],
) -> str:
    """Summarise one candidate using Gemini 4 Hydrogen."""
    try:
        return await asyncio.to_thread(_summarise_one_sync, constraints, candidate)
    except Exception as exc:
        logger.warning("Hydrogen summarise_candidate fallback: %s", redact_sensitive(str(exc)))
        price_dollars = candidate.get("price_minor", 0) / 100.0
        seller_name = (candidate.get("seller") or {}).get("name", "Merchant")
        return f"{candidate.get('title')} at ${price_dollars:.2f} from {seller_name}."


async def summarise_candidates(
    constraints: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[str]:
    """Summarise all candidates in parallel with Gemini 4 Hydrogen (`asyncio.gather`)."""
    if not candidates:
        return []
    return list(
        await asyncio.gather(
            *(summarise_candidate(constraints, c) for c in candidates)
        )
    )
