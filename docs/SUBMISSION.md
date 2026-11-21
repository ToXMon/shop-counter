# Shop Counter submission

Nov 21, 2026 · Owner: Tolu · Deadline: 5:00 p.m. ET. Paste these into the [submission form](https://cerebralvalley.ai/e/gemini-4-nyc/hackathon/submit). Nothing has been submitted.

| Field | Answer |
| --- | --- |
| Team Name | Shop Counter |
| Team Members | Keep the existing solo member entry if it is yours. |
| Public GitHub Repository | https://github.com/ToXMon/shop-counter, after publishing and verifying the demo code |
| 1-Minute Demo Video | Paste the finished video URL. Check it in a signed-out window. |
| Problem Statement | Problem Statement Two: Element 119 |
| Gemini 4 models | Neon and Hydrogen |
| Best Use of Managed Agents | Yes |
| Best Use of Shopify | Yes |

## Project Description

Shop Counter is a voice-first shopping counter for independent Shopify stores. Hold the M5Stack CoreS3 to ask for something, then change your mind out loud. The agent searches live product data, compares options, and explains its recommendation. The Mac speaks the reply and displays the item, merchant, and price.

Tap the center of the CoreS3 to request checkout for the displayed item. Shop MCP creates the checkout and the Mac displays a QR. Scan it to review the merchant checkout on your own phone. The tap does not charge you, and the device never handles payment details.

I verified the Monday Cartoons Digital Sticker checkout on my phone and stopped before payment. The sticker comes from the merchant’s live storefront; broader discovery uses Shopify’s catalog.

## What job does each model do?

Gemini 4 Hydrogen extracts shopping constraints from the transcript and summarizes candidates. Gemini 4 Neon compares the candidates, picks a product, and explains the recommendation. Gemini Decision 1 routes requests, identifies when clarification is needed, scores candidate fit, and checks the recommendation against the shopper’s constraints.

Gemini 3.5 Transcribe turns short CoreS3 recordings into text. I tested Gemini 3.8 Flash TTS as an optional speech path; the demo uses local Mac speech. An Antigravity Managed Agent completed a hosted evaluation audit outside the live shopping flow.

## Optional Google DeepMind feedback

The biggest challenge was variable response time in a multi-step voice turn. In three runs per condition using the same WAV, mean time from backend audio receipt to reply ready went from 34.48 s to 23.44 s after honoring the speech-generation opt-out. The single TTS-enabled control measured 5.55 s for TTS itself. These are replay measurements, not measured live voice timings. More predictable time to first grounded reply from Neon and per-call timing metadata would help teams diagnose slow turns.

## Before clicking Submit

- Record one verified talk → tap → phone review flow. Stop before payment and mask the checkout QR in the footage.
- Publish the reviewed backend, screen, and device code. At 3:46 p.m. ET public main still lagged the local build branches.
- Do not publish secrets, raw audio, checkout links, or session details. Review the release diff and run the secret scan before pushing.
- Open the public repo and the one-minute video link signed out. Submit by 5:00 p.m. ET.
