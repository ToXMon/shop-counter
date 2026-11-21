# Launch Shop Counter

2026-11-21 · Owner: Tolu · Freeze 16:15 ET; submit by 17:00 ET.

## Verified sticker

The merchant storefront returned Digital Sticker, variant `68033173323939`, available and not shipped. Its price was $0.50 USD. Shop MCP accepted one unit for `monday-cartoons.myshopify.com` using `gid://shopify/ProductVariant/68033173323939`. It returned an `incomplete` checkout with a handoff URL and a buyer-contact warning. The sample total was $0.54 with tax. No payment was made. A phone scan still needs testing. Shopify Global Catalog searches did not surface the sticker; do not claim it is excluded or that it cannot be sold.

Ask the owner now whether they want the current price or will change it to $0.99. If they change it, recheck both storefront and fresh checkout. Never hard-code or advertise either price. Keep the exact SKU as an explicitly sourced merchant listing, and use live shop.dev search for broader discovery. Do not silently swap in another seller.

## Start three sessions at once

Use one worktree per lane and the same base commit. If a lane already has a session, give it the updated prompt rather than starting a second writer. The main checkout is for integration. Each lane records its claim and handoff in separate commits; the integrator reconciles shared docs rather than merging competing edits. Do not stage other agents' untracked files. Check `/model` or the harness model picker before engineering work. The current AdaL catalog lists DeepSeek V4 Flash (`deepseek-deepseek-v4-flash`) for ordinary coding and tests. Use a verified open-weight route whenever available; note the concrete blocker before using a proprietary coding model. The deployed product's two Gemini 4 models and Decisions API are event requirements, independent of the coding model.

### Antigravity: backend

> Read AGENTS.md, STATE.md, agent-backend/AGENTS.md, docs/INTERFACES.md and the Verified sticker section here. Own only agent-backend/. Ship a typed utterance to a live result first. For an explicit Monday Cartoons Digital Sticker request, resolve the verified merchant variant from the storefront source; keep broad discovery on live shop.dev. Implement a one-item Shop MCP checkout only after explicit intent tied to the displayed offer. Treat an incomplete checkout with a valid continue_url and buyer-contact requirement as needing phone review. Never collect contact or payment details on the device. If seller, item, or confirmed price changes, invalidate the old intent and request a fresh one. Never log checkout IDs or URLs. Restrict checkout-bearing state to the paired companion screen; do not serve it over an open venue LAN. Run one redacted checkout check, never complete payment. Then verify Hydrogen and Neon on the event key and wire audio, constraint parsing, recommendation, and a Decisions API clarification gate. Keep the managed eval off the live critical path. Report commit, tests, and blockers.

### Claude Code: companion screen

> Read AGENTS.md, STATE.md, companion-screen/AGENTS.md, docs/INTERFACES.md and docs/LAUNCH.md. Own only companion-screen/. Start against the stub now. Build a readable product card with live price, a typed input for testing, and browser push-to-talk as the hardware fallback. Render a local QR only for a valid handoff, including when the shopper must finish contact details on their phone. Never send a checkout URL to a QR service or log it. Clear the QR when the offer or session changes. Do not hard-code $0.99 or claim that payment happened. Use Matt Pocock's seam-testing approach. Return a build result and run command. Do not change the API spec without the integrator.

### Codex: CoreS3

> Read AGENTS.md, STATE.md, device/AGENTS.md, docs/INTERFACES.md and docs/LAUNCH.md. Own only device/. Start the Arduino/M5Unified PlatformIO project. First prove the board compiles and a button sends intent for the current paired offer against the stub. Then add push-to-talk WAV capture. Add RFID 2 only after the button path works; use a demo tag, not an attendee credential. Never send a tag ID, store checkout URLs, or guess at session pairing. Document USB flashing and the private-hotspot setup. Report compile evidence, board evidence separately, and your blocker. If audio slips, keep the button and use browser audio.

## Integration order

1. Tolu plugs in the CoreS3, adds the Gemini key locally, confirms the selling price with the owner, and asks a few attendees for consent to contribute unrehearsed requests. Keep raw recordings and identifying data out of the public repo.
2. At the first checkpoint, screen and device prove their seams against the stub. Backend proves live sticker lookup and checkout. Agree on pairing and offer revision before wiring intent.
3. Integrate backend and screen on the laptop first. Scan a fresh QR on a phone and confirm the merchant, item, quantity, and current price. Stop before payment. Test stale intent and session clear. Keep the checkout QR out of public recordings or mask it.
4. Add CoreS3 intent and voice. Keep the browser mic as fallback. Demo a genuine follow-up, such as switching from a mailed item to a digital product. Report baseline and full-system results honestly on the same attendee requests.
5. Freeze at 16:15 ET. Record the one-minute demo and submit at 16:50 ET. Only claim Managed Agents if a hosted run actually completed.
