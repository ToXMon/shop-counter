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

Keep the existing React app and same-origin proxy. Make a single fixture-only polish pass using Taste as a reference. Show the real product image when available, one readable price and short reason. Give the QR a white square, clean margin, no animation, and the instruction “Scan to review and pay.” Keep fixture mode visible. In the existing UI, provide Mac playback or browser push-to-talk only as a fallback. Use Pocock TDD for stale QR and late responses after Clear. Coordinate the exact offer binding with Antigravity before changing behavior. Test on the Mac at presentation width and at 390 px, and report the build, screenshots, and commit. Preserve the screen if the optional reference tool fails. No new UI framework.

## Send to Codex in build/device

Prioritize live paired push-to-talk and bottom-center touch intent on the flashed board. Wait for Antigravity's exact contract before wiring offer binding. Keep the proven tag as an optional tap path. Present one large status: Ready, Listening, Looking it up, or Scan on the Mac. Preserve bottom-left Hold to talk and bottom-center Tap to review. Use high-contrast text and the shared accent. Show failures as short recovery instructions. Do not show a QR or claim payment. Use Pocock TDD at the API seam; use diagnosing-bugs if the board fails. Report flashed-board evidence separately from compile evidence. If speaker playback is flaky, use Mac audio and say so.

## Integration checkpoint

Tolu owns integration. Do not merge lane branches blindly. First prove the real backend and Mac reach the sticker checkout. Then prove the CoreS3 talk and tap against the same fresh session. Try a changed offer before tapping and verify old QR removal. Use a fresh phone scan and stop before payment. Show the judge the exact same flow in the video, with the checkout QR masked. Freeze at 16:15 ET and aim to submit at 16:50 ET.
