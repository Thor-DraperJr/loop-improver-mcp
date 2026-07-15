# Last modified: 2026-07-14T00:00:00.000Z

from pathlib import Path

from loop_improver_mcp.server import compare_loops


def test_compare_reports_loaded_server_provenance(tmp_path: Path) -> None:
    result = compare_loops([str(tmp_path)])

    assert result["serverInfo"]["version"] == "0.2.5"
    assert Path(result["serverInfo"]["sourcePath"]).name == "server.py"