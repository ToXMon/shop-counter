"""Baseline model runner for Shop Counter evaluation.

Per docs/INTERFACES.md section 3:
One `gemini-4-neon` call with the raw transcript and raw top-5 catalog JSON,
no Hydrogen workers, no Decision 1 gates.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

import agent
import models
import shop


def _baseline_sync(utterance: str, raw_candidates: list[dict[str, Any]]) -> dict[str, Any]:
    client = models.get_client()
    safe_cands = [
        {k: v for k, v in c.items() if k != "checkout_url"}
        for c in raw_candidates[:5]
    ]
    prompt = json.dumps(
        {
            "utterance": utterance,
            "catalog_top_5": safe_cands,
        }
    )
    interaction = client.interactions.create(
        model=models.AGENT_MODEL,
        system_instruction=(
            "Choose one product_id from catalog_top_5 for the shopper's utterance, "
            "give 3 short reasons, and a spoken response under 45 words."
        ),
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": agent.AgentPickOutput.model_json_schema(),
        },
        generation_config={"thinking_level": "medium"},
    )
    parsed = agent.AgentPickOutput.model_validate_json(interaction.output_text or "{}")
    valid_ids = {c["product_id"] for c in safe_cands}
    pick_id = parsed.pick_id if parsed.pick_id in valid_ids else (safe_cands[0]["product_id"] if safe_cands else None)
    pick_cand = next((c for c in safe_cands if c["product_id"] == pick_id), safe_cands[0] if safe_cands else None)
    return {
        "pick_id": pick_id,
        "pick": pick_cand,
        "reasons": parsed.reasons[:3],
        "speech": agent.sanitize_speech(parsed.speech),
    }


async def run_baseline(utterance: str) -> dict[str, Any]:
    """Run unfiltered catalog search + single Neon call without Hydrogen or Decision 1."""
    raw_candidates = await shop.search_catalog(query=utterance, budget_max_minor=None, limit=5)
    if not raw_candidates:
        return {"pick_id": None, "pick": None, "reasons": [], "speech": "No products found."}
    return await asyncio.to_thread(_baseline_sync, utterance, raw_candidates)
