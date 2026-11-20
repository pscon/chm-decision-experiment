import type { Player } from "../types";

interface Props {
  players: Player[];
  you: Player;
  enabled: boolean;
  myVote: Player | null;
  onVote: (target: Player) => void;
}

export default function VotePanel({ players, you, enabled, myVote, onVote }: Props) {
  return (
    <div className="vote-panel">
      <h3>Vote for the Decision Maker</h3>
      <div className="vote-options">
        {players.map((p) => (
          <button
            key={p}
            className={myVote === p ? "selected" : "secondary"}
            disabled={!enabled || myVote !== null}
            onClick={() => onVote(p)}
          >
            Player {p}
            {p === you && " (you)"}
          </button>
        ))}
      </div>
      {enabled && myVote && <p className="muted">Vote recorded. Waiting for the others…</p>}
      {!enabled && <p className="muted">Voting opens after the discussion.</p>}
    </div>
  );
}
