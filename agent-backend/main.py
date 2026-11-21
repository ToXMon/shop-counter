"""FastAPI server for Shop Counter `agent-backend` (docs/INTERFACES.md section 1).

Hard rules enforced:
- Fails loudly at boot if `GEMINI_API_KEY` is missing.
- Never logs or returns `continue_url` or checkout IDs on `/intent` or device routes.
- Restricts `continue_url` in `GET /state` to loopback companion requests.
- Clears shopper session completely on `POST /session/clear`.
- Invalidates intent (`stale_pick`) if merchant, item, or confirmed price changes.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
import uuid
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

import agent
import models
import pipeline
import shop
import speech

# Fail loudly at import/boot if GEMINI_API_KEY is missing
models.require_api_key()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("shop_counter.main")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:8787",
    "http://127.0.0.1:8787",
]

app = FastAPI(title="Shop Counter Agent Backend", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# In-memory session store. Track latest active session_id so companion screen / device pair seamlessly.
SESSIONS: dict[str, dict[str, Any]] = {}
ACTIVE_SESSION_ID: str | None = None


def fresh_session(session_id: str | None = None) -> dict[str, Any]:
    sid = session_id or f"s_{uuid.uuid4().hex[:8]}"
    return {
        "session_id": sid,
        "phase": "idle",
        "constraints": {
            "query": None,
            "budget_max_minor": None,
            "currency": "USD",
            "country": "US",
        },
        "candidates": [],
        "pick": None,
        "history": [],
        "handoff": None,
        "updated_at": int(time.time()),
    }


def get_or_create_session(session_id: str | None = None) -> dict[str, Any]:
    global ACTIVE_SESSION_ID
    if session_id and session_id in SESSIONS:
        ACTIVE_SESSION_ID = session_id
        return SESSIONS[session_id]
    if not session_id and ACTIVE_SESSION_ID and ACTIVE_SESSION_ID in SESSIONS:
        return SESSIONS[ACTIVE_SESSION_ID]
    st = fresh_session(session_id)
    SESSIONS[st["session_id"]] = st
    ACTIVE_SESSION_ID = st["session_id"]
    return st


def _is_loopback_request(request: Request) -> bool:
    client_host = (request.client.host if request.client else "") or ""
    return client_host in ("127.0.0.1", "::1", "localhost", "testclient")


def public_state_view(state: dict[str, Any], *, allow_continue_url: bool = True) -> dict[str, Any]:
    """Build the public JSON snapshot for `GET /state`, stripping internal fields."""
    handoff = state.get("handoff")
    if isinstance(handoff, dict):
        if allow_continue_url:
            handoff_view = {
                "status": handoff.get("status", "ready"),
                "continue_url": handoff.get("continue_url"),
                "offer_id": handoff.get("offer_id"),
                "product_id": handoff.get("product_id"),
                "variant_id": handoff.get("variant_id"),
                "merchant": handoff.get("merchant"),
                "total_minor": handoff.get("total_minor"),
                "currency": handoff.get("currency", "USD"),
                "expires_at": handoff.get("expires_at"),
            }
            if handoff.get("via"):
                handoff_view["via"] = handoff["via"]
            if handoff.get("requires_phone_contact") is not None:
                handoff_view["requires_phone_contact"] = handoff["requires_phone_contact"]
        else:
            handoff_view = {
                k: v
                for k, v in handoff.items()
                if k != "continue_url"
            }
    else:
        handoff_view = None

    return {
        "session_id": state["session_id"],
        "phase": state.get("phase", "idle"),
        "constraints": state.get(
            "constraints",
            {"query": None, "budget_max_minor": None, "currency": "USD", "country": "US"},
        ),
        "candidates": state.get("candidates", []),
        "pick": state.get("pick"),
        "reply": state.get("reply"),
        "history": state.get("history", []),
        "handoff": handoff_view,
        "updated_at": state.get("updated_at", int(time.time())),
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    catalog_ok = await shop.check_catalog_health()
    gemini_ok = False
    try:
        models.require_api_key()
        gemini_ok = True
    except Exception:
        gemini_ok = False
    return {
        "ok": bool(catalog_ok and gemini_ok),
        "catalog": "ok" if catalog_ok else "error",
        "gemini": "ok" if gemini_ok else "error",
    }


@app.get("/state")
async def get_state(request: Request, session_id: str | None = None) -> dict[str, Any]:
    if not _is_loopback_request(request):
        raise HTTPException(status_code=403, detail="State is restricted to the local companion screen")
    st = get_or_create_session(session_id)
    return public_state_view(st, allow_continue_url=True)


@app.get("/state/stream")
async def stream_state(request: Request, session_id: str | None = None) -> StreamingResponse:
    if not _is_loopback_request(request):
        raise HTTPException(status_code=403, detail="State stream is restricted to the local companion screen")

    async def event_gen():
        last_updated = -1
        while True:
            if await request.is_disconnected():
                break
            st = get_or_create_session(session_id)
            if st.get("updated_at") != last_updated:
                last_updated = st.get("updated_at", 0)
                payload = json.dumps(public_state_view(st, allow_continue_url=True))
                yield f"data: {payload}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_gen(), media_type="text/event-stream")


def _parse_optional_bool(raw: Any) -> bool | None:
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    val = str(raw).strip().lower()
    if val in ("1", "true", "yes", "on"):
        return True
    if val in ("0", "false", "no", "off"):
        return False
    return None


@app.post("/utterance")
async def post_utterance(request: Request) -> dict[str, Any]:
    content_type = (request.headers.get("content-type") or "").lower()
    session_id: str | None = None
    text: str | None = None
    audio_bytes: bytes | None = None
    audio_mime_type = "audio/wav"
    include_tts: bool | None = _parse_optional_bool(request.query_params.get("include_tts"))

    if "multipart/form-data" in content_type:
        form = await request.form()
        session_id = str(form["session_id"]) if "session_id" in form and form["session_id"] else None
        text = str(form["text"]) if "text" in form and form["text"] else None
        if "include_tts" in form:
            include_tts = _parse_optional_bool(form.get("include_tts"))
        audio_field = form.get("audio")
        if audio_field is not None and hasattr(audio_field, "read"):
            audio_bytes = await audio_field.read()
            audio_mime_type = getattr(audio_field, "content_type", None) or "audio/wav"
    else:
        try:
            body = await request.json()
        except Exception:
            body = {}
        session_id = body.get("session_id")
        text = body.get("text")
        if "include_tts" in body:
            include_tts = _parse_optional_bool(body.get("include_tts"))
        if body.get("audio_b64"):
            audio_bytes = base64.b64decode(body["audio_b64"])
            audio_mime_type = body.get("audio_mime_type", "audio/wav")

    st = get_or_create_session(session_id)
    return await pipeline.run_utterance_pipeline(
        st,
        text=text,
        audio_bytes=audio_bytes,
        audio_mime_type=audio_mime_type,
        include_tts=include_tts,
    )


@app.post("/transcribe")
async def post_transcribe(request: Request) -> dict[str, Any]:
    """Standalone audio transcription endpoint for push-to-talk verification."""
    content_type = (request.headers.get("content-type") or "").lower()
    audio_bytes: bytes = b""
    mime_type = "audio/wav"
    if "multipart/form-data" in content_type:
        form = await request.form()
        audio_field = form.get("audio")
        if audio_field is not None and hasattr(audio_field, "read"):
            audio_bytes = await audio_field.read()
            mime_type = getattr(audio_field, "content_type", None) or "audio/wav"
    else:
        body = await request.json()
        if body.get("audio_b64"):
            audio_bytes = base64.b64decode(body["audio_b64"])
            mime_type = body.get("mime_type", "audio/wav")

    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Missing audio payload")
    text = await speech.transcribe_audio(audio_bytes, mime_type=mime_type)
    return {"ok": True, "text": text}


@app.post("/tts")
async def post_tts(request: Request) -> dict[str, Any]:
    """Standalone text-to-speech endpoint for push-to-talk verification."""
    body = await request.json()
    text = str(body.get("text") or "").strip()
    voice = str(body.get("voice") or "Kore")
    if not text:
        raise HTTPException(status_code=400, detail="Missing text")
    res = await speech.synthesize_speech(text, voice=voice)
    return {"ok": bool(res.get("audio_b64")), **res}


@app.get("/session/offer")
async def get_session_offer(session_id: str | None = None) -> dict[str, Any]:
    """Device-safe session pairing and current offer-ID lookup (never contains continue_url)."""
    st = get_or_create_session(session_id)
    pick_info = st.get("pick") or {}
    pick_cand = next(
        (c for c in st.get("candidates", []) if c.get("is_pick")),
        None,
    )
    return {
        "session_id": st["session_id"],
        "phase": st.get("phase", "idle"),
        "offer_id": pick_info.get("offer_id"),
        "pick_id": pick_info.get("product_id"),
        "variant_id": pick_info.get("variant_id"),
        "price_minor": pick_info.get("price_minor"),
        "merchant": (pick_cand.get("seller") or {}).get("name") if pick_cand else None,
        "updated_at": st.get("updated_at", int(time.time())),
    }


@app.post("/intent")
async def post_intent(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        body = {}

    session_id = body.get("session_id")
    st = get_or_create_session(session_id)

    if not st.get("pick") or not st.get("candidates"):
        return {
            "session_id": st["session_id"],
            "handoff": {
                "status": "error",
                "offer_id": None,
                "merchant": None,
                "total_minor": None,
                "currency": "USD",
            },
            "reply": {
                "speech": "I don't have a pick yet. Tell me what you're looking for."
            },
        }

    pick_id = st["pick"]["product_id"]
    raw_cands = st.get("_raw_candidates") or st["candidates"]
    pick_cand = next(
        (c for c in raw_cands if c["product_id"] == pick_id),
        next((c for c in st["candidates"] if c.get("is_pick")), st["candidates"][0]),
    )
    current_offer_id = st["pick"].get("offer_id") or pipeline.make_offer_id(pick_cand)

    # Require the tap to reference the displayed offer. Reject missing or stale references.
    expected_offer_id = body.get("offer_id")
    expected_product_id = body.get("product_id") or body.get("pick_id")
    expected_variant_id = body.get("variant_id")
    expected_price_minor = body.get("price_minor")
    expected_seller = body.get("seller_domain") or body.get("merchant")

    missing_reference = (
        expected_offer_id is None
        and expected_product_id is None
        and expected_variant_id is None
    )

    mismatch = False
    if expected_offer_id is not None and str(expected_offer_id) != str(current_offer_id):
        mismatch = True
    if expected_product_id is not None and str(expected_product_id) != str(pick_cand["product_id"]):
        mismatch = True
    if expected_variant_id is not None and str(expected_variant_id) != str(pick_cand["variant_id"]):
        mismatch = True
    if expected_price_minor is not None and int(expected_price_minor) != int(pick_cand["price_minor"]):
        mismatch = True
    if expected_seller and str(expected_seller).lower() not in (
        str(pick_cand["seller"]["domain"]).lower(),
        str(pick_cand["seller"]["name"]).lower(),
    ):
        mismatch = True

    if missing_reference or mismatch or st.get("_stale_pick_pending"):
        st["_stale_pick_pending"] = False
        st["handoff"] = None
        st["phase"] = "pick"
        st["updated_at"] = int(time.time())
        spoken_price = shop.minor_to_spoken(int(pick_cand["price_minor"]))
        return {
            "session_id": st["session_id"],
            "handoff": {
                "status": "stale_pick",
                "offer_id": current_offer_id,
                "merchant": pick_cand["seller"]["name"],
                "total_minor": int(pick_cand["price_minor"]),
                "currency": pick_cand.get("currency", "USD"),
            },
            "reply": {
                "speech": agent.sanitize_speech(
                    f"Current offer is {pick_cand['title']} at {spoken_price} from {pick_cand['seller']['name']}. Tap again to confirm this offer."
                )
            },
        }

    checkout_info = await shop.create_checkout(
        seller_domain=pick_cand["seller"]["domain"],
        variant_id=pick_cand["variant_id"],
        quantity=1,
        country=st["constraints"].get("country", "US"),
        fallback_checkout_url=pick_cand.get("checkout_url"),
        fallback_merchant=pick_cand["seller"]["name"],
        fallback_price_minor=int(pick_cand["price_minor"]),
        fallback_currency=pick_cand.get("currency", "USD"),
    )

    # If the merchant changed the item's live price on Shopify since it was displayed, invalidate & require fresh approval
    live_item_price = checkout_info.get("item_price_minor")
    if (
        live_item_price is not None
        and int(live_item_price) != int(pick_cand["price_minor"])
    ):
        new_price = int(live_item_price)
        pick_cand["price_minor"] = new_price
        new_offer_id = pipeline.make_offer_id(pick_cand)
        for pub_c in st["candidates"]:
            if pub_c["product_id"] == pick_cand["product_id"]:
                pub_c["price_minor"] = new_price
                pub_c["offer_id"] = new_offer_id
        st["pick"]["price_minor"] = new_price
        st["pick"]["offer_id"] = new_offer_id
        st["_offer_signature"] = (
            pick_cand["seller"]["domain"],
            pick_cand["variant_id"],
            new_price,
        )
        st["handoff"] = None
        st["phase"] = "pick"
        st["updated_at"] = int(time.time())
        spoken_new = shop.minor_to_spoken(new_price)
        return {
            "session_id": st["session_id"],
            "handoff": {
                "status": "stale_pick",
                "offer_id": new_offer_id,
                "merchant": pick_cand["seller"]["name"],
                "total_minor": new_price,
                "currency": pick_cand.get("currency", "USD"),
            },
            "reply": {
                "speech": agent.sanitize_speech(
                    f"The merchant updated the price to {spoken_new}. Please review the card and tap again to confirm."
                )
            },
        }

    if checkout_info.get("status") != "ready" or not checkout_info.get("continue_url"):
        return {
            "session_id": st["session_id"],
            "handoff": {
                "status": "error",
                "merchant": pick_cand["seller"]["name"],
                "total_minor": int(pick_cand["price_minor"]),
                "currency": pick_cand.get("currency", "USD"),
            },
            "reply": {
                "speech": "Checkout handoff could not be created right now. Please try tapping again."
            },
        }

    st["handoff"] = {
        "status": "ready",
        "continue_url": checkout_info["continue_url"],
        "offer_id": current_offer_id,
        "product_id": pick_cand["product_id"],
        "variant_id": pick_cand["variant_id"],
        "merchant": checkout_info["merchant"],
        "total_minor": int(checkout_info["total_minor"]),
        "currency": checkout_info["currency"],
        "expires_at": checkout_info["expires_at"],
        "via": checkout_info.get("via", "shop_mcp"),
        "requires_phone_contact": checkout_info.get("requires_phone_contact", False),
    }
    st["phase"] = "handoff"
    st["updated_at"] = int(time.time())

    # Device response NEVER includes continue_url
    device_handoff = {
        "status": "ready",
        "offer_id": current_offer_id,
        "merchant": st["handoff"]["merchant"],
        "total_minor": st["handoff"]["total_minor"],
        "currency": st["handoff"]["currency"],
    }
    return {
        "session_id": st["session_id"],
        "handoff": device_handoff,
        "reply": {
            "speech": "Got it. Scan the code on the screen to review and pay on your phone."
        },
    }


@app.post("/session/clear")
async def post_session_clear(request: Request) -> JSONResponse:
    global ACTIVE_SESSION_ID
    try:
        body = await request.json()
    except Exception:
        body = {}
    sid = body.get("session_id")
    if sid and sid in SESSIONS:
        SESSIONS[sid] = fresh_session(sid)
    else:
        SESSIONS.clear()
        ACTIVE_SESSION_ID = None
    return JSONResponse({"ok": True})


if __name__ == "__main__":
    import os
    import uvicorn

    host = os.environ.get("BACKEND_HOST", "127.0.0.1")
    port = int(os.environ.get("BACKEND_PORT", "8787"))
    uvicorn.run("main:app", host=host, port=port, log_level="info")
