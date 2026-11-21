# PENDING.md - decisions blocked on Tolu

Agents: add an item with your recommendation. Tolu: answer inline, then move it to "Resolved".

## Open

### P7. Demo product: the digital sticker is not in the Global Catalog
- Verified 12:33 EST: Monday Cartoons has 5 products in the catalog (Hat $38, two Celestial tees $89, Champions tee $99, "Balance" Photo Print $9). The digital sticker is absent. Digital goods are probably not published to the Shop sales channel.
- Options: (a) demo with Hat -> re-search -> "Balance" print ($9, cheapest, real checkout); (b) ask the judge (store owner) to publish the sticker to the Shop channel and wait for the catalog to pick it up (unknown delay, risky); (c) both: build for (a), try (b) if he is willing.
- Recommendation: (a) now. Mention (b) to him only if there is time after 15:00. Decide by 13:30.

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
