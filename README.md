<!-- Last modified: 2026-07-09T11:56:00.989Z -->

# loop-improver-mcp

MCP server for modernizing agent guidance across repositories.

`loop-improver-mcp` inspects an older repo, identifies stale or missing collaboration surfaces, and installs a small managed foundation for better Copilot work: durable instructions, objectives, specialist guidance, and current insight files.

It handles repos that already have mature `.github` files and repos that have no `.github` folder at all. The MCP call owns the architecture pass; generated agents are only for recurring domain work that needs a dedicated instruction surface.

## Tools

- `compare_loops` inspects README, `.github/copilot-instructions.md`, `.github/objectives.md`, specialist agents, insights, and inferred repo profile.
- `improve_loop` creates missing `.github` structure, installs or refreshes objectives, a repo-specialist agent, and current insight files, and preserves user-authored instructions outside managed blocks.
- `record_loop_insight` overwrites the current architecture learning in `.github/insights/loop-improver-mcp.md`.

## Outcome Rubric

The server evaluates canonical files against a desired shape:

- `README.md`: names the repo, audience, capabilities, and durable entry points without becoming an operational runbook.
- `.github/copilot-instructions.md`: holds durable rules, validation expectations, safety boundaries, and canonical file ownership.
- `.github/objectives.md`: names repo-specific outcomes, maps active loops to those outcomes, and defines evidence for improvement.
- Last modified hygiene: surfaces text files missing a `Last modified` timestamp and files whose timestamp is older than 30 days by default, then suggests objective and folder focus for the next session.
- `.github/agents/`: contains specialist guidance only for recurring domain work.
- `.github/insights/`: records one current insight per MCP or specialist surface with verified improvements, prune candidates, reusable learnings, and self-improvement notes.

## Usage Shape

Call `compare_loops` against older repos, then call `improve_loop` on repos missing the foundation or carrying stale guidance. Managed files are marked with `<!-- Managed by loop-improver-mcp -->` so later refreshes can update the loop without overwriting unrelated repo guidance.

The generated specialist guidance adapts to the repo profile, such as Python MCP hygiene, Rust hygiene, TypeScript product hygiene, blog voice/editing, docs clarity, infrastructure validation, or Security SE demo validation. The architecture loop remains in the MCP server.

## Use With GitHub Copilot

Paste this into GitHub Copilot Chat after opening the repository:

```text
Install and configure this repository's loop-improver MCP server for my VS Code GitHub Copilot environment. Follow .github/mcp-install.md, verify that the server starts, and keep the configuration portable for future updates.
```