import { useEffect, useRef, useState } from "react";
import { clearSession } from "./api.ts";
import { Screen } from "./Screen.ts";
import type { Health, SessionState } from "./view.ts";

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? "";
const POLL_MS = 500;

export function App() {
  // The last /state payload and the input box are the only state, per companion-screen/AGENTS.md.
  const [state, setState] = useState<SessionState | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [text, setText] = useState("");
  const sid = useRef<string | undefined>(undefined);

  async function refresh(forSession?: string): Promise<void> {
    try {
      const q = forSession ? `?session_id=${encodeURIComponent(forSession)}` : "";
      const [s, h] = await Promise.all([
        fetch(`${BACKEND}/state${q}`).then((r) => r.json()),
        fetch(`${BACKEND}/health`).then((r) => r.json()),
      ]);
      sid.current = s.session_id;
      setState(s);
      setHealth(h);
    } catch {
      setHealth(null); // backend unreachable: show offline, keep the last state
    }
  }

  useEffect(() => {
    const tick = () => {
      if (document.hidden) return; // stop polling when the tab is hidden
      void refresh(sid.current);
    };
    tick();
    const id = setInterval(tick, POLL_MS);
    return () => clearInterval(id);
  }, []);

  async function send(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    const utterance = text.trim();
    if (!utterance) return;
    setText("");
    await fetch(`${BACKEND}/utterance`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sid.current, text: utterance }),
    });
    await refresh(sid.current);
  }

  async function clear(): Promise<void> {
    if (!sid.current) return;
    await clearSession(sid.current, BACKEND);
    // Drop everything shown right away, including any QR, then pick up the fresh session.
    sid.current = undefined;
    setState(null);
    await refresh();
  }

  return <Screen state={state} health={health} text={text} onText={setText} onSend={send} onClear={clear} />;
}
