# AGENTS.md - Shop Counter (root)

This repo uses DOX (github.com/agent0ai/dox): a hierarchy of AGENTS.md files keeps project context precise for every coding agent that works here.

- This root file holds project-wide rules and the doc index.
- Each module folder has its own AGENTS.md with local rules.
- Before you edit, walk the doc tree from this root to the folder you will touch. Read every AGENTS.md on that path.
- After a meaningful change, update the AGENTS.md files you affected, and update STATE.md.

This file is written for Antigravity, Claude Code, and Codex alike. CLAUDE.md points here; every tool reads AGENTS.md.

## Doc index

- BRIEF.md - the project brief: problem, demo loop, architecture, build plan, cut points.
- STATE.md - living status: what works, what is in flight, who owns what, what is next. Update it every time you start or finish a chunk.
- GLOSSARY.md - shared project language. One term per concept, used in prose and in code names.
- LESSONS.md - problems we solved, newest first. Read it when stuck; the answer may already be there.
- PENDING.md - decisions blocked on Tolu.
- docs/INTERFACES.md - the contracts between modules. Cross-module work goes through these, never by editing another module's folder.
- docs/HACKATHON.md - event facts, prizes, what judges score, submission checklist.
- docs/ORCHESTRATION.md - how Antigravity, Claude Code and Codex share this repo; which skill to use when; hour plan with owners.
- scripts/ - `smoke_catalog.sh` (live Shopify search), `stub_backend.py` (fake backend on :8787), `smoke_backend.sh` (asserts the API contract). Run them; do not re-derive what they prove.
- .agents/skills/ - project skills (Matt Pocock engineering + productivity, Kun). `.claude/skills` points here. Antigravity and Codex read `.agents/skills/` directly.
- .handoffs/ - session handoff notes, newest first. Committed on purpose: parallel agents on different machines need them.
- device/AGENTS.md - CoreS3 firmware rules.
- agent-backend/AGENTS.md - agent and Shop API backend rules.
- companion-screen/AGENTS.md - web UI rules.

## Session start (every agent, every session)

1. `git pull --rebase`.
2. Read STATE.md, then the newest file in .handoffs/ if any exist.
3. Read the AGENTS.md of the module you will touch.
4. Claim your chunk: add one line under "In flight" in STATE.md before you start, and commit it.

## Hard rules (never break)

- No secrets in the repo. `.env` is gitignored; use the names in `.env.example`. If a secret ever lands in a commit, say so in STATE.md immediately.
- Never log or commit checkout IDs or checkout URLs. They contain checkout-access keys. Redact them in logs.
- No card numbers, auth tokens, or shopper credentials on the device. Payment approval happens on the shopper's phone only.
- A badge tap signals intent, not payment authorization. The phone review is the trust boundary. If merchant, items, or total change, require a fresh approval.
- Clear each shopper session. Never reuse one shopper's session or token for the next.
- Shopify catalog products go through Shop cart/checkout. Never use spend requests for them; the Shop docs say spend requests are for non-Shopify stores and are not a fallback for failed Shop checkout.
- Shop checkout can be created without shopper sign-in. Hand it to the shopper with the returned `continue_url` so they review and pay on their phone. Keep anything credential-bearing on the backend, never on the device.
- x402 is out of the MVP. A testnet-only stretch goal at most, and only after the demo works end to end.
- This repo is **public** (hackathon rule: https://github.com/ToXMon/shop-counter). Run `scripts/secret_scan.sh` before every push. A leaked key means rotate it first, then rewrite history.
- Hackathon hard requirements (docs/HACKATHON.md): at least two Gemini 4 models with distinct jobs plus the Decisions API; voice central, not a text box; the companion screen is never "the main feature"; no mocked model responses in the demo; eval inputs must include utterances we did not write.

## Parallel work rules

- One agent per top-level module folder at a time. Current owners are listed in STATE.md.
- Commit early, commit often, in small commits. `git pull --rebase` before you push. Commit message format: `module: what changed` (example: `device: badge tap posts intent`).
- Interfaces between modules live in docs/INTERFACES.md. Change an interface only when it really has to change, and record the change in STATE.md so the other agents see it.
- If your chunk is blocked on another module, note it in PENDING.md and pick up the next unblocked chunk from STATE.md instead of guessing at the other module.

## Engineering discipline

Adapted from Matt Pocock's AI Hero skills (github.com/mattpocock/skills), Kun Chen's published engineering opinions (github.com/kunchenguid/kun), and the agent.me reference Tolu supplied. Adapted for hackathon speed; the intent is preserved, the ceremony is cut.

- Align before you build. If a task is ambiguous, grill Tolu with questions until the design tree is resolved (the /grill-me pattern). Do not guess on load-bearing decisions: interfaces, the demo flow, anything touching checkout.
- Use the GLOSSARY. One term per concept, in prose and in code. If you coin a new domain term, add it to GLOSSARY.md in the same commit.
- Feedback loops beat reasoning. Verify with the real thing: run the code, hit the real shop.dev endpoint, read the real response. Never claim behavior you did not observe.
- Small, deliberate steps. Get the thinnest vertical slice working end to end before adding breadth. The build plan in BRIEF.md is ordered this way.
- Tests at the seams. Full TDD is optional today, but every contract in docs/INTERFACES.md gets at least one smoke check that runs unattended, so a parallel agent can verify its side without the other side running.
- Match validation rigor to stakes. The demo path and anything touching checkout gets adversarial review (a second agent pass or a careful manual pass). Internal tooling gets a light pass.
- Fresh context per chunk. Start a new session for each new chunk and pick up from STATE.md and the handoffs, instead of dragging a rotting context window.
- Escalate, do not silently decide. Anything subjective or risky goes to PENDING.md for Tolu, with your recommendation.
- Tolu is accountable for this repo; agents are tools. Do not add yourself as commit co-author.
- Complexity is a disease. Ask, in order: does this need to exist? Is it already in this codebase? Does a dependency do it? Then build the minimum that works, and stop.
- Judge the work, not the theater: prefer honest live behavior with hiccups over a polished fake. No recorded happy-path demos passed off as live.

## Documentation style

From the agent.me reference Tolu supplied (AJ-Gonzalez gist), lightly adapted.

- Document well enough that a human could work on this repo with no agent help.
- Technical docs use simplified English: short sentences (instructions under 20 words), one instruction per sentence, one word per meaning, active voice, no synonym rotation.
- Read a file before you edit it, every time. Re-read after editing; line numbers die with each change.
- Comment the why, not the what.
- Type hints on every function in typed languages.
- When you solve a non-obvious problem (build failure, environment quirk, subtle bug), add a LESSONS.md entry: symptom, root cause, fix.

## When you pause or finish a session

1. Write `.handoffs/HANDOFF-YYYY-MM-DD-HHMM.md`: what is live, what is in flight, open decisions (point to PENDING.md), next steps.
2. Update STATE.md.
3. Commit both. Handoffs are committed in this repo (hackathon exception to the usual gitignored-handoffs pattern) because parallel agents work from different machines.
