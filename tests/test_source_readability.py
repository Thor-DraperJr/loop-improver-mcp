# Last modified: 2026-07-14T00:00:00.000Z

"""Verify that production Python files remain approachable and easy to audit."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path(__file__).parents[1] / "src" / "loop_improver_mcp"
DOCUMENTED_SYMBOLS = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def test_production_source_has_orientation_and_symbol_docstrings() -> None:
    """Require a dated file overview and a purpose statement for every code symbol."""

    missing: list[str] = []
    for path in sorted(SOURCE_ROOT.glob("*.py")):
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content)
        relative_path = path.relative_to(SOURCE_ROOT.parent.parent).as_posix()

        if not content.startswith("# Last modified:"):
            missing.append(f"{relative_path}: Last modified header")
        if not ast.get_docstring(tree):
            missing.append(f"{relative_path}: module description")

        for node in ast.walk(tree):
            if isinstance(node, DOCUMENTED_SYMBOLS) and not ast.get_docstring(node):
                missing.append(f"{relative_path}:{node.lineno}: {node.name} docstring")

    assert not missing, "Missing source orientation:\n" + "\n".join(missing)