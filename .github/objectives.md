<!-- Last modified: 2026-07-14T22:58:57.752Z -->
<!-- Managed by loop-improver-mcp -->

# Repository Objectives

Use this file for the repo's aspirational objectives: what the repo is trying to become, what quality means here, and which loops keep it improving.

## Working Profile

- Detected profile: python
- Suggested specialist: Python code quality specialist

## Aspirational Objectives

1. Make the README a clear, concise capability page for the repo.
2. Keep Copilot instructions focused on durable rules, validation, and cleanup expectations.
3. Create missing `.github` collaboration surfaces when older repos do not have them.
4. Use repo agents only for recurring domain work that benefits from a dedicated instruction surface.
5. Tune repo-specialist guidance around the repo's actual language, content, product, or infrastructure work.
6. Surface files without `Last modified` timestamps and files older than the current freshness threshold as attention candidates that help a session choose one objective and focus folder.

## Agent Map

- loop-improver-mcp: owns README/Copilot/objectives hygiene and decides which managed surfaces should exist.
- repo-specialist-agent: Keep the Python MCP surface small, tested, typed, and aligned to the repo objectives.

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
  - States the repo-specific outcomes that should improve over time.
  - Maps each active loop or specialist surface to the outcomes it serves.
  - Defines evidence or verification that shows an improvement actually landed.
- Last modified hygiene
  - Surfaces text files without a Last modified timestamp as attention candidates.
  - Surfaces text files with timestamps older than the configured stale threshold, defaulting to 30 days.
  - Uses timestamp age to help the session choose one objective and focus folder, not as proof that a file is wrong.
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
