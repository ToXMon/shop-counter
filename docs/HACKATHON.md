# docs/HACKATHON.md - Gemini 4 NYC Hackathon (from the gated Participant Guide, read 12:32 EST)

Source: https://cerebralvalley.ai/e/gemini-4-nyc/details (logged in). Builder guide PDF: `docs/GEMINI4_BUILDER_GUIDE.pdf` (12 pages, read it before touching agent-backend).

## Clock (hard)

| Time | What |
| --- | --- |
| 10:30 | Hacking began |
| 13:00 | Lunch |
| **17:00** | **Project submissions due** at https://cerebralvalley.ai/e/gemini-4-nyc/hackathon/submit |
| 17:00-18:45 | Round one judging: 3 min live demo + 2 min Q&A, in groups by room |
| 19:00-20:00 | Round two: top six, on stage, same format |
| 20:15 | Winners |

Venue: The Malin Chelsea, 220 W 26th St. See the participant guide for venue Wi-Fi.

## Submission needs

- Public repo (rule: "repositories must be public"). Done: https://github.com/ToXMon/shop-counter
- **One-minute demo video** showing only what was built today.
- Demo link accessible. All team members on the submission page.
- Judges must be able to tell what was built during the event. No pre-existing project.

## Hard requirements (every project)

1. Build inside one of two problem statements (below).
2. **Use at least two Gemini 4 models (Argon, Carbon, Neon, Hydrogen), each with a clear job.**
3. **Go beyond a text box**: voice, camera, video, images, documents or generated media central to how it works.
4. Not allowed: text-only chatbots, demos that only run on scripted inputs, evals made entirely of examples the team wrote to pass.
5. Anti-projects (disqualify): any project where **a dashboard is the main feature**, image analyzers, Streamlit apps, basic RAG, chatbots for education/health/nutrition, etc.

## Problem statements

**One: 5 Sigma.** Pick a real task today's agents do unreliably; build a Gemini 4 system that does it reliably; prove it with an eval on inputs you did not prepare, against a simple baseline; show where it still fails and what you changed.

**Two: Element 119.** Something that only works because Gemini 4 can see, hear and generate media. Audio/video/images are the core input. Use any Gemini 4 models plus the Decisions API. Push until it breaks, show where.

**Bonus: Build with Commerce (Shopify).** Use shop.dev, product discovery to shopping agent. Prize: Best use of Shopify, $2,500 Shop Cash. Shopify solutions engineers on site and in Discord.

### Shop Counter's placement

Primary: **Element 119**. Voice is the core input (a physical device you talk to), speech is the core output, the companion screen is secondary. We also borrow the 5 Sigma proof: a small eval of unrehearsed utterances against a single-model baseline. That feeds "Proof It Works".

Say this sentence to judges: "The device is the product. The screen is a window into what the agent is doing."

## Judging rubric (round one weights; round two equal weights)

| Criterion | Weight | What we show |
| --- | --- | --- |
| Live demo | 35% | Judge speaks an unrehearsed request to the CoreS3. Live catalog search, spoken pick, re-search on a changed constraint, badge tap, QR to the judge's own store checkout. |
| Proof it works | 25% | `eval/` folder: 20+ utterances we did not write for the demo (collected from other attendees), scored by Decision 1 rubric against a single-Neon-call baseline; a `FAILURES.md` with what broke and what we changed. The agent also checks its own pick against the constraints before speaking (self-check gate). |
| Creativity | 20% | Voice-first physical commerce for independent merchants; intent-not-payment trust boundary; checkout lands on the shopper's phone. |
| Gemini 4 + Decisions API use | 20% | Two Gemini 4 models with distinct jobs plus Decision 1 gates. See docs/INTERFACES.md section 3. |

## Prizes

1st $7,500 · 2nd $5,000 · 3rd $2,500 · **Best use of Managed Agents $5,000** · **Best use of Shopify $2,500 Shop Cash**.

Targets, in order: Best use of Shopify (we are the only voice-device shop.dev build in the room, probably), Best use of Managed Agents (the managed agent runs the eval harness and the self-check), then top three.

## Model plan (from the Builder Guide; IDs verified there)

| Job | Model ID | Why this one |
| --- | --- | --- |
| Shopping agent: plan search, compare candidates, choose and explain the pick | `gemini-4-neon` (thinking high) | Fast frontier reasoning while a person waits |
| Parallel workers: parse constraints from a transcript, normalise prices, draft the 45-word spoken reply, score each candidate's fit in parallel | `gemini-4-hydrogen` (thinking medium) | Fast workhorse, cheap, subagents |
| Gates: "did the constraint change?" (re-search trigger), "is this a buy intent?", "does the pick satisfy the constraints?" (self-check), candidate rubric scoring | `gemini-decision-1` (v1beta Decisions API) | 150-250 ms, calibrated confidence, zero output tokens |
| Speech to text | `gemini-3.5-transcribe` (batch WAV from device) | Device posts WAV; backend transcribes |
| Text to speech | `gemini-3.8-flash-tts` | Spoken reply back to device/laptop |
| Eval harness + self-check runner (Managed Agents prize) | `antigravity-preview-09-2026`, `environment="remote"`, model `gemini-4-hydrogen` | Runs the eval in a Google-hosted sandbox, writes `eval/REPORT.md` |

Builder-guide prohibitions: no temperature/top-p/top-k/thinking-budget on Gemini 4; no `minimal` thinking level on Neon/Hydrogen; no manual context caching; declare native tools or structured output, never ask for raw JSON in prose; no mocked responses or exposed keys in the demo.

Setup from the guide (run in agent-backend's venv): `pip install -U "google-genai>=3.2.0"`. Skills `gemini-api-dev` and `gemini-live-api-dev` are already in `.agents/skills/`. Live docs MCP: `npx add-mcp "https://gemini-api-docs-mcp.dev"` (optional).

## Demo product (the judge's store)

The judge owns https://mondaycartoons.com (`monday-cartoons.myshopify.com`, shop id 46411219107). Verified in the Global Catalog at 12:33 EST, five products:

| Product | Price | Variant id |
| --- | --- | --- |
| Monday Cartoons Hat | $38.00 | gid://shopify/ProductVariant/46159175811235 |
| Men's Celestial T-Shirt | $89.00 | gid://shopify/ProductVariant/45342455595171 |
| Women's Celestial T-Shirt | $89.00 | gid://shopify/ProductVariant/45402961182883 |
| Champions T-Shirt | $99.00 | gid://shopify/ProductVariant/47778026520739 |
| "Balance" Photo Print | $9.00 | gid://shopify/ProductVariant/45772598444195 |

Global Catalog searches did not surface Digital Sticker. The storefront returned an available variant, and Shop MCP accepted it for checkout. See `docs/LAUNCH.md` for evidence and `PENDING.md` P7 for the price decision.

Demo: ask for a Monday Cartoons item, then narrow the request to a digital sticker. Identify the storefront as the sticker source. Tap for intent and scan the QR to review the sticker on the merchant checkout. Show the live price; leave payment to the shopper.

Keep the espresso-machine query as the open-catalog demo for the "unrehearsed input" test: let the judge ask for anything.

## Do not claim

BRIEF.md list stands. Add: never call the companion screen "the dashboard" in front of judges.
