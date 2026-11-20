# AI Usage

**Tool:** Claude Code (VS Code extension) · **Model:** Claude Opus 5.5

## How I used AI

I used Claude Code to scaffold the project, help write utility functions and tests, and check the core experiment flow. I set the scope, worked on the integration, and tested the app myself in the browser.

### My contributions

- Defined the implementation scope and requirements, including the stack, experiment rules, participant anonymity, and what to verify within the four-hour limit.
- Worked on integrating parts of the application and checked how they behaved together by playing full sessions across multiple browser tabs.
- Checked the round timings against the assessment brief and captured the screenshots used in the README.
- Reviewed the initial UI and directed revisions to the styling and frontend structure. I asked for Tailwind CSS, a clearer interface, and a frontend organized into `components`, `hooks`, `lib`, and `types`.
- Reviewed the README and asked for a shorter version that still covered setup, configuration, and the main design decisions. I also chose the repository name and managed the Git branches and commits.

### Claude Code’s contributions

- Scaffolded the React frontend, FastAPI backend, and Docker Compose setup. It also drafted the initial README.
- Helped implement utility functions and write unit tests.
- Ran the Docker stack and used a temporary WebSocket test script to exercise all three participant configurations.
- Applied the UI, frontend structure, and documentation changes I requested during review.

## Prompts

**Initial prompt.** I attached the assessment brief with a structured build specification covering:

- the required stack
- the experiment flow and tie-break rule
- the participant configurations and how participant types stay hidden
- server-side validation and concurrency
- the deliverables

**Follow-up prompts** came out of reviewing and testing the running app. Each one targeted a specific change:

1. **Code structure:** split a file that mixed hooks, API calls and storage, and organise the frontend into `components`, `hooks`, `lib` and `types`.
2. **Documentation:** Helped with wiring the README while keeping setup, configuration and design decisions, and add clone instructions and screenshots.
3. **Testing:** extend the unit tests beyond the result tally to cover chat and vote validation, duplicate votes, concurrent joins, anonymity of client payloads, config loading and agent chat parsing.
