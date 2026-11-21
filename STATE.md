# STATE.md - Shop Counter

Living status. Update it when you start or finish a chunk. Newest changes at the top of each list.

Last updated: 2026-11-21 12:20 EST by AdaL (orchestration setup)

## Clock

- Hackathon: Sat Nov 21, 9:00 AM - 10:00 PM EST, The Malin Chelsea.
- Tolu's target: build complete and rehearsed by **17:00 EST**. See PENDING.md P1 (official submission time still unconfirmed).
- Hour plan: BRIEF.md "Hour-by-hour plan". Cut points: BRIEF.md "Cut points".

## Owners

| Module | Owner tool | Status |
| --- | --- | --- |
| agent-backend/ | Antigravity (Gemini credits, Managed Agents) | unclaimed |
| companion-screen/ | Claude Code | unclaimed |
| device/ | Codex (or Tolu by hand) | unclaimed |
| docs/, STATE.md, PENDING.md | Tolu + whichever agent is in a session | AdaL set up |

Change an owner here before you start on a module. One agent per module at a time.

## Works (verified live)

- shop.dev Catalog `search_catalog` with no API key. `scripts/smoke_catalog.sh` runs it. "espresso machine" under $300 in US returned 749 products with price (minor units), seller, media, and a per-variant `checkout_url`. (12:12 EST)

## In flight

- (none yet; claim here with `- module: chunk - tool - HH:MM`)

## Next (ordered, from BRIEF.md)

1. agent-backend: `POST /utterance` with a typed string -> real catalog search -> JSON per docs/INTERFACES.md. No Gemini yet. (vertical slice)
2. companion-screen: poll `GET /state` and render one product card from the slice.
3. agent-backend: Gemini managed agent with `shop_search`, `create_cart`, `create_checkout` tools. Re-search on "under two hundred". Spoken explanation text.
4. agent-backend: `POST /intent {type: "buy"}` -> `create_checkout` via Shop MCP -> `continue_url` into state (never logged).
5. companion-screen: QR of `continue_url`, transaction-flow view.
6. device: push-to-talk voice -> `POST /utterance`; TTS of `reply.speech`; badge/button -> `POST /intent`.
7. Hardening: fresh approval on cart change, log redaction, session clear.
8. Rehearse twice. Screen-record a backup.

## Blocked

- (none)

## Decisions made today

- 12:20 Catalog search goes direct to `https://catalog.shopify.com/api/ucp/mcp` with Shopify's sample agent profile (no key). Cart/checkout go to Shop MCP `https://mcp.shop.com/`. Publishing our own agent profile is cut unless Shopify rejects the sample at demo time.
- 12:20 Fallback if `create_checkout` fights us: the Catalog already returns a per-variant `checkout_url`. QR that instead. It is a real merchant checkout the shopper reviews on their phone. Document which path the demo uses.
