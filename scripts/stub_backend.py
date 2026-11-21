#!/usr/bin/env python3
"""Stub agent-backend. Serves the shapes in docs/INTERFACES.md section 1 on :8787.

Stdlib only, so it runs anywhere. Companion-screen and device agents build
against this until the real backend lands. It walks through phases on each
call so the flow bar and QR can be exercised without Gemini or Shop.

Run: python3 scripts/stub_backend.py
"""
from __future__ import annotations

import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = 8787

# One fake session. Enough for a UI to render.
STATE: dict = {}


def fresh(session_id: str | None = None) -> dict:
    sid = session_id or f"s_{uuid.uuid4().hex[:8]}"
    return {
        "session_id": sid,
        "phase": "idle",
        "constraints": {"query": None, "budget_max_minor": None, "currency": "USD", "country": "US"},
        "candidates": [],
        "pick": None,
        "history": [],
        "handoff": None,
        "updated_at": int(time.time()),
    }


CANDIDATES_300 = [
    {
        "product_id": "gid://shopify/p/stub1",
        "variant_id": "gid://shopify/ProductVariant/stub1",
        "title": "Gaggia Carezza De LUXE Espresso Machine",
        "price_minor": 19900,
        "currency": "USD",
        "image_url": "https://placehold.co/600x600/222/fff?text=Gaggia",
        "seller": {"name": "Whole Latte Love", "domain": "wholelattelove.myshopify.com"},
        "rating": {"value": 4.6, "count": 128},
        "is_pick": True,
    },
    {
        "product_id": "gid://shopify/p/stub2",
        "variant_id": "gid://shopify/ProductVariant/stub2",
        "title": "Casabrews Compact 20-Bar Espresso Machine",
        "price_minor": 13999,
        "currency": "USD",
        "image_url": "https://placehold.co/600x600/333/fff?text=Casabrews",
        "seller": {"name": "Sabavi Home", "domain": "sabavi.myshopify.com"},
        "rating": {"value": 4.3, "count": 2140},
        "is_pick": False,
    },
    {
        "product_id": "gid://shopify/p/stub3",
        "variant_id": "gid://shopify/ProductVariant/stub3",
        "title": "CraftBrew Espresso Machine",
        "price_minor": 11999,
        "currency": "USD",
        "image_url": "https://placehold.co/600x600/444/fff?text=CraftBrew",
        "seller": {"name": "Chefman", "domain": "chefman.myshopify.com"},
        "rating": {"value": 4.1, "count": 410},
        "is_pick": False,
    },
]


def respond_utterance(state: dict, text: str) -> dict:
    """Pretend to search. 'two hundred' flips the budget and the pick."""
    cheaper = "two hundred" in text.lower() or "200" in text
    cands = [dict(c) for c in CANDIDATES_300]
    if cheaper:
        cands = [c for c in cands if c["price_minor"] <= 20000]
        for c in cands:
            c["is_pick"] = c["product_id"] == "gid://shopify/p/stub2"
        budget = 20000
        speech = (
            "Under two hundred, I'd take the Casabrews at one thirty-nine. "
            "Twenty-bar pump, pressure gauge, and over two thousand reviews. Want it?"
        )
        pick_id = "gid://shopify/p/stub2"
        reasons = ["Only 20-bar machine under $200", "2,140 reviews at 4.3 stars", "Pressure gauge for dialing in shots"]
    else:
        budget = 30000
        speech = (
            "I'd go with the Gaggia Carezza at one ninety-nine from Whole Latte Love. "
            "Real fifteen-bar pump and a steam wand. Want me to look cheaper?"
        )
        pick_id = "gid://shopify/p/stub1"
        reasons = ["Only one under $300 with a 15-bar pump", "Steam wand for milk drinks", "4.6 stars from 128 reviews"]

    did_research = bool(state["history"])  # any later utterance counts as a re-search in the stub
    state.update(
        phase="pick",
        constraints={"query": "espresso machine", "budget_max_minor": budget, "currency": "USD", "country": "US"},
        candidates=cands,
        pick={"product_id": pick_id, "reasons": reasons},
        handoff=None,
        updated_at=int(time.time()),
    )
    state["history"].append({"t": int(time.time()), "text": text, "did_research": did_research})
    return {"session_id": state["session_id"], "reply": {"speech": speech, "pick_id": pick_id, "did_research": did_research}}


def respond_intent(state: dict) -> dict:
    if not state["pick"]:
        return {
            "session_id": state["session_id"],
            "handoff": {"status": "error", "merchant": None, "total_minor": None, "currency": "USD"},
            "reply": {"speech": "I don't have a pick yet. Tell me what you're looking for."},
        }
    pick = next(c for c in state["candidates"] if c["is_pick"])
    # Fake continue_url. The real one carries an access key and must never be logged.
    state["handoff"] = {
        "status": "ready",
        "continue_url": f"https://example.com/checkout/stub/{uuid.uuid4().hex}",
        "merchant": pick["seller"]["name"],
        "total_minor": pick["price_minor"],
        "currency": pick["currency"],
        "expires_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 6 * 3600)),
    }
    state["phase"] = "handoff"
    state["updated_at"] = int(time.time())
    return {
        "session_id": state["session_id"],
        "handoff": {k: v for k, v in state["handoff"].items() if k != "continue_url"},
        "reply": {"speech": "Got it. Scan the code on the screen to review and pay on your phone."},
    }


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b"{}"
        try:
            return json.loads(raw or b"{}")
        except json.JSONDecodeError:
            return {}

    def _session(self, sid: str | None) -> dict:
        global STATE
        if not STATE or (sid and STATE.get("session_id") != sid):
            STATE = fresh(sid)
        return STATE

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._json(204, {})

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        if url.path == "/health":
            return self._json(200, {"ok": True, "catalog": "stub", "gemini": "stub"})
        if url.path == "/state":
            sid = parse_qs(url.query).get("session_id", [None])[0]
            return self._json(200, self._session(sid))
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        body = self._body()
        sid = body.get("session_id")
        if url.path == "/utterance":
            st = self._session(sid)
            st["phase"] = "searching"
            return self._json(200, respond_utterance(st, body.get("text", "")))
        if url.path == "/intent":
            return self._json(200, respond_intent(self._session(sid)))
        if url.path == "/session/clear":
            global STATE
            STATE = {}
            return self._json(200, {"ok": True})
        self._json(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:  # quiet, and never prints bodies
        print(f"{self.command} {self.path.split('?')[0]}")


if __name__ == "__main__":
    print(f"stub agent-backend on http://0.0.0.0:{PORT}  (Ctrl-C to stop)")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
