// Seam: the HTTP contract in docs/INTERFACES.md 1.4. fetch is the system boundary, so it is injected.
import { test } from "node:test";
import assert from "node:assert/strict";
import { clearSession } from "./api.ts";

test("clearing a session posts the session id to /session/clear and reports success", async () => {
  const calls: { url: string; init: RequestInit }[] = [];
  const fakeFetch = (async (url: string, init: RequestInit) => {
    calls.push({ url, init });
    return { json: async () => ({ ok: true }) } as Response;
  }) as unknown as typeof fetch;

  const ok = await clearSession("s_fixture", "", fakeFetch);

  assert.equal(ok, true);
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/session/clear");
  assert.equal(calls[0].init.method, "POST");
  assert.deepEqual(JSON.parse(String(calls[0].init.body)), { session_id: "s_fixture" });
});
