<!-- Last modified: 2026-07-14T00:00:00.000Z -->
<!-- Managed by loop-improver-mcp -->

# repo-specialist-agent insight

## 2026-07-14T00:00:00.000Z - Enforce readable code in specialist loops
**Mission:** repo specialist
**Improved:** Added concise orientation docstrings across production source, an AST readability audit for every module and symbol, and a generated-agent code audit that searches usages and runs dead-code tooling; verified with tests, Ruff, and Vulture.
**Prune candidates:** duplicate helpers and high-confidence unused symbols found during future reference audits.
**Reusable learnings:** File and symbol descriptions make code easier to enter, while usage searches plus dead-code tooling make long-session bloat easier to detect and remove safely.
**Agent self-improvement:** Require agents to search before adding helpers, audit changed and nearby symbol references, and verify automated dead-code findings before deletion.
