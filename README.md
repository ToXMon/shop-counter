# Shop Counter

A physical shopping agent for independent commerce. Talk to it, it searches Shopify's live catalog with a Gemini managed agent, explains its pick on a companion screen, and a badge tap hands the real checkout to your phone. Gemini 4 NYC Hackathon, 2026-11-21.

Private repo. Read `BRIEF.md` for the product, `AGENTS.md` for the rules, `STATE.md` for where we are.

## Start here (any agent, any tool)

```sh
cp .env.example .env            # fill GEMINI_API_KEY
scripts/smoke_catalog.sh        # live Shopify search, no key. Should print 5 espresso machines.
python3 scripts/stub_backend.py # fake backend on :8787 for UI/device work
scripts/smoke_backend.sh        # asserts the API contract (stub or real)
```

## Launch the agents

Run each in its own terminal, in this folder. Each reads `AGENTS.md` and claims a module in `STATE.md`.

| Tool | Command | Default module |
| --- | --- | --- |
| Antigravity | open `Antigravity.app`, File > Open `gem_hack` | `agent-backend/` |
| Claude Code | `npm i -g @anthropic-ai/claude-code` once, then `claude` | `companion-screen/` |
| Codex | `codex` | `device/` |

Skills are in `.agents/skills/` (Claude Code sees them via `.claude/skills`). Start a load-bearing chunk with `/grill-me`. End a session with `/handoff`.

Full playbook: `docs/ORCHESTRATION.md`. Contracts: `docs/INTERFACES.md`. Event: `docs/HACKATHON.md`.
