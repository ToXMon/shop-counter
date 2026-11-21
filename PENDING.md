# PENDING.md - decisions blocked on Tolu

Agents: add an item with your recommendation. Tolu: answer inline, then move it to "Resolved".

## Open

### P1. Real deadline: 17:00 or 22:00?
- BRIEF.md says the event runs to 10 PM. Tolu said "execute by 5 pm".
- Recommendation: treat 17:00 as build-freeze and rehearsal start. Read the gated details page for the actual submission form, time, and what to submit (repo link? video? live demo slot?). Write the answer here.

### P2. Device firmware language
- Options: MicroPython (fast iteration, `mpremote`), Arduino/C++ (M5Unified has best CoreS3 audio + RFID support), or UIFlow 2.
- Recommendation: Arduino + M5Unified if Tolu has used it before; otherwise MicroPython. Neither `mpremote` nor `arduino-cli` is installed yet. Decide before 14:00 or the device chunk slips.

### P3. Speech-to-text path
- Options: (a) device records WAV, backend transcribes with Gemini audio input; (b) phone mic via companion screen Web Speech API; (c) typed input on companion screen.
- Recommendation: (a) is the demo-worthy path and uses Gemini credits. Build (c) first as the vertical slice, keep (b) as live fallback. Confirm.

### P4. "Peter Yang MCP"
- Tolu asked to include "Peter Yang MCP for his skills". The repo linked (`kunchenguid/kun`) is Kun Chen's opinions + tools distro, not Peter Yang's. Kun's skill is installed as `/kun`. Peter Yang's public material is a Claude Code "Personal OS" tutorial, not an MCP.
- Recommendation: proceed with Kun's skills (already wired). If there is a specific Peter Yang MCP server URL or repo, paste it here and an agent will add it.

### P5. Which Gemini model for the managed agent
- Catalog on this machine shows Gemini 4 Argon, Gemini 3.1 Pro, Gemini 3.x Flash. Judges want "something that wasn't possible last week", so Gemini 4 Argon for the agent loop is the story. Flash for TTS/STT helpers if latency bites.
- Recommendation: Argon for planning + explaining the pick; verify the Interactions API supports it on your key during setup.

### P6. Repo visibility and remote
- AGENTS.md says the repo stays private. No remote yet.
- Recommendation: `gh repo create shop-counter --private --source . --push` once Tolu confirms the name. Parallel agents need the remote for handoffs.

## Resolved

- (none yet)
