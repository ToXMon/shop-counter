# PENDING.md - decisions blocked on Tolu

Agents: add an item with your recommendation. Tolu: answer inline, then move it to "Resolved".

## Open

### P7. Confirm the demo price and scan the sticker checkout
- Digital Sticker is available on the storefront. Shop MCP accepted its exact variant and returned a handoff URL.
- Live observed price: $0.50 USD before tax. The test checkout showed $0.54 total and required buyer contact.
- Ask the merchant whether to keep the live price or set $0.99. Recheck both surfaces after any change.
- No phone scan or payment has been verified. Implement the sticker route now; see `docs/LAUNCH.md`.


### P8. Where do the 20 unrehearsed eval utterances come from?
- "Proof it works" is 25%. Evals made only of examples we wrote are banned.
- Recommendation: Tolu walks the room at lunch (13:00) with a phone, records 20 attendees each saying one shopping request with a budget. Save as `eval/utterances/*.wav` + a transcript CSV. That is the test set. Takes 20 minutes. Alternative: ask in Discord #general.

## Resolved

- **P1. Deadline.** Submissions due **17:00**, live judging 17:00-18:45. Build-freeze 16:15, rehearsal + video 16:15-16:50. (Participant guide, 12:32)
- **P2. Device firmware.** PlatformIO + Arduino + M5Unified for the CoreS3 (`pio` installed 12:38). Reason: M5Unified has the mic, speaker and RFID2 paths in one library; `pio run -t upload` is scriptable for Codex. MicroPython kept as fallback if the audio path fights us by 14:30.
- **P3. Speech path.** Build (c) typed input on companion screen first (vertical slice), then (a) device records WAV -> backend transcribes with `gemini-3.5-transcribe`. (b) phone-mic via Web Speech stays as live fallback. Reference: OpenAI's "Reflect" project used CoreS3 + phone session for audio, so a phone-mic fallback is a known pattern.
- **P4. "Peter Yang MCP".** Proceeding with Kun Chen's `/kun` skills (already wired). No Peter Yang MCP exists publicly.
- **P5. Models.** Superseded by the Participant Guide: at least two Gemini 4 models with distinct jobs plus Decisions API. Plan: `gemini-4-neon` (agent), `gemini-4-hydrogen` (workers), `gemini-decision-1` (gates), `gemini-3.5-transcribe`, `gemini-3.8-flash-tts`, `antigravity-preview-09-2026` managed agent for the eval harness. See docs/HACKATHON.md.
- **P6. Remote.** https://github.com/ToXMon/shop-counter, **public** (hackathon rule). Root AGENTS.md updated. Secret scan before every push is now mandatory, not advisory.
