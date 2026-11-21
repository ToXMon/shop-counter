// Backend calls that tests need to observe. fetch is injected: it is the system boundary.
export async function clearSession(sessionId: string, base = "", fetchFn: typeof fetch = fetch): Promise<boolean> {
  const res = await fetchFn(`${base}/session/clear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return (await res.json()).ok === true;
}
