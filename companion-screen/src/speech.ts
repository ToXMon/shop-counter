// Browser speech recognition, dev fallback only (?dev). The engine is injected: it is the system boundary.
export interface RecognitionLike {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}
export type RecognitionCtor = new () => RecognitionLike;

export function listenOnce(Engine: RecognitionCtor): Promise<string> {
  return new Promise((resolve, reject) => {
    const rec = new Engine();
    let heard = false;
    rec.lang = "en-US";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (e) => {
      heard = true;
      resolve(e.results[0][0].transcript);
    };
    rec.onerror = (e) => reject(new Error(e.error));
    rec.onend = () => {
      if (!heard) reject(new Error("no-speech"));
    };
    rec.start();
  });
}

// The device (or Codex's Mac proxy, which already uses `say`) owns playback. The Mac speaks a reply
// only when ?dev&speak is set, so one reply is never spoken twice.
export function speakReply(speech: string, enabled: boolean, say: (text: string) => void): void {
  if (enabled && speech) say(speech);
}
