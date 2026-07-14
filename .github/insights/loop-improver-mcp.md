<!-- Last modified: 2026-07-14T21:07:07.709Z -->
<!-- Managed by loop-improver-mcp -->

# loop-improver-mcp insight

## 2026-07-14T21:07:07.709Z - Harden generated session contracts and legacy repository analysis
**Mission:** loop architecture improvement
**Improved:** Generated Copilot contracts and repo-specialist agents now require a concise session title, direction, and agreed endpoint before starting a loop. Repository analysis now tolerates unreadable non-UTF-8 canonical files by returning normal hygiene findings instead of failing the MCP call; verified with focused regression tests and the full pytest suite.
**Prune candidates:** none
**Reusable learnings:** Durable instructions must be propagated through generated templates, and repository inspection should treat unreadable legacy text as a finding rather than a tool failure.
**Agent self-improvement:** Trace policy changes through emitted templates and exercise analysis against malformed legacy repository inputs.

