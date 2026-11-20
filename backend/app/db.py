"""Thin persistence layer. The live game state is held in memory by the
single backend process; every session, participant, message and vote is also
written to Postgres so the experiment data survives and can be analysed."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid

import asyncpg

log = logging.getLogger(__name__)
pool: asyncpg.Pool | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id             UUID PRIMARY KEY,
    config         JSONB NOT NULL,
    status         TEXT NOT NULL DEFAULT 'waiting',  -- waiting | running | finished | aborted
    phase          TEXT NOT NULL DEFAULT 'waiting',
    round          INT  NOT NULL DEFAULT 0,
    decision_maker TEXT,
    result         JSONB,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at     TIMESTAMPTZ,
    finished_at    TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS participants (
    id         SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id),
    label      TEXT NOT NULL,
    kind       TEXT NOT NULL,          -- human | ai (never sent to clients)
    token      TEXT UNIQUE,            -- NULL for AI agents
    joined_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, label)
);

CREATE TABLE IF NOT EXISTS messages (
    id         SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id),
    round      INT  NOT NULL,
    sender     TEXT NOT NULL,
    text       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS votes (
    id         SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES sessions(id),
    round      INT  NOT NULL,
    voter      TEXT NOT NULL,
    target     TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (session_id, round, voter)
);
"""


async def connect() -> None:
    global pool
    dsn = os.environ["DATABASE_URL"]
    for attempt in range(30):
        try:
            pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
            break
        except (OSError, asyncpg.PostgresError):
            log.info("database not ready yet (attempt %s)", attempt + 1)
            await asyncio.sleep(1)
    else:
        raise RuntimeError("could not connect to database")

    async with pool.acquire() as conn:
        await conn.execute(SCHEMA)
        # Live state is in memory, so sessions interrupted by a restart can't resume.
        await conn.execute(
            "UPDATE sessions SET status = 'aborted' WHERE status IN ('waiting', 'running')"
        )


async def close() -> None:
    if pool:
        await pool.close()


async def create_session(session_id: uuid.UUID, config: dict, ai_labels: list[str]) -> None:
    async with pool.acquire() as conn, conn.transaction():
        await conn.execute(
            "INSERT INTO sessions (id, config) VALUES ($1, $2::jsonb)", session_id, json.dumps(config)
        )
        for label in ai_labels:
            await conn.execute(
                "INSERT INTO participants (session_id, label, kind) VALUES ($1, $2, 'ai')",
                session_id, label,
            )


async def add_human(session_id: uuid.UUID, label: str, token: str) -> None:
    await pool.execute(
        "INSERT INTO participants (session_id, label, kind, token) VALUES ($1, $2, 'human', $3)",
        session_id, label, token,
    )


async def update_phase(session_id: uuid.UUID, phase: str, round_: int) -> None:
    await pool.execute(
        """UPDATE sessions SET phase = $2, round = $3, status = 'running',
               started_at = COALESCE(started_at, now())
           WHERE id = $1""",
        session_id, phase, round_,
    )


async def insert_message(session_id: uuid.UUID, round_: int, sender: str, text: str) -> int:
    return await pool.fetchval(
        "INSERT INTO messages (session_id, round, sender, text) VALUES ($1, $2, $3, $4) RETURNING id",
        session_id, round_, sender, text,
    )


async def insert_vote(session_id: uuid.UUID, round_: int, voter: str, target: str) -> None:
    await pool.execute(
        "INSERT INTO votes (session_id, round, voter, target) VALUES ($1, $2, $3, $4)",
        session_id, round_, voter, target,
    )


async def finish_session(session_id: uuid.UUID, result: dict) -> None:
    await pool.execute(
        """UPDATE sessions SET status = 'finished', phase = 'results', decision_maker = $2,
               result = $3::jsonb, finished_at = now()
           WHERE id = $1""",
        session_id, result["decision_maker"], json.dumps(result),
    )
