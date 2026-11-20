import { FormEvent, useEffect, useRef, useState } from "react";
import type { ChatMessage, Player } from "../types";
import { Avatar } from "./ui";

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
    <div className="overflow-hidden rounded-xl ring-1 ring-slate-200">
      <div className="h-80 space-y-3 overflow-y-auto bg-slate-50 p-4">
        {messages.length === 0 && (
          <p className="pt-24 text-center text-sm text-slate-400">
            No messages yet. Say hello 👋
          </p>
        )}
        {messages.map((m, i) => {
          const mine = m.player === you;
          return (
            <div key={m.id}>
              {(i === 0 || messages[i - 1].round !== m.round) && (
                <div className="my-3 flex items-center gap-3 text-xs font-medium tracking-wider text-slate-400 uppercase">
                  <span className="h-px flex-1 bg-slate-200" />
                  Round {m.round}
                  <span className="h-px flex-1 bg-slate-200" />
                </div>
              )}
              <div className={`flex items-end gap-2 ${mine ? "flex-row-reverse" : ""}`}>
                <Avatar player={m.player} size="sm" />
                <div className={`max-w-[75%] ${mine ? "text-right" : ""}`}>
                  <p className="mb-0.5 px-1 text-xs text-slate-500">
                    Player {m.player}
                    {mine && " (you)"}
                  </p>
                  <p
                    className={`inline-block rounded-2xl px-3.5 py-2 text-left ${
                      mine
                        ? "rounded-br-sm bg-indigo-600 text-white"
                        : "rounded-bl-sm bg-white text-slate-800 shadow-sm ring-1 ring-slate-200"
                    }`}
                  >
                    {m.text}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
        <div ref={bottom} />
      </div>
      <form className="flex gap-2 border-t border-slate-200 bg-white p-3" onSubmit={submit}>
        <input
          className="min-w-0 flex-1 rounded-full border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none disabled:bg-slate-100 disabled:text-slate-400"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={enabled ? "Type a message…" : "Chat is closed"}
          maxLength={300}
          disabled={!enabled}
        />
        <button className="btn rounded-full" type="submit" disabled={!enabled || !draft.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
