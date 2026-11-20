import pytest

from app import game
from app.config import ExperimentConfig


class FakeDb:
    """In-memory stand-in for app.db, so game logic can be tested without Postgres."""

    def __init__(self):
        self.messages = []
        self.votes = []

    async def create_session(self, *args):
        pass

    async def add_human(self, *args):
        pass

    async def update_phase(self, *args):
        pass

    async def finish_session(self, *args):
        pass

    async def insert_message(self, session_id, round_, sender, text):
        self.messages.append((round_, sender, text))
        return len(self.messages)

    async def insert_vote(self, session_id, round_, voter, target):
        self.votes.append((round_, voter, target))


@pytest.fixture
def fake_db(monkeypatch):
    fake = FakeDb()
    monkeypatch.setattr(game, "db", fake)
    return fake


def make_config(*participants, discussion=60, voting=20):
    return ExperimentConfig(tuple(participants), discussion, voting)
