# docs/ORCHESTRATION.md - running three agents on one repo

Date: 2026-11-21. Owner: Tolu. TL;DR: one agent per module folder, all reading the same `AGENTS.md`, coordinating only through `STATE.md`, `PENDING.md`, `docs/INTERFACES.md`, and git. Tolu is the captain. The agents are crew.

## The layout agents share

```
AGENTS.md            rules for every agent (DOX root)
CLAUDE.md, GEMINI.md pointers to AGENTS.md (Claude Code, Antigravity)
STATE.md             who owns what, what works, what is next
PENDING.md           decisions only Tolu can make
GLOSSARY.md          one word per concept
LESSONS.md           symptom / cause / fix, newest first
docs/INTERFACES.md   the contracts; build against these, not against each other's code
docs/HACKATHON.md    event facts, prizes, judging story
.handoffs/           one file per session end, committed
.agents/skills/      project skills (Matt Pocock engineering + productivity, Kun)
.claude/skills  ->   symlink to .agents/skills
scripts/             smoke checks and the stub backend
device/ agent-backend/ companion-screen/   one owner each, own AGENTS.md each
```

## Tool assignment (default; change in STATE.md)

| Tool | Module | Why |
| --- | --- | --- |
| **Antigravity** | `agent-backend/` | Has the Gemini credits and Managed Agents (Interactions API). Gemini 4 Argon for the agent loop. Built-in browser to eyeball the companion screen. |
| **Claude Code** | `companion-screen/` | Strong at React/Vite UI and TDD. `claude` CLI is not on PATH yet: `npm i -g @anthropic-ai/claude-code`. |
| **Codex** | `device/` or scripts/stub | Installed (`codex` 0.147). Good for non-interactive, well-specified work: firmware HTTP client, stub backend, smoke scripts. |
| **AdaL (this session)** | docs, orchestration, research, pitch, backup video | Keeps STATE.md honest, runs smoke checks, drafts the pitch and records the backup. |

Model policy for sub-tasks that are purely coding and well-specified: an open-weight model (DeepSeek V4, Qwen 3.8, GLM-5.3, Kimi K3, MiniMax M3) is fine and cheap. Escalate to Gemini 4 Argon / Claude / GPT-6 only for the agent-loop prompt design, ambiguous product calls, and adversarial review of anything touching checkout. State the reason when escalating. The in-product agent itself is Gemini (that is the hackathon).

## Session protocol (every tool, every session)

1. `git pull --rebase` (once the remote exists; PENDING P6).
2. Read `STATE.md`, then newest `.handoffs/*.md`.
3. Read the `AGENTS.md` of the module you own.
4. Claim a chunk: one line under "In flight" in `STATE.md`, commit `state: claim <chunk>`.
5. Build the thinnest slice. Run the module's smoke check. Commit small: `module: what changed`.
6. On stop: `/handoff` -> `.handoffs/HANDOFF-YYYY-MM-DD-HHMM.md`, update `STATE.md`, commit, push.

Blocked on another module? Write it in `PENDING.md` or `STATE.md` "Blocked", pick the next unblocked chunk. Never edit another module's folder.

## Which skill when (Matt Pocock skills, adapted for hackathon speed)

| Moment | Skill | Note |
| --- | --- | --- |
| Starting a load-bearing chunk (agent prompt, checkout, interface change) | `/grill-me` | 5 minutes of questions saves an hour. Stop when the design tree is resolved, not when it feels thorough. |
| Starting a chunk that coins new terms | `/grill-with-docs` | Updates GLOSSARY.md as you go. |
| Breaking the next hour into pieces | `/to-tickets` | Local files mode. Tickets become "Next" lines in STATE.md. |
| Implementing a contract in INTERFACES.md | `/tdd` | One failing smoke test at the seam, then green. Full TDD is optional elsewhere. |
| Something is broken and unclear | `/diagnosing-bugs` | Reproduce first. Add the fix to LESSONS.md. |
| Before committing anything that touches checkout or the demo path | `/code-review` | Spec axis against INTERFACES.md and AGENTS.md hard rules. |
| Ending a session | `/handoff` | Writes the handoff note. |
| A message from another agent does not make sense | `/wait-what` | Re-pitch with GLOSSARY terms. |
| End of day | `/retro` | What to fix in AGENTS.md for next time. |

