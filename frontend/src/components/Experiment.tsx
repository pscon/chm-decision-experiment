import type { SessionState } from "../types";
import { useCountdown } from "../hooks/useCountdown";
import { useExperiment } from "../hooks/useExperiment";
import Chat from "./Chat";
import Results from "./Results";
import { Avatar, Card } from "./ui";
import VotePanel from "./VotePanel";

interface Props {
  token: string;
  onLeave: () => void;
}

const STAGES = ["Discuss 1", "Vote 1", "Discuss 2", "Vote 2", "Results"];

function stageIndex(state: SessionState) {
  if (state.phase === "waiting") return -1;
  if (state.phase === "results") return 4;
  return (state.round - 1) * 2 + (state.phase === "voting" ? 1 : 0);
}

export default function Experiment({ token, onLeave }: Props) {
  const { state, connected, error, clockOffset, send } = useExperiment(token, onLeave);
  const secondsLeft = useCountdown(state?.deadline ?? null, clockOffset);

  if (!state) {
    return (
      <Card className="flex items-center gap-3 text-slate-500">
        <Spinner /> Connecting…
      </Card>
    );
  }

  const current = stageIndex(state);
  const live = state.phase === "discussion" || state.phase === "voting";
  const urgent = secondsLeft != null && secondsLeft <= 10;

  const header = (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <Avatar player={state.you} />
          <div className="leading-tight">
            <p className="text-xs tracking-wide text-slate-500 uppercase">You are</p>
            <p className="font-semibold text-slate-900">Player {state.you}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!connected && (
            <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 ring-1 ring-red-200">
              Reconnecting…
            </span>
          )}
          {live && secondsLeft != null && (
            <span
              className={`rounded-full px-4 py-1.5 text-lg font-bold tabular-nums ring-1 transition-colors ${
                urgent
                  ? "animate-pulse bg-red-50 text-red-600 ring-red-200"
                  : "bg-slate-100 text-slate-800 ring-slate-200"
              }`}
            >
              {formatTime(secondsLeft)}
            </span>
          )}
        </div>
      </div>

      {current >= 0 && (
        <ol className="flex gap-1.5">
          {STAGES.map((label, i) => (
            <li key={label} className="flex-1">
              <div
                className={`h-1.5 rounded-full ${
                  i < current ? "bg-indigo-500" : i === current ? "bg-indigo-400 animate-pulse" : "bg-slate-200"
                }`}
              />
              <p
                className={`mt-1 hidden text-xs sm:block ${
                  i === current ? "font-semibold text-indigo-700" : "text-slate-400"
                }`}
              >
                {label}
              </p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );

  if (state.phase === "waiting") {
    return (
      <Card className="space-y-8">
        {header}
        <div className="flex flex-col items-center gap-4 py-8 text-center">
          <Spinner large />
          <div>
            <h2 className="text-xl font-semibold text-slate-900">Waiting room</h2>
            <p className="text-slate-500">
              Waiting for the other participants to join. The study starts automatically.
            </p>
          </div>
        </div>
      </Card>
    );
  }

  if (state.phase === "results" && state.result) {
    return (
      <Card className="space-y-6">
        {header}
        <Results result={state.result} players={state.players} you={state.you} />
        <button className="btn btn-secondary" onClick={onLeave}>
          Leave the study
        </button>
      </Card>
    );
  }

  return (
    <Card className="space-y-5">
      {header}
      <div className="rounded-xl bg-indigo-50 px-4 py-3 text-sm text-indigo-900 ring-1 ring-indigo-100">
        {state.phase === "discussion"
          ? "💬 Discuss who should be the Decision Maker. Voting opens when the timer ends."
          : "🗳️ Chat is closed. Cast your vote for this round."}
      </div>
      <Chat
        messages={state.messages}
        you={state.you}
        enabled={state.phase === "discussion"}
        onSend={(text) => send({ type: "chat", text })}
      />
      <VotePanel
        players={state.players}
        you={state.you}
        enabled={state.phase === "voting"}
        myVote={state.my_vote}
        onVote={(target) => send({ type: "vote", target })}
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
    </Card>
  );
}

function Spinner({ large = false }: { large?: boolean }) {
  return (
    <div
      className={`animate-spin rounded-full border-slate-200 border-t-indigo-600 ${
        large ? "size-12 border-4" : "size-5 border-2"
      }`}
      aria-hidden
    />
  );
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}
