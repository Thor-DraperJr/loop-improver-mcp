<!-- Last modified: 2026-07-14T00:00:00.000Z -->
---
mode: agent
description: 'Run one loop architecture pass on loop-improver-mcp.'
---

# Improvement loop

Run one focused pass on this MCP server.

1. Check README.md and .github/copilot-instructions.md hygiene first.
2. Read .github/objectives.md and choose MCP architecture work or repo-specialist guidance for Python MCP behavior.
3. Name one gap in loop comparison, loop application, specialist inference, or insight recording.
4. Run `python -m pytest`, `python -m ruff check src tests`, and `python -m vulture`.
5. Record durable notes in `.github/insights/loop-improver-mcp.md`.
6. Review the final diff and working tree, separating unrelated changes before closeout.
7. Commit the verified loop changes with a meaningful message.
8. Push the commit to the current branch when the user has authorized the push and the branch is safe to update.

Stop after one gap and leave additional discoveries as prune or learning candidates. If validation, commit, or push cannot complete safely, leave an explicit handoff with repository status and the exact next Git action.