"""Evaluation runner: full Shop Counter pipeline vs single-call Neon baseline.

Usage:
    PYTHONPATH=agent-backend agent-backend/.venv/bin/python -m eval.run_eval --limit 3
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from eval.baseline import run_baseline
import main
import models
import pipeline

_EVAL_DIR = Path(__file__).resolve().parent
_UTTERANCES_DIR = _EVAL_DIR / "utterances"

# Seed utterances for smoke checks (`--limit 3`). Attendee utterances go in `eval/utterances/*.txt` or `*.wav`.
SEED_UTTERANCES: list[dict[str, Any]] = [
    {
        "id": "seed_01",
        "source": "seed_smoke",
        "text": "Find me an espresso machine under two hundred dollars",
        "budget_max_minor": 20000,
    },
    {
        "id": "seed_02",
        "source": "seed_smoke",
        "text": "Find me the Monday Cartoons Digital Sticker under one dollar",
        "budget_max_minor": 100,
    },
    {
        "id": "seed_03",
        "source": "seed_smoke",
        "text": "Show me a Monday Cartoons hat under fifty dollars",
        "budget_max_minor": 5000,
    },
]


def score_with_decision_rubric(
    utterance: str,
    budget_max_minor: int | None,
    pick: dict[str, Any] | None,
    speech_text: str,
) -> dict[str, Any]:
    """Score a pick + spoken explanation with `gemini-decision-1` rubric + deterministic budget check."""
    if not pick:
        return {"rubric_score": 0.0, "confidence": 1.0, "budget_ok": False}

    price_minor = int(pick.get("price_minor", 0))
    budget_ok = True if budget_max_minor is None else (price_minor <= int(budget_max_minor))

    beta_client = models.get_beta_client()
    payload = {
        "utterance": utterance,
        "budget_max_minor": budget_max_minor,
        "pick": {
            "title": pick.get("title"),
            "price_minor": price_minor,
            "seller": pick.get("seller"),
        },
        "speech": speech_text,
    }
    decision = beta_client.decisions.create(
        model=models.DECISION_MODEL,
        input=json.dumps(payload),
        questions={
            "eval_rubric": {
                "type": "score",
                "instructions": (
                    "Does the pick satisfy the stated constraints and is the spoken reason true to the product data?"
                ),
                "criteria": [
                    "Violates stated constraints or invents product facts not in the candidate data.",
                    "Partially satisfies constraints with mostly accurate product facts.",
                    "Fully satisfies stated constraints and spoken explanation is completely faithful to product data.",
                ],
            }
        },
    )
    ans = decision.answers["eval_rubric"]
    norm_score = float(getattr(ans, "score", 0.0)) / 2.0
    return {
        "rubric_score": round(norm_score, 4),
        "confidence": round(float(getattr(ans, "confidence", 0.0)), 4),
        "budget_ok": budget_ok,
    }


def load_utterances(limit: int | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if _UTTERANCES_DIR.is_dir():
        for p in sorted(_UTTERANCES_DIR.glob("*.json")):
            data = json.loads(p.read_text())
            if isinstance(data, list):
                items.extend(data)
            elif isinstance(data, dict):
                items.append(data)
    if not items:
        items = list(SEED_UTTERANCES)
    return items[:limit] if limit else items


async def evaluate_all(limit: int | None = None) -> dict[str, Any]:
    utterances = load_utterances(limit=limit)
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for item in utterances:
        u_id = item["id"]
        text = item["text"]
        budget = item.get("budget_max_minor")

        # Full system run
        st = main.fresh_session(f"s_eval_{u_id}")
        sys_out = await pipeline.run_utterance_pipeline(st, text=text, include_tts=False)
        sys_pick_id = sys_out["reply"]["pick_id"]
        sys_pick = next((c for c in st["candidates"] if c["product_id"] == sys_pick_id), None)
        sys_score = await asyncio.to_thread(
            score_with_decision_rubric, text, budget, sys_pick, sys_out["reply"]["speech"]
        )

        # Baseline run
        base_out = await run_baseline(text)
        base_score = await asyncio.to_thread(
            score_with_decision_rubric, text, budget, base_out["pick"], base_out["speech"]
        )

        row = {
            "id": u_id,
            "source": item.get("source", "attendee"),
            "text": text,
            "budget_max_minor": budget,
            "system_pick": (sys_pick or {}).get("title"),
            "system_price_minor": (sys_pick or {}).get("price_minor"),
            "system_score": sys_score["rubric_score"],
            "system_budget_ok": sys_score["budget_ok"],
            "baseline_pick": (base_out.get("pick") or {}).get("title"),
            "baseline_price_minor": (base_out.get("pick") or {}).get("price_minor"),
            "baseline_score": base_score["rubric_score"],
            "baseline_budget_ok": base_score["budget_ok"],
        }
        rows.append(row)

        if not sys_score["budget_ok"] or sys_score["rubric_score"] < 0.7:
            failures.append({"side": "system", **row})
        if not base_score["budget_ok"] or base_score["rubric_score"] < 0.7:
            failures.append({"side": "baseline", **row})

    sys_mean = round(sum(r["system_score"] for r in rows) / max(1, len(rows)), 4)
    base_mean = round(sum(r["baseline_score"] for r in rows) / max(1, len(rows)), 4)
    sys_violations = sum(0 if r["system_budget_ok"] else 1 for r in rows)
    base_violations = sum(0 if r["baseline_budget_ok"] else 1 for r in rows)

    report_lines = [
        "# Evaluation Report — Shop Counter (System vs Single-Call Neon Baseline)",
        "",
        f"- Utterance count: {len(rows)} (sources: { sorted({r['source'] for r in rows}) })",
        f"- System mean Decision 1 rubric score: **{sys_mean:.3f}** (budget violations: **{sys_violations}**)",
        f"- Baseline mean Decision 1 rubric score: **{base_mean:.3f}** (budget violations: **{base_violations}**)",
        "",
        "| ID | Source | Utterance | System Pick (minor) | Sys Score | Sys Budget OK | Baseline Pick (minor) | Base Score | Base Budget OK |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        report_lines.append(
            f"| {r['id']} | {r['source']} | {r['text']} | {r['system_pick']} ({r['system_price_minor']}) | "
            f"{r['system_score']:.2f} | {r['system_budget_ok']} | {r['baseline_pick']} ({r['baseline_price_minor']}) | "
            f"{r['baseline_score']:.2f} | {r['baseline_budget_ok']} |"
        )
    (_EVAL_DIR / "REPORT.md").write_text("\n".join(report_lines) + "\n")

    failure_lines = [
        "# Evaluation Failures & Root Causes",
        "",
    ]
    if not failures:
        failure_lines.append("No system failures observed on the current utterance set.")
    else:
        for f in failures:
            failure_lines.append(
                f"- **{f['id']} ({f['side']})**: utterance=`{f['text']}` -> pick=`{f.get(f['side'] + '_pick')}` "
                f"(price_minor={f.get(f['side'] + '_price_minor')}, budget_max_minor={f['budget_max_minor']}, "
                f"score={f.get(f['side'] + '_score')}, budget_ok={f.get(f['side'] + '_budget_ok')})"
            )
    (_EVAL_DIR / "FAILURES.md").write_text("\n".join(failure_lines) + "\n")

    return {
        "count": len(rows),
        "system_mean_score": sys_mean,
        "baseline_mean_score": base_mean,
        "system_budget_violations": sys_violations,
        "baseline_budget_violations": base_violations,
        "rows": rows,
    }


def main_cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()
    summary = asyncio.run(evaluate_all(limit=args.limit))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main_cli()
