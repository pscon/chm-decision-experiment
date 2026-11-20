from app.results import tally


def test_clear_winner_across_rounds():
    votes = {1: {"A": "B", "B": "B", "C": "A"}, 2: {"A": "B", "B": "C", "C": "B"}}
    result = tally(votes)
    assert result["decision_maker"] == "B"
    assert result["totals"] == {"A": 1, "B": 4, "C": 1}
    assert result["tie_break"] is None


def test_tie_broken_by_final_round():
    # A and C both have 3 in total, C got more votes in round 2.
    votes = {1: {"A": "A", "B": "A", "C": "C"}, 2: {"A": "A", "B": "C", "C": "C"}}
    result = tally(votes)
    assert result["totals"]["A"] == result["totals"]["C"] == 3
    assert result["decision_maker"] == "C"
    assert result["tie_break"] == "final_round"


def test_tie_falls_back_to_player_order():
    votes = {1: {"A": "A", "B": "B", "C": "C"}, 2: {"A": "C", "B": "B", "C": "A"}}
    result = tally(votes)
    assert result["decision_maker"] == "A"
    assert result["tie_break"] == "player_order"


def test_abstentions_count_as_no_vote():
    votes = {1: {"A": "C"}, 2: {}}
    result = tally(votes)
    assert result["decision_maker"] == "C"
    assert result["by_round"]["2"] == {"A": 0, "B": 0, "C": 0}
