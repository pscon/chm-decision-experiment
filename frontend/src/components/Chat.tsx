import { FormEvent, useEffect, useRef, useState } from "react";
import type { ChatMessage, Player } from "../types";

interface Props {
  messages: ChatMessage[];
  you: Player;
  enabled: boolean;
  onSend: (text: string) => void;
}

export default function Chat({ messages, you, enabled, onSend }: Props) {
  const [draft, setDraft] = useState("");
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "nearest" });
  }, [messages.length]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    onSend(text);
    setDraft("");
  };

  return (
    <div className="chat">
      <div className="chat-log">
        {messages.length === 0 && <p className="muted">No messages yet.</p>}
        {messages.map((m, i) => (
          <div key={m.id}>
            {(i === 0 || messages[i - 1].round !== m.round) && (
              <div className="round-divider">Round {m.round}</div>
            )}
            <div className={m.player === you ? "msg mine" : "msg"}>
              <span className="msg-author">
                Player {m.player}
                {m.player === you && " (you)"}
              </span>
              <span>{m.text}</span>
            </div>
          </div>
        ))}
        <div ref={bottom} />
      </div>
      <form className="chat-input" onSubmit={submit}>
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={enabled ? "Type a message…" : "Chat is closed"}
          maxLength={300}
          disabled={!enabled}
        />
        <button type="submit" disabled={!enabled || !draft.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
