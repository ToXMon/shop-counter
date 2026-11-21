# docs/INTERFACES.md - contracts between modules

Cross-module work goes through these contracts. Change one only when you must, and record the change in STATE.md "Decisions made today".

All three modules can be built against this file with the others stubbed. Each contract has a smoke check an agent can run alone.

Terms are from GLOSSARY.md.

---

## 1. agent-backend HTTP API

Use `http://127.0.0.1:8787` for the laptop. JSON in, JSON out. The stub has fake data only. For live checkout, keep companion state on loopback with a same-origin UI proxy or an explicit origin allowlist. Never expose checkout-bearing state on the venue LAN. If hardware is on a private hotspot, expose only device routes there and pair them to the active session. See `docs/LAUNCH.md`.

Every response carries `session_id`. One session per shopper. `POST /session/clear` ends it.

### 1.1 `POST /utterance`

Device or companion screen sends what the shopper said.

Request:
```json
{ "session_id": "s_abc123", "text": "find me an espresso machine under three hundred dollars" }
```
`session_id` optional on the first call; the backend creates one. For audio-in (PENDING P3 option a) the device instead posts `multipart/form-data` with `audio` (WAV, 16 kHz mono) and the backend transcribes before the same pipeline.

Response (also written to state):
```json
{
  "session_id": "s_abc123",
  "reply": {
    "speech": "I'd go with the Gaggia Carezza at $199 from Whole Latte Love. It's the only one under three hundred with a real 15-bar pump and a steam wand. Want me to look cheaper?",
    "pick_id": "gid://shopify/p/...",
    "did_research": false
  }
}
```
- `speech` is what the device says aloud. Under 45 words. Plain English, no markdown.
- `did_research` is `true` when this utterance changed a constraint and triggered a new catalog search. The companion screen animates the flow on it.

### 1.2 `POST /intent`

Device sends a physical buy signal.

Request:
```json
{ "session_id": "s_abc123", "type": "buy", "source": "badge" }
```
`source` is `badge`, `button`, or `screen`.

Response:
```json
{
  "session_id": "s_abc123",
  "handoff": { "status": "ready", "merchant": "Whole Latte Love", "total_minor": 19900, "currency": "USD" },
  "reply": { "speech": "Got it. Scan the code on the screen to review and pay on your phone." }
}
```
- `handoff.status` is `ready`, `requires_escalation`, `stale_pick`, or `error`.
- `stale_pick` means the pick changed since the shopper last heard it. The backend refuses and asks the shopper to confirm again (fresh approval rule). Device speaks `reply.speech`.
- **`continue_url` is NOT in this response.** The device never receives it. It lives only in `GET /state` for the companion screen.

### 1.3 `GET /state?session_id=s_abc123`

Companion screen polls this every 500 ms (or opens `GET /state/stream` for SSE with the same body per event).

```json
{
  "session_id": "s_abc123",
  "phase": "handoff",
  "constraints": { "query": "espresso machine", "budget_max_minor": 20000, "currency": "USD", "country": "US" },
  "candidates": [
    {
      "product_id": "gid://shopify/p/...",
      "variant_id": "gid://shopify/ProductVariant/...",
      "title": "Gaggia Carezza De LUXE Espresso Machine",
      "price_minor": 19900,
      "currency": "USD",
      "image_url": "https://cdn.shopify.com/...",
      "seller": { "name": "Whole Latte Love", "domain": "wholelattelove.myshopify.com" },
      "rating": { "value": 4.6, "count": 128 },
      "is_pick": true
    }
  ],
  "pick": { "product_id": "gid://shopify/p/...", "reasons": ["Only one under budget with a 15-bar pump", "Steam wand for milk", "4.6 stars from 128 reviews"] },
  "history": [ { "t": 1763746800, "text": "find me an espresso machine under three hundred dollars", "did_research": true } ],
  "handoff": { "status": "ready", "continue_url": "https://...", "merchant": "Whole Latte Love", "total_minor": 19900, "currency": "USD", "expires_at": "2026-11-21T23:00:00Z" },
  "updated_at": 1763746812
}
```
- `phase` is one of `idle`, `listening`, `searching`, `comparing`, `pick`, `handoff`, `done`.
- `candidates` has 3 to 5 entries. The pick is in the list with `is_pick: true`.
- `handoff` is `null` until intent. When present, `continue_url` is the only place it appears in the whole system.

