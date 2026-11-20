from app.agents import mentioned_players


def msg(text, player="A"):
    return {"text": text, "player": player}


def test_detects_player_references():
    assert mentioned_players(msg("I think Player B should do it")) == ["B"]
    assert mentioned_players(msg("player c or B?")) == ["C", "B"]


def test_ignores_leading_article_a():
    assert mentioned_players(msg("A good choice would be Player C")) == ["C"]


def test_volunteering_counts_as_self_mention():
    assert mentioned_players(msg("I can do it", player="B")) == ["B"]


def test_no_mentions():
    assert mentioned_players(msg("hello everyone")) == []
