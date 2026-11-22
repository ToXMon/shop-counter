# Shop Counter

Shop Counter is a voice-first shopping counter for independent Shopify sellers.
Hold the M5Stack CoreS3 to ask for something, hear and see the pick on the Mac,
tap the device to request checkout, and scan a QR to review on your own phone.

Gemini 4 NYC Hackathon · Nov 21, 2026 · Problem Statement Two: Element 119
Public repo: https://github.com/ToXMon/shop-counter
1-Minute Demo Video: `https://youtu.be/QMoHmjNEPio?feature=shared`

## How it works

1. **Talk to the CoreS3.** Hold the device to state an utterance, then change a
   constraint out loud ("under two hundred" or "something digital under a
   dollar"). The agent runs a live re-search when constraints change. Broader
   discovery queries Shopify's live catalog; the Monday Cartoons Digital Sticker
   resolves from the seller's live storefront.
2. **Mac speaks and shows the pick.** The Mac speaks the reply aloud while the
   companion screen displays candidates, the pick, seller, live price, and
   reasons. The device is the primary interface; the companion screen is a
   read-only window into session state, not a second set of shopping controls.
3. **Tap the device to request checkout.** Tap the center of the CoreS3 to send
   physical buy intent for the displayed pick. **The tap never charges anyone**,
   and voice alone never creates a checkout.
4. **Scan a QR and review on your own phone.** Shop MCP creates a checkout
   without shopper sign-in and returns a `continue_url` to the backend. The
   companion screen renders a QR handoff; the shopper scans it to review the
   seller, item, quantity, and total on their own phone.

**Trust boundary:** The device never handles payment cards, credentials, or
`continue_url` (which stays in backend/companion state and is redacted from
logs). Phone review is the authorization boundary: if seller, items, or total
change, fresh intent is required, and sessions clear between shoppers.

## What job does each model do?

| Model | Role |
| --- | --- |
| **Gemini 4 Hydrogen** | Extracts shopping constraints from the transcript and summarizes candidates. |
| **Gemini 4 Neon** | Compares the candidates, picks a product, and explains the recommendation. |
| **Gemini Decision 1** | Routes requests, identifies when clarification is needed, scores candidate fit, and checks the recommendation against the shopper's constraints. |
| **Gemini 3.5 Transcribe** | Turns short CoreS3 recordings into text. |
| **Gemini 3.8 Flash TTS** | Tested as an optional speech path; the demo uses local Mac speech. |

**Managed Agent (off-path audit):** An Antigravity Managed Agent completed an
off-path hosted evaluation audit of our eval numbers outside the live shopping
flow. It is an offline auditor, not part of the live request path.

## Architecture and module status

```text
[Shopper] --voice / tap--> [M5Stack CoreS3] --POST /utterance, /intent--> [agent-backend]
                                                                             |        |
          [companion-screen] <----------------GET /state---------------------+        v
          (cards, reasons, QR handoff;                             Gemini 4 + Decision 1
           Mac speaks reply aloud)                                 Shopify Catalog & Shop MCP
```

Build-lane implementations live on sibling branches and are **being merged** into
this integration checkout:

- `device/` *(firmware being merged; `device/smoke_http.sh` present)* — CoreS3
  thin client for push-to-talk audio, center-tap intent, and short status text.
- `agent-backend/` *(being merged)* — Session state, Gemini 4 + Decision 1
  pipeline, Shopify Catalog and Shop MCP tools, and the `eval/` harness +
  Managed Agent audit report.
- `companion-screen/` *(being merged)* — Web app polling `GET /state` to render
  the transaction flow, candidate cards, pick reasons, QR handoff, and Clear.
- Docs and contracts in this checkout: `BRIEF.md`, `docs/INTERFACES.md`,
  `docs/DEMO.md`, `docs/SUBMISSION.md`.

## Verified evidence and honest limits

- **Live discovery and phone handoff:** Anonymous Shopify Catalog search works
  live (`scripts/smoke_catalog.sh`). For the Monday Cartoons Digital Sticker
  (sourced from the seller's live storefront), Shop MCP created a live checkout
  that was scanned and reviewed on a phone. **We stopped before payment; no
  purchase was completed.**
- **No guaranteed latency:** Multi-step voice turns have variable response time.
  Across three replay runs per condition using the same recorded WAV, mean time
  from backend audio receipt to reply ready dropped from 34.48 s to 23.44 s
  after honoring the TTS opt-out (single TTS-enabled control: 5.55 s for TTS).
  These are WAV replay measurements, not live voice guarantees.
- **Fixtures vs. live:** Checks run against `scripts/stub_backend.py` validate
  API contracts on canned fixtures only and are never claimed as live runs.

## Run the checks in this checkout

Until the build-lane branches finish merging, this checkout runs the live
catalog check and contract smoke suite directly:

```sh
cp .env.example .env             # local config only; .env stays untracked
scripts/smoke_catalog.sh         # live Shopify Catalog search (no API key)
python3 scripts/stub_backend.py  # stub backend on 127.0.0.1:8787 (fixture data)
scripts/smoke_backend.sh         # verifies HTTP contract shapes
device/smoke_http.sh             # verifies device utterance + intent seams
```
