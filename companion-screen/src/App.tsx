import { useEffect, useRef, useState } from "react";
import { cardView, type Health, type SessionState } from "./view.ts";

const BACKEND = import.meta.env.VITE_BACKEND_URL ?? "http://localhost:8787";
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

  const { card, fixtureMode } = cardView(state, health);

  return (
    <main>
      <header>
        <h1>Shop Counter</h1>
        {fixtureMode && <span className="badge" data-testid="fixture-badge">FIXTURE MODE: stub data, not live</span>}
        {!health && <span className="badge offline">backend offline</span>}
      </header>

      {card ? (
        <article className="card" data-testid="product-card">
          {card.imageUrl && <img src={card.imageUrl} alt="" />}
          <div>
            <h2 className="title">{card.title}</h2>
            <p className="price" data-testid="price">{card.priceText}</p>
            <p className="seller">{card.sellerName}</p>
            {card.reasons.map((r) => <p className="reason" key={r}>{r}</p>)}
          </div>
        </article>
      ) : (
        <p className="empty">Tell me what you are looking for.</p>
      )}

      <form onSubmit={send}>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Type a request" aria-label="Request" />
        <button type="submit">Send</button>
      </form>
    </main>
  );
}
