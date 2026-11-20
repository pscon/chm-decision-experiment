/** Asks the server for a seat and returns the opaque session token. */
export async function joinExperiment(): Promise<string> {
  const res = await fetch("/api/join", { method: "POST" });
  if (!res.ok) throw new Error(`Join failed (${res.status})`);
  const { token } = await res.json();
  return token;
}

export function socketUrl(token: string) {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${location.host}/ws?token=${encodeURIComponent(token)}`;
}
