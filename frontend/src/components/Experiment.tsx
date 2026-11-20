import { useCountdown, useExperiment } from "../useExperiment";
import Chat from "./Chat";
import Results from "./Results";
import VotePanel from "./VotePanel";

interface Props {
  token: string;
  onLeave: () => void;
}

export default function Experiment({ token, onLeave }: Props) {
  const { state, connected, error, clockOffset, send } = useExperiment(token, onLeave);
  const secondsLeft = useCountdown(state?.deadline ?? null, clockOffset);

  if (!state) {
    return <section className="card">Connecting…</section>;
  }

  const header = (
    <div className="status-bar">
      <span className="badge">You are Player {state.you}</span>
      {state.phase === "discussion" || state.phase === "voting" ? (
        <span>
          Round {state.round} of {state.total_rounds} ·{" "}
          {state.phase === "discussion" ? "Discussion" : "Voting"}
          {secondsLeft != null && <strong className="timer"> {formatTime(secondsLeft)}</strong>}
        </span>
      ) : null}
      {!connected && <span className="error">Reconnecting…</span>}
    </div>
  );

  if (state.phase === "waiting") {
    return (
      <section className="card">
        {header}
        <h2>Waiting room</h2>
        <p>Waiting for the other participants to join. The study starts automatically.</p>
        <div className="spinner" aria-hidden />
      </section>
    );
  }

  if (state.phase === "results" && state.result) {
    return (
      <section className="card">
        {header}
        <Results result={state.result} players={state.players} you={state.you} />
        <button className="secondary" onClick={onLeave}>
          Leave
        </button>
      </section>
    );
  }

  return (
    <section className="card">
      {header}
      <p className="muted">
        {state.phase === "discussion"
          ? "Discuss who should be the Decision Maker. Voting opens when the timer ends."
          : "Chat is closed. Cast your vote for this round."}
      </p>
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
      {error && <p className="error">{error}</p>}
    </section>
  );
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}
