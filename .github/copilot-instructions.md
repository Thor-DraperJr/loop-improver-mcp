<!-- Last modified: 2026-07-15T00:26:29.191Z -->

# Copilot instructions - loop-improver-mcp

This repo is a Python MCP server that helps older repositories modernize improvement loops from canonical files: README, Copilot instructions, objectives, specialist agents, and insights.

## SDK References

- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP docs: https://modelcontextprotocol.io/docs

## Ground Rules

- Source lives in `src/loop_improver_mcp/`, tests live in `tests/`.
- Use `python` on Windows. On macOS/Linux, the equivalent command is often `python3`.
- Keep the MCP tool surface deterministic. The server inspects structure, infers simple repo profiles, generates managed loop files, and overwrites current insights; it should not ask a model to invent repo strategy.
- Prioritize readable code: names and structure should make behavior clear. Use focused comments for non-obvious behavior, invariants, and rationale; documentation must not substitute for code that explains itself.
- Validate Python changes with `python -m pytest`, `python -m ruff check src tests`, and `python -m vulture`.
- Before adding helpers, search for existing implementations. After changing symbols, inspect their references and remove high-confidence dead code once dynamic or framework usage has been ruled out.
- End completed loops by recording durable insight notes, reviewing the final diff and status, committing only verified loop changes with a meaningful message, and pushing when the user has authorized it. Otherwise leave an explicit Git handoff.
- README hygiene comes first: the README should be a clear human-facing capability page, not the operational home for agent rules.
- Copilot instructions hold durable ground rules and validation, while `.github/objectives.md` holds the shared repository mission, outcomes, and evidence model for active loops and specialist guidance.
- Use the opening exchange of every session to establish a concise title, direction, and agreed endpoint. Once the endpoint is clear, use the applicable coding-agent loops to carry the work through completion.
- Preserve durable user-authored repo guidance. Deterministic cleanup may remove command summaries when equivalent canonical prompts already exist, but every removal must be reported by the MCP response.

<!-- Managed by loop-improver-mcp -->

## Loop Architecture Contract

Last refreshed: 2026-07-15T00:26:29.191Z

Canonical files have separate jobs:

- README.md explains the repo's brand, capability, and human reason to care.
- .github/copilot-instructions.md holds durable agent ground rules, validation, and hygiene rules.
- .github/objectives.md names the shared repository mission, outcomes, and evidence model.
- .github/agents/ contains specialists that contribute their distinct evidence and insight to the shared repository mission.
- .github/insights/ records the current learning for each loop surface and what should improve next.

### Ground Rules

- Start with README and Copilot hygiene before adding new agents.
- Use the opening exchange to establish a concise session title, direction, and agreed endpoint before starting a loop.
- Identify the shared repository mission from the repo's actual files, tests, docs, and recurring work.
- Let this MCP server own loop architecture; deploy repo agents only for recurring domain work.
- Let each specialist serve the shared repository mission through its existing lens rather than assigning it a separate objective.
- Consolidate reusable command summaries into canonical prompt files when equivalent prompts already exist.
- Prioritize readable code: names and structure should make behavior clear. Use focused comments for non-obvious behavior, invariants, and rationale; documentation must not substitute for code that explains itself.
- Each agent must end passes by recording insights and applying obvious agent/doc improvements directly.
- Each agent must keep the insights loop current by overwriting its current insight after focused passes.
- Completed loops record durable notes, review the final diff and status, commit verified changes, and push when authorized.
- Blocked loops leave an explicit handoff instead of claiming completion.
- Prefer pruning, moving, or merging stale code and docs over adding parallel surfaces.
- When files are moved or removed, delete empty directories and check for stale references.

### Definition Of Done

- README remains human-facing and concise.
- Copilot instructions remain durable ground rules, not a primary prompt warehouse.
- Objectives define one shared mission, evidence model, and verification methods; active loops contribute specialized evidence and insight to it.
- Agent passes produce insights that improve future passes.
- Completed loop changes are committed and pushed, or an explicit Git handoff records why they are not.
