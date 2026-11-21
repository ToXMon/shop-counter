# BRIEF.md - Shop Counter

Gemini 4 NYC Hackathon, Saturday Nov 21, 2026, 9:00 AM to 10:00 PM EST, The Malin Chelsea.
Tracks: Shopify track, plus eligibility for the Best Use of Managed Agents prize ($5k).
Builder: Tolu Shekoni, solo. Tooling: Antigravity (primary, Gemini credits + Managed Agents), Claude Code, Codex in parallel.

## Problem

Shopping agents have become another chat window. The one voice-shopping device people know is tied to Amazon. Independent commerce (Shopify's million-plus merchants) has no physical, voice-first shopping interface.

## Product

Shop Counter is a physical shopping agent. You talk to it like a person. It searches Shopify's live catalog, compares options, explains its pick, and shows rich product cards and the transaction flow on a companion screen it drives. A badge tap on the device says "I want this." The actual checkout opens on the shopper's phone for review and payment. The device never sees a card, an account, or a password.

## The demo loop (this is what judges see)

1. Judge speaks to the device: "Find me an espresso machine under three hundred dollars."
2. The agent searches Shopify's live catalog, compares options, speaks its pick and why, and renders product cards on the companion screen.
3. Judge pushes back: "Under two hundred." The agent searches again. New pick, new reasons. This re-search on constraint change is the agentic beat; it must be live, not scripted.
4. Judge taps an RFID badge on the device: buy intent.
5. The backend creates a Shop checkout without any shopper sign-in and returns a `continue_url`. The companion screen shows it as a QR code; the device shows a confirmation.
6. Judge scans the QR with their own phone, reviews the real checkout, and sees they would pay there. The device held nothing sensitive.
7. Optional bonus beat: if a judge has a product with a barcode, scan it as an alternate entry point. Barcode is theater, never a dependency.

## Architecture

```
        voice                HTTP (JSON)
[Judge] <--> [M5Stack CoreS3] <---------> [agent-backend]
               |  badge tap                  |         |
               |  (intent)                   v         v
               |                       [Gemini Managed Agent]
               |                       tools: shop_search,
               |                       create_cart,
               |                       create_checkout
               |                              |
               v                              v
        [companion-screen] <---- state ---- shop.dev
         product cards, flow,                 (search, cart,
         QR for continue_url                   checkout)
```

- Device (CoreS3): voice capture and playback, badge tap via RFID, minimal display. It is a thin client: it sends utterances and intent events to the backend and speaks what the backend returns.
- agent-backend: a Gemini managed agent (Interactions API) with tools for shop.dev search, cart, and checkout. Owns session state. Serves state to the companion screen.
- companion-screen: web app (runs on a laptop or the judge's phone browser). Renders the rich product visualization and transaction flow the 2-inch device screen cannot.
- shop.dev: text search over the live catalog needs no API key. Checkout is created without shopper sign-in and handed off via `continue_url` for phone review and payment.

## Module ownership (parallel agents)

One agent per module. Confirm actual assignments in STATE.md.

- device/ - CoreS3 firmware (MicroPython or Arduino). Voice in/out, RFID read, HTTP client, QR display fallback.
- agent-backend/ - Gemini managed agent, shop tools, session state, REST API per docs/INTERFACES.md.
- companion-screen/ - web UI: product cards, comparison view, transaction-flow visualization, QR handoff.

## Hour-by-hour plan (noon to 10 PM)

Times are anchors, not promises. Cut points are ordered: cut from the bottom up.

- 12:00-12:30 Setup. Clone, .env, GEMINI_API_KEY. Verify shop.dev text search with curl. Verify Gemini Interactions API responds. STATE.md owners filled in.
- 12:30-14:00 Vertical slice, no voice: typed utterance to backend, real shop.dev search, one product rendered on companion screen.
- 14:00-16:00 Agent loop: Gemini managed agent compares options, explains a pick, re-searches on budget change. Cart + checkout creation with continue_url handoff. QR on companion screen.
- 16:00-18:00 Device: voice capture (push-to-talk is fine), speak the reply, badge tap posts intent, end-to-end with the backend.
- 18:00-19:30 Integration and the hardening controls: fresh approval on cart change, log redaction, session clearing.
- 19:30-20:30 Polish: product card visuals, transaction-flow animation, spoken explanations tightened.
- 20:30-21:15 Demo rehearsal twice, plus a screen-recorded backup of the full loop in case hardware fails live.
- 21:15-22:00 Buffer, submission, pitch.

## Cut points (in order)

1. Barcode scanning. Optional from the start.
2. On-device speech-to-text. Fallback: push-to-talk typed input on the device or a phone mic through the companion screen.
3. Rich visualization on the companion screen. Fallback: clean product cards.
4. RFID badge. Fallback: a physical button on the CoreS3 labeled TAP TO BUY.
5. Never cut: live search, agent re-search on constraint change, checkout handoff to the phone.

## Hardening rules (also in AGENTS.md; repeated here because they are demo talking points)

- Badge tap is intent, not payment authorization. The phone review is the trust boundary.
- Fresh approval required if merchant, items, or total change.
- No card, tokens, or shopper credentials on the device. Credential-bearing steps live on the backend.
- Redact checkout IDs and URLs from all logs.
- Clear each shopper session; never reuse sessions or tokens across shoppers.

## Pitch (60 seconds, keep current with reality)

Shopping agents are becoming another chat window. And the one voice-shopping device people know is tied to Amazon. Shop Counter is a physical shopping agent for independent commerce, powered by Shopify and Gemini.

You talk to it like a person. "Find me an espresso machine under three hundred." The agent searches Shopify's live catalog, compares options, and tells you its pick and why. Change your budget or reject the pick, and it goes back and searches again. That's agentic, not a recording.

The product cards and the transaction flow render on the big screen it drives. This device is the part you hold: the voice, and the physical approval moment. A badge tap says "I want this," then the actual purchase shows up on your phone to review and approve. No card, no account, no typing on the device.

The point is shopping you can touch and talk to, not another chatbot.

## Do not claim

- First-ever or only. No sponsor endorsement. No universal barcode coverage. No guaranteed savings.
- Never say the badge tap authenticates payment. It signals intent; the phone approves.
- Do not claim spend requests work for Shopify catalog products. They do not.
- If a judge pushes on crypto: "We separate shopping from payment authority. The device browses and proposes; the shopper approves on their phone. x402 could let the agent buy a specialist tool later, but it is not a substitute for Shopify checkout or a privacy guarantee."