### 1.4 `POST /session/clear`

```json
{ "session_id": "s_abc123" }
```
Returns `{ "ok": true }`. Deletes everything, including any checkout id. Call it between shoppers. The companion screen shows a "Clear" button that calls it; the device clears on a long-press.

### 1.5 `GET /health`

`{ "ok": true, "catalog": "ok", "gemini": "ok" }`. The companion screen shows red if either is not `ok`.

### Smoke check (any agent, backend not required)

`scripts/stub_backend.py` serves canned responses for all five routes on port 8787. Companion-screen and device agents build against it. The backend agent replaces it with the real thing and keeps the same shapes; `scripts/smoke_backend.sh` asserts the shapes above against whichever is running.

---

## 2. agent-backend -> Shopify

### 2.1 Search: Catalog API (no key)

`POST https://catalog.shopify.com/api/ucp/mcp`, headers `Content-Type: application/json`, `Accept: application/json`.

```json
{
  "jsonrpc": "2.0", "id": 1, "method": "tools/call",
  "params": {
    "name": "search_catalog",
    "arguments": {
      "meta": { "ucp-agent": { "profile": "https://shopify.dev/ucp/agent-profiles/examples/2026-08-25/valid-with-capabilities.json" } },
      "catalog": {
        "query": "espresso machine",
        "context": { "address_country": "US", "currency": "USD" },
        "filters": { "price": { "max": 30000 } },
        "pagination": { "limit": 5 }
      }
    }
  }
}
```
Read `result.structuredContent`. Check `ucp.status == "success"`. Products: `products[i].title`, `.media`, `.rating`, `.variants[0]` -> `id`, `price.amount` (minor units), `seller.name`, `seller.domain`, `availability`, `checkout_url`.

Verified live 2026-11-21 12:12: `scripts/smoke_catalog.sh`.

Other tools on the same endpoint: `lookup_catalog { ids: [...] }`, `get_product { id, selected: [{name, label}] }`.

### 2.2 Cart and checkout: Shop MCP (no sign-in)

`POST https://mcp.shop.com/`, headers:
```
Content-Type: application/json
Accept: application/json, text/event-stream
MCP-Protocol-Version: 2026-07-28
Mcp-Method: tools/call
Mcp-Name: create_checkout
```
Body:
```json
{
  "jsonrpc": "2.0", "id": 2, "method": "tools/call",
  "params": {
    "name": "create_checkout",
    "arguments": {
      "shop": "<variant.seller.domain>",
      "checkout": {
        "line_items": [ { "item": { "id": "<variant.id>" }, "quantity": 1 } ],
        "context": { "address_country": "US" }
      },
      "meta": { "idempotency-key": "<uuid4>" }
    },
    "_meta": {
      "io.modelcontextprotocol/protocolVersion": "2026-07-28",
      "io.modelcontextprotocol/clientInfo": { "name": "shop-counter", "version": "0.1.0" },
      "io.modelcontextprotocol/clientCapabilities": {}
    }
  }
}
```
Read `result.structuredContent`: `id`, `status`, `totals`, `continue_url`, `expires_at`, `messages`. Do not send `meta.ucp-agent` to Shop MCP.

Rules (from shop.dev/docs/checkout):
- Create a checkout only on intent, never on interest.
- `shop` = `seller.domain` and `item.id` = `variant.id`, exactly as returned. Never rebuild IDs.
- `id` and `continue_url` contain access keys. Redact both in logs. Share `continue_url` only via `GET /state`.
- We never call `complete_checkout`. The shopper pays on their phone. Any status other than `completed` is "not purchased".
- Use `create_cart` only if we want the companion screen to show a cart before intent. Optional.

### 2.3 Fallback handoff

If `create_checkout` fails at demo time, the Catalog's per-variant `checkout_url` is a real merchant checkout. QR it. Mark `handoff.status: "ready"` and set `handoff.via: "variant_checkout_url"` so the flow view can label it honestly.

---

## 3. agent-backend -> Gemini (two Gemini 4 models + Decisions API, per the hackathon rules)

Model IDs come from `docs/GEMINI4_BUILDER_GUIDE.pdf`. Keep them in one module, `agent-backend/models.py`, never inline.

