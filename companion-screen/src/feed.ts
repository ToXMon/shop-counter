// Polls /state and clears the session. fetch is injected: it is the system boundary.
import { clearSession } from "./api.ts";
import type { Health, SessionState } from "./view.ts";

export interface Snapshot {
  state: SessionState | null;
  health: Health | null;
}

export function createFeed(base = "", fetchFn: typeof fetch = fetch) {
  let state: SessionState | null = null;
  let health: Health | null = null;
  let sid: string | undefined;
  let clearing = false; // true while the Clear request is on the wire
  let epoch = 0; // advances on Clear; responses from an earlier epoch are dropped
  const listeners = new Set<() => void>();
  // A new object only when something changed, so React's useSyncExternalStore sees a stable snapshot.
  let snap: Snapshot = { state, health };
  const notify = () => {
    snap = { state, health };
    listeners.forEach((l) => l());
  };

  async function refresh(): Promise<void> {
    const started = epoch;
    try {
      const q = sid ? `?session_id=${encodeURIComponent(sid)}` : "";
      const [s, h] = await Promise.all([
        fetchFn(`${base}/state${q}`).then((r) => r.json()),
        fetchFn(`${base}/health`).then((r) => r.json()),
      ]);
      if (started !== epoch || clearing) return; // answered a question asked before Clear
      sid = s.session_id;
      state = s;
      health = h;
    } catch {
      if (started !== epoch || clearing) return;
      health = null; // backend unreachable: show offline, keep the last state
    }
    notify();
  }

  async function clear(): Promise<void> {
    if (!sid) return;
    epoch++; // drop anything already in flight
    clearing = true; // and anything that lands before the server has actually cleared
    try {
      await clearSession(sid, base, fetchFn);
    } finally {
      clearing = false;
      epoch++; // polls that started while the server still held the old session are stale too
    }
    sid = undefined;
    state = null;
    notify();
    await refresh();
  }

  return {
    refresh,
    clear,
    sessionId: () => sid,
    snapshot: (): Snapshot => snap,
    subscribe: (l: () => void) => {
      listeners.add(l);
      return () => listeners.delete(l);
    },
  };
}
