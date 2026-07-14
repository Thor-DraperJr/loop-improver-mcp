<!-- Last modified: 2026-07-09T11:56:00.989Z -->

# Copilot instructions - loop-improver-mcp

This repo is a Python MCP server that helps older repositories modernize improvement loops from canonical files: README, Copilot instructions, objectives, specialist agents, and insights.

## SDK References

- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP docs: https://modelcontextprotocol.io/docs

## Ground Rules

- Source lives in `src/loop_improver_mcp/`, tests live in `tests/`.
- Use `python` on Windows. On macOS/Linux, the equivalent command is often `python3`.
- Keep the MCP tool surface deterministic. The server inspects structure, infers simple repo profiles, generates managed loop files, and overwrites current insights; it should not ask a model to invent repo strategy.
- README hygiene comes first: the README should be a clear human-facing capability page, not the operational home for agent rules.
- Copilot instructions hold durable ground rules and validation, while `.github/objectives.md` holds aspirational objectives mapped to active loops and specialist guidance.
- Use the opening exchange of every session to establish a concise title, direction, and agreed endpoint. Once the endpoint is clear, use the applicable coding-agent loops to carry the work through completion.
- Preserve user-authored repo guidance. Only replace blocks marked `<!-- Managed by loop-improver-mcp -->`.

## Loop Architecture Contract

Last refreshed: 2026-07-09T11:55:41.048Z

Canonical files have separate jobs:

- README.md explains the repo's brand, capability, and human reason to care.
- .github/copilot-instructions.md holds durable agent ground rules, validation, and hygiene rules.
- .github/objectives.md names the repo's aspirational objectives and maps them to loops.
- .github/agents/ contains repo-specialist agents only when they help recurring work.
- .github/insights/ records the current learning for each loop surface and what should improve next.

### Ground Rules

- Start with README and Copilot hygiene before adding new agents.
- Identify objectives from the repo's actual files, tests, docs, and recurring work.
- Let this MCP server own loop architecture; deploy repo agents only for recurring domain work.
- Each agent must keep the insights loop current by overwriting its current insight after focused passes.
- Each agent must end passes by recording insights and applying obvious agent/doc improvements directly.
- Prefer pruning, moving, or merging stale code and docs over adding parallel surfaces.
- When files are moved or removed, delete empty directories and check for stale references.

### Definition Of Done

- README remains human-facing and concise.
- Copilot instructions remain durable ground rules, not a primary prompt warehouse.
- Objectives map to active loops and verification methods.
- Agent passes produce insights that improve future passes.