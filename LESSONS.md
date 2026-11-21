# LESSONS.md - Shop Counter

Problems we solved, newest first. Format: symptom, root cause, fix. Read this when stuck.

## 2026-11-21 Screen dependencies install on the Mac

- Symptom: Claude Desktop reported HTTP 403 from the npm registry.
- Cause: The failure occurred in that session. The same install succeeded on the Mac.
- Fix: Run `npm ci`, `npm run build`, and `npm test` from `companion-screen/` in Mac Terminal. Run Vite on loopback. Use a fixture backend for local checks. No sandbox settings need to change.

## 2026-11-21 Digital Sticker checkout works by exact variant

- Symptom: Global Catalog searches did not return the sticker, although its merchant page exists.
- Cause: Search results, storefront inventory, and exact-variant checkout are separate checks. The reason the sticker did not surface in search is unconfirmed.
- Fix: Verify the exact variant and live price on the merchant storefront. Send the variant to Shop MCP only on buy intent. A returned handoff with a contact warning is for review on the phone, not proof of payment.

## 2026-11-21 12:12 Catalog search works with zero credentials

- Symptom: unsure whether shop.dev search needs an API key before the vertical slice can start.
- Root cause: two endpoints exist. Shop MCP (`https://mcp.shop.com/`) and the Catalog API (`https://catalog.shopify.com/api/ucp/mcp`). The Catalog needs an agent profile URL in `meta.ucp-agent.profile` or it returns HTTP 422; Shop MCP sends its own profile and must not receive `meta`.
- Fix: `scripts/smoke_catalog.sh` uses the Catalog with Shopify's sample profile. 749 espresso machines came back under $300. Shop MCP needs headers `MCP-Protocol-Version: 2026-07-28`, `Mcp-Method: tools/call`, `Mcp-Name: <tool>` and `params._meta` with protocol version and clientInfo. See docs/INTERFACES.md.

## 2026-11-21 12:12 Prices are integers in minor units

- Symptom: "$300" budget must be sent as `30000`.
- Root cause: Shop returns `price.amount` as integer cents and filters on the same scale, on a USD basis.
- Fix: all budget math in the backend is in minor units. Convert to dollars only when rendering or speaking.

## 2026-11-21 12:05 Cerebral Valley event page is login-gated

- Symptom: `https://cerebralvalley.ai/e/gemini-4-nyc/details` returns a login page to tools.
- Root cause: details tab requires an account.
- Fix: the public page `https://cerebralvalley.ai/e/gemini-4-nyc` has prizes and format. docs/HACKATHON.md records it. Tolu reads the gated details on his phone and fills PENDING.md P1 (submission time and format).

## 2026-11-21 12:10 `claude` is not on PATH on this Mac

- Symptom: `claude --version` -> missing. `~/.claude/skills` exists with 40 skills, so Claude Code was used before.
- Root cause: CLI binary not installed or not linked. Claude.app (desktop) is installed.
- Fix: `npm install -g @anthropic-ai/claude-code` then `claude` in the repo root. Or use Claude Code inside the Claude desktop app. Codex (`codex` 0.147) and Antigravity.app are installed.
