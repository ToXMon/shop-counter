import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { sendUtterance } from "./api.ts";
import { createFeed } from "./feed.ts";
import { Screen } from "./Screen.ts";
import { listenOnce, speakReply, type RecognitionCtor } from "./speech.ts";

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? "";
const POLL_MS = 500;
const flags = new URLSearchParams(window.location.search);
const DEV = flags.has("dev");
const SPEAK = DEV && flags.has("speak"); // the Mac speaks only on request; the device owns playback
type SpeechWindow = { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor };
// Looked up on click, so the browser (or a test page) can supply the engine late.
const engine = (): RecognitionCtor | undefined => {
  const w = window as unknown as SpeechWindow;
  return w.SpeechRecognition ?? w.webkitSpeechRecognition;
};

export function App() {
  // The feed owns the last /state payload; the input box is the only other state.
  const feed = useMemo(() => createFeed(BACKEND), []);
  const { state, health } = useSyncExternalStore(feed.subscribe, feed.snapshot);
  const [text, setText] = useState("");
  const [talkStatus, setTalkStatus] = useState("");

  useEffect(() => {
    const tick = () => {
      if (document.hidden) return; // stop polling when the tab is hidden
      void feed.refresh();
    };
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => clearInterval(id);
  }, [feed]);

  async function say(utterance: string): Promise<void> {
    const speech = await sendUtterance(feed.sessionId(), utterance, BACKEND);
    speakReply(speech, SPEAK, (t) => window.speechSynthesis.speak(new SpeechSynthesisUtterance(t)));
    await feed.refresh();
  }

  async function send(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    const utterance = text.trim();
    if (!utterance) return;
    setText("");
    await say(utterance);
  }

  async function talk(): Promise<void> {
    const Engine = engine();
    if (!Engine) return setTalkStatus("Speech recognition is not available in this browser.");
    setTalkStatus("Listening…");
    try {
      const heard = await listenOnce(Engine);
      setTalkStatus(`Heard: ${heard}`);
      await say(heard);
    } catch (err) {
      setTalkStatus(`Mic: ${err instanceof Error ? err.message : "failed"}`);
    }
  }

  return (
    <Screen
      state={state}
      health={health}
      text={text}
      onText={setText}
      onSend={send}
      onClear={() => void feed.clear().catch(() => undefined)}
      devControls={DEV}
      onTalk={DEV ? () => void talk() : undefined}
      talkStatus={DEV ? talkStatus : undefined}
    />
  );
}
