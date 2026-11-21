# STATE.md - Shop Counter

Living status. Update it when you start or finish a chunk. Newest at the top of each list.

Last updated: 2026-11-21 12:45 EST by AdaL

## Clock (confirmed from the participant guide)

- **17:00 submissions due** (form: https://cerebralvalley.ai/e/gemini-4-nyc/hackathon/submit, needs a 1-minute video).
- 17:00-18:45 round-one live judging, 3 min demo + 2 min Q&A. 19:00 top six on stage. 20:15 winners.
- Build-freeze **16:15**. 16:15-16:50 rehearse twice + record the video. 16:50 submit.
- Wi-Fi `Hackathon` / `hackathon`.

## Owners

| Module | Owner tool | Status |
| --- | --- | --- |
| agent-backend/ | Antigravity | unclaimed |
| companion-screen/ | Claude Code (`claude` installed 12:36) | unclaimed |
| device/ | Codex (PlatformIO + M5Unified, `pio` installed 12:38) | unclaimed |
| eval/ (inside agent-backend) | Antigravity, after chunk 4 | unclaimed |
| docs, pitch, video, STATE | Tolu + AdaL | live |

## Works (verified live)

- 12:33 Monday Cartoons (the judge's store) is in the Global Catalog with 5 physical products. Variant ids in docs/HACKATHON.md. Digital sticker is not (PENDING P7).
- 12:30 Remote: https://github.com/ToXMon/shop-counter (public, per rules).
- 12:12 Catalog `search_catalog`, no key. `scripts/smoke_catalog.sh`.
- 12:25 `scripts/stub_backend.py` + `scripts/smoke_backend.sh` + `device/smoke_http.sh` all green.

## In flight

- (claim here: `- module: chunk - tool - HH:MM`)

## Next (ordered)

1. agent-backend chunk 1 (13:15): skeleton, `/utterance` text -> real catalog -> `/state`. smoke passes.
2. companion-screen chunk 1 (13:15): Vite+React vs stub, one card, flow bar.
3. device chunk 1 (13:15): `pio` project, Wi-Fi, button -> `/intent`, screen text.
4. Tolu at 13:00 lunch: collect 20 attendee utterances with budgets for `eval/` (PENDING P8). Phone voice memos are fine.
5. agent-backend chunk 2 (14:00): Hydrogen constraints + Neon pick. Re-search works typed.
6. companion-screen chunk 2 (14:00): candidate grid, pick, reasons, QR view.
7. device chunk 2 (14:30): push-to-talk WAV -> `/utterance`; RFID -> `/intent`.
8. agent-backend chunk 3-4 (15:15): Decision 1 gates, checkout, redaction, stale_pick.
9. agent-backend chunk 5-6 (16:15): transcribe/TTS, eval + managed-agent run, REPORT.md, FAILURES.md.
10. 16:15 freeze. Rehearse. Record 1-min video. Submit 16:50.

## Blocked

- (none)

## Decisions made today

- 12:45 Problem statement: Element 119 (voice is the core input), with a 5-Sigma-style eval for Proof It Works. docs/HACKATHON.md.
- 12:45 Models: Neon (agent), Hydrogen (workers), Decision 1 (gates), 3.5-transcribe, 3.8-flash-tts; Managed Agent runs the eval. docs/INTERFACES.md section 3.
- 12:45 Demo store product path: Hat $38 -> "under ten" -> "Balance" print $9. Judge pays on his own store. Open-catalog query (espresso) stays for unrehearsed input.
- 12:38 Repo flipped to public (rule). `scripts/secret_scan.sh` before every push.
- 12:38 Device: PlatformIO + Arduino + M5Unified.
- 12:20 Catalog search direct to `catalog.shopify.com` with Shopify's sample profile. Cart/checkout via Shop MCP. Fallback: per-variant `checkout_url` from the catalog.
