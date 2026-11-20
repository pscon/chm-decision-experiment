from __future__ import annotations

import os
from dataclasses import dataclass

import yaml

PLAYERS = ("A", "B", "C")
ROUNDS = 2
PARTICIPANT_TYPES = {"human", "ai"}


@dataclass(frozen=True)
class ExperimentConfig:
    participants: tuple[str, ...]
    discussion_seconds: int
    voting_seconds: int

    @property
    def human_count(self) -> int:
        return self.participants.count("human")

    def as_dict(self) -> dict:
        return {
            "participants": list(self.participants),
            "discussion_seconds": self.discussion_seconds,
            "voting_seconds": self.voting_seconds,
        }


def load_config(path: str | None = None) -> ExperimentConfig:
    path = path or os.getenv("CONFIG_PATH", "config.yml")
    with open(path) as f:
        raw = yaml.safe_load(f) or {}

    participants = tuple(str(p).strip().lower() for p in raw.get("participants", []))
    if len(participants) != len(PLAYERS):
        raise ValueError(f"config: expected {len(PLAYERS)} participants, got {len(participants)}")
    unknown = set(participants) - PARTICIPANT_TYPES
    if unknown:
        raise ValueError(f"config: unknown participant type(s) {sorted(unknown)}")
    if "human" not in participants:
        raise ValueError("config: at least one participant must be human")

    discussion = int(raw.get("discussion_seconds", 60))
    voting = int(raw.get("voting_seconds", 20))
    if discussion < 5 or voting < 5:
        raise ValueError("config: discussion_seconds and voting_seconds must be >= 5")

    return ExperimentConfig(participants, discussion, voting)
