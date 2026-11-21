# GEMINI.md (Antigravity)

Read `AGENTS.md`. It is the single source of rules for this repo. Every tool (Antigravity, Claude Code, Codex) reads the same file.

Then follow the "Session start" steps in `AGENTS.md`.

Antigravity-specific notes:
- Project skills live in `.agents/skills/`. Antigravity loads them from there.
- Antigravity is the primary tool for `agent-backend/` because it has the Gemini credits and the Managed Agents (Interactions API) access. See `agent-backend/AGENTS.md`.
- Use the built-in browser to verify `companion-screen/` renders. Never paste secrets into the browser.
- `GEMINI_API_KEY` comes from `.env`, never from a file in the repo.
