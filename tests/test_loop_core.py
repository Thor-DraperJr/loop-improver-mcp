# Last modified: 2026-07-09T11:56:00.989Z

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loop_improver_mcp.loop_core import analyze_github_loop, apply_github_loop, write_current_insight


def test_analyze_reports_missing_loop_pieces(tmp_path: Path) -> None:
    summary = analyze_github_loop(str(tmp_path))

    assert summary["githubExists"] is False
    assert "README.md" in summary["missing"]
    assert ".github/copilot-instructions.md" in summary["missing"]
    assert ".github/objectives.md" in summary["missing"]
    assert "no-insights" in summary["signals"]
    assert summary["primaryKind"] == "generic"
    assert "README.md" in summary["outcomeExpectations"]
    assert ".github/copilot-instructions.md" in summary["outcomeExpectations"]


def test_analyze_surfaces_missing_and_stale_last_modified_files(tmp_path: Path) -> None:
    (tmp_path / "fresh.md").write_text("<!-- Last modified: 2026-07-01T00:00:00.000Z -->\n# Fresh\n", encoding="utf-8")
    (tmp_path / "stale.md").write_text("<!-- Last modified: 2026-05-01T00:00:00.000Z -->\n# Stale\n", encoding="utf-8")
    (tmp_path / "missing.md").write_text("# Missing\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "missing-a.md").write_text("# Missing A\n", encoding="utf-8")
    (docs / "missing-b.md").write_text("# Missing B\n", encoding="utf-8")
    (tmp_path / "data.json").write_text("{}\n", encoding="utf-8")

    summary = analyze_github_loop(str(tmp_path), now=datetime(2026, 7, 9, tzinfo=timezone.utc))

    assert "missing.md" in summary["attention"]["missingLastModified"]
    assert "docs/missing-a.md" in summary["attention"]["missingLastModified"]
    assert "data.json" not in summary["attention"]["missingLastModified"]
    assert {item["path"] for item in summary["attention"]["staleLastModified"]} == {"stale.md"}
    assert summary["attention"]["staleAfterDays"] == 30
    assert summary["attention"]["sessionGuidance"]["focusFolders"][0] == {"folder": "docs", "attentionCount": 2}
    assert "choose one objective" in summary["attention"]["sessionGuidance"]["instruction"]
    assert summary["attention"]["sessionGuidance"]["objectiveCandidates"]


def test_analyze_respects_last_modified_stale_threshold(tmp_path: Path) -> None:
    (tmp_path / "recent.md").write_text("<!-- Last modified: 2026-06-20 -->\n# Recent\n", encoding="utf-8")

    strict = analyze_github_loop(str(tmp_path), stale_after_days=10, now=datetime(2026, 7, 9, tzinfo=timezone.utc))
    relaxed = analyze_github_loop(str(tmp_path), stale_after_days=30, now=datetime(2026, 7, 9, tzinfo=timezone.utc))

    assert {item["path"] for item in strict["attention"]["staleLastModified"]} == {"recent.md"}
    assert relaxed["attention"]["staleLastModified"] == []


def test_analyze_infers_rust_specialist(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Rust Tool\n\nA small capability for testing.\n", encoding="utf-8")
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "rust-tool"\nversion = "0.1.0"\n', encoding="utf-8")

    summary = analyze_github_loop(str(tmp_path))

    assert summary["primaryKind"] == "rust"
    assert summary["suggestedSpecialist"] == "Rust hygiene specialist"
    assert "has-brand-heading" in summary["readmeSignals"]


def test_analyze_infers_python_mcp_specialist(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Python MCP\n\nA small MCP capability for testing.\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "python-mcp"\nversion = "0.1.0"\n', encoding="utf-8")

    summary = analyze_github_loop(str(tmp_path))

    assert summary["primaryKind"] == "python"
    assert summary["suggestedSpecialist"] == "Python MCP hygiene specialist"
    assert "profile-python" in summary["signals"]
    assert any("detected python profile" in expectation for expectation in summary["outcomeExpectations"][".github/agents/repo-specialist-agent.agent.md"])


def test_analyze_infers_security_demo_specialist(tmp_path: Path) -> None:
    scout = tmp_path / "scout"
    infra = tmp_path / "infra"
    scout.mkdir()
    infra.mkdir()
    (tmp_path / "README.md").write_text("# Security Demo\n\nA Microsoft Security demo lab for customer use.\n", encoding="utf-8")
    loops = scout / "loops"
    loops.mkdir()
    (loops / "security-se-loop.json").write_text("{}\n", encoding="utf-8")
    (infra / "main.bicep").write_text("param location string\n", encoding="utf-8")

    summary = analyze_github_loop(str(tmp_path))

    assert summary["primaryKind"] == "security-demo"
    assert summary["suggestedSpecialist"] == "Security demo infrastructure specialist"
    assert "profile-security-demo" in summary["signals"]


def test_apply_preserves_existing_instructions_and_adds_managed_files(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "copilot-instructions.md").write_text("# Existing rules\n\nKeep this repo small.\n", encoding="utf-8")

    result = apply_github_loop(str(tmp_path), overwrite_managed_files=True)
    instructions = (github / "copilot-instructions.md").read_text(encoding="utf-8")

    assert instructions.startswith("# Existing rules")
    assert "Loop Architecture Contract" in instructions
    assert ".github/agents/repo-specialist-agent.agent.md" in result["changed"]


def test_apply_does_not_overwrite_unmarked_existing_prompt(tmp_path: Path) -> None:
    prompts = tmp_path / ".github" / "prompts"
    prompts.mkdir(parents=True)
    prompt = prompts / "improvement-loop.prompt.md"
    prompt.write_text("# Existing local prompt\n", encoding="utf-8")

    result = apply_github_loop(str(tmp_path), overwrite_managed_files=True)

    assert prompt.read_text(encoding="utf-8") == "# Existing local prompt\n"
    assert ".github/prompts/improvement-loop.prompt.md" not in result["changed"]


def test_apply_creates_loop_architecture_foundation(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "rust-tool"\nversion = "0.1.0"\n', encoding="utf-8")

    result = apply_github_loop(str(tmp_path), overwrite_managed_files=True)

    assert ".github/copilot-instructions.md" in result["changed"]
    assert ".github/objectives.md" in result["changed"]
    assert "repo-specialist-agent" in result["after"]["signals"]
    assert result["after"]["primaryKind"] == "rust"
    assert "agents/repo-specialist-agent.agent.md" in result["after"]["files"]
    assert "agents/loop-architect-agent.agent.md" not in result["after"]["files"]


def test_apply_creates_missing_github_structure(tmp_path: Path) -> None:
    result = apply_github_loop(str(tmp_path), overwrite_managed_files=True)

    assert result["before"]["githubExists"] is False
    assert result["after"]["githubExists"] is True
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()
    assert (tmp_path / ".github" / "objectives.md").exists()
    assert (tmp_path / ".github" / "agents" / "repo-specialist-agent.agent.md").exists()
    assert (tmp_path / ".github" / "insights" / "loop-improver-mcp.md").exists()
    assert "README.md" in result["after"]["missing"]


def test_apply_refreshes_managed_objective_rubric_and_preserves_repo_sections(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "python-mcp"\nversion = "0.1.0"\n', encoding="utf-8")
    (github / "objectives.md").write_text(
        "<!-- Last modified: old -->\n"
        "<!-- Managed by loop-improver-mcp -->\n\n"
        "# Custom Objectives\n\n"
        "## Working Profile\n\n"
        "- Detected profile: bicep\n"
        "- Suggested specialist: Infrastructure validation specialist\n\n"
        "## Aspirational Objectives\n\n"
        "1. Preserve this repo-specific outcome.\n\n"
        "## Agent Map\n\n"
        "- custom-agent: preserve this mapping.\n\n"
        "## Verification\n\n"
        "Old verification.\n",
        encoding="utf-8",
    )

    apply_github_loop(str(tmp_path), overwrite_managed_files=True)
    objectives = (github / "objectives.md").read_text(encoding="utf-8")

    assert "# Custom Objectives" in objectives
    assert "Detected profile: python" in objectives
    assert "Suggested specialist: Python MCP hygiene specialist" in objectives
    assert "1. Preserve this repo-specific outcome." in objectives
    assert "- custom-agent: preserve this mapping." in objectives
    assert "## Outcome Expectations" in objectives
    assert "Old verification" not in objectives


def test_generated_guidance_uses_modern_contract(tmp_path: Path) -> None:
    apply_github_loop(str(tmp_path), overwrite_managed_files=True)

    instructions = (tmp_path / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
    objectives = (tmp_path / ".github" / "objectives.md").read_text(encoding="utf-8")

    assert "Let this MCP server own loop architecture" in instructions
    assert "Create one foundational loop architect" not in instructions
    assert "Create missing `.github` collaboration surfaces" in objectives
    assert "what quality means here, and which loops keep it improving" in objectives
    assert "## Outcome Expectations" in objectives
    assert "operational runbooks or agent rules" in objectives
    assert "verified improvements" in objectives
    assert "Last modified hygiene" in objectives


def test_outcome_expectations_follow_detected_profile(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "rust-tool"\nversion = "0.1.0"\n', encoding="utf-8")

    summary = analyze_github_loop(str(tmp_path))

    specialist_expectations = summary["outcomeExpectations"][".github/agents/repo-specialist-agent.agent.md"]
    assert any("detected rust profile" in expectation for expectation in specialist_expectations)
    assert any("Prune dead Rust code" in expectation for expectation in specialist_expectations)


def test_write_current_insight_overwrites_current_entry(tmp_path: Path) -> None:
    apply_github_loop(str(tmp_path), overwrite_managed_files=True)
    write_current_insight(str(tmp_path), title="first", improved="verified with test")
    write_current_insight(str(tmp_path), title="second", improved="verified with build")

    insight = (tmp_path / ".github" / "insights" / "loop-improver-mcp.md").read_text(encoding="utf-8")

    assert " - second" in insight
    assert " - first" not in insight
    assert insight.count("## ") == 1