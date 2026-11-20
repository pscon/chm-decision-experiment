import type { Player } from "../types";
import { Avatar } from "./ui";

interface Props {
  players: Player[];
  you: Player;
  enabled: boolean;
  myVote: Player | null;
  onVote: (target: Player) => void;
}

export default function VotePanel({ players, you, enabled, myVote, onVote }: Props) {
  const locked = !enabled || myVote !== null;
  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between">
        <h3 className="font-semibold text-slate-900">Vote for the Decision Maker</h3>
        <p className="text-sm text-slate-500">
          {!enabled
            ? "Opens after the discussion"
            : myVote
              ? "Vote recorded. Waiting for the others…"
              : "Choose one player"}
        </p>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {players.map((p) => {
          const selected = myVote === p;
          return (
            <button
              key={p}
              disabled={locked}
              onClick={() => onVote(p)}
              className={`relative flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all disabled:cursor-not-allowed ${
                selected
                  ? "border-indigo-600 bg-indigo-50 shadow-md"
                  : "border-slate-200 bg-white enabled:hover:-translate-y-0.5 enabled:hover:border-indigo-300 enabled:hover:shadow-md"
              } ${locked && !selected ? "opacity-50" : ""}`}
            >
              {selected && (
                <span className="absolute top-2 right-2 flex size-5 items-center justify-center rounded-full bg-indigo-600 text-xs text-white">
                  ✓
                </span>
              )}
              <Avatar player={p} />
              <span className="font-medium">
                Player {p}
                {p === you && <span className="text-slate-500"> (you)</span>}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