```
utterance (WAV or text)
  -> [gemini-3.5-transcribe]            WAV -> text                      (skip if text came in)
  -> [gemini-decision-1]  GATE 1        "Is this a new/changed shopping constraint, a buy intent,
                                         a question about the pick, or other?"  choice + confidence
  -> [gemini-4-hydrogen]  WORKER        parse constraints -> {query, budget_max_minor, must_have[]}   (structured output)
  -> shop_search tool (Catalog API)     candidates[]
  -> [gemini-4-hydrogen] x N in parallel  one call per candidate: fit summary (2 lines) from title+description+price
  -> [gemini-decision-1]  SCORE         rubric per candidate: "How well does this satisfy the constraints?"  0..1
  -> [gemini-4-neon]      AGENT         choose the pick from scored candidates, write reasons[] + speech (<=45 words)
  -> [gemini-decision-1]  GATE 2        self-check: "Does the pick satisfy every stated constraint?"  yes/no + confidence
                                         if no or confidence < 0.7 -> Neon retries once with the failure as input
  -> [gemini-3.8-flash-tts]             speech -> audio for the device (optional; laptop speechSynthesis is the fallback)
```

| Model | Job (one each, say it this way to judges) |
| --- | --- |
| `gemini-4-neon` | The shopper's advocate. Reasons over scored candidates, picks one, explains it in spoken English. |
| `gemini-4-hydrogen` | The fast hands. Parses constraints, summarises candidates in parallel, drafts text. |
| `gemini-decision-1` | The referee. Three gates with calibrated confidence: what kind of utterance, how well each candidate fits, does the pick pass. Zero output tokens, ~200 ms. |
| `gemini-3.5-transcribe` / `gemini-3.8-flash-tts` | Ears and mouth. |
| `antigravity-preview-09-2026` (Managed Agent, hosted sandbox, Hydrogen) | The auditor. Runs `eval/` against the baseline and writes `eval/REPORT.md`. Not in the live request path. |

Tools the agent code calls (plain functions; declare them as native tools where a model needs them):

| Tool | Args | Returns |
| --- | --- | --- |
| `shop_search` | `{ query: string, budget_max_minor?: int, country: "US", currency: "USD", limit: 5 }` | `candidates[]` as in 1.3 |
| `create_checkout` | `{ seller_domain: string, variant_id: string, quantity: 1 }` | `{ status, merchant, total_minor, currency, expires_at }` and stores `continue_url` server-side only |

Neon's structured output: `{ pick_id, reasons: string[3], speech: string }`. Hydrogen's constraint output: `{ query, budget_max_minor: int|null, must_have: string[], seller_hint: string|null }`. The backend assembles `state` from these.

Gate rules: `GATE 1 = buy_intent` with confidence >= 0.8 counts as intent only when a physical intent (badge/button) also arrived within 30 s; voice alone never creates a checkout. `GATE 1 = constraint_change` sets `did_research = true`.

Baseline for the eval: one `gemini-4-neon` call with the raw transcript and the raw top-5 catalog JSON, no Hydrogen, no gates. Same rubric scores both.

System prompts live in `agent-backend/prompts/`. They encode the hardening rules from AGENTS.md and the "Do not claim" list from BRIEF.md. Builder-guide prohibitions apply: no temperature/top-p/top-k, no `minimal` thinking level, native structured output only.

---

## 4. device -> agent-backend

The device is a thin client. It knows two URLs: `POST /utterance` and `POST /intent`. It stores `session_id` in RAM. It speaks `reply.speech`. Long-press clears the session (`POST /session/clear`) and shows "Ready".

The device never requests `/state`. It never sees `continue_url`.

Smoke check: `device/smoke_http.sh` posts both routes to the stub backend from the laptop, so firmware work can start before Wi-Fi is sorted.

---

## 5. companion-screen -> agent-backend

Polls `GET /state`. Renders:
1. Flow bar: search -> compare -> pick -> intent -> handoff, lit by `phase`.
2. Candidate cards from `candidates`, pick highlighted, `reasons` under it.
3. QR of `handoff.continue_url` when present, with merchant and total. Hide the URL text; show only the QR and "Scan to review and pay on your phone".
4. "Clear session" button -> `POST /session/clear`.
5. Fallback input: a text box that posts to `/utterance` (PENDING P3 option c) and, if time allows, a mic button using Web Speech API (option b).

Price display: `price_minor / 100` with `Intl.NumberFormat`.

Smoke check: `npm run dev` against `scripts/stub_backend.py`, confirm one card and a QR render.
