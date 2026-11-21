# Shop Counter demo polish

Nov 21, 2026 · POC: Tolu · Priority: prove the phone handoff while the screen gets one focused polish pass. See `docs/DEMO.md` for the judge walkthrough and the one-minute shot list.

## Status at 14:09 ET

- Backend `e45102e`: agent reported successful Gemini, voice, Shopify and hosted Managed Agent checks. The Mac preview still read from the stub. Separate backend verification is not an integrated demo.
- Screen `e9b3479`: Mac production build and nine tests passed. QR and Clear worked against fixture data. Live phone scan, browser audio, and same-seller offer invalidation need verification.
- Device `696f8b5`: agent reported a touch tap and RFID demo-tag tap against the stub, and a WAV sent to a test receiver. Live pairing and offer-bound intent remain open. Speaker playback is not verified.
- Price: $0.50 was the verified listing price. Show the current price; do not hard-code it. The phone scan remains open even though the backend branch closed its price decision.

## Proposed direction

A modern independent shop counter: warm off-white, near-black ink, one orange accent, large product image and price, plain instructions. The CoreS3 uses the same accent and words. It shows one state and the two existing touch controls. The Mac shows the product and switches focus to the high-contrast QR after intent. The phone stays on native merchant checkout. Do not restyle it.

Borrow composition, hierarchy, typography, and responsive screenshot checks from [Leonxlnx Taste Skill](https://github.com/Leonxlnx/taste-skill/tree/main/skills/taste-skill). Use it as a reference, not as a landing-page template. Do not install its hooks or copy its scaffolding. If a layout reference is needed, use one fixture-only mock in Google Stitch or Claude Design, not both. Do not upload a real QR, checkout link, recordings, or secrets.

## Send to Antigravity in build/backend

Own the live integration seam. Keep the shared stub running and start the real backend separately. Give the screen and device agents the tested endpoints and one exact pairing/offer contract, including the fields they send and receive. Bind a tap to the displayed offer and reject missing or stale references. Keep checkout-bearing state local to the companion screen. Test same-seller offer changes and Clear. Prove the live sticker flows to the screen and ask Tolu to scan it on a phone. Stop before payment. Report the tested command, branch commit, and remaining blocker. Use Pocock TDD for the intent seam, then code review for checkout. Do not add models or expand eval scope now.

## Send to Claude Code in build/screen

Source: [Peter Yang's GitHub transcript](https://github.com/petergyang/behind-the-craft-transcripts/blob/HEAD/transcripts/2026/194-full-tutorial-how-to-fix-ai-slop-with-claude-design-in-40-minutes-nate-parrott.md) and [episode notes](https://creatoreconomy.so/p/how-to-fix-ai-slop-with-claude-design-nate-parrott). Two options and one review are our hackathon adaptation, not Nate's suggested option count. The earlier palette is a suggestion, not a requirement.

```text
Continue in ~/shop-counter-screen on build/screen. Own only companion-screen/.
The judge talks and taps on the CoreS3, glances at the Mac, then scans with
their phone. The Mac is a counter display, not the main controls.

1. Read the existing React and CSS. Capture the current fixture screen if
   available. Treat working code as the source of truth. Use two familiar
   patterns for structure: a store product display and a scan-to-pay terminal.
   Borrow hierarchy and alignment from Taste Skill. Do not install its hooks.
2. Show two low-fi wireframes side by side, using identical fixture content.
   A: product-first, then switch focus to a dedicated scan view after the tap.
   B: keep the product visible beside a dedicated scan panel at desktop width.
   Show the recommendation and handoff states for each. If screenshots are
   unavailable, ASCII is fine. Recommend one and tell me what you'd borrow
   from the other. Stop for one A/B or remix decision before changing the UI.
3. Implement only the approved direction in the existing React app. Use
   merchant product art when available, one large price from state, a short
   reason, and “Scan to review and pay.” Keep the QR still with a white quiet
   zone. Avoid the default serif/off-white/orange/card-edge-stripe combination,
   decorative gradients, and nested cards. Pick color from the product and
   the room's readability needs, not a template. Keep fixture mode visible.
4. Preserve the same-origin proxy and checkout behavior. Never expose a
   readable live QR or checkout URL in screenshots, logs, or external tools.
   Coordinate offer binding with Antigravity before changing the contract.
   Use Matt Pocock's TDD only for behavior changes such as stale QR or Clear.
5. Check the fixture at presentation width and 390 px: no clipping, no
   horizontal scroll, item and price legible, next action obvious, QR visible
   only for a valid handoff. Report screenshots, tests, and the commit.
   If Desktop's Rollup build fails, ask for the Mac build. No new framework,
   no separate Claude Design or Stitch setup, no merge to main.
```

## Send to Codex in build/device

Prioritize live paired push-to-talk and bottom-center touch intent on the flashed board. Wait for Antigravity's exact contract before wiring offer binding. Keep the proven tag as an optional tap path. Present one large status: Ready, Listening, Looking it up, or Scan on the Mac. Preserve bottom-left Hold to talk and bottom-center Tap to review. Use high-contrast text and the shared accent. Show failures as short recovery instructions. Do not show a QR or claim payment. Use Pocock TDD at the API seam; use diagnosing-bugs if the board fails. Report flashed-board evidence separately from compile evidence. If speaker playback is flaky, use Mac audio and say so.

## Integration checkpoint

Tolu owns integration. Do not merge lane branches blindly. First prove the real backend and Mac reach the sticker checkout. Then prove the CoreS3 talk and tap against the same fresh session. Try a changed offer before tapping and verify old QR removal. Use a fresh phone scan and stop before payment. Show the judge the exact same flow in the video, with the checkout QR masked. Freeze at 16:15 ET and aim to submit at 16:50 ET.
