# STATE.md - Shop Counter

Living status. Update it when you start or finish a chunk. Newest at the top of each list.

Last updated: 2026-11-21 by Codex

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
| device/ | Codex (PlatformIO + M5Unified) | in progress |
| eval/ (inside agent-backend) | Antigravity, after chunk 4 | unclaimed |
| docs, pitch, video, STATE | Tolu + AdaL | live |

## Works (verified live)

- CoreS3 touch sent intent for a paired stub offer over the iPhone hotspot. Laptop smoke passed.
- CoreS3 push-to-talk sent a valid 16 kHz mono WAV to a local test receiver.
- RFID 2 and the black demo tag sent badge intent to a paired stub offer.

- Monday Cartoons Digital Sticker is available on the storefront. Shop MCP returned a handoff for its exact variant. Test price was $0.50 before tax; phone scan and $0.99 price are unverified. See `docs/LAUNCH.md` and `PENDING.md` P7.
- Earlier Global Catalog searches found five physical products but did not return the sticker.
- 12:30 Remote: https://github.com/ToXMon/shop-counter (public, per rules).
- 12:12 Catalog `search_catalog`, no key. `scripts/smoke_catalog.sh`.
- 12:25 `scripts/stub_backend.py` + `scripts/smoke_backend.sh` + `device/smoke_http.sh` all green.

## In flight

- device: Live offer-bound touch verified; asynchronous live voice retry in progress - Codex

## Next (ordered)

1. Start all three lanes with the copy-paste prompts in `docs/LAUNCH.md`.
2. Integrate the laptop flow first: exact sticker, displayed offer, intent, then the phone handoff.
3. Verify the event-key model calls and add the live voice loop. Add CoreS3 audio and RFID after the button works.
4. Collect consented unrehearsed inputs while the agents build. Keep recordings out of the public repo.
5. Freeze at 16:15. Rehearse, record the one-minute video, and submit at 16:50.

## Blocked

- device: Live voice retry and phone QR scan remain unverified.

## Decisions made today

- 12:45 Problem statement: Element 119 (voice is the core input), with a 5-Sigma-style eval for Proof It Works. docs/HACKATHON.md.
- 12:45 Models: Neon (agent), Hydrogen (workers), Decision 1 (gates), 3.5-transcribe, 3.8-flash-tts; Managed Agent runs the eval. docs/INTERFACES.md section 3.
- Demo: search Monday Cartoons live, then narrow to the Digital Sticker. Use the verified storefront variant and Shop MCP checkout. See `docs/LAUNCH.md` for lane prompts and integration order.
- 12:38 Repo flipped to public (rule). `scripts/secret_scan.sh` before every push.
- 12:38 Device: PlatformIO + Arduino + M5Unified.
- 12:20 Catalog search direct to `catalog.shopify.com` with Shopify's sample profile. Cart/checkout via Shop MCP. Fallback: per-variant `checkout_url` from the catalog.
