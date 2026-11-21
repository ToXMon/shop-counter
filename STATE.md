# STATE.md - Shop Counter

Living status. Update it when you start or finish a chunk. Newest at the top of each list.

Last updated: 2026-11-21 15:15 EST by Claude Code (companion-screen)

## Clock (confirmed from the participant guide)

- **17:00 submissions due** (form: https://cerebralvalley.ai/e/gemini-4-nyc/hackathon/submit, needs a 1-minute video).
- 17:00-18:45 round-one live judging, 3 min demo + 2 min Q&A. 19:00 top six on stage. 20:15 winners.
- Build-freeze **16:15**. 16:15-16:50 rehearse twice + record the video. 16:50 submit.
- Use a private hotspot for hardware integration. See the participant guide for venue Wi-Fi.

## Owners

| Module | Owner tool | Status |
| --- | --- | --- |
| agent-backend/ | Antigravity | unclaimed |
| companion-screen/ | Claude Code (`claude` installed 12:36) | claimed 13:25 (build/screen) |
| device/ | Codex (PlatformIO + M5Unified, `pio` installed 12:38) | unclaimed |
| eval/ (inside agent-backend) | Antigravity, after chunk 4 | unclaimed |
| docs, pitch, video, STATE | Tolu + AdaL | live |

## Works (verified live)

- Monday Cartoons Digital Sticker is available on the storefront. Shop MCP returned a handoff for its exact variant. Test price was $0.50 before tax; phone scan and $0.99 price are unverified. See `docs/LAUNCH.md` and `PENDING.md` P7.
- Earlier Global Catalog searches found five physical products but did not return the sticker.
- 12:30 Remote: https://github.com/ToXMon/shop-counter (public, per rules).
- 12:12 Catalog `search_catalog`, no key. `scripts/smoke_catalog.sh`.
- 12:25 `scripts/stub_backend.py` + `scripts/smoke_backend.sh` + `device/smoke_http.sh` all green.

## In flight

- companion-screen: in-store display (direction A), QR bound to offer_id, stale-response guard after Clear, dev push-to-talk (a7327b4). 23 tests pass. Mac build last verified at 28b3ccd; rerun on a7327b4. Live QR check against :8788 still open. Not merged. - Claude Code - 15:15
- (claim here: `- module: chunk - tool - HH:MM`)

## Next (ordered)

1. Start all three lanes with the copy-paste prompts in `docs/LAUNCH.md`.
2. Integrate the laptop flow first: exact sticker, displayed offer, intent, then the phone handoff.
3. Verify the event-key model calls and add the live voice loop. Add CoreS3 audio and RFID after the button works.
4. Collect consented unrehearsed inputs while the agents build. Keep recordings out of the public repo.
5. Freeze at 16:15. Rehearse, record the one-minute video, and submit at 16:50.

## Blocked

- (none)

## Decisions made today

- 15:15 Companion screen binds the QR to the offer: `pick.offer_id` and `handoff.offer_id` (contract: build/backend 9c452a0). Live mode shows a QR only when both are present and equal. The merchant-only match survives in fixture mode only. Responses that land after Clear are dropped (`companion-screen/src/feed.ts`).
- 15:15 The Mac stays silent by default. Browser push-to-talk and speech exist only with `?dev` (`?dev&speak` to speak). Codex's Mac proxy already speaks device replies with `say`.
- 15:15 Mac display copy: product view says "Tap the center of the device screen to open checkout."; scan view says "Scan to review and pay on your phone." The tap does not charge anyone.
- 12:45 Problem statement: Element 119 (voice is the core input), with a 5-Sigma-style eval for Proof It Works. docs/HACKATHON.md.
- 12:45 Models: Neon (agent), Hydrogen (workers), Decision 1 (gates), 3.5-transcribe, 3.8-flash-tts; Managed Agent runs the eval. docs/INTERFACES.md section 3.
- Demo: search Monday Cartoons live, then narrow to the Digital Sticker. Use the verified storefront variant and Shop MCP checkout. See `docs/LAUNCH.md` for lane prompts and integration order.
- 12:38 Repo flipped to public (rule). `scripts/secret_scan.sh` before every push.
- 12:38 Device: PlatformIO + Arduino + M5Unified.
- 12:20 Catalog search direct to `catalog.shopify.com` with Shopify's sample profile. Cart/checkout via Shop MCP. Fallback: per-variant `checkout_url` from the catalog.
