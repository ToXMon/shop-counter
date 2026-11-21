# companion-screen/AGENTS.md

Owner: see STATE.md (default Claude Code). Read root AGENTS.md first.

## What this module is

A single-page web app (Vite + React + TypeScript; no backend of its own) that polls `GET /state` and renders the shopper's session for a big screen. Spec: docs/INTERFACES.md section 5.

Backend URL from `VITE_BACKEND_URL` (default `http://localhost:8787`).

## Build order

1. Skeleton. Poll `/state` from `scripts/stub_backend.py`. Render one candidate card. Commit.
2. Candidate grid (3-5), pick highlighted, reasons list, price via `Intl.NumberFormat`.
3. Flow bar lit by `phase`. Animate on `did_research`.
4. Handoff view: QR of `continue_url` (use `qrcode` npm package, render to canvas), merchant, total, "Scan to review and pay on your phone". Never render the URL as text.
5. Clear button -> `POST /session/clear`. Health dot from `/health`.
6. Fallback input: text box -> `POST /utterance`. Mic button via Web Speech API if time allows (PENDING P3b).
7. Polish last: typography, motion, dark background for the projector.

## Hard rules (module-specific)

- The companion screen is the only thing that ever displays `continue_url`, and only as a QR. No `<a href>`, no text, no console.log of it.
- Readable from 3 metres: product title >= 28 px, price >= 36 px, one pick reason per line.
- Works in Chrome on the laptop and on a phone browser. No native deps.
- Poll interval 500 ms. Stop polling when the tab is hidden.
- No state of its own beyond the last `/state` payload and the input box.

## Smoke

`npm run dev` with `python3 scripts/stub_backend.py` running. One card and the QR render. `npm run build` passes typecheck.
