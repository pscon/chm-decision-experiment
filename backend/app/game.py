"""Server-authoritative experiment flow.

Phases: waiting -> discussion 1 -> voting 1 -> discussion 2 -> voting 2 -> results

Each session has exactly one `run()` task that moves through the phases, so
a phase can never be advanced twice. Chat and votes are validated under the
session lock against the current phase.
"""

from __future__ import annotations

import asyncio
import logging
import random
import secrets
import time
import uuid

from fastapi import WebSocket

from . import db
from .agents import RuleBasedAgent
from .config import PLAYERS, ROUNDS, ExperimentConfig
from .results import tally

log = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 300


def now_ms() -> int:
    return int(time.time() * 1000)


class GameSession:
    def __init__(self, config: ExperimentConfig):
        self.id = uuid.uuid4()
        self.config = config

        # Map the configured seat types onto shuffled labels, so the AI
        # isn't predictably "Player C".
        labels = list(PLAYERS)
        random.shuffle(labels)
        seats = dict(zip(labels, config.participants))
        self.human_labels = [label for label in labels if seats[label] == "human"]
        self.ai_labels = [label for label in labels if seats[label] == "ai"]
        self.joined: list[str] = []

        self.phase = "waiting"
        self.round = 0
        self.deadline_ms: int | None = None
        self.messages: list[dict] = []
        self.votes: dict[int, dict[str, str]] = {r: {} for r in range(1, ROUNDS + 1)}
        self.result: dict | None = None

        self.sockets: dict[str, set[WebSocket]] = {label: set() for label in PLAYERS}
        self.lock = asyncio.Lock()
        self.all_voted = asyncio.Event()
        self.agents = [RuleBasedAgent(label, self) for label in self.ai_labels]
        self._tasks: set[asyncio.Task] = set()

    # ---- joining -------------------------------------------------------

    @property
    def open_slots(self) -> int:
        return len(self.human_labels) - len(self.joined)

    def claim_slot(self) -> str:
        label = self.human_labels[len(self.joined)]
        self.joined.append(label)
        return label

    def spawn(self, coro) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    # ---- phase loop ----------------------------------------------------

    async def run(self) -> None:
        try:
            for r in range(1, ROUNDS + 1):
                await self._enter_phase("discussion", r, self.config.discussion_seconds)
                for agent in self.agents:
                    self.spawn(agent.discuss(r, self.config.discussion_seconds))
                await asyncio.sleep(self.config.discussion_seconds)

                self.all_voted.clear()
                await self._enter_phase("voting", r, self.config.voting_seconds)
                for agent in self.agents:
                    self.spawn(agent.vote(r, self.config.voting_seconds))
                try:
                    await asyncio.wait_for(self.all_voted.wait(), self.config.voting_seconds)
                except asyncio.TimeoutError:
                    missing = set(PLAYERS) - set(self.votes[r])
                    log.info("session %s round %s: voting timed out, abstained: %s", self.id, r, missing)

            await self._finish()
        except Exception:
            log.exception("session %s crashed", self.id)

    async def _enter_phase(self, phase: str, round_: int, seconds: int) -> None:
        async with self.lock:
            self.phase = phase
            self.round = round_
            self.deadline_ms = now_ms() + seconds * 1000
            await db.update_phase(self.id, phase, round_)
        await self.broadcast_state()

    async def _finish(self) -> None:
        async with self.lock:
            self.result = tally(self.votes)
            self.phase = "results"
            self.deadline_ms = None
            await db.finish_session(self.id, self.result)
        for task in list(self._tasks):
            if task is not asyncio.current_task():
                task.cancel()
        await self.broadcast_state()
        log.info("session %s finished: %s", self.id, self.result)

    # ---- participant actions -------------------------------------------

    async def post_chat(self, sender: str, text: str) -> str | None:
        """Returns an error message, or None on success."""
        text = (text or "").strip()
        if not text:
            return "Message is empty."
        if len(text) > MAX_MESSAGE_LENGTH:
            return f"Messages are limited to {MAX_MESSAGE_LENGTH} characters."

        async with self.lock:
            if self.phase != "discussion":
                return "Chat is only open during the discussion."
            msg_id = await db.insert_message(self.id, self.round, sender, text)
            message = {"id": msg_id, "player": sender, "round": self.round, "text": text, "ts": now_ms()}
            self.messages.append(message)

        await self.broadcast({"type": "chat", "message": message})
        return None

    async def cast_vote(self, voter: str, target: str) -> str | None:
        """Returns an error message, or None on success."""
        if target not in PLAYERS:
            return "Unknown player."

        async with self.lock:
            if self.phase != "voting":
                return "Voting is not open right now."
            ballots = self.votes[self.round]
            if voter in ballots:
                return "You have already voted this round."
            await db.insert_vote(self.id, self.round, voter, target)
            ballots[voter] = target
            if len(ballots) == len(PLAYERS):
                self.all_voted.set()

        await self.send_state(voter)
        return None

    # ---- what clients see ----------------------------------------------

    def snapshot(self, label: str) -> dict:
        """Everything a participant may see. Participant types are never included,
        and round votes stay hidden until the final result."""
        my_vote = self.votes.get(self.round, {}).get(label) if self.phase == "voting" else None
        return {
            "type": "state",
            "you": label,
            "server_time": now_ms(),
            "phase": self.phase,
            "round": self.round,
            "total_rounds": ROUNDS,
            "deadline": self.deadline_ms,
            "players": list(PLAYERS),
            "messages": self.messages,
            "my_vote": my_vote,
            "result": self.result,
        }

    def attach(self, label: str, ws: WebSocket) -> None:
        self.sockets[label].add(ws)

    def detach(self, label: str, ws: WebSocket) -> None:
        self.sockets[label].discard(ws)

    async def _send(self, ws: WebSocket, payload: dict) -> None:
        try:
            await ws.send_json(payload)
        except Exception:
            pass  # socket already gone; the endpoint cleans it up

    async def send_state(self, label: str) -> None:
        for ws in list(self.sockets[label]):
            await self._send(ws, self.snapshot(label))

    async def broadcast_state(self) -> None:
        for label in PLAYERS:
            await self.send_state(label)

    async def broadcast(self, payload: dict) -> None:
        for label in PLAYERS:
            for ws in list(self.sockets[label]):
                await self._send(ws, payload)


class SessionManager:
    """Hands out seats. Humans fill the current waiting session; when its last
    human seat is taken the experiment starts and the next join opens a new one."""

    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.waiting: GameSession | None = None
        self.by_token: dict[str, tuple[GameSession, str]] = {}
        self.lock = asyncio.Lock()

    async def join(self) -> str:
        # The lock makes concurrent joins sequential, so a session can't be
        # overfilled and `run()` is started exactly once.
        async with self.lock:
            session = self.waiting
            if session is None:
                session = GameSession(self.config)
                await db.create_session(session.id, self.config.as_dict(), session.ai_labels)
                self.waiting = session

            label = session.claim_slot()
            token = secrets.token_urlsafe(24)
            await db.add_human(session.id, label, token)
            self.by_token[token] = (session, label)

            if session.open_slots == 0:
                self.waiting = None
                session.spawn(session.run())
            return token

    def lookup(self, token: str) -> tuple[GameSession, str] | None:
        return self.by_token.get(token)
