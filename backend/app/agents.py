"""Rule-based simulated participants.

No LLM: each agent starts with a random favourite candidate, reads the chat
for mentions of players ("Player B", "B", "I can do it"), sends a few casual
templated messages at random times, replies when someone addresses it, and
votes for whoever has the most support in the chat (falling back to its
favourite). It goes through exactly the same chat/vote validation as humans.
"""

from __future__ import annotations

import asyncio
import random
import re
from typing import TYPE_CHECKING

from .config import PLAYERS

if TYPE_CHECKING:
    from .game import GameSession

PLAYER_REF = re.compile(r"\bplayer\s*([abc])\b", re.IGNORECASE)
BARE_LETTER = re.compile(r"(?<![\w'])([ABC])(?![\w'])")
VOLUNTEER = re.compile(
    r"\b(i('ll| will| can| could| would)? (do it|lead|take it|volunteer)|pick me|vote (for )?me|i'?m happy to)\b",
    re.IGNORECASE,
)

OPENERS = [
    "hi all! so we need to pick a decision maker. anyone keen?",
    "hey :) should everyone just say if they want to do it or not?",
    "hi. honestly I don't mind who it is as long as they take it seriously",
]
ENDORSE = [
    "I'd go with Player {x}, seems like a reasonable choice",
    "maybe Player {x}? no strong reason, just a feeling",
    "I'm leaning towards Player {x} tbh",
]
VOLUNTEER_LINES = [
    "I could do it if nobody else wants to",
    "happy to take it, I'm usually pretty careful with decisions",
    "I wouldn't mind being the decision maker tbh",
]
AGREE = [
    "ok yeah, Player {x} works for me",
    "fine by me, Player {x} it is",
    "agreed, Player {x} sounds good",
]
DISAGREE = [
    "hmm not sure, I was thinking Player {x}",
    "could be, but I'd still lean Player {x}",
]
ADDRESSED = [
    "me? sure, I can do it if you all want",
    "haha ok, I wouldn't say no",
    "thanks! happy to if that's what we decide",
]
ANSWER = [
    "good question. I'd say Player {x}",
    "not sure honestly, maybe Player {x}?",
]
ROUND_TWO = [
    "ok last round, let's just settle on someone. Player {x}?",
    "so are we going with Player {x}? I'm fine with that",
    "I think Player {x} still makes sense",
]


def mentioned_players(message: dict) -> list[str]:
    """Players a chat message seems to point at."""
    text = message["text"]
    refs = [m.upper() for m in PLAYER_REF.findall(text)]
    for match in BARE_LETTER.finditer(text):
        # A capital "A" at the start of a message is usually the article.
        if not (match.group(1) == "A" and match.start() == 0):
            refs.append(match.group(1))
    if VOLUNTEER.search(text):
        refs.append(message["player"])
    return list(dict.fromkeys(refs))  # dedupe, keep order


class RuleBasedAgent:
    def __init__(self, label: str, session: GameSession):
        self.label = label
        self.session = session
        self.rng = random.Random()
        others = [p for p in PLAYERS if p != label]
        # Mostly backs someone else, sometimes puts itself forward.
        self.favourite = label if self.rng.random() < 0.3 else self.rng.choice(others)
        self.last_seen_id = 0
        self.spoke_this_round = False
        self.used_lines: set[str] = set()

    # ---- reading the chat ------------------------------------------------

    def support(self) -> dict[str, int]:
        scores = {p: 0 for p in PLAYERS}
        scores[self.favourite] += 1
        for message in self.session.messages:
            if message["player"] == self.label:
                continue
            for p in mentioned_players(message):
                scores[p] += 1
        return scores

    def preferred(self) -> str:
        scores = self.support()
        best = max(scores.values())
        leaders = [p for p in PLAYERS if scores[p] == best]
        return self.favourite if self.favourite in leaders else self.rng.choice(leaders)

    def unseen_messages(self) -> list[dict]:
        return [
            m for m in self.session.messages
            if m["id"] > self.last_seen_id and m["player"] != self.label
        ]

    # ---- writing ---------------------------------------------------------

    def _pick(self, lines: list[str]) -> str:
        """Random line, avoiding ones this agent already used if possible."""
        fresh = [line for line in lines if line not in self.used_lines] or lines
        line = self.rng.choice(fresh)
        self.used_lines.add(line)
        return line

    def _about(self, candidate: str, lines: list[str]) -> str:
        if candidate == self.label:
            return self._pick(VOLUNTEER_LINES)
        return self._pick(lines).format(x=candidate)

    def compose(self, round_: int) -> str:
        new = self.unseen_messages()
        if self.session.messages:
            self.last_seen_id = self.session.messages[-1]["id"]

        if new:
            last = new[-1]
            refs = [p for p in mentioned_players(last) if p != last["player"]] or mentioned_players(last)
            if self.label in refs:
                self.favourite = self.label  # accepted the nomination, stay consistent
                return self._pick(ADDRESSED)
            if refs:
                candidate = refs[0]
                if candidate == self.favourite or self.rng.random() < 0.6:
                    self.favourite = candidate  # go along with the group
                    return self._about(candidate, AGREE)
                return self._about(self.favourite, DISAGREE)
            if "?" in last["text"]:
                return self._about(self.preferred(), ANSWER)

        if round_ == 1 and not self.spoke_this_round:
            return self._pick(OPENERS)
        return self._about(self.preferred(), ROUND_TWO if round_ == 2 else ENDORSE)

    def _addressed(self) -> bool:
        return any(self.label in mentioned_players(m) for m in self.unseen_messages())

    async def discuss(self, round_: int, duration: int) -> None:
        loop = asyncio.get_running_loop()
        start = loop.time()
        self.spoke_this_round = False
        schedule = sorted(self.rng.uniform(0.1, 0.85) * duration for _ in range(self.rng.randint(2, 3)))
        replied = False

        while self.session.phase == "discussion" and self.session.round == round_:
            await asyncio.sleep(1)
            elapsed = loop.time() - start

            if not replied and self._addressed():
                await asyncio.sleep(self.rng.uniform(2, 4))  # "typing"
                replied = True
            elif schedule and elapsed >= schedule[0]:
                schedule.pop(0)
            else:
                continue

            if self.session.phase != "discussion" or self.session.round != round_:
                return
            await self.session.post_chat(self.label, self.compose(round_))
            self.spoke_this_round = True

    async def vote(self, round_: int, voting_seconds: int) -> None:
        high = max(2.5, min(8.0, voting_seconds * 0.6))
        await asyncio.sleep(self.rng.uniform(2.0, high))
        await self.session.cast_vote(self.label, self.preferred())
