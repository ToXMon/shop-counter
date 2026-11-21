// Seam: the feed that polls /state and clears the session. fetch is the system boundary, so it is injected.
// Links are fake. A response from before a Clear must never repaint the old QR.
import { test } from "node:test";
import assert from "node:assert/strict";
import { createFeed } from "./feed.ts";

const OLD_URL = "https://checkout.example.test/fake-old-offer-1d2e3f";

const oldState = {
  session_id: "s_old",
  phase: "handoff",
  candidates: [{ product_id: "p1", title: "Old item", price_minor: 100, currency: "USD", seller: { name: "Shop", domain: "shop.example.test" }, is_pick: true }],
  pick: { product_id: "p1", reasons: [], offer_id: "shop.example.test:v1:100" },
  handoff: { status: "ready", continue_url: OLD_URL, merchant: "Shop", total_minor: 100, currency: "USD", offer_id: "shop.example.test:v1:100" },
};
const health = { ok: true, catalog: "ok", gemini: "ok" };

/** A fetch whose responses the test releases by hand, in any order. */
function controllableFetch() {
  const pending: { path: string; done: boolean; release: (body: unknown) => void }[] = [];
  const fn = ((url: string) =>
    new Promise((resolve) => {
      const entry = { path: url, done: false, release: (body: unknown) => { entry.done = true; resolve({ json: async () => body } as Response); } };
      pending.push(entry);
    })) as unknown as typeof fetch;
  /** Release the oldest unanswered request whose path starts with `prefix`. */
  const answer = (prefix: string, body: unknown) => pending.find((p) => !p.done && p.path.startsWith(prefix))!.release(body);
  return { fn, answer };
}

const tick = () => new Promise((r) => setTimeout(r, 0));
const freshSession = { session_id: "s_new", phase: "idle", candidates: [], pick: null, handoff: null };

async function sessionWithOldQr() {
  const net = controllableFetch();
  const feed = createFeed("", net.fn);
  const first = feed.refresh();
  await tick();
  net.answer("/state", oldState);
  net.answer("/health", health);
  await first;
  assert.equal(feed.snapshot().state?.handoff?.continue_url, OLD_URL, "setup: the old QR is showing");
  return { net, feed };
}

test("a /state response that arrives after Clear does not bring the old QR back", async () => {
  const { net, feed } = await sessionWithOldQr();
  const seen: unknown[] = [];
  feed.subscribe(() => seen.push(feed.snapshot().state));

  const late = feed.refresh();    // a poll is in flight...
  await tick();
  const clearing = feed.clear();  // ...the shopper presses Clear...
  await tick();
  net.answer("/state", oldState); // ...and the old response lands afterwards
  net.answer("/health", health);
  await late;
  net.answer("/session/clear", { ok: true });
  await tick();
  net.answer("/state", freshSession);
  net.answer("/health", health);
  await clearing;

  assert.ok(seen.every((s) => (s as { handoff?: unknown } | null)?.handoff == null), "no snapshot after Clear may carry the old handoff");
  assert.equal(feed.snapshot().state?.session_id, "s_new");
});

test("a poll that starts while Clear is still in flight cannot bring the old QR back", async () => {
  const { net, feed } = await sessionWithOldQr();
  const seen: unknown[] = [];
  feed.subscribe(() => seen.push(feed.snapshot().state));

  const clearing = feed.clear();   // Clear request is on the wire, the server has not processed it yet
  await tick();
  const early = feed.refresh();    // a poll starts now and will still see the old session
  await tick();
  net.answer("/state", oldState);
  net.answer("/health", health);
  await early;
  net.answer("/session/clear", { ok: true });
  await tick();
  net.answer("/state", freshSession);
  net.answer("/health", health);
  await clearing;

  assert.ok(seen.every((s) => (s as { handoff?: unknown } | null)?.handoff == null), "no snapshot after Clear may carry the old handoff");
});
