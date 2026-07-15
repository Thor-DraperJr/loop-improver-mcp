<!-- Last modified: 2026-07-15T00:26:29.191Z -->
<!-- Managed by loop-improver-mcp -->

# Repository Objectives

Use this file for the shared repository mission: what the repo is trying to become, what quality means here, and how specialized loops contribute to that mission.

## Working Profile

- Detected profile: python
- Suggested specialist: Python code quality specialist

## Aspirational Objectives

1. Keep the Python capability deterministic, readable, and stable at its public interfaces.
2. Cover behavior changes with focused tests and configured quality checks.
3. Remove dead or duplicated code after verifying references and framework usage.
4. Keep collaboration guidance concise and create specialist surfaces only for recurring work.

## Agent Map

- loop-improver-mcp: owns README/Copilot/objectives hygiene and decides which managed surfaces should exist.
- repo-specialist-agent: Keep the Python code small, typed, tested, readable, and aligned to the repo objectives.


## Outcome Expectations

- README.md
  - Names what the repository is and who it serves in the first screen.
  - Explains capabilities and outcomes without carrying operational runbooks or agent rules.
  - Points to deeper docs only when those docs are durable entry points.
- .github/copilot-instructions.md
  - Contains durable rules, validation expectations, safety boundaries, and canonical file ownership.
  - Prunes legacy session-management, tool-ordering, setup, and prompt-command boilerplate.
  - Separates broad repo rules from specialist-agent instructions and temporary troubleshooting notes.
- .github/objectives.md
  - States the shared repository mission and the outcomes that define success.
  - Names specialized loops that contribute evidence and learning to that mission.
  - Defines evidence or verification that shows the mission is advancing.
- Last modified hygiene
  - Surfaces text files without a Last modified timestamp as attention candidates.
  - Surfaces text files with timestamps older than the configured stale threshold, defaulting to 30 days.
  - Uses timestamp age to help the session choose a mission-serving focus and folder, not as proof that a file is wrong.
- .github/agents/repo-specialist-agent.agent.md
  - Focuses on recurring domain work for the detected python profile.
  - Uses this mission as its default lens: Keep the Python code small, typed, tested, readable, and aligned to the repo objectives.
  - Reads objectives and latest insights before changing files, then records reusable learnings after focused passes.
- .github/insights/
  - Keeps one current insight per MCP or specialist surface instead of growing forever.
  - Records verified improvements, prune candidates, reusable learnings, and self-improvement notes.
  - Turns one-off discoveries into better future repo guidance instead of scattered chat memory.

## Verification

Each loop pass should name the changed behavior, run the cheapest relevant check, capture evidence, and record what improved in .github/insights/.

Detected commands:

- `python -m pytest`
- `python -m ruff check src tests`
- `python -m vulture`
