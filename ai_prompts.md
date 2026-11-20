# AI Usage Log

## Tools and models

| Field | Value |
| ----- | ----- |
| Agent / tool | Claude Code (VS Code extension) |
| Model | Claude Opus 5.5 (`claude-opus-5-5`), as reported by the agent's own environment. **TODO (author): confirm with `/status` or `/model` in Claude Code.** |
| Other AI tools | **TODO (author): if you drafted Prompt 1 with another assistant (e.g. ChatGPT), add that tool, the model and the prompts you gave it here.** |

The agent wrote the code, ran the Docker stack and ran an end-to-end WebSocket
test script (scratch file, not committed) against all three configurations.

---

## Prompt 1

The message had four parts: the assessment brief (attached as a file), a build
prompt, the invitation email, and one line of my own.

- **Attachment:** `technical-assessment-multi-participant-human-ai-experiment-platform-v4.md`, the assessment brief from CHM (not reproduced here).
- **Pasted invitation email:** *omitted from this public log because it contains personal details and contact addresses.*

**My line (verbatim):**

> i wanna build this sumarize if you understand create a folder under my persnal perojects and lets do something standard not too extensive human like

**Pasted build prompt (verbatim):**

```text
Build the Max Planck Institute for Human Development technical assessment for the Student Research Assistant – Full-Stack Developer role. The project is a lightweight web application for a three-participant human–AI decision-making experiment.

Work directly in the current repository. Inspect it first and preserve any existing user work. Give me a brief implementation plan, then implement it and verify the core flow. The assessment has a four-hour effort limit. Keep the scope small and prioritize a working experiment, readable code, and a demo I can explain in an interview.

## Required stack

- Frontend: React. Use TypeScript and Vite if starting from an empty repository.
- Backend: Python with FastAPI.
- Database: PostgreSQL.
- Local setup: Docker Compose. `docker compose up --build` must start the entire application.
- Configuration: a root `config.yml` that controls participant types and round duration.

## Experiment flow

1. A human opens the app and joins a session. Assign each participant a neutral identity: Player A, Player B, or Player C. Each session has exactly three participants.
2. Put humans in a waiting room. Start the experiment once all human slots specified by the configuration are filled. AI agents fill the other slots automatically.
3. Run two rounds of real-time text discussion. Each discussion lasts about 60 seconds by default. The group’s goal is to elect one of the three players as the Decision Maker for a hypothetical future experiment.
4. After each discussion, switch to voting. Each participant, including each AI agent, casts one vote for any of the three players.
5. After the second vote, display the final tally and the selected Decision Maker to everyone. Use the combined votes across both rounds. If there is a tie, use second-round votes among the tied players, then use player order as a deterministic fallback. Keep round-one totals hidden until the final result. Document these choices as implementation decisions.

## Configuration and anonymity

- Support all three configurations by editing YAML and restarting, without changing source code:
  - 3 humans
  - 2 humans and 1 AI agent
  - 1 human and 2 AI agents
- Keep participant types on the server. Every player should appear under their neutral label. Keep human/AI status out of browser payloads, public API responses, WebSocket events, and participant-facing UI.
- Use lightweight, rule-based simulated agents that send timed messages relevant to the discussion and cast votes. Have them react to basic chat context where practical. Document the simulation approach. The Docker demo must work without an external API key.

## Implementation

- Use a server-authoritative flow: waiting → discussion 1 → voting 1 → discussion 2 → voting 2 → results. Use WebSockets to broadcast chat and phase updates. The browser countdown should use the server’s phase deadline.
- Validate actions on the backend. A participant can chat only during discussion and cast only one vote per round during voting. Derive the acting player from a server-issued session token. Make sure two simultaneous joins or final votes cannot overfill the room or advance the phase twice.
- Store sessions, messages, and votes in PostgreSQL. Keep the deployment single-instance for this assessment. Document how you handle refreshes, disconnects, and stalled votes. Prefer a simple, predictable behavior that is easy to demo.
- Build a minimal UI showing the player’s identity, waiting status, current round, countdown, chat, voting options, and final result. Disable controls outside their relevant phase.

## Repository deliverables

- Working source code, `config.yml`, and Docker setup.
- A short `README.md` with the startup command, local URL, how to switch through all three configurations, how to demo using separate browser sessions, and key trade-offs. Document the result calculation, tie-break, and simulated AI behavior.
- An `ai_prompts.md` file. Record my actual prompts verbatim, starting with this prompt, and leave clearly marked fields for the exact tool and model if you cannot verify them. Never invent prompts, model names, or tool usage. Flag any log entries I need to add myself.
- Keep credentials and personal information out of the public repository. Do not publish the repository or send an email.

## Verification

Start the app via Docker Compose if Docker is available. Use a shorter round duration for verification, then restore the default of approximately 60 seconds. Exercise all three configurations end to end. Confirm the waiting room starts at the right human count, chat updates across clients, both rounds complete, duplicate votes are rejected, and everyone sees identical final results. Check browser-facing payloads for participant-type leaks. Run the frontend build and any relevant existing checks. If anything cannot be run, report exactly what remains unverified.

At the end, tell me how to start the app, what you verified, and any gaps or trade-offs. Give me a short outline for my five-minute interview presentation, grounded in the work we actually did and the decisions I need to be ready to explain.
```

---

## Later prompts

**TODO (author): add every follow-up prompt you send in this or later sessions, verbatim, below.**
