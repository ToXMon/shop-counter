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

function render(state: unknown) {
  return renderToStaticMarkup(
    createElement(Screen, { state: state as never, health: stubHealth, text: "", onText: () => {}, onSend: () => {}, onClear: () => {} }),
  );
}

test("a valid fixture handoff shows a locally generated QR, never the link", () => {
  const html = render(fixtureState);
  assert.match(html, /data-testid="handoff-qr"/);
  assert.match(html, /<svg/);
  assert.match(html, /Scan to review and pay on your phone/);
  assert.match(html, /Whole Latte Love/);
  assert.match(html, /FIXTURE MODE/);
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
