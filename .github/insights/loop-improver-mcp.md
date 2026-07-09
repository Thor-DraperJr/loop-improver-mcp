<!-- Last modified: 2026-07-09T21:11:50.072Z -->
<!-- Managed by loop-improver-mcp -->

# loop-improver-mcp insight

## 2026-07-09T21:11:50.072Z - Prefer objectives and Teams Live intent over TypeScript fallback
**Mission:** loop architecture improvement
**Improved:** Profile inference now honors Teams Live objectives/content before language fallback, preventing fresh Teams Live shim repos from being routed to TypeScript product hygiene; verified with python -m pytest tests/test_loop_core.py and live compare_loops after global uv reinstall.
**Prune candidates:** cached uv tool installs can preserve old local-package wheels when version stays unchanged; use --reinstall --no-cache for global republish after source edits.
**Reusable learnings:** Repo objectives can carry authoritative Working Profile intent, so analyzer profile inference should consult them before implementation-language signals.
**Agent self-improvement:** Global publish validation should inspect the installed uv tool environment and then call the MCP tool surface, not rely on uv install success alone.

