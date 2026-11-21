# STATE.md - Shop Counter

Living status. Update it when you start or finish a chunk. Newest at the top of each list.

Last updated: 2026-11-21 12:45 EST by AdaL

## Clock (confirmed from the participant guide)

- **17:00 submissions due** (form: https://cerebralvalley.ai/e/gemini-4-nyc/hackathon/submit, needs a 1-minute video).
- 17:00-18:45 round-one live judging, 3 min demo + 2 min Q&A. 19:00 top six on stage. 20:15 winners.
- Build-freeze **16:15**. 16:15-16:50 rehearse twice + record the video. 16:50 submit.
- Use a private hotspot for hardware integration. See the participant guide for venue Wi-Fi.

## Owners

| Module | Owner tool | Status |
| --- | --- | --- |
| agent-backend/ | Antigravity | unclaimed |
| companion-screen/ | Claude Code (`claude` installed 12:36) | unclaimed |
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

- (claim here: `- module: chunk - tool - HH:MM`)

## Next (ordered)

1. Send the three lane prompts in `docs/DEMO-POLISH.md`. Keep the stub for fixture work.
2. Start a separate live backend. Test the exact sticker, offer-bound intent, and phone handoff.
3. Run one focused visual pass in parallel. Then test CoreS3 voice and tap against the same live session.
4. Rehearse with an unrehearsed request. Keep any consented recordings out of the public repo.
5. Freeze at 16:15. Record the one-minute video and aim to submit at 16:50.

## Blocked

- The Mac preview still uses the fixture backend. The live backend and screen have not passed a joint phone checkout.
- The CoreS3 can send touch intent and a WAV in separate bench tests. Live pairing and offer-bound intent are not yet verified. The current firmware displays reply text; plan on Mac playback unless board playback is proven.
- At 14:15 ET, all three worktrees were clean. Backend `e45102e` includes the price and evaluation scope decisions. Screen `e9b3479` passed the Mac build and nine tests. Device `696f8b5` records the RFID demo-tag test against the stub.
- Port 5173 still reached the stub. No live backend answered the health check on port 8788. See `docs/DEMO.md` for the walkthrough and `docs/DEMO-POLISH.md` for lane prompts.

## Decisions made today

- 12:45 Problem statement: Element 119 (voice is the core input), with a 5-Sigma-style eval for Proof It Works. docs/HACKATHON.md.
- 12:45 Models: Neon (agent), Hydrogen (workers), Decision 1 (gates), 3.5-transcribe, 3.8-flash-tts; Managed Agent runs the eval. docs/INTERFACES.md section 3.
- Demo: search Monday Cartoons live, then narrow to the Digital Sticker. Use the verified storefront variant and Shop MCP checkout. See `docs/LAUNCH.md` for lane prompts and integration order.
- 12:38 Repo flipped to public (rule). `scripts/secret_scan.sh` before every push.
- 12:38 Device: PlatformIO + Arduino + M5Unified.
- 12:20 Catalog search direct to `catalog.shopify.com` with Shopify's sample profile. Cart/checkout via Shop MCP. Fallback: per-variant `checkout_url` from the catalog.
