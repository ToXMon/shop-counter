"""Managed Agent sandbox evaluation runner (`antigravity-preview-09-2026` on v1beta).

Kept strictly off the live request path. Launches a Google-hosted remote Linux
sandbox to audit the evaluation results and reports completion status honestly.
"""
from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

import models
from shop import redact_sensitive

_EVAL_DIR = Path(__file__).resolve().parent


def run_hosted_audit(timeout_s: int = 90) -> dict[str, Any]:
    """Run an off-path audit interaction in the Google-hosted Antigravity Managed Agent sandbox."""
    beta_client = models.get_beta_client()
    report_path = _EVAL_DIR / "REPORT.md"
    report_text = report_path.read_text() if report_path.is_file() else "No REPORT.md yet."

    prompt = (
        "You are running inside a Google-hosted Linux sandbox as the Shop Counter eval auditor.\n"
        "Write a short Python script `audit_eval.py` that verifies the summary statistics in the "
        "following evaluation report table, runs it with `python3 audit_eval.py`, and prints the "
        "verified delta between system and baseline scores.\n\n"
        f"{report_text}"
    )
    try:
        interaction = beta_client.interactions.create(
            agent=models.MANAGED_AGENT_ID,
            environment="remote",
            agent_config={
                "type": "antigravity",
                "model": models.WORKER_MODEL,
                "max_total_tokens": 50000,
            },
            input=prompt,
        )
        deadline = time.time() + timeout_s
        while interaction.status in ("in_progress", "queued") and time.time() < deadline:
            time.sleep(3)
            interaction = beta_client.interactions.get(interaction.id)

        result = {
            "completed": interaction.status == "completed",
            "status": interaction.status,
            "interaction_id": interaction.id,
            "environment_id": getattr(interaction, "environment_id", None),
            "output_text": (interaction.output_text or "")[:600],
        }
        (_EVAL_DIR / "MANAGED_RUN.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    except Exception as exc:
        err = {
            "completed": False,
            "status": "error",
            "error": f"{type(exc).__name__}: {redact_sensitive(str(exc))[:240]}",
        }
        (_EVAL_DIR / "MANAGED_RUN.json").write_text(json.dumps(err, indent=2) + "\n")
        return err


if __name__ == "__main__":
    print(json.dumps(run_hosted_audit(), indent=2))
