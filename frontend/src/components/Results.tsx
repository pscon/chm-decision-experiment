import type { Player, Result } from "../types";

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
  return (
    <div>
      <h2>Results</h2>
      <p className="winner">
        Player {winner}
        {winner === you && " (you)"} has been selected as the Decision Maker.
      </p>
      <table>
        <thead>
          <tr>
            <th>Player</th>
            <th>Round 1</th>
            <th>Round 2</th>
            <th>Total</th>
          </tr>
        </thead>
        <tbody>
          {players.map((p) => (
            <tr key={p} className={p === winner ? "highlight" : undefined}>
              <td>
                Player {p}
                {p === you && " (you)"}
              </td>
              <td>{result.by_round["1"]?.[p] ?? 0}</td>
              <td>{result.by_round["2"]?.[p] ?? 0}</td>
              <td>{result.totals[p]}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {result.tie_break && <p className="muted">{TIE_BREAK_NOTE[result.tie_break]}</p>}
    </div>
  );
}
