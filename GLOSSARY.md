# GLOSSARY.md - Shop Counter

One term per concept. Use these words in prose, code names, and API fields. Add a term in the same commit that introduces it.

| Term | Meaning | Not |
| --- | --- | --- |
| **shopper** | The person talking to the device. At the demo, a judge. | user, customer, buyer |
| **utterance** | One spoken or typed request from the shopper, as text. | query, prompt, message |
| **pick** | The one product the agent recommends, with its **reasons**. | recommendation, result, top hit |
| **offer_id** | Deterministic identifier `<seller.domain>:<variant_id>:<price_minor>` binding a physical **intent** tap to the currently displayed **pick** offer. | quote id, cart token |
| **candidates** | The products the agent compared before choosing the pick. Shown as cards. | results, options, list |
| **constraint** | A limit the shopper states: budget, brand, feature. "Under two hundred" is a budget constraint. | filter, preference |
| **re-search** | A new catalog search triggered by a changed constraint. The agentic beat of the demo. | refine, retry |
| **intent** | A physical signal that the shopper wants to buy the pick. Badge tap or button. Never payment authorization. | purchase, approval, confirm |
| **handoff** | Moving the purchase to the shopper's phone via `continue_url` shown as a QR. | redirect, checkout link |
| **continue_url** | Shop's URL where the shopper reviews and pays. Contains an access key. Never logged. | checkout URL, payment link |
| **session** | One shopper's state on the backend: utterances, candidates, pick, cart, checkout. Cleared between shoppers. | conversation, thread |
| **state** | The JSON snapshot of a session the companion screen renders. `GET /state`. | view model, store |
| **device** | The M5Stack CoreS3: mic, speaker, RFID, 2-inch screen. A thin client. | hardware, terminal, kiosk |
| **companion screen** | The web app on a laptop/phone that renders cards, flow, and the QR. | dashboard, display, UI |
| **agent** | The Gemini managed agent inside agent-backend that plans searches and explains the pick. | bot, model, LLM |
| **catalog** | Shopify's Global Catalog, searched via `catalog.shopify.com`. | store, inventory, Shopify |
| **variant** | The specific purchasable item (size/color) a product search returns. Carries `id`, `price`, `seller`. | SKU, product |
| **seller** | The Shopify merchant selling a variant. `seller.domain` is what checkout needs. | store, shop, vendor |
| **minor units** | Prices from Shop are integers in cents: `19900` = $199.00. | dollars, float price |
| **flow** | The transaction-flow visualization on the companion screen: search -> compare -> pick -> intent -> handoff. | pipeline, steps |
| **cut point** | A feature we drop, in order, if time runs out. BRIEF.md lists them. | nice-to-have, stretch |
| **chunk** | One unit of work an agent claims in STATE.md. Fits one session. | task, ticket, story |
| **handoff note** | A file in `.handoffs/` an agent writes when it stops. Different from the shopper **handoff**. | summary, log |
