# Last modified: 2026-07-14T00:00:00.000Z

import subprocess
import sys
from pathlib import Path

from loop_improver_mcp.server import compare_loops


def test_compare_reports_loaded_server_provenance(tmp_path: Path) -> None:
    result = compare_loops([str(tmp_path)])

    assert result["serverInfo"]["version"] == "0.2.5"
    assert Path(result["serverInfo"]["sourcePath"]).name == "server.py"


def test_module_help_exits_without_starting_stdio_server() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "loop_improver_mcp.server", "--help"],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert "Start the loop-improver MCP server" in result.stdout