`/setup-matt-pocock-skills` was pre-answered: tracker = local files (`STATE.md` + `PENDING.md`), triage labels not used today, docs in `docs/`.

## Kun Chen's discipline (from `/kun`, OPINIONS.md)

Folded into AGENTS.md "Engineering discipline". The short version for today:
- Verify with the real thing. Hit `catalog.shopify.com`, read the real JSON. Never describe behavior you did not observe.
- Match validation to stakes. Checkout and the demo path get a second-agent adversarial pass. The stub backend gets a glance.
- Fresh context per chunk. New session, read STATE.md, go. Do not drag a 3-hour window.
- Complexity is a disease. Ask: does it need to exist, is it already here, does a dependency do it, then build the minimum.
- Judge the work, not the theater. A live demo with a hiccup you handle calmly beats a polished recording.
- Tolu is accountable. Agents do not add themselves as co-authors.

Kun's tools available on this Mac (global skills in `~/.claude/skills`): `/kun`, `/no-mistakes` (git gate; skip today unless a remote and CI exist), `lavish` (HTML review artifacts; good for a judge-facing architecture diagram), `gh-axi`, `quota-axi` (check remaining Claude/Codex/Antigravity quota before a long run), `chrome-devtools-axi`.

## Parallel-safety rules (git)

- One agent per top-level folder at a time. Owners in STATE.md.
- Small commits, `git pull --rebase` before push. Conflicts in STATE.md: keep both lines, newest on top.
- Shared files (`STATE.md`, `PENDING.md`, `GLOSSARY.md`, `LESSONS.md`, `docs/INTERFACES.md`): append, do not rewrite. Commit them separately from code: `state: ...`, `docs: ...`.
- Secrets: `.env` only. `.env.example` lists the names. `git grep -iE "AIza|sk-|api_key *= *['\"]"` must be empty before every push.

## Hour plan with owners (anchors, cut from the bottom)

| Time | agent-backend (Antigravity) | companion-screen (Claude Code) | device (Codex / Tolu) | Tolu |
| --- | --- | --- | --- | --- |
| 12:30 | `.env`, FastAPI skeleton, `/utterance` -> real catalog search, `/state` | Vite + React skeleton vs `scripts/stub_backend.py`, one card | Confirm CoreS3 toolchain (PENDING P2), `smoke_http.sh` vs stub | Answer PENDING P1-P6, create private remote |
| 13:30 | Gemini managed agent + `shop_search` tool, structured output, re-search | Candidate grid, pick highlight, reasons, flow bar | Wi-Fi + HTTP POST from device, speak canned text | Grill the agent prompt with `/grill-me` |
| 14:30 | `/intent` -> `create_checkout` via Shop MCP, `continue_url` in state only, redaction | QR view, clear button, health indicator | Push-to-talk record -> POST audio or text; button -> `/intent` | Walk the full loop on laptop only |
| 15:30 | Hardening: stale_pick, session clear, log redaction, `/health` | Polish: transaction-flow animation, typography | RFID badge read -> `/intent source: badge` | `/code-review` on backend checkout path |
| 15:30 | eval/: run system vs baseline on attendee utterances, managed-agent run, REPORT.md | Polish | RFID badge -> `/intent source: badge` | `/code-review` on checkout path; collect eval utterances if not done |
| 16:15 | **Freeze.** Demo-path bugs only. | Freeze. | Freeze. | Rehearse twice. Record the 1-minute video (phone filming device + screen + judge's phone). |
| 16:50 | | | | **Submit** at cerebralvalley.ai/e/gemini-4-nyc/hackathon/submit. Public repo link, video, demo link. |
| 17:00 | Round-one judging. 3 min live + 2 min Q&A. Laptop + device + hotspot ready. | | | |
