// Backend calls that tests need to observe. fetch is injected: it is the system boundary.
export async function clearSession(sessionId: string, base = "", fetchFn: typeof fetch = fetch): Promise<boolean> {
  const res = await fetchFn(`${base}/session/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return (await res.json()).ok === true;
}

// POST /utterance per docs/INTERFACES.md 1.1. Returns reply.speech; the screen shows no shopper controls for it.
export async function sendUtterance(sessionId: string | undefined, text: string, base = "", fetchFn: typeof fetch = fetch): Promise<string> {
  const res = await fetchFn(`${base}/utterance`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, text }),
  });
  return (await res.json()).reply?.speech ?? "";
}
