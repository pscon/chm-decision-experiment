# Group Decision Experiment

A small real-time web app for a 3-participant group decision experiment. Three
players, shown only as **Player A / B / C**, discuss for two rounds and vote
after each round for who should be the **Decision Maker**. Some seats can be
filled by simulated (rule-based) agents. Participants can't tell which seats
are human.

**Stack:** React + TypeScript (Vite) · FastAPI · PostgreSQL · Docker Compose

## Run it

```bash
docker compose up --build
```

Open **http://localhost:8080**.

To demo several humans on one machine, open each participant in its **own tab
or private window** and click *Join the study*. Each tab is a separate
participant, and refreshing a tab keeps your seat.

## Switch configuration

Edit [`config.yml`](config.yml), then restart the backend:

```bash
docker compose restart backend
```

| Condition         | `participants`            |
| ----------------- | ------------------------- |
| 3 humans          | `[human, human, human]`   |
| 2 humans + 1 AI   | `[human, human, ai]`      |
| 1 human + 2 AIs   | `[human, ai, ai]`         |

`discussion_seconds` (default 60) and `voting_seconds` (default 20) set the
timings. Shorter values like 10/8 are handy for a quick run-through.

Unit tests for the result calculation:

```bash
docker compose run --rm --no-deps backend python -m pytest -q
```

## How it works

```
browser ──HTTP/WS──> nginx (:8080) ──> FastAPI (backend:8000) ──> Postgres
```

- **Join:** `POST /api/join` returns an opaque token. The browser opens
  `/ws?token=…`, and the server works out the player from the token. Clients
  never send their own label.
- **Server-authoritative flow:** `waiting → discussion 1 → voting 1 →
  discussion 2 → voting 2 → results`. Each session has a single `run()` task
  that advances the phases, so a phase can't be advanced twice. Every phase
  change pushes the full state, including a server `deadline` timestamp. The
  browser countdown uses that deadline, corrected for the client's clock offset.
- **Validation (server side):** chat only during discussion (max 300 chars),
  one vote per round only during voting, and the target must be A/B/C.
  Duplicates are rejected in memory and again by a `UNIQUE(session, round,
  voter)` constraint in the database.
- **Concurrency:** joins go through one lock, so simultaneous joins can't
  overfill a session. Chat and votes take a per-session lock. When the third
  vote arrives, the run task is woken; the vote itself never advances the
  phase.
- **Persistence:** sessions (with a snapshot of the config/condition),
  participants (including their type), messages and votes are stored in
  Postgres.

Code map: [`backend/app/game.py`](backend/app/game.py) (flow and validation),
[`agents.py`](backend/app/agents.py) (simulated participants),
[`results.py`](backend/app/results.py) (tally),
[`frontend/src/useExperiment.ts`](frontend/src/useExperiment.ts) (WebSocket and
countdown).

## Design decisions

**Result and tie-break.** Votes from both rounds are added up and the player
with the most total votes wins. On a tie, the round-2 votes among the tied
players decide. If they're still tied, player order (A, then B, then C)
decides. Round-1 numbers are hidden until the end, and the final screen shows
round 1, round 2 and totals for everyone. Self-votes are allowed.

**Blind condition.** Participant types live only on the server, in memory and
in the `participants.kind` column. They never appear in API responses,
WebSocket messages or the UI. Configured seat types are mapped onto
**shuffled** labels per session, so the AI isn't always "Player C". The
waiting room doesn't show how many people are still missing, because that
would reveal how many seats are AI.

**Simulated agents (rule-based, no API key).** Each agent:
- starts with a random favourite (usually another player, ~30% itself)
- sends 2–3 short, casual, templated messages at random times during each
  discussion
- reads the chat for mentions ("Player B", a bare "B", "I can do it") and
  replies within a few seconds when it's addressed directly
- tends to agree with suggestions (~60%), which makes the group converge
- votes after a random 2–8 s "thinking" delay for whoever has the most support
  in the chat, falling back to its favourite

Agents go through exactly the same chat and vote checks as humans. An LLM
could be plugged into `RuleBasedAgent.compose()` later.

**Refresh, disconnects, stalled votes.**
- *Refresh:* the token is kept in `sessionStorage`, so reloading reconnects to
  the same seat and gets the full current state (chat history, your vote,
  timer).
- *Disconnect:* the client retries every 1.5 s. The experiment keeps running
  without anyone being dropped.
- *Stalled votes:* voting ends early once all 3 votes are in. Otherwise it
  closes after `voting_seconds`, and missing votes count as abstentions.
- *Server restart:* live state is in memory, so sessions that were running are
  marked `aborted` on startup. Browsers with an old token go back to the join
  screen.

## Trade-offs / not done (4-hour scope)

- **Single backend process.** The live state is in memory, which keeps the code
  simple. Scaling out would need shared state (e.g. Postgres row locks or
  Redis pub/sub) and resumable sessions.
- If a human leaves the **waiting room**, their seat isn't released (no
  heartbeat), so the session starts with a no-show.
- No authentication or consent flow, no admin/export UI (query Postgres
  directly), and no chat rate limiting.
- Agent language is template-based, so it can repeat itself in long sessions.
- Database credentials in `docker-compose.yml` are local demo values, and the
  database isn't exposed outside Docker.

## AI usage

See [`ai_prompts.md`](ai_prompts.md).
