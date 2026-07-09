# Last modified: 2026-07-09T11:56:00.989Z

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .loop_core import analyze_github_loop, apply_github_loop, write_current_insight


mcp = FastMCP("loop-improver", json_response=True)


@mcp.tool()
def compare_loops(repo_paths: list[str]) -> dict:
    """Compare repositories against README/Copilot/objectives/agents/insights loop architecture."""
    return {"repositories": [analyze_github_loop(repo_path) for repo_path in repo_paths]}


@mcp.tool()
def improve_loop(repo_path: str, overwrite_managed_files: bool = True) -> dict:
    """Install or refresh the foundational loop architecture in a target repository."""
    return apply_github_loop(repo_path, overwrite_managed_files=overwrite_managed_files)


@mcp.tool()
def record_loop_insight(
    repo_path: str,
    title: str,
    improved: str,
    prune_candidates: str | None = None,
    reusable_learnings: str | None = None,
    agent_self_improvement: str | None = None,
) -> dict:
    """Write the current architecture insight to .github/insights/loop-improver-mcp.md."""
    return write_current_insight(
        repo_path=repo_path,
        title=title,
        improved=improved,
        prune_candidates=prune_candidates,
        reusable_learnings=reusable_learnings,
        agent_self_improvement=agent_self_improvement,
    )


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()