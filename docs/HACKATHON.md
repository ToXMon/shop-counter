# docs/HACKATHON.md - Gemini 4 NYC Hackathon

Sources: https://cerebralvalley.ai/e/gemini-4-nyc (public page, read 2026-11-21 12:05 EST), Yat's List listing. The `/details` tab is login-gated; Tolu fills the gaps in PENDING.md P1.

## Facts

- Name: Gemini 4 NYC Hackathon. Hosts: Cerebral Valley and Google DeepMind.
- When: Sat Nov 21, 2026, 9:00 AM - 10:00 PM EST. Where: The Malin Chelsea, New York.
- Fully in-person. Max team size 4. Tolu is solo.
- Theme (verbatim): "Push the boundaries of what's possible with Gemini 4. Explore the frontier, from advanced reasoning and visual coding to robotics and world models. We're looking for ambitious projects that push Gemini to its limits. We want to see something that wasn't possible last week."
- Judges: Google DeepMind team in-house, plus ecosystem judges.

## Prizes

| Prize | Amount |
| --- | --- |
| First | $7,500 |
| Second | $5,000 |
| Third | $2,500 |
| Best Use of Managed Agents | $5,000 |

Shop Counter targets **Best Use of Managed Agents** first and a top-three place second. The brief also names a Shopify track; confirm on the gated page (PENDING P1).

## What judges will score (inferred from the theme; confirm on the gated page)

1. Pushes Gemini: the agent loop must be visibly agentic. Re-search on a changed constraint, live, with the model explaining its pick. Not a scripted happy path.
2. Managed Agents: the backend uses the Interactions API managed agent with real tools (`shop_search`, `create_cart`, `create_checkout`). Say "managed agent" in the pitch and show the tool calls in the flow view.
3. Not possible last week: the physical, voice-first form factor on top of Shopify's live catalog and sign-in-free checkout. Say why that combination is new.
4. Works live. Judges in this format walk the floor; a 60-second loop that works beats a 5-minute video.

## Demo loop (from BRIEF.md, in judge-time)

| Beat | What the judge sees | Must be live? |
| --- | --- | --- |
| 1 | Speaks "espresso machine under three hundred" to the device | yes |
| 2 | Cards appear on the companion screen; device speaks the pick and why | yes |
| 3 | "Under two hundred" -> re-search, new pick, new reasons | **yes, this is the prize** |
| 4 | Badge tap -> device says "scan to review" | yes (button fallback ok) |
| 5 | QR on companion screen -> judge's phone -> real Shop checkout | yes |
| 6 | Barcode scan as alternate entry | no, cut first |

## Pitch (60 s) and "Do not claim" list

Both are in BRIEF.md. Keep them current with what actually works. Never say the badge authorizes payment. Never say spend requests work for Shopify catalog products.

## Submission checklist (fill from the gated page)

- [ ] Submission form URL and time (PENDING P1)
- [ ] Repo link (private? make a judge-readable copy if required)
- [ ] 60-s pitch rehearsed twice
- [ ] Screen-recorded backup of the full loop (laptop + phone)
- [ ] Device charged, Wi-Fi hotspot tested at the venue
- [ ] Companion screen open on the laptop, `GET /health` green
- [ ] `.env` present, no secrets in the repo (`git grep -i api_key` clean)
