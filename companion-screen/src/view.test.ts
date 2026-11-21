// Seam: state payload (+ health) in, card view out. Expected values are literals
// from docs/INTERFACES.md section 1.3, not recomputed from the code.
import { test } from "node:test";
import assert from "node:assert/strict";
import { cardView } from "./view.ts";

const state = {
  session_id: "s_abc123",
  phase: "pick",
  candidates: [
    { product_id: "p1", title: "Casabrews Compact 20-Bar Espresso Machine", price_minor: 13999, currency: "USD",
      image_url: "https://example.test/c.png", seller: { name: "Sabavi Home", domain: "sabavi.myshopify.com" }, is_pick: false },
    { product_id: "p2", title: "Gaggia Carezza De LUXE Espresso Machine", price_minor: 19900, currency: "USD",
      image_url: "https://example.test/g.png", seller: { name: "Whole Latte Love", domain: "wholelattelove.myshopify.com" }, is_pick: true },
  ],
  pick: { product_id: "p2", reasons: ["Only one under $300 with a 15-bar pump"] },
};

test("card shows the pick with its price taken from state", () => {
  const v = cardView(state, { ok: true, catalog: "ok", gemini: "ok" });
  assert.equal(v.card?.title, "Gaggia Carezza De LUXE Espresso Machine");
  assert.equal(v.card?.priceText, "$199.00");
  assert.equal(v.card?.sellerName, "Whole Latte Love");
});

test("price follows state: a changed price_minor changes the card", () => {
  const changed = { ...state, candidates: state.candidates.map((c) => (c.is_pick ? { ...c, price_minor: 50 } : c)) };
  assert.equal(cardView(changed, { ok: true, catalog: "ok", gemini: "ok" }).card?.priceText, "$0.50");
});

test("stub backend is labelled fixture mode", () => {
  assert.equal(cardView(state, { ok: true, catalog: "stub", gemini: "stub" }).fixtureMode, true);
});

test("live backend is not labelled fixture mode", () => {
  assert.equal(cardView(state, { ok: true, catalog: "ok", gemini: "ok" }).fixtureMode, false);
});

test("no candidates means no card", () => {
  assert.equal(cardView({ ...state, candidates: [], pick: null }, null).card, null);
});
