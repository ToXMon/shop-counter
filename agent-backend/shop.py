"""Shopify Global Catalog search, verified storefront lookup, and Shop MCP checkout.

Follows docs/INTERFACES.md section 2 and docs/LAUNCH.md:
- Never log or expose checkout IDs or continue_url values.
- All price/budget math uses integer minor units (cents).
- 10s timeout on HTTP calls; honor Retry-After on HTTP 429.
"""
from __future__ import annotations

import asyncio
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import logging
import os
import re
import time
import uuid
from typing import Any

import httpx

logger = logging.getLogger("shop_counter.shop")

CATALOG_MCP_URL = "https://catalog.shopify.com/api/ucp/mcp"
SHOP_MCP_URL = "https://mcp.shop.com/"
DEFAULT_UCP_PROFILE = (
    "https://shopify.dev/ucp/agent-profiles/examples/2026-08-25/valid-with-capabilities.json"
)

MONDAY_CARTOONS_DOMAIN = "monday-cartoons.myshopify.com"
MONDAY_CARTOONS_NAME = "Monday Cartoons"
MONDAY_CARTOONS_STICKER_VARIANT_NUM = "68033173323939"
MONDAY_CARTOONS_STICKER_VARIANT_GID = (
    f"gid://shopify/ProductVariant/{MONDAY_CARTOONS_STICKER_VARIANT_NUM}"
)

_SENSITIVE_PATTERNS = [
    re.compile(r"https?://[^\s\"']*checkout[^\s\"']*", re.IGNORECASE),
    re.compile(r"https?://[^\s\"']*/checkouts/[^\s\"']*", re.IGNORECASE),
    re.compile(r"https?://[^\s\"']*/cart/[^\s\"']*", re.IGNORECASE),
    re.compile(r"https?://shop\.app/checkout/[^\s\"']*", re.IGNORECASE),
    re.compile(r"gid://shopify/Checkout/[^\s\"']+", re.IGNORECASE),
    re.compile(r"gid://shopify/CartLine/[^\s\"']+", re.IGNORECASE),
    re.compile(r"AQ\.[A-Za-z0-9_-]{15,}"),
    re.compile(r"AIza[A-Za-z0-9_-]{20,}"),
]
_SENSITIVE_KEYS = {"continue_url", "checkout_url", "id", "checkout_id", "api_key", "gemini_api_key"}


def redact_sensitive(value: Any) -> Any:
    """Recursively redact checkout IDs, continue_urls, and API keys from logs or dicts."""
    if isinstance(value, str):
        out = value
        for pat in _SENSITIVE_PATTERNS:
            out = pat.sub("[REDACTED]", out)
        return out
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for k, v in value.items():
            k_lower = str(k).lower()
            if k_lower in _SENSITIVE_KEYS and isinstance(v, str) and (
                "http" in v.lower()
                or "checkout" in v.lower()
                or k_lower in ("continue_url", "checkout_id", "api_key", "gemini_api_key")
            ):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = redact_sensitive(v)
        return cleaned
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value


def dollars_to_minor(amount: str | int | float | Decimal) -> int:
    """Convert a dollar string or number (e.g. '$300', '0.50', 199.99) into integer minor units."""
    if isinstance(amount, int):
        return amount * 100
    cleaned = str(amount).strip().replace("$", "").replace(",", "")
    try:
        dec = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid currency amount: {amount!r}") from exc
    return int((dec * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


_ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen",
]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _int_to_words(n: int) -> str:
    if n < 0:
        return "minus " + _int_to_words(-n)
    if n < 20:
        return _ONES[n]
    if n < 100:
        tens, rem = divmod(n, 10)
        return _TENS[tens] if rem == 0 else f"{_TENS[tens]}-{_ONES[rem]}"
    if n < 1000:
        hundreds, rem = divmod(n, 100)
        prefix = f"{_ONES[hundreds]} hundred"
        return prefix if rem == 0 else f"{prefix} {_int_to_words(rem)}"
    thousands, rem = divmod(n, 1000)
    prefix = f"{_int_to_words(thousands)} thousand"
    return prefix if rem == 0 else f"{prefix} {_int_to_words(rem)}"


def minor_to_spoken(price_minor: int) -> str:
    """Format minor units as spoken English words ('fifty cents', 'thirty-eight dollars')."""
    dollars, cents = divmod(max(0, int(price_minor)), 100)
    if dollars == 0:
        unit = "cent" if cents == 1 else "cents"
        return f"{_int_to_words(cents)} {unit}"
    dollar_unit = "dollar" if dollars == 1 else "dollars"
    if cents == 0:
        return f"{_int_to_words(dollars)} {dollar_unit}"
    if cents == 99 and dollars >= 100:
        hundreds, rem = divmod(dollars, 100)
        if rem > 0:
            return f"{_int_to_words(hundreds)} {_int_to_words(rem)} ninety-nine"
    cent_unit = "cent" if cents == 1 else "cents"
    return f"{_int_to_words(dollars)} {dollar_unit} and {_int_to_words(cents)} {cent_unit}"


async def _post_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    headers: dict[str, str],
    json_body: dict[str, Any],
) -> httpx.Response:
    resp = await client.post(url, headers=headers, json=json_body)
    if resp.status_code == 429:
        retry_after = float(resp.headers.get("Retry-After", "1.0"))
        await asyncio.sleep(min(retry_after, 5.0))
        resp = await client.post(url, headers=headers, json=json_body)
    resp.raise_for_status()
    return resp


