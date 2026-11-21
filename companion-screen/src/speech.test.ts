// Seam: one browser speech recognition in, text out. The recognition engine is the system boundary,
// so tests pass a fake. No microphone is needed.
import { test } from "node:test";
import assert from "node:assert/strict";
import { listenOnce, speakReply, type RecognitionLike } from "./speech.ts";

function fakeEngine(script: (r: RecognitionLike) => void) {
  return class implements RecognitionLike {
    lang = "";
    interimResults = false;
    maxAlternatives = 1;
    onresult: RecognitionLike["onresult"] = null;
    onerror: RecognitionLike["onerror"] = null;
    onend: RecognitionLike["onend"] = null;
    start() { queueMicrotask(() => script(this)); }
    stop() {}
  };
}

test("listening once resolves to what the shopper said", async () => {
  const Engine = fakeEngine((r) => { r.onresult?.({ results: [[{ transcript: "something cheaper please" }]] }); r.onend?.(); });
  assert.equal(await listenOnce(Engine), "something cheaper please");
});

test("a recognition error rejects with the engine's reason", async () => {
  const Engine = fakeEngine((r) => r.onerror?.({ error: "not-allowed" }));
  await assert.rejects(listenOnce(Engine), /not-allowed/);
});

test("silence rejects as no-speech", async () => {
  const Engine = fakeEngine((r) => r.onend?.());
  await assert.rejects(listenOnce(Engine), /no-speech/);
});

test("the Mac stays silent unless speaking is switched on", () => {
  const said: string[] = [];
  speakReply("Take the Casabrews.", false, (t) => said.push(t));
  assert.equal(said.length, 0, "default: the device (or Codex proxy) owns playback, so the Mac must not speak");
  speakReply("Take the Casabrews.", true, (t) => said.push(t));
  assert.deepEqual(said, ["Take the Casabrews."]);
});
