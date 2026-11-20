import type { Player, Result } from "../types";
import { Avatar } from "./ui";

interface Props {
  result: Result;
  players: Player[];
  you: Player;
}

const TIE_BREAK_NOTE = {
  final_round: "There was a tie on total votes; it was decided by the round 2 votes.",
  player_order: "There was a tie on total and round 2 votes; it was decided by player order.",
};

export default function Results({ result, players, you }: Props) {
  const winner = result.decision_maker;
  const maxTotal = Math.max(1, ...players.map((p) => result.totals[p]));

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-3 rounded-2xl bg-gradient-to-br from-indigo-600 to-blue-600 p-8 text-center text-white shadow-lg shadow-indigo-500/30">
        <p className="text-sm font-medium tracking-wider text-indigo-100 uppercase">
          🏆 Decision Maker
        </p>
        <div className="rounded-full ring-4 ring-white/40">
          <Avatar player={winner} size="lg" />
        </div>
        <p className="text-2xl font-bold">
          Player {winner}
          {winner === you && " (you)"}
        </p>
        <p className="text-indigo-100">has been selected by the group.</p>
      </div>

      <div className="space-y-3">
        <h3 className="font-semibold text-slate-900">Vote breakdown</h3>
        {players.map((p) => {
          const total = result.totals[p];
          return (
            <div
              key={p}
              className={`flex items-center gap-3 rounded-xl p-3 ring-1 ${
                p === winner ? "bg-indigo-50 ring-indigo-200" : "bg-white ring-slate-200"
              }`}
            >
              <Avatar player={p} size="sm" />
              <div className="min-w-0 flex-1 space-y-1.5">
                <div className="flex items-baseline justify-between gap-2 text-sm">
                  <span className="font-medium">
                    Player {p}
                    {p === you && <span className="text-slate-500"> (you)</span>}
                  </span>
                  <span className="text-slate-500">
                    R1: {result.by_round["1"]?.[p] ?? 0} · R2: {result.by_round["2"]?.[p] ?? 0} ·{" "}
                    <strong className="text-slate-900">
                      {total} vote{total === 1 ? "" : "s"}
                    </strong>
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full ${p === winner ? "bg-indigo-600" : "bg-slate-400"}`}
                    style={{ width: `${(total / maxTotal) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {result.tie_break && (
        <p className="text-sm text-slate-500">{TIE_BREAK_NOTE[result.tie_break]}</p>
      )}
    </div>
  );
}
