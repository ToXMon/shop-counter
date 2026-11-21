import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import { createFeed } from "./feed.ts";
import { Screen } from "./Screen.ts";

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? "";
const POLL_MS = 500;

export function App() {
  // The feed owns the last /state payload; the input box is the only other state.
  const feed = useMemo(() => createFeed(BACKEND), []);
  const { state, health } = useSyncExternalStore(feed.subscribe, feed.snapshot);
  const [text, setText] = useState("");

  useEffect(() => {
    const tick = () => {
      if (document.hidden) return; // stop polling when the tab is hidden
      void feed.refresh();
    };
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => clearInterval(id);
  }, [feed]);

  async function send(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    const utterance = text.trim();
    if (!utterance) return;
    setText("");
    await fetch(`${BACKEND}/utterance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: feed.sessionId(), text: utterance }),
    });
    await feed.refresh();
  }

  return (
    <Screen
      state={state}
      health={health}
      text={text}
      onText={setText}
      onSend={send}
      onClear={() => void feed.clear().catch(() => undefined)}
      devControls={new URLSearchParams(window.location.search).has("dev")}
    />
  );
}
