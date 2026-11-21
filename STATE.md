# STATE.md - Shop Counter

Living status. Update it when you start or finish a chunk. Newest at the top of each list.

Last updated: 2026-11-21 13:55 EST by Antigravity

## Clock (confirmed from the participant guide)

- **17:00 submissions due** (form: https://cerebralvalley.ai/e/gemini-4-nyc/hackathon/submit, needs a 1-minute video).
- 17:00-18:45 round-one live judging, 3 min demo + 2 min Q&A. 19:00 top six on stage. 20:15 winners.
- Build-freeze **16:15**. 16:15-16:50 rehearse twice + record the video. 16:50 submit.
- Use a private hotspot for hardware integration. See the participant guide for venue Wi-Fi.

## Owners

| Module | Owner tool | Status |
| --- | --- | --- |
| agent-backend/ | Antigravity | live |
| companion-screen/ | Claude Code (`claude` installed 12:36) | unclaimed |
| device/ | Codex (PlatformIO + M5Unified, `pio` installed 12:38) | unclaimed |
| eval/ (inside agent-backend) | Antigravity | live (seed smoke + hosted Managed Agent verified; awaiting attendee utterances P8) |
| docs, pitch, video, STATE | Tolu + AdaL | live |

## Works (verified live)

- 13:55 `agent-backend/` live and verified against `scripts/smoke_backend.sh` and `pytest` (`5 passed`):
  - Centralized `MODEL_IDS` in `agent-backend/models.py` (stale `GEMINI_MODEL` removed from `.env.example`).
  - Live API checks passed for `gemini-4-hydrogen`, `gemini-4-neon`, `gemini-decision-1` (`v1beta`), `gemini-3.5-transcribe` (`v1beta`), `gemini-3.8-flash-tts` (`v1beta`), and `antigravity-preview-09-2026` Managed Agent (`v1beta`, `environment="remote"`).
  - Typed Monday Cartoons search -> narrow to Digital Sticker (`gid://shopify/ProductVariant/68033173323939`, live storefront price `50` minor units) -> Shop MCP checkout handoff (`total_minor=54`, `status=incomplete`, buyer contact required on phone) -> `stale_pick` invalidation -> `/session/clear`.
  - Push-to-talk voice loop verified end-to-end: WAV audio -> `gemini-3.5-transcribe` -> Decision 1 clarification/routing gate -> Hydrogen constraints -> live Shopify lookup -> Hydrogen parallel summaries -> Decision 1 candidate rubric -> Neon pick & speech (`<=45` words) -> Decision 1 self-check -> `gemini-3.8-flash-tts` WAV output.
  - Off-path Managed Agent (`eval/managed.py`) completed in Google-hosted sandbox (`interaction_id`: `v1_Chc1LWdCYThxWkRLMmhvX1VQdmJTOGlRYxIXNS1nQmE4cVpESzJob19VUHZiUzhpUWM`, `environment_id`: `5d9190371e82a4026621854813262c66`).
- Monday Cartoons Digital Sticker is available on the storefront. Shop MCP returned a handoff for its exact variant. Test price was $0.50 before tax; phone scan and $0.99 price are unverified. See `docs/LAUNCH.md` and `PENDING.md` P7.
- Earlier Global Catalog searches found five physical products but did not return the sticker.
- 12:30 Remote: https://github.com/ToXMon/shop-counter (public, per rules).
- 12:12 Catalog `search_catalog`, no key. `scripts/smoke_catalog.sh`.
- 12:25 `scripts/stub_backend.py` + `scripts/smoke_backend.sh` + `device/smoke_http.sh` all green.

## In flight

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

- 12:45 Problem statement: Element 119 (voice is the core input), with a 5-Sigma-style eval for Proof It Works. docs/HACKATHON.md.
- 12:45 Models: Neon (agent), Hydrogen (workers), Decision 1 (gates), 3.5-transcribe, 3.8-flash-tts; Managed Agent runs the eval. docs/INTERFACES.md section 3.
- Demo: search Monday Cartoons live, then narrow to the Digital Sticker. Use the verified storefront variant and Shop MCP checkout. See `docs/LAUNCH.md` for lane prompts and integration order.
- 12:38 Repo flipped to public (rule). `scripts/secret_scan.sh` before every push.
- 12:38 Device: PlatformIO + Arduino + M5Unified.
- 12:20 Catalog search direct to `catalog.shopify.com` with Shopify's sample profile. Cart/checkout via Shop MCP. Fallback: per-variant `checkout_url` from the catalog.