async def fetch_monday_cartoons_storefront(
    budget_max_minor: int | None = None,
    only_sticker: bool = False,
) -> list[dict[str, Any]]:
    """Fetch live products from Monday Cartoons storefront without hardcoding prices."""
    url = f"https://{MONDAY_CARTOONS_DOMAIN}/products.json?limit=50"
    headers = {"User-Agent": "shop-counter/0.1", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", "1.0"))
            await asyncio.sleep(min(retry_after, 5.0))
            resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        payload = resp.json()

    candidates: list[dict[str, Any]] = []
    for prod in payload.get("products", []):
        variants = prod.get("variants") or []
        if not variants:
            continue
        chosen_var = None
        for v in variants:
            if str(v.get("id")) == MONDAY_CARTOONS_STICKER_VARIANT_NUM:
                chosen_var = v
                break
        if chosen_var is None:
            chosen_var = variants[0]

        if not chosen_var.get("available", True):
            continue

        is_sticker = (
            str(chosen_var.get("id")) == MONDAY_CARTOONS_STICKER_VARIANT_NUM
            or prod.get("handle") == "digital-sticker"
            or "digital sticker" in str(prod.get("title", "")).lower()
        )
        if only_sticker and not is_sticker:
            continue

        price_minor = dollars_to_minor(chosen_var.get("price", "0"))
        if budget_max_minor is not None and price_minor > budget_max_minor:
            continue

        images = prod.get("images") or []
        image_url = images[0].get("src") if images else None
        requires_shipping = bool(chosen_var.get("requires_shipping", True))
        body_html = re.sub(r"<[^>]+>", " ", str(prod.get("body_html") or "")).strip()

        cand: dict[str, Any] = {
            "product_id": f"gid://shopify/Product/{prod['id']}",
            "variant_id": f"gid://shopify/ProductVariant/{chosen_var['id']}",
            "title": prod.get("title") or "Monday Cartoons Product",
            "price_minor": price_minor,
            "currency": os.environ.get("SHOP_CURRENCY", "USD"),
            "image_url": image_url,
            "seller": {
                "name": prod.get("vendor") or MONDAY_CARTOONS_NAME,
                "domain": MONDAY_CARTOONS_DOMAIN,
            },
            "rating": None,
            "is_pick": False,
            "requires_shipping": requires_shipping,
            "description": body_html or (
                "Instant digital sticker download, no shipping required."
                if not requires_shipping
                else f"Physical item from {MONDAY_CARTOONS_NAME}."
            ),
            "checkout_url": f"https://{MONDAY_CARTOONS_DOMAIN}/cart/{chosen_var['id']}:1",
            "source": "storefront",
        }
        if is_sticker:
            candidates.insert(0, cand)
        else:
            candidates.append(cand)

    return candidates


def _is_monday_cartoons_or_sticker_query(
    query: str,
    must_have: list[str] | None = None,
    seller_hint: str | None = None,
) -> tuple[bool, bool]:
    """Return (wants_monday_cartoons, wants_sticker_specifically)."""
    combined = " ".join(
        [query or "", seller_hint or "", " ".join(must_have or [])]
    ).lower()
    wants_sticker = any(
        kw in combined
        for kw in ("digital sticker", "sticker", "digital item", "digital download", "no shipping", "unshipped")
    )
    wants_mc = wants_sticker or any(
        kw in combined for kw in ("monday cartoons", "monday-cartoons", "monday cartoon")
    )
    return wants_mc, wants_sticker


async def search_catalog(
    query: str,
    budget_max_minor: int | None = None,
    country: str = "US",
    currency: str = "USD",
    limit: int = 5,
    must_have: list[str] | None = None,
    seller_hint: str | None = None,
) -> list[dict[str, Any]]:
    """Search Shopify Global Catalog and resolve verified Monday Cartoons storefront items when requested."""
    wants_mc, wants_sticker = _is_monday_cartoons_or_sticker_query(
        query, must_have=must_have, seller_hint=seller_hint
    )

    storefront_candidates: list[dict[str, Any]] = []
    if wants_mc or wants_sticker:
        try:
            storefront_candidates = await fetch_monday_cartoons_storefront(
                budget_max_minor=budget_max_minor,
                only_sticker=False,
            )
        except Exception as exc:
            logger.warning("Storefront lookup warning: %s", redact_sensitive(str(exc)))

    profile = os.environ.get("UCP_AGENT_PROFILE", DEFAULT_UCP_PROFILE)
    catalog_args: dict[str, Any] = {
        "query": query,
        "context": {"address_country": country, "currency": currency},
        "pagination": {"limit": max(1, min(limit, 10))},
    }
    if budget_max_minor is not None:
        catalog_args["filters"] = {"price": {"max": int(budget_max_minor)}}

    rpc_body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_catalog",
            "arguments": {
                "meta": {"ucp-agent": {"profile": profile}},
                "catalog": catalog_args,
            },
        },
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    catalog_candidates: list[dict[str, Any]] = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await _post_with_retry(
                client, CATALOG_MCP_URL, headers=headers, json_body=rpc_body
            )
            body = resp.json()
            structured = (body.get("result") or {}).get("structuredContent") or {}
            products = structured.get("products") or []
            for p in products:
                variants = p.get("variants") or []
                if not variants:
                    continue
                v = variants[0]
                price_obj = v.get("price") or {}
                price_minor = int(price_obj.get("amount", 0))
                if budget_max_minor is not None and price_minor > budget_max_minor:
                    continue
                media = p.get("media") or []
                image_url = media[0].get("url") if media else None
                seller = v.get("seller") or {}
                rating_raw = p.get("rating")
                rating = (
                    {
                        "value": float(rating_raw["value"]),
                        "count": int(rating_raw.get("count", 0)),
                    }
                    if isinstance(rating_raw, dict) and "value" in rating_raw
                    else None
                )
                catalog_candidates.append(
                    {
                        "product_id": str(p.get("id") or v.get("id")),
                        "variant_id": str(v.get("id")),
                        "title": str(p.get("title") or "Product"),
                        "price_minor": price_minor,
                        "currency": str(price_obj.get("currency") or currency),
                        "image_url": image_url,
                        "seller": {
                            "name": str(seller.get("name") or "Merchant"),
                            "domain": str(seller.get("domain") or ""),
                        },
                        "rating": rating,
                        "is_pick": False,
                        "description": str(p.get("description") or p.get("title") or ""),
                        "checkout_url": v.get("checkout_url"),
                        "source": "catalog",
                    }
                )
    except Exception as exc:
        logger.warning("Catalog search warning: %s", redact_sensitive(str(exc)))

    merged: list[dict[str, Any]] = []
    seen_variants: set[str] = set()

    # If the shopper specifically asked for the sticker or Monday Cartoons, surface the storefront sticker first
    ordered_sources = (
        storefront_candidates + catalog_candidates
        if (wants_sticker or wants_mc)
        else catalog_candidates + storefront_candidates
    )
    for cand in ordered_sources:
        vid = cand["variant_id"]
        if vid in seen_variants:
            continue
        seen_variants.add(vid)
        merged.append(cand)
        if len(merged) >= limit:
            break

    return merged


