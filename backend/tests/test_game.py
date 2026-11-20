import asyncio
import json

from app import game
from app.game import GameSession, SessionManager

from .conftest import make_config


def run(coro):
    return asyncio.run(coro)


def session_in(phase, round_=1):
    session = GameSession(make_config("human", "human", "ai"))
    session.phase = phase
    session.round = round_
    return session


# ---- chat --------------------------------------------------------------


def test_chat_accepted_during_discussion(fake_db):
    session = session_in("discussion")
    assert run(session.post_chat("A", "  hello  ")) is None
    assert session.messages[-1]["text"] == "hello"
    assert fake_db.messages == [(1, "A", "hello")]


def test_chat_rejected_outside_discussion(fake_db):
    for phase in ("waiting", "voting", "results"):
        session = session_in(phase)
        assert run(session.post_chat("A", "hi")) is not None
        assert session.messages == []
    assert fake_db.messages == []


def test_chat_rejects_empty_and_too_long_messages(fake_db):
    session = session_in("discussion")
    assert run(session.post_chat("A", "   ")) is not None
    assert run(session.post_chat("A", "x" * (game.MAX_MESSAGE_LENGTH + 1))) is not None
    assert session.messages == []


# ---- voting ------------------------------------------------------------


def test_vote_rejected_outside_voting(fake_db):
    session = session_in("discussion")
    assert run(session.cast_vote("A", "B")) is not None
    assert session.votes[1] == {}


def test_vote_rejects_unknown_target(fake_db):
    session = session_in("voting")
    assert run(session.cast_vote("A", "D")) is not None
    assert session.votes[1] == {}


def test_duplicate_vote_rejected(fake_db):
    session = session_in("voting")
    assert run(session.cast_vote("A", "B")) is None
    assert run(session.cast_vote("A", "C")) is not None
    assert session.votes[1] == {"A": "B"}
    assert fake_db.votes == [(1, "A", "B")]


def test_self_vote_allowed(fake_db):
    session = session_in("voting")
    assert run(session.cast_vote("A", "A")) is None


def test_all_voted_only_after_third_vote(fake_db):
    session = session_in("voting")
    run(session.cast_vote("A", "B"))
    run(session.cast_vote("B", "B"))
    assert not session.all_voted.is_set()
    run(session.cast_vote("C", "A"))
    assert session.all_voted.is_set()


# ---- anonymity ---------------------------------------------------------


def test_snapshot_does_not_leak_participant_types(fake_db):
    session = GameSession(make_config("human", "ai", "ai"))
    for label in "ABC":
        payload = json.dumps(session.snapshot(label))
        assert '"human"' not in payload
        assert '"ai"' not in payload
        assert "ai_labels" not in payload and "human_labels" not in payload


def test_seat_types_match_config():
    session = GameSession(make_config("human", "ai", "ai"))
    assert len(session.human_labels) == 1
    assert len(session.ai_labels) == 2
    assert sorted(session.human_labels + session.ai_labels) == ["A", "B", "C"]


def test_round_one_votes_hidden_during_round_two(fake_db):
    session = session_in("voting")
    run(session.cast_vote("A", "B"))
    session.phase, session.round = "discussion", 2
    snap = session.snapshot("A")
    assert snap["my_vote"] is None
    assert snap["result"] is None


# ---- joining -----------------------------------------------------------


def test_concurrent_joins_do_not_overfill(fake_db, monkeypatch):
    async def no_run(self):
        pass

    monkeypatch.setattr(GameSession, "run", no_run)
    manager = SessionManager(make_config("human", "human", "human"))

    async def join_many():
        return await asyncio.gather(*(manager.join() for _ in range(6)))

    tokens = run(join_many())
    seats = [manager.lookup(t) for t in tokens]
    sessions = {id(s) for s, _ in seats}
    assert len(sessions) == 2
    for session_id in sessions:
        labels = [label for s, label in seats if id(s) == session_id]
        assert sorted(labels) == ["A", "B", "C"]
