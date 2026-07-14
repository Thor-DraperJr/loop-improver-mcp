# Last modified: 2026-07-14T00:00:00.000Z

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loop_improver_mcp.loop_core import (
    analyze_github_loop,
    apply_github_loop,
    write_current_insight,
)


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


def test_analyze_tolerates_non_utf8_canonical_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_bytes(b"\xff\xfe\x00")

    summary = analyze_github_loop(str(tmp_path))

    assert "README.md" in summary["missing"]
    assert "no-readme" in summary["signals"]


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


def test_analyze_infers_portable_python_specialist(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Python MCP\n\nA small MCP capability for testing.\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "python-mcp"\nversion = "0.1.0"\n', encoding="utf-8")

    summary = analyze_github_loop(str(tmp_path))

    assert summary["primaryKind"] == "python"
    assert summary["suggestedSpecialist"] == "Python code quality specialist"
    assert "profile-python" in summary["signals"]
    assert any("detected python profile" in expectation for expectation in summary["outcomeExpectations"][".github/agents/repo-specialist-agent.agent.md"])


def test_analyze_uses_portable_infrastructure_signals(tmp_path: Path) -> None:
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

    assert summary["primaryKind"] == "bicep"
    assert summary["suggestedSpecialist"] == "Infrastructure validation specialist"
    assert "profile-bicep" in summary["signals"]


def test_analyze_uses_portable_language_signals_for_product_repos(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    src = tmp_path / "src" / "channel-core"
    docs.mkdir()
    src.mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "# Family Teams Live Agent\n\nA local shim for teams.live.com consumer chats.\n",
        encoding="utf-8",
    )
    (docs / "api-research.md").write_text(
        "# Teams Consumer API Research\n\nUse teams.live.com/api/chatsvc/consumer and msgapi.teams.live.com behind a local browser session.\n",
        encoding="utf-8",
    )
    (src / "types.ts").write_text("export type Message = { id: string };\n", encoding="utf-8")

    summary = analyze_github_loop(str(tmp_path))

    assert summary["primaryKind"] == "typescript"
    assert summary["suggestedSpecialist"] == "TypeScript product hygiene specialist"
    assert "profile-typescript" in summary["signals"]


def test_analyze_keeps_product_context_in_objectives_without_hardcoded_profiles(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (tmp_path / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")
    (github / "objectives.md").write_text(
        "# Repository Objectives\n\n"
        "## Working Profile\n\n"
        "- Detected profile: Teams Live local-agent shim\n"
        "- Suggested specialist: Teams Live shim agent\n",
        encoding="utf-8",
    )

    summary = analyze_github_loop(str(tmp_path))

    assert summary["primaryKind"] == "typescript"
    assert summary["suggestedSpecialist"] == "TypeScript product hygiene specialist"
    assert "profile-from-objectives" not in summary["signals"]


def test_apply_preserves_existing_instructions_and_adds_managed_files(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "copilot-instructions.md").write_text("# Existing rules\n\nKeep this repo small.\n", encoding="utf-8")

    result = apply_github_loop(str(tmp_path), overwrite_managed_files=True)
    instructions = (github / "copilot-instructions.md").read_text(encoding="utf-8")

    assert instructions.startswith("# Existing rules")
    assert "Loop Architecture Contract" in instructions
    assert ".github/agents/repo-specialist-agent.agent.md" in result["changed"]


def test_apply_only_replaces_managed_marker_on_its_own_line(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    inline_rule = "Only replace blocks marked `<!-- Managed by loop-improver-mcp -->`."
    (github / "copilot-instructions.md").write_text(
        f"# Existing rules\n\n{inline_rule}\n\n"
        "<!-- Managed by loop-improver-mcp -->\n\n"
        "## Old managed content\n",
        encoding="utf-8",
    )

    apply_github_loop(str(tmp_path), overwrite_managed_files=True)
    instructions = (github / "copilot-instructions.md").read_text(encoding="utf-8")

    assert inline_rule in instructions
    assert "Old managed content" not in instructions
    assert instructions.count("<!-- Managed by loop-improver-mcp -->") == 2


def test_analyze_reports_duplicate_loop_contracts(tmp_path: Path) -> None:
    github = tmp_path / ".github"
    github.mkdir()
    (github / "copilot-instructions.md").write_text(
        "# Rules\n\n## Loop Architecture Contract\n\nOld\n\n"
        "<!-- Managed by loop-improver-mcp -->\n\n"
        "## Loop Architecture Contract\n\nCurrent\n",
        encoding="utf-8",
    )

    summary = analyze_github_loop(str(tmp_path))

    assert "duplicate-loop-contract" in summary["copilotSignals"]
    assert "Copilot hygiene: should contain exactly one Loop Architecture Contract" in summary["missing"]


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


def test_apply_creates_objectives_for_typescript_repo(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name":"social-promoter-mcp","type":"module"}\n', encoding="utf-8")

    result = apply_github_loop(str(tmp_path), overwrite_managed_files=True)

    assert ".github/objectives.md" in result["changed"]
    assert (tmp_path / ".github" / "objectives.md").exists()
    assert result["after"]["primaryKind"] == "typescript"


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
    assert "Suggested specialist: Python code quality specialist" in objectives
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
    assert "establish a concise session title, direction, and agreed endpoint" in instructions
    assert "Completed loops record durable notes" in instructions
    assert "commit verified changes, and push when authorized" in instructions
    assert "Blocked loops leave an explicit handoff" in instructions

    specialist = (tmp_path / ".github" / "agents" / "repo-specialist-agent.agent.md").read_text(encoding="utf-8")
    assert "Use the opening exchange to establish a concise session title, direction, and agreed endpoint." in specialist
    assert "Prefer intention-revealing names, small single-purpose units, and direct control flow." in specialist
    assert "Comment only when rationale, invariants, constraints, or non-obvious tradeoffs" in specialist
    assert "Remove comments that narrate the code, repeat names, or no longer match behavior." in specialist
    assert "Treat a need for explanatory prose as a signal to simplify the code first." in specialist
    assert "Review source comments in every changed code file" in specialist
    assert "Add or update focused comments where the code cannot preserve purpose" in specialist
    assert "Derive domain-specific loops from this repository's objectives" in specialist
    assert "Give each source file a brief header description" in specialist
    assert "Give functions and classes concise docstrings" in specialist
    assert "Write for a reader who is still learning the language or repository" in specialist
    assert "Search for existing code before adding a new helper" in specialist
    assert "Check references to changed and nearby symbols" in specialist
    assert "Run the repository's dead-code tooling" in specialist
    assert "Remove unused functions, classes, imports, tests, and comments" in specialist
    assert "Write durable notes before closing the loop" in specialist
    assert "Review the final diff and working tree" in specialist
    assert "Commit only the loop's intended changes with a meaningful message" in specialist
    assert "Push the commit when the user has authorized it" in specialist
    assert "leave an explicit handoff" in specialist


def test_repository_loop_prompt_requires_verified_git_closeout() -> None:
    prompt = Path(".github/prompts/improvement-loop.prompt.md").read_text(encoding="utf-8")

    assert "Record durable notes" in prompt
    assert "Review the final diff and working tree" in prompt
    assert "Commit the verified loop changes with a meaningful message" in prompt
    assert "Push the commit to the current branch" in prompt


def test_generated_guidance_contains_no_product_specific_profiles(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"type":"module"}\n', encoding="utf-8")

    apply_github_loop(str(tmp_path), overwrite_managed_files=True)

    generated = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (tmp_path / ".github").rglob("*")
        if path.is_file()
    )
    assert "Scout" not in generated
    assert "Teams Live" not in generated
    assert "Security demo" not in generated


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