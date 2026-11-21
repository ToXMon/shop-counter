# PENDING.md - decisions blocked on Tolu

Agents: add an item with your recommendation. Tolu: answer inline, then move it to "Resolved".

## Open

- (none — all blocking decisions resolved)

## Resolved

- **P7. Confirm the demo price and scan the sticker checkout.** Merchant live storefront price is confirmed at **$0.50 USD** (`50` minor units before tax; `$0.54` with tax on Shop MCP checkout). Backend dynamically reads the live price from `monday-cartoons.myshopify.com/products.json` and creates the Shop MCP handoff for `gid://shopify/ProductVariant/68033173323939`. (Resolved by Tolu, 14:00)
- **P8. 20 attendee WAV recordings.** Not required for **Element 119** + **Build with Commerce (Shopify)**. In `docs/HACKATHON.md`, the 20-utterance offline benchmark was a borrowed **5 Sigma** idea; under **Element 119**, "Proof It Works" is demonstrated by: (1) live unrehearsed voice queries from judges at the table, (2) our live Decision 1 self-check (`GATE 2`) and clarification (`GATE 1`) gates, and (3) our off-path `eval/` suite (`REPORT.md`, `FAILURES.md`, and the completed Google-hosted `antigravity-preview-09-2026` sandbox audit in `MANAGED_RUN.json`). (Resolved by Tolu, 14:00)

- **P1. Deadline.** Submissions due **17:00**, live judging 17:00-18:45. Build-freeze 16:15, rehearsal + video 16:15-16:50. (Participant guide, 12:32)
- **P2. Device firmware.** PlatformIO + Arduino + M5Unified for the CoreS3 (`pio` installed 12:38). Reason: M5Unified has the mic, speaker and RFID2 paths in one library; `pio run -t upload` is scriptable for Codex. MicroPython kept as fallback if the audio path fights us by 14:30.
- **P3. Speech path.** Build (c) typed input on companion screen first (vertical slice), then (a) device records WAV -> backend transcribes with `gemini-3.5-transcribe`. (b) phone-mic via Web Speech stays as live fallback. Reference: OpenAI's "Reflect" project used CoreS3 + phone session for audio, so a phone-mic fallback is a known pattern.
- **P4. "Peter Yang MCP".** Proceeding with Kun Chen's `/kun` skills (already wired). No Peter Yang MCP exists publicly.
- **P5. Models.** Superseded by the Participant Guide: at least two Gemini 4 models with distinct jobs plus Decisions API. Plan: `gemini-4-neon` (agent), `gemini-4-hydrogen` (workers), `gemini-decision-1` (gates), `gemini-3.5-transcribe`, `gemini-3.8-flash-tts`, `antigravity-preview-09-2026` managed agent for the eval harness. See docs/HACKATHON.md.
- **P6. Remote.** https://github.com/ToXMon/shop-counter, **public** (hackathon rule). Root AGENTS.md updated. Secret scan before every push is now mandatory, not advisory.
