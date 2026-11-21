# agent-backend/AGENTS.md

Owner: see STATE.md (default Antigravity). Read root AGENTS.md first.

## What this module is

A small HTTP server (Python 3.14 + FastAPI, or Node 24 + Hono; pick one in the first commit and write it here) that:
1. Serves the API in docs/INTERFACES.md section 1.
2. Runs a Gemini managed agent (Interactions API) with the three tools in section 3.
3. Calls Shopify per section 2.
4. Holds session state in memory. No database.

Stack decision: ______ (fill in, first commit).

## Build order

1. `GET /health`, `POST /utterance` with a hard-coded search (no Gemini), `GET /state`. Run `scripts/smoke_backend.sh`. Commit.
2. Gemini managed agent with `shop_search` only. Structured output. Re-search on "under two hundred" must work with a typed utterance before voice exists.
3. `POST /intent` -> `create_checkout` on Shop MCP. `continue_url` into state only.
4. `stale_pick` rule, `POST /session/clear`, redaction.
5. Audio in (PENDING P3a) if time allows.

## Hard rules (module-specific)

- `continue_url` and checkout `id` never appear in: logs, stdout, error messages, `/intent` responses, device responses. One redaction helper, used everywhere. Test it.
- Budget math is in minor units. `"$300"` -> `30000`.
- Pass `seller.domain` and `variant.id` to checkout exactly as the Catalog returned them.
- The agent proposes; the shopper approves on their phone. Never call `complete_checkout`.
- If the pick changes after intent was signalled, require a fresh intent (`stale_pick`).
- `GEMINI_API_KEY` from environment only. Fail loudly at boot if missing.
- Catalog and Shop MCP calls get a 10 s timeout. On 429 honour `Retry-After`.
- Speech replies under 45 words, plain English, no markdown, no URLs.

## The agent prompt (`prompts/shop_counter.md`)

Must include: the glossary terms, the three tools, the rule "re-search whenever a constraint changes", the output schema, the "Do not claim" list from BRIEF.md, and "explain the pick in two sentences a person would say out loud". Grill Tolu with `/grill-me` on tone before writing it.

## Smoke

`scripts/smoke_backend.sh` against `localhost:8787`. Must pass before every commit that touches routes.