async def create_checkout(
    seller_domain: str,
    variant_id: str,
    quantity: int = 1,
    country: str = "US",
    fallback_checkout_url: str | None = None,
    fallback_merchant: str | None = None,
    fallback_price_minor: int | None = None,
    fallback_currency: str = "USD",
) -> dict[str, Any]:
    """Create a one-item checkout via Shop MCP (no shopper sign-in).

    Never logs or prints checkout IDs or continue_url.
    Treat status='incomplete' with a valid continue_url (e.g. buyer-contact required)
    as handoff status='ready' for phone review.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2026-07-28",
        "Mcp-Method": "tools/call",
        "Mcp-Name": "create_checkout",
    }
    rpc_body = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "create_checkout",
            "arguments": {
                "shop": seller_domain,
                "checkout": {
                    "line_items": [{"item": {"id": variant_id}, "quantity": int(quantity)}],
                    "context": {"address_country": country},
                },
                "meta": {"idempotency-key": str(uuid.uuid4())},
            },
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": "2026-07-28",
                "io.modelcontextprotocol/clientInfo": {
                    "name": "shop-counter",
                    "version": "0.1.0",
                },
                "io.modelcontextprotocol/clientCapabilities": {},
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await _post_with_retry(
                client, SHOP_MCP_URL, headers=headers, json_body=rpc_body
            )
            raw_text = resp.text.strip()
            # Handle either JSON or SSE data lines
            data: dict[str, Any] = {}
            if raw_text.startswith("{"):
                import json

                data = json.loads(raw_text)
            else:
                import json

                for line in raw_text.splitlines():
                    if line.startswith("data:"):
                        chunk = line[len("data:") :].strip()
                        if chunk.startswith("{"):
                            data = json.loads(chunk)
                            if "result" in data or "error" in data:
                                break

            sc = (data.get("result") or {}).get("structuredContent") or {}
            continue_url = sc.get("continue_url")
            mcp_status = str(sc.get("status") or "")
            totals_raw = sc.get("totals")
            subtotal_minor = fallback_price_minor or 0
            total_minor = fallback_price_minor or 0
            if isinstance(totals_raw, list):
                for item in totals_raw:
                    if isinstance(item, dict) and item.get("amount") is not None:
                        if item.get("type") == "subtotal":
                            subtotal_minor = int(item["amount"])
                        elif item.get("type") == "total":
                            total_minor = int(item["amount"])
            elif isinstance(totals_raw, dict):
                total_obj = totals_raw.get("total") or totals_raw.get("subtotal") or {}
                if isinstance(total_obj, dict) and total_obj.get("amount") is not None:
                    total_minor = int(total_obj["amount"])
            currency = str(sc.get("currency") or fallback_currency)
            expires_at = sc.get("expires_at") or time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 6 * 3600)
            )
            messages = sc.get("messages") or []
            requires_contact = any(
                "contact" in str(m).lower() or "buyer" in str(m).lower() or "email" in str(m).lower()
                for m in messages
            )

            line_items = sc.get("line_items") or []
            item_price_minor = subtotal_minor
            if line_items and isinstance(line_items[0], dict):
                item_obj = line_items[0].get("item") or {}
                if item_obj.get("price") is not None:
                    item_price_minor = int(item_obj["price"])

            if isinstance(continue_url, str) and continue_url.startswith("https://"):
                return {
                    "status": "ready",
                    "mcp_status": mcp_status or "incomplete",
                    "requires_phone_contact": requires_contact or (mcp_status == "incomplete"),
                    "continue_url": continue_url,
                    "merchant": fallback_merchant or seller_domain,
                    "total_minor": total_minor,
                    "subtotal_minor": subtotal_minor,
                    "item_price_minor": item_price_minor,
                    "currency": currency,
                    "expires_at": expires_at,
                    "via": "shop_mcp",
                }
    except Exception as exc:
        logger.warning("Shop MCP create_checkout warning: %s", redact_sensitive(str(exc)))

    # Fallback per docs/INTERFACES.md 2.3
    if fallback_checkout_url and fallback_checkout_url.startswith("https://"):
        return {
            "status": "ready",
            "mcp_status": "fallback",
            "requires_phone_contact": True,
            "continue_url": fallback_checkout_url,
            "merchant": fallback_merchant or seller_domain,
            "total_minor": fallback_price_minor or 0,
            "subtotal_minor": fallback_price_minor or 0,
            "currency": fallback_currency,
            "expires_at": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 6 * 3600)
            ),
            "via": "variant_checkout_url",
        }

    return {
        "status": "error",
        "merchant": fallback_merchant or seller_domain,
        "total_minor": fallback_price_minor,
        "currency": fallback_currency,
    }


async def check_catalog_health() -> bool:
    """Fast health check against Shopify Global Catalog."""
    try:
        cands = await search_catalog("espresso machine", budget_max_minor=30000, limit=1)
        return len(cands) > 0
    except Exception:
        return False
