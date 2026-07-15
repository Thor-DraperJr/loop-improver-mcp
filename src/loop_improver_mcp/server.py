# Last modified: 2026-07-14T00:00:00.000Z

"""Expose loop analysis, installation, and insight recording as MCP tools.

This module is the transport layer. Each tool delegates repository work to
``loop_core`` so the MCP entry points stay small and easy to audit.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from . import __version__
from .loop_core import (
    analyze_github_loop,
    apply_github_loop,
    write_current_insight,
)

mcp = FastMCP("loop-improver", json_response=True)


@mcp.tool()
def compare_loops(repo_paths: list[str]) -> dict:
    """Compare repositories against README/Copilot/objectives/agents/insights loop architecture."""
    return {
        "serverInfo": _server_info(),
        "repositories": [analyze_github_loop(repo_path) for repo_path in repo_paths],
    }


@mcp.tool()
def improve_loop(repo_path: str, overwrite_managed_files: bool = True) -> dict:
    """Install or refresh the foundational loop architecture in a target repository."""
    result = apply_github_loop(repo_path, overwrite_managed_files=overwrite_managed_files)
    return {"serverInfo": _server_info(), **result}


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
    result = write_current_insight(
        repo_path=repo_path,
        title=title,
        improved=improved,
        prune_candidates=prune_candidates,
        reusable_learnings=reusable_learnings,
        agent_self_improvement=agent_self_improvement,
    )
    return {"serverInfo": _server_info(), **result}


def _server_info() -> dict[str, str]:
    """Identify the package version and source file loaded by this MCP process."""

    return {"version": __version__, "sourcePath": str(Path(__file__).resolve())}


def main() -> None:
    """Start the MCP server over standard input and output for editor clients."""

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()