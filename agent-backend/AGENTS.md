# agent-backend/AGENTS.md

Owner: see STATE.md (default Antigravity). Read root AGENTS.md, docs/INTERFACES.md section 3, and `docs/GEMINI4_BUILDER_GUIDE.pdf` first. Skills `gemini-api-dev` and `gemini-live-api-dev` are in `.agents/skills/`.

## What this module is

Python 3.14 + FastAPI + `google-genai>=3.2.0`, in a `uv venv` at `agent-backend/.venv`. It:
1. Serves the API in docs/INTERFACES.md section 1.
2. Runs the pipeline in section 3: Decision 1 gates, Hydrogen workers, Neon agent, self-check.
3. Calls Shopify per section 2.
4. Holds session state in memory. No database.
5. Ships `eval/` (see below) and a Managed Agent runner for it.

## Files (create in this order)

```
agent-backend/
  models.py          MODEL_IDS dict copied from the builder guide, p.3-4. The only place model strings live.
  shop.py            catalog search + create_checkout, redaction helper, minor-unit math
  gates.py           Decision 1 calls: classify_utterance, score_candidates, self_check
  workers.py         Hydrogen: parse_constraints, summarise_candidate (asyncio.gather)
  agent.py           Neon: choose_pick -> {pick_id, reasons[3], speech}
  pipeline.py        glue in the order of INTERFACES.md section 3
  speech.py          transcribe (gemini-3.5-transcribe), tts (gemini-3.8-flash-tts)
  main.py            FastAPI routes, CORS, session store
  prompts/           one .md per model role
  eval/              run_eval.py, baseline.py, utterances/, REPORT.md, FAILURES.md
  eval/managed.py    launches antigravity-preview-09-2026 (remote sandbox, hydrogen) to run run_eval.py and write REPORT.md
```

## Build order

1. `models.py`, `shop.py`, `main.py` with `/health`, `/utterance` (text only, hard-coded search), `/state`. `scripts/smoke_backend.sh` passes. Commit. **Target 13:15.**
2. `workers.parse_constraints` (Hydrogen, structured output) + `agent.choose_pick` (Neon). Typed "under two hundred" re-searches and changes the pick. Commit. **14:00.**
3. `gates.py`: all three Decision 1 calls wired. `did_research` comes from GATE 1. Self-check retry. Commit. **14:45.**
4. `/intent` -> `create_checkout` on Shop MCP. `continue_url` into state only. `stale_pick`. Redaction tested. Commit. **15:15.**
5. `speech.py`: multipart WAV in -> transcribe. TTS out as base64 in `reply.audio_b64` (device plays) or skip if the device uses screen text. **15:45.**
6. `eval/`: 20 attendee utterances (PENDING P8) -> system vs baseline, Decision 1 rubric, REPORT.md, FAILURES.md. `eval/managed.py` runs it in the hosted sandbox once and saves the interaction id for the pitch. **16:15.**

## Hard rules (module-specific)

- `continue_url` and checkout `id` never appear in logs, stdout, errors, `/intent` responses or device responses. One redaction helper, used everywhere. Test it.
- Budget math in minor units. `"$300"` -> `30000`.
- Pass `seller.domain` and `variant.id` exactly as the Catalog returned them.
- Never call `complete_checkout`. Voice alone never creates a checkout; a physical intent must arrive.
- `GEMINI_API_KEY` from environment only. Fail loudly at boot if missing.
- Gemini 4 calls: no temperature/top-p/top-k/thinking-budget fields. No `minimal` thinking level. Native structured output (`response_schema`), never "return JSON" in prose.
- Decisions API: always branch on `confidence`; below 0.7 escalate to Neon or ask the shopper. Use an explicit `other` key in every choice question.
- Catalog and Shop MCP calls: 10 s timeout, honour `Retry-After` on 429.
- Speech under 45 words, plain English, no markdown, no URLs, prices said as words ("thirty-eight dollars").
- Model strings only from `models.py`.

## Eval (Proof It Works, 25% of the score)

- Inputs: `eval/utterances/*.wav` or `.txt`, collected from other attendees (not written by us). Each has a budget. See PENDING P8.
- System: the full pipeline. Baseline: one Neon call with the transcript and the raw top-5 catalog JSON.
- Metric: Decision 1 rubric "Does the pick satisfy the stated constraints and is the spoken reason true to the product data?" 0..1, plus budget-respect (deterministic: `price_minor <= budget_max_minor`).
- `REPORT.md`: table per utterance, system vs baseline, mean score, budget-violation count. `FAILURES.md`: each failure, cause, what we changed.
- Run it once via the Managed Agent (`eval/managed.py`) so we can say "the agent audited itself in a Google-hosted sandbox" and show the interaction id.

## Smoke

`scripts/smoke_backend.sh` against `localhost:8787` before every commit that touches routes. `python -m eval.run_eval --limit 3` before every commit that touches `pipeline.py`.
