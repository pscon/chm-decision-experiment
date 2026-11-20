from __future__ import annotations

from .config import PLAYERS


def tally(votes: dict[int, dict[str, str]], players: tuple[str, ...] = PLAYERS) -> dict:
    """Pick the Decision Maker from the votes of all rounds.

    `votes` maps round number -> {voter: target}. Missing voters are abstentions.

    1. Most votes across all rounds wins.
    2. Tie: among the tied players, most votes in the final round wins.
    3. Still tied: first in player order (A, then B, then C).
    """
    by_round = {r: {p: 0 for p in players} for r in sorted(votes)}
    for r, ballots in votes.items():
        for target in ballots.values():
            by_round[r][target] += 1

    totals = {p: sum(counts[p] for counts in by_round.values()) for p in players}

    best = max(totals.values())
    leaders = [p for p in players if totals[p] == best]
    tie_break = None

    if len(leaders) > 1:
        final_round = by_round[max(by_round)]
        best_final = max(final_round[p] for p in leaders)
        leaders = [p for p in leaders if final_round[p] == best_final]
        tie_break = "final_round" if len(leaders) == 1 else "player_order"

    return {
        "decision_maker": leaders[0],
        "totals": totals,
        "by_round": {str(r): counts for r, counts in by_round.items()},
        "tie_break": tie_break,
    }
