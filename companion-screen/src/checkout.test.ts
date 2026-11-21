// Seam (approved): backend fixture state in, visible checkout UI out.
// Links below are fake. Expected values are literals from docs/INTERFACES.md 1.3.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Screen } from "./Screen.ts";

const FAKE_URL = "https://checkout.example.test/fake-handoff-7f3a9c";

const fixtureState = {
  session_id: "s_fixture",
  phase: "handoff",
  candidates: [
    { product_id: "p2", title: "Gaggia Carezza De LUXE Espresso Machine", price_minor: 19900, currency: "USD",
      seller: { name: "Whole Latte Love", domain: "wholelattelove.myshopify.com" }, is_pick: true },
  ],
  pick: { product_id: "p2", reasons: ["Only one under $300 with a 15-bar pump"] },
  handoff: { status: "ready", continue_url: FAKE_URL, merchant: "Whole Latte Love", total_minor: 19900, currency: "USD",
    expires_at: "2026-11-21T23:00:00Z" },
};
const stubHealth = { ok: true, catalog: "stub", gemini: "stub" };

const liveHealth = { ok: true, catalog: "ok", gemini: "ok" };

function render(state: unknown, devControls = false, health = stubHealth) {
  return renderToStaticMarkup(
    createElement(Screen, { state: state as never, health, text: "", onText: () => {}, onSend: () => {}, onClear: () => {}, devControls }),
  );
}

test("a valid fixture handoff shows a locally generated QR, never the link", () => {
  const html = render(fixtureState);
  assert.match(html, /data-testid="handoff-qr"/);
  assert.match(html, /<svg/);
  assert.match(html, /Scan to review and pay on your phone\./);
  assert.match(html, /Whole Latte Love/);
  assert.match(html, /Fixture mode/);
  assert.ok(!html.includes(FAKE_URL), "continue_url must not appear in the markup");
  assert.ok(!html.includes("fake-handoff-7f3a9c"), "no part of continue_url may appear in the markup");
});

test("the QR disappears when the pick changes after the handoff was made", () => {
  // Handoff is still for the Gaggia, but the shopper has since moved to the Casabrews.
  const changed = {
    ...fixtureState,
    candidates: [
      { product_id: "p3", title: "Casabrews Compact 20-Bar Espresso Machine", price_minor: 13999, currency: "USD",
        seller: { name: "Sabavi Home", domain: "sabavi.myshopify.com" }, is_pick: true },
    ],
    pick: { product_id: "p3", reasons: ["Only 20-bar machine under $200"] },
  };
  const html = render(changed);
  assert.match(html, /Casabrews/);
  assert.ok(!html.includes('data-testid="handoff-qr"'), "stale offer must not show a QR");
});

test("a live session offers a Clear session button", () => {
  assert.match(render(fixtureState), /<button[^>]*>Clear session<\/button>/);
});

test("after the tap the scan view replaces the product view and keeps a compact offer row", () => {
  const html = render(fixtureState);
  assert.match(html, /data-testid="handoff-qr"/);
  assert.match(html, /data-testid="offer-summary"[^>]*>.*Gaggia Carezza De LUXE Espresso Machine.*\$199\.00/);
  assert.ok(!html.includes('data-testid="product-card"'), "the large product view must give way to the scan view");
});

test("the product view shows one short reason and tells the shopper what to do next", () => {
  const noHandoff = {
    ...fixtureState,
    handoff: null,
    pick: { product_id: "p2", reasons: ["Only one under $300 with a 15-bar pump", "Steam wand for milk drinks", "4.6 stars from 128 reviews"] },
  };
  const html = render(noHandoff);
  assert.match(html, /Only one under \$300 with a 15-bar pump/);
  assert.ok(!html.includes("Steam wand for milk drinks"), "only the first reason is shown");
  assert.ok(!html.includes("4.6 stars from 128 reviews"), "only the first reason is shown");
  assert.match(html, /Tap the center of the device screen to open checkout\./);
});

test("the typed request box is a dev tool: absent by default, present with dev controls", () => {
  assert.ok(!render(fixtureState).includes("<input"), "shoppers get no second set of controls");
  assert.match(render(fixtureState, true), /<input/);
});

// Live mode: the QR is bound to the offer by pick.offer_id === handoff.offer_id (contract: build/backend 9c452a0).
const OFFER_1 = "shop.example.test:variant-1:19900";
const OFFER_2 = "shop.example.test:variant-2:13999";
const liveState = {
  ...fixtureState,
  pick: { ...fixtureState.pick, offer_id: OFFER_1 },
  handoff: { ...fixtureState.handoff, offer_id: OFFER_1 },
};

test("live: a same-seller offer change hides the old QR", () => {
  // Same merchant, but the shopper moved to another item from that seller. Only the offer_id differs.
  const changed = { ...liveState, pick: { ...liveState.pick, offer_id: OFFER_2 } };
  assert.ok(!render(changed, false, liveHealth).includes('data-testid="handoff-qr"'));
});

test("live: a handoff without offer_ids never shows a QR", () => {
  const legacy = { ...fixtureState }; // no offer_id on pick or handoff
  assert.ok(!render(legacy, false, liveHealth).includes('data-testid="handoff-qr"'));
});

test("live: matching offer_ids on pick and handoff show the QR", () => {
  assert.match(render(liveState, false, liveHealth), /data-testid="handoff-qr"/);
});

test("dev mode offers a Talk button with its status; the default display shows neither", () => {
  const dev = renderToStaticMarkup(
    createElement(Screen, { state: fixtureState as never, health: stubHealth, text: "", onText: () => {}, onSend: () => {}, onClear: () => {},
      devControls: true, onTalk: () => {}, talkStatus: "Listening…" }),
  );
  assert.match(dev, /<button[^>]*>Talk<\/button>/);
  assert.match(dev, /Listening…/);
  const shopper = render(fixtureState);
  assert.ok(!shopper.includes(">Talk<") && !shopper.includes("Listening"), "shoppers get no mic controls");
});
