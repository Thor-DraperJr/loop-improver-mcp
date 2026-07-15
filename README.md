<!-- Last modified: 2026-07-14T00:00:00.000Z -->

# loop-improver-mcp

MCP server for modernizing agent guidance across repositories.

`loop-improver-mcp` inspects an older repo, identifies stale or missing collaboration surfaces, and installs a small managed foundation for better Copilot work: durable instructions, one repository-wide mission and evidence model, specialist guidance, and current insight files.

It handles repos that already have mature `.github` files and repos that have no `.github` folder at all. The MCP call owns the architecture pass; generated agents are only for recurring domain work that needs a dedicated instruction surface.

## Tools

- `compare_loops` inspects README, `.github/copilot-instructions.md`, `.github/objectives.md`, specialist agents, insights, and inferred repo profile.
- `improve_loop` creates missing `.github` structure, installs or refreshes objectives, specialist guidance, and current insight files. `objectives.md` defines the shared repository mission; each specialist contributes its own evidence and current insight without receiving a separate objective. It preserves agent missions while adding a managed improvement loop and matching current insight ledger to each user-owned specialist. It also preserves durable user-authored instructions while consolidating reported command summaries when equivalent canonical prompts already exist.
- `record_loop_insight` overwrites the current architecture learning in `.github/insights/loop-improver-mcp.md`.

Every tool response includes `serverInfo.version` and `serverInfo.sourcePath` so clients can identify stale installations or confirm that a workspace checkout is loaded.

## Outcome Rubric

The server evaluates canonical files against a desired shape:

- `README.md`: names the repo, audience, capabilities, and durable entry points without becoming an operational runbook.
- `.github/copilot-instructions.md`: holds durable rules, validation expectations, safety boundaries, and canonical file ownership.
- `.github/objectives.md`: names repo-specific outcomes, maps active loops to those outcomes, and defines evidence for improvement.
- Last modified hygiene: surfaces text files missing a `Last modified` timestamp and files whose timestamp is older than 30 days by default, then suggests objective and folder focus for the next session.
- `.github/agents/`: contains specialist guidance only for recurring domain work.
- `.github/insights/`: records one current insight per MCP or specialist surface with verified improvements, prune candidates, reusable learnings, and self-improvement notes.

Generated specialists also audit changed and nearby symbols for duplicate helpers and unused code. In this repository, Ruff enforces source orientation and code-quality rules, the readability test checks every production module and symbol for concise descriptions, and Vulture reports high-confidence dead-code candidates for reference verification.

## Usage Shape

Call `compare_loops` against older repos, then call `improve_loop` on repos missing the foundation or carrying stale guidance. Managed files are marked with `<!-- Managed by loop-improver-mcp -->` so later refreshes can update the loop without overwriting unrelated repo guidance.

The generated specialist guidance adapts to portable repository signals such as Python, Rust, TypeScript, content, documentation, or infrastructure files. Domain-specific context comes from the target repository's objectives and existing guidance, so the server can create useful loops without carrying assumptions from another project or machine.

## Use With GitHub Copilot

Paste this into GitHub Copilot Chat after opening the repository:

```text
Install and configure this repository's loop-improver MCP server for my VS Code GitHub Copilot environment. Follow .github/mcp-install.md, verify that the server starts, and keep the configuration portable for future updates.
```