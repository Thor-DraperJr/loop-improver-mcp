<!-- Last modified: 2026-07-09T13:40:00.146Z -->
<!-- Managed by loop-improver-mcp -->

# Repository Objectives

Use this file for the repo's aspirational objectives: what the repo is trying to become, what quality means here, and which loops keep it improving.

## Working Profile

- Detected profile: python
- Suggested specialist: Python MCP hygiene specialist

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

- `README.md`: standalone capability page with repo purpose, audience, tool surface, and durable entry points.
- `.github/copilot-instructions.md`: durable repo rules, validation expectations, safety boundaries, and canonical file ownership.
- `.github/objectives.md`: current outcomes, active loop map, and evidence that proves improvement.
- Last modified hygiene: missing timestamps and files older than 30 days are surfaced as review candidates that guide objective and folder selection, not automatic failures.
- `.github/agents/`: specialist guidance only when recurring domain work needs its own instruction surface.
- `.github/insights/`: one current insight per MCP or specialist surface with verified improvements, prune candidates, reusable learnings, and self-improvement notes.

## Verification

Each loop pass should name the changed behavior, run the cheapest relevant check, capture evidence, and record what improved in .github/insights/.
