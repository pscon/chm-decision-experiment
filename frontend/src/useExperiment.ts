import { useCallback, useEffect, useRef, useState } from "react";
import type { ClientAction, ServerEvent, SessionState } from "./types";

const TOKEN_KEY = "experiment-token";

// sessionStorage: a refresh keeps your seat, while each new tab / window is a
// new participant (handy for demoing three players on one machine).
export const tokenStore = {
  get: () => sessionStorage.getItem(TOKEN_KEY),
  set: (token: string) => sessionStorage.setItem(TOKEN_KEY, token),
  clear: () => sessionStorage.removeItem(TOKEN_KEY),
};

export async function joinExperiment(): Promise<string> {
  const res = await fetch("/api/join", { method: "POST" });
  if (!res.ok) throw new Error(`Join failed (${res.status})`);
  const { token } = await res.json();
  return token;
}

function socketUrl(token: string) {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${location.host}/ws?token=${encodeURIComponent(token)}`;
}

/** Keeps a WebSocket to the server open and mirrors the session state it sends. */
export function useExperiment(token: string, onInvalidToken: () => void) {
  const [state, setState] = useState<SessionState | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // server clock minus local clock, so countdowns follow the server deadline
  const [clockOffset, setClockOffset] = useState(0);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    let stopped = false;
    let retryTimer: number | undefined;

    const connect = () => {
      const ws = new WebSocket(socketUrl(token));
      socket.current = ws;

      ws.onopen = () => setConnected(true);
      ws.onmessage = (event) => {
        const msg: ServerEvent = JSON.parse(event.data);
        if (msg.type === "state") {
          setClockOffset(msg.server_time - Date.now());
          setState(msg);
          setError(null);
        } else if (msg.type === "chat") {
          setState((s) => (s ? { ...s, messages: [...s.messages, msg.message] } : s));
        } else if (msg.type === "error") {
          setError(msg.message);
        }
      };
      ws.onclose = (event) => {
        setConnected(false);
        if (stopped) return;
        if (event.code === 4401) {
          onInvalidToken(); // server doesn't know this seat (e.g. it restarted)
          return;
        }
        retryTimer = window.setTimeout(connect, 1500);
      };
    };

    connect();
    return () => {
      stopped = true;
      window.clearTimeout(retryTimer);
      socket.current?.close();
    };
    // Reconnect only when the token changes, not when the callback identity does.
  }, [token]);

  const send = useCallback((action: ClientAction) => {
    if (socket.current?.readyState === WebSocket.OPEN) {
      socket.current.send(JSON.stringify(action));
    }
  }, []);

  return { state, connected, error, clockOffset, send };
}

/** Seconds left until `deadline` (server time), re-rendering a few times a second. */
export function useCountdown(deadline: number | null, clockOffset: number) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (deadline == null) return;
    const id = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(id);
  }, [deadline]);
  if (deadline == null) return null;
  return Math.max(0, Math.ceil((deadline - (now + clockOffset)) / 1000));
}
