# STATE.md - Shop Counter

Living status. Update it when you start or finish a chunk. Newest at the top of each list.

Last updated: 2026-11-21 15:18 EST by Antigravity

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
| eval/ (inside agent-backend) | Antigravity | live (verified with hosted Managed Agent sandbox) |
| docs, pitch, video, STATE | Tolu + AdaL | live |

## Works (verified live)

- 15:18 Fixed `include_tts=false` on audio input (`cd8bd2e`, `4 passed` in `test_include_tts.py`) and added grounded `question_about_pick` fast-path (`358fffe`, `test_pick_question.py` passed). Replayed the same WAV 3x before (`mean 34.48s` on live `:8788`) vs after (`mean 23.44s` on `:8789`, `tts_ms=0`; `include_tts=true` control `29.48s` with `tts_ms=5554ms`). CoreS3 multipart audio + offer-bound tap-to-QR smoke-tested on `:8789`. Working demo on `:8788` kept untouched during tests.
- 14:36 Live backend running on `http://127.0.0.1:8788` alongside shared stub on `http://127.0.0.1:8787`; live companion-screen preview running on `http://127.0.0.1:5174/` displaying the fresh Monday Cartoons Digital Sticker QR (`session_id: s_ca99bb83`, `offer_id: monday-cartoons.myshopify.com:gid://shopify/ProductVariant/68033173323939:50`, `$0.54` total with tax, ready for Tolu's phone scan).
- 14:36 Offer-bound `/intent` seam tested with TDD (`test_offer_binding_seam.py`) and two-axis Code Review (Standards + Spec): rejects missing or stale offer references (`stale_pick`), invalidates old handoff on same-seller item change (Monday Cartoons Hat -> Monday Cartoons Digital Sticker), and restricts `GET /state` (`403`) to loopback.
- 14:00 P7 & P8 resolved: Monday Cartoons Digital Sticker live price confirmed at $0.50 USD (`50` minor units, `$0.54` with tax on Shop MCP checkout); P8 attendee recording walk dropped as unnecessary for Element 119 + Shopify track (`eval/` + hosted Managed Agent audit + live judge queries cover Proof It Works).
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

- companion-screen: in-store display (direction A), QR bound to offer_id, stale-response guard after Clear, dev push-to-talk (a7327b4). 23 tests pass. Mac build last verified at 28b3ccd; rerun on a7327b4. Live QR check against :8788 still open. Not merged. - Claude Code - 15:15
- (claim here: `- module: chunk - tool - HH:MM`)

## Next (ordered)

1. Send the three lane prompts in `docs/DEMO-POLISH.md`. Keep the stub for fixture work.
2. Start a separate live backend. Test the exact sticker, offer-bound intent, and phone handoff.
3. Run one focused visual pass in parallel. Then test CoreS3 voice and tap against the same live session.
4. Rehearse with an unrehearsed request. Keep any consented recordings out of the public repo.
5. Freeze at 16:15. Record the one-minute video and aim to submit at 16:50.

## Blocked

- Tolu verified the Monday Cartoons phone checkout on the working demo and stopped before payment.
- The candidate preview and backend answered health checks. The device proxy was not listening on port 8790 at the last check. Rehearse once on a reachable setup rather than running more latency benchmarks.
- Public `main` still lagged the local build branches at 15:46 ET. Review and publish the demo code before submitting the repository link.
- See `.handoffs/HANDOFF-2026-11-21-1544.md` for device takeover and `docs/SUBMISSION.md` for the inspected form and paste-ready answers.

## Decisions made today

- 14:36 Offer-binding & pairing contract: canonical `offer_id` is `<seller.domain>:<variant_id>:<price_minor>` (e.g. `monday-cartoons.myshopify.com:gid://shopify/ProductVariant/68033173323939:50`), returned in `POST /utterance` (`reply.offer_id`), `GET /state` (`pick.offer_id`, `handoff.offer_id`), and `GET /session/offer` (`offer_id`). `POST /intent` requires `offer_id` (or `product_id`/`variant_id` matching the current pick) and rejects missing or stale references (`handoff.status = "stale_pick"`). `GET /state` is restricted to Mac loopback (`127.0.0.1`/`::1`/`localhost`).
- 12:45 Problem statement: Element 119 (voice is the core input), with a 5-Sigma-style eval for Proof It Works. docs/HACKATHON.md.
- 12:45 Models: Neon (agent), Hydrogen (workers), Decision 1 (gates), 3.5-transcribe, 3.8-flash-tts; Managed Agent runs the eval. docs/INTERFACES.md section 3.
- Demo: search Monday Cartoons live, then narrow to the Digital Sticker. Use the verified storefront variant and Shop MCP checkout. See `docs/LAUNCH.md` for lane prompts and integration order.
- 12:38 Repo flipped to public (rule). `scripts/secret_scan.sh` before every push.
- 12:38 Device: PlatformIO + Arduino + M5Unified.
- 12:20 Catalog search direct to `catalog.shopify.com` with Shopify's sample profile. Cart/checkout via Shop MCP. Fallback: per-variant `checkout_url` from the catalog.
