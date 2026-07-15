# Last modified: 2026-07-14T00:00:00.000Z

"""Inspect repositories and create the managed files used by their improvement loops.

The public functions analyze a repository, install its loop foundation, and record
the latest learning. Private helpers handle file discovery, hygiene checks, profile
selection, safe updates to managed content, and rendering the generated Markdown.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal, TypedDict

RepoKind = Literal[
    "rust",
    "python",
    "typescript",
    "blog",
    "docs",
    "bicep",
    "generic",
]

MANAGED_MARKER = "<!-- Managed by loop-improver-mcp -->"
AGENT_LOOP_MARKER = "<!-- Managed by loop-improver-mcp: agent loop -->"


@dataclass(frozen=True)
class RepoProfile:
    """Describe the broad technology profile used to seed specialist guidance."""

    primary_kind: RepoKind
    signals: list[str]
    suggested_specialist: str
    specialist_mission: str


@dataclass(frozen=True)
class Hygiene:
    """Collect machine-readable signals and human-readable findings for one file."""

    signals: list[str]
    findings: list[str]


class StaleTimestamp(TypedDict):
    """Identify a file whose declared modification date is older than the cutoff."""

    path: str
    lastModified: str


class TimestampHygiene(TypedDict):
    """Group files with missing or stale modification timestamps."""

    missingLastModified: list[str]
    staleLastModified: list[StaleTimestamp]


def analyze_github_loop(repo_path: str, stale_after_days: int = 30, now: datetime | None = None) -> dict[str, Any]:
    """Inspect one repository and return its loop files, findings, and suggested profile."""

    repo = Path(repo_path)
    github = repo / ".github"
    github_files = _list_relative_files(github) if github.exists() else []
    repo_files = _list_repo_files(repo)
    profile = _infer_repo_profile(repo_files)

    readme = _read_optional(repo / "README.md")
    copilot = _read_optional(github / "copilot-instructions.md")
    objectives = _read_optional(github / "objectives.md")

    readme_hygiene = _analyze_readme(readme)
    copilot_hygiene = _analyze_copilot_instructions(copilot)
    objectives_hygiene = _analyze_objectives(objectives)
    timestamp_hygiene = _analyze_file_timestamps(repo, repo_files, stale_after_days, now or datetime.now(timezone.utc))

    has_specialist = "agents/repo-specialist-agent.agent.md" in github_files
    existing_agent_names = _list_existing_agent_names(github)
    loop_enabled_agents = _list_loop_enabled_agents(github, existing_agent_names)
    agents_missing_loops = sorted(set(existing_agent_names) - set(loop_enabled_agents))
    existing_specialists = _find_existing_specialists(github, profile)
    specialist_needed = not existing_specialists
    has_specialist_coverage = has_specialist or not specialist_needed
    has_insights = any(file.startswith("insights/") for file in github_files)

    signals = [
        "readme" if readme else "no-readme",
        "copilot-instructions" if copilot else "no-copilot-instructions",
        "objectives" if objectives else "no-objectives",
        "repo-specialist-agent" if has_specialist else "no-repo-specialist-agent",
        "existing-specialist-coverage" if existing_specialists else "no-existing-specialist-coverage",
        "existing-agent-loops" if not agents_missing_loops else "existing-agents-missing-loops",
        "agents" if any(file.startswith("agents/") for file in github_files) else "no-agents",
        "insights" if has_insights else "no-insights",
        "last-modified-ground-rule" if re.search(r"last modified", copilot, re.I) else "no-last-modified-ground-rule",
        "pruning-rule" if re.search(r"prun(e|ing)|dead code", copilot, re.I) else "no-pruning-rule",
        "recursive-learning" if re.search(r"insights loop|reusable learnings|agent self-improvement", copilot, re.I) else "no-recursive-learning",
        *profile.signals,
    ]

    missing = [
        "" if readme else "README.md",
        "" if copilot else ".github/copilot-instructions.md",
        "" if objectives else ".github/objectives.md",
        "" if has_specialist_coverage else ".github/agents/repo-specialist-agent.agent.md",
        "" if has_insights else ".github/insights/README.md",
        *[f"Existing agent missing improvement loop: .github/agents/{name}.agent.md" for name in agents_missing_loops],
        *[f"README hygiene: {finding}" for finding in readme_hygiene.findings],
        *[f"Copilot hygiene: {finding}" for finding in copilot_hygiene.findings],
        *[f"Objectives hygiene: {finding}" for finding in objectives_hygiene.findings],
    ]
    missing = [item for item in missing if item]

    if missing:
        recommendation = "Run improve_loop to install or refresh the modernization foundation, then resolve the remaining hygiene findings."
    elif existing_specialists:
        recommendation = f"Modernization foundation is present; use existing specialist coverage ({', '.join(existing_specialists)}) and record insights after each pass."
    else:
        recommendation = f"Modernization foundation is present; use {profile.suggested_specialist} for domain work and record insights after each pass."

    return {
        "repoPath": str(repo),
        "githubExists": github.exists(),
        "files": github_files,
        "signals": signals,
        "missing": missing,
        "attention": {
            "missingLastModified": timestamp_hygiene["missingLastModified"],
            "staleLastModified": timestamp_hygiene["staleLastModified"],
            "staleAfterDays": stale_after_days,
            "sessionGuidance": _attention_session_guidance(timestamp_hygiene),
        },
        "recommendation": recommendation,
        "outcomeExpectations": _outcome_expectations(profile, specialist_needed),
        "readmeSignals": readme_hygiene.signals,
        "copilotSignals": copilot_hygiene.signals,
        "objectivesSignals": objectives_hygiene.signals,
        "primaryKind": profile.primary_kind,
        "suggestedSpecialist": profile.suggested_specialist,
        "specialistMission": profile.specialist_mission,
        "specialistNeeded": specialist_needed,
        "existingSpecialists": existing_specialists,
        "existingAgents": existing_agent_names,
        "loopEnabledAgents": loop_enabled_agents,
        "validationCommands": _infer_validation_commands(repo, repo_files),
    }


def apply_github_loop(repo_path: str, overwrite_managed_files: bool = True) -> dict[str, Any]:
    """Create or refresh loop files while preserving durable user-owned guidance."""

    repo = Path(repo_path)
    before = analyze_github_loop(str(repo))
    timestamp = _now_iso()
    github = repo / ".github"
    for directory in [github, github / "agents", github / "insights"]:
        directory.mkdir(parents=True, exist_ok=True)

    changed: list[str] = []
    copilot_path = github / "copilot-instructions.md"
    existing_copilot = _read_optional(copilot_path)
    improved_copilot, instruction_improvements = (
        _improve_copilot_instructions(existing_copilot, github) if overwrite_managed_files else (existing_copilot, [])
    )
    next_copilot = _merge_managed_block(improved_copilot, _copilot_managed_block(timestamp))
    if next_copilot != existing_copilot:
        next_copilot = _set_last_modified_header(next_copilot, timestamp)
    next_copilot = _preserve_timestamp_only_change(existing_copilot, next_copilot)
    if next_copilot != existing_copilot:
        copilot_path.write_text(next_copilot, encoding="utf-8")
        changed.append(".github/copilot-instructions.md")

    _write_objectives(github / "objectives.md", _objectives_template(timestamp, before), overwrite_managed_files, changed)
    specialist_path = github / "agents" / "repo-specialist-agent.agent.md"
    specialist_insight_path = github / "insights" / "repo-specialist-agent.md"
    if before["specialistNeeded"]:
        _write_managed(specialist_path, _specialist_agent_template(timestamp, before), overwrite_managed_files, changed)
        _write_managed(specialist_insight_path, _insight_ledger_template(timestamp, "repo-specialist-agent"), False, changed)
    else:
        _remove_managed(specialist_path, changed)
        _remove_managed(specialist_insight_path, changed)
    agent_improvements = _apply_existing_agent_loops(github, timestamp, overwrite_managed_files, changed)
    _write_managed(github / "insights" / "README.md", _insights_readme_template(timestamp), overwrite_managed_files, changed)
    _write_managed(github / "insights" / "loop-improver-mcp.md", _insight_ledger_template(timestamp, "loop-improver-mcp"), False, changed)

    return {
        "before": before,
        "after": analyze_github_loop(str(repo)),
        "changed": changed,
        "instructionImprovements": instruction_improvements,
        "agentImprovements": agent_improvements,
    }


def write_current_insight(
    repo_path: str,
    title: str,
    improved: str,
    prune_candidates: str | None = None,
    reusable_learnings: str | None = None,
    agent_self_improvement: str | None = None,
) -> dict[str, str]:
    """Replace the current architecture insight with one newly verified learning."""

    repo = Path(repo_path)
    timestamp = _now_iso()
    insight = repo / ".github" / "insights" / "loop-improver-mcp.md"
    insight.parent.mkdir(parents=True, exist_ok=True)
    next_content = (
        f"<!-- Last modified: {timestamp} -->\n"
        f"{MANAGED_MARKER}\n\n"
        "# loop-improver-mcp insight\n\n"
        f"## {timestamp} - {title}\n"
        "**Mission:** loop architecture improvement\n"
        f"**Improved:** {improved}\n"
        f"**Prune candidates:** {prune_candidates or 'none'}\n"
        f"**Reusable learnings:** {reusable_learnings or 'none'}\n"
        f"**Agent self-improvement:** {agent_self_improvement or 'none'}\n\n"
    )
    insight.write_text(next_content, encoding="utf-8")
    return {"path": ".github/insights/loop-improver-mcp.md", "timestamp": timestamp}


def _list_relative_files(root: Path) -> list[str]:
    """Return every file below a directory as a sorted, portable relative path."""

    return sorted(_to_posix(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def _list_repo_files(root: Path) -> list[str]:
    """List repository files while skipping generated dependency and cache folders."""

    if not root.exists():
        return []
    ignored = {".git", "node_modules", "dist", "target", ".venv", "__pycache__"}
    files: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in ignored for part in relative.parts):
            continue
        files.append(_to_posix(relative))
    return sorted(files)


def _read_optional(path: Path) -> str:
    """Read a UTF-8 text file, returning an empty string when it cannot be read."""

    return _read_text_optional(path) or ""


def _read_text_optional(path: Path) -> str | None:
    """Read a UTF-8 text file without making missing or binary files fatal."""

    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _analyze_file_timestamps(
    repo: Path,
    files: list[str],
    stale_after_days: int,
    now: datetime,
) -> TimestampHygiene:
    """Find text files with missing or older-than-allowed modification headers."""

    missing: list[str] = []
    stale: list[StaleTimestamp] = []
    cutoff = _ensure_utc(now) - timedelta(days=stale_after_days)
    for file in files:
        if _skip_timestamp_scan(file):
            continue
        content = _read_text_optional(repo / file)
        if content is None:
            continue
        timestamp = _extract_last_modified(content)
        if timestamp is None:
            missing.append(file)
            continue
        if timestamp < cutoff:
            stale.append({"path": file, "lastModified": timestamp.isoformat().replace("+00:00", "Z")})
    return {"missingLastModified": missing, "staleLastModified": stale}


def _attention_session_guidance(timestamp_hygiene: TimestampHygiene) -> dict[str, Any]:
    """Turn timestamp findings into a practical starting point for the next session."""

    missing = timestamp_hygiene["missingLastModified"]
    stale = [item["path"] for item in timestamp_hygiene["staleLastModified"]]
    attention_files = [*missing, *stale]
    if not attention_files:
        return {
            "instruction": "No timestamp attention items surfaced. Choose a concrete focus that advances the shared repository mission in .github/objectives.md.",
            "objectiveCandidates": [],
            "focusFolders": [],
        }
    return {
        "instruction": "Use these attention items to choose one concrete focus that advances the shared repository mission, then work in the highest-signal folder or file cluster.",
        "objectiveCandidates": [
            "Review files missing Last modified timestamps and decide whether they are durable enough to keep, update, move, or prune.",
            "Review stale timestamp files and refresh only the files whose content still serves the shared repository mission.",
        ],
        "focusFolders": _rank_focus_folders(attention_files),
    }


def _rank_focus_folders(files: list[str]) -> list[dict[str, int | str]]:
    """Rank top-level folders by how many files currently need attention."""

    counts: dict[str, int] = {}
    for file in files:
        folder = file.split("/", 1)[0] if "/" in file else "."
        counts[folder] = counts.get(folder, 0) + 1
    return [
        {"folder": folder, "attentionCount": count}
        for folder, count in sorted(counts.items(), key=lambda item: (-item[1], item[0] == ".", item[0]))
    ]


def _skip_timestamp_scan(file: str) -> bool:
    """Limit timestamp attention to durable repository and collaboration guidance."""

    if "/" not in file and file.endswith(".md"):
        return False
    if file.startswith("docs/") and file.endswith(".md"):
        return False
    collaboration_prefixes = (".github/agents/", ".github/instructions/", ".github/prompts/")
    canonical_files = (".github/copilot-instructions.md", ".github/objectives.md")
    return not (file in canonical_files or (file.startswith(collaboration_prefixes) and file.endswith(".md")))


def _extract_last_modified(content: str) -> datetime | None:
    """Parse a date-only or ISO Last modified header into a UTC datetime."""

    # Generated files use ISO timestamps, while older repositories often use date-only headers.
    match = re.search(r"last modified:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}(?:[T ][0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})?)?)", content, re.I)
    if not match:
        return None
    value = match.group(1).strip().replace("Z", "+00:00")
    if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        value = f"{value}T00:00:00+00:00"
    try:
        return _ensure_utc(datetime.fromisoformat(value))
    except ValueError:
        return None


def _ensure_utc(value: datetime) -> datetime:
    """Normalize naive and timezone-aware datetime values to UTC."""

    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _analyze_readme(content: str) -> Hygiene:
    """Evaluate whether a README gives humans a concise capability overview."""

    if not content.strip():
        return Hygiene(["missing"], ["missing human capability overview"])
    explains_capability = bool(
        re.search(r"what|capabilit|purpose|why|use|\bsite\b|\bblog\b|working resume|place to share|actual app", content, re.I)
    )
    signals = [
        "has-brand-heading" if re.search(r"^#\s+\S", content, re.M) else "no-brand-heading",
        "explains-capability" if explains_capability else "thin-capability-story",
        "has-usage-entry" if re.search(r"quickstart|setup|install|usage", content, re.I) else "no-usage-entry",
        "concise" if len(content) <= 5000 else "too-long-for-human-orientation",
        "mentions-ai-surface" if re.search(r"copilot|agent|mcp|prompt", content, re.I) else "human-first",
    ]
    findings = [
        "" if re.search(r"^#\s+\S", content, re.M) else "needs a clear repo brand heading",
        "" if explains_capability else "should explain the repo capability in human terms",
        "" if len(content) <= 5000 else "may be carrying too much operational detail for a human README",
    ]
    return Hygiene(signals, [finding for finding in findings if finding])


def _analyze_copilot_instructions(content: str) -> Hygiene:
    """Evaluate whether Copilot instructions contain durable repository rules."""

    if not content.strip():
        return Hygiene(["missing"], ["missing durable agent ground rules"])
    contract_count = len(re.findall(r"^## Loop Architecture Contract$", content, re.M))
    signals = [
        "has-ground-rules" if re.search(r"ground rules|definition of done|validation", content, re.I) else "thin-ground-rules",
        "names-canonical-files" if re.search(r"README\.md|objectives\.md|canonical", content, re.I) else "no-canonical-file-map",
        "has-learning-loop" if re.search(r"insights|learning|reusable", content, re.I) else "no-learning-loop",
        "has-pruning-rule" if re.search(r"prun(e|ing)|dead code|stale", content, re.I) else "no-pruning-rule",
        "one-loop-contract" if contract_count <= 1 else "duplicate-loop-contract",
        "concise" if len(content) <= 7000 else "possible-prompt-warehouse",
    ]
    findings = [
        "" if re.search(r"ground rules|definition of done|validation", content, re.I) else "needs durable ground rules and validation expectations",
        "" if re.search(r"README\.md|objectives\.md|canonical", content, re.I) else "should name README, objectives, agents, and insights as separate canonical surfaces",
        "" if re.search(r"insights|learning|reusable", content, re.I) else "should require an insight loop after focused passes",
        "" if re.search(r"prun(e|ing)|dead code|stale", content, re.I) else "should include pruning and stale-reference cleanup",
        "" if contract_count <= 1 else "should contain exactly one Loop Architecture Contract",
        "" if len(content) <= 7000 else "may contain primary prompts that belong in prompts, skills, or agents",
    ]
    return Hygiene(signals, [finding for finding in findings if finding])


def _analyze_objectives(content: str) -> Hygiene:
    """Evaluate whether objectives connect desired outcomes to loops and evidence."""

    if not content.strip():
        return Hygiene(["missing"], ["missing aspirational objectives file"])
    signals = [
        "has-aspirations" if re.search(r"aspiration|objective|mission|outcome", content, re.I) else "thin-aspirations",
        "maps-to-agents" if re.search(r"agent|loop|insight", content, re.I) else "no-agent-map",
        "has-verification-language" if re.search(r"measure|verify|evidence|done", content, re.I) else "no-verification-language",
    ]
    findings = [
        "" if re.search(r"aspiration|objective|mission|outcome", content, re.I) else "should name the repo's aspirational objectives",
        "" if re.search(r"agent|loop|insight", content, re.I) else "should map objectives to agent loops and insights",
        "" if re.search(r"measure|verify|evidence|done", content, re.I) else "should describe how improvements are verified",
    ]
    return Hygiene(signals, [finding for finding in findings if finding])


def _infer_repo_profile(files: list[str]) -> RepoProfile:
    """Choose broad specialist guidance from portable files and extensions."""

    file_set = set(files)

    # Portable ecosystem signals choose the starting agent; domain context stays in the target repo's objectives.
    if "Cargo.toml" in file_set or _any_file_ends_with(files, ".rs"):
        return RepoProfile("rust", ["profile-rust"], "Rust hygiene specialist", "Prune dead Rust code, reduce unnecessary verbosity, and keep tests or CLI behavior aligned with the repo objectives.")
    if "pyproject.toml" in file_set or _any_file_ends_with(files, ".py"):
        return RepoProfile("python", ["profile-python"], "Python code quality specialist", "Keep the Python code small, typed, tested, readable, and aligned to the repo objectives.")
    if _any_path_matches(files, r"(^|/)(content|src/content|posts|blog)/") or _any_file_ends_with(files, "astro.config.mjs"):
        return RepoProfile("blog", ["profile-blog"], "Voice and editor specialist", "Improve article quality, voice consistency, publish readiness, and editorial insight loops.")
    if "package.json" in file_set or _any_file_ends_with(files, ".ts") or _any_file_ends_with(files, ".tsx"):
        return RepoProfile("typescript", ["profile-typescript"], "TypeScript product hygiene specialist", "Keep the TypeScript surface small, tested, typed, and aligned to the repo objectives.")
    if _any_file_ends_with(files, ".bicep") or _any_file_ends_with(files, ".bicepparam"):
        return RepoProfile("bicep", ["profile-bicep"], "Infrastructure validation specialist", "Keep deployment templates minimal, validated, and aligned to the repo's environment objectives.")
    markdown_count = sum(1 for file in files if file.endswith(".md"))
    if markdown_count >= max(3, len(files) / 2):
        return RepoProfile("docs", ["profile-docs"], "Documentation clarity specialist", "Keep documentation concise, human-readable, accurate, and free of duplicated operational guidance.")
    return RepoProfile("generic", ["profile-generic"], "Repository specialist", "Identify the repo's recurring work and create small verified improvement loops around it.")


def _find_existing_specialists(github: Path, profile: RepoProfile) -> list[str]:
    """Find user-owned agents whose identity directly covers the detected specialist mission."""

    keywords: dict[RepoKind, tuple[str, ...]] = {
        "blog": ("article", "content", "editor", "narrative", "publish", "voice"),
        "python": ("python",),
        "rust": ("rust",),
        "typescript": ("typescript",),
        "bicep": ("bicep", "infrastructure"),
        "docs": ("documentation", "editor"),
        "generic": (),
    }
    matches: list[str] = []
    for agent_name in _list_existing_agent_names(github):
        identity = agent_name.lower()
        if any(keyword in identity for keyword in keywords[profile.primary_kind]):
            matches.append(agent_name)
    return matches


def _list_existing_agent_names(github: Path) -> list[str]:
    """Return user-owned agent names without the generated generic specialist."""

    agents = github / "agents"
    if not agents.exists():
        return []
    return [
        path.name.removesuffix(".agent.md")
        for path in sorted(agents.glob("*.agent.md"))
        if path.name != "repo-specialist-agent.agent.md"
    ]


def _list_loop_enabled_agents(github: Path, agent_names: list[str]) -> list[str]:
    """Return user-owned agents that already carry the managed improvement-loop suffix."""

    return [
        agent_name
        for agent_name in agent_names
        if AGENT_LOOP_MARKER in _read_optional(github / "agents" / f"{agent_name}.agent.md")
    ]


def _infer_validation_commands(repo: Path, files: list[str]) -> list[str]:
    """Infer executable checks from project manifests without inventing unavailable scripts."""

    commands: list[str] = []
    for package_file in (file for file in files if file.endswith("package.json")):
        try:
            package = json.loads((repo / package_file).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        scripts = package.get("scripts", {})
        if not isinstance(scripts, dict):
            continue
        parent = Path(package_file).parent.as_posix()
        prefix = "" if parent == "." else f"cd {parent} && "
        for script in ("test", "lint", "build"):
            if script in scripts:
                commands.append(f"{prefix}npm run {script}")
    if "pyproject.toml" in files:
        pyproject = _read_optional(repo / "pyproject.toml").lower()
        if "pytest" in pyproject:
            commands.append("python -m pytest")
        if "ruff" in pyproject:
            commands.append("python -m ruff check src tests")
        if "vulture" in pyproject:
            commands.append("python -m vulture")
    if "Cargo.toml" in files:
        commands.append("cargo test")
    return commands


def _any_file_ends_with(files: list[str], suffix: str) -> bool:
    """Return whether any repository file has the requested suffix."""

    return any(file.endswith(suffix) for file in files)


def _any_path_matches(files: list[str], pattern: str) -> bool:
    """Return whether a regular expression matches any repository-relative path."""

    return any(re.search(pattern, file) for file in files)


def _outcome_expectations(profile: RepoProfile, specialist_needed: bool) -> dict[str, list[str]]:
    """Describe the expected role and quality of each generated loop surface."""

    return {
        "README.md": [
            "Names what the repository is and who it serves in the first screen.",
            "Explains capabilities and outcomes without carrying operational runbooks or agent rules.",
            "Points to deeper docs only when those docs are durable entry points.",
        ],
        ".github/copilot-instructions.md": [
            "Contains durable rules, validation expectations, safety boundaries, and canonical file ownership.",
            "Prunes legacy session-management, tool-ordering, setup, and prompt-command boilerplate.",
            "Separates broad repo rules from specialist-agent instructions and temporary troubleshooting notes.",
        ],
        ".github/objectives.md": [
            "States the shared repository mission and the outcomes that define success.",
            "Names specialized loops that contribute evidence and learning to that mission.",
            "Defines evidence or verification that shows the mission is advancing.",
        ],
        "Last modified hygiene": [
            "Surfaces text files without a Last modified timestamp as attention candidates.",
            "Surfaces text files with timestamps older than the configured stale threshold, defaulting to 30 days.",
            "Uses timestamp age to help the session choose a mission-serving focus and folder, not as proof that a file is wrong.",
        ],
        ".github/agents/repo-specialist-agent.agent.md" if specialist_needed else "Existing specialist agents": (
            [
                f"Focuses on recurring domain work for the detected {profile.primary_kind} profile.",
                f"Uses this mission as its default lens: {profile.specialist_mission}",
                "Reads objectives and latest insights before changing files, then records reusable learnings after focused passes.",
            ]
            if specialist_needed
            else [
                f"Collectively serve the shared repository mission for the detected {profile.primary_kind} profile.",
                "Remain user-owned while their specialized lenses contribute to the shared improvement loop.",
                "Read their own current insight and overwrite it directly or return a ready-to-write record to their conductor.",
                "Prevent generation of a redundant generic repo specialist.",
            ]
        ),
        ".github/insights/": [
            "Keeps one current insight per MCP or specialist surface instead of growing forever.",
            "Records verified improvements, prune candidates, reusable learnings, and self-improvement notes.",
            "Turns one-off discoveries into better future repo guidance instead of scattered chat memory.",
        ],
    }


def _write_managed(path: Path, content: str, overwrite_managed_files: bool, changed: list[str]) -> None:
    """Write a fully managed file when ownership and overwrite settings allow it."""

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        content = _preserve_timestamp_only_change(existing, content)
        if existing == content:
            return
        if MANAGED_MARKER not in existing:
            return
        if not overwrite_managed_files:
            return
    path.write_text(content, encoding="utf-8")
    changed.append(_github_relative(path))


def _write_objectives(path: Path, content: str, overwrite_managed_files: bool, changed: list[str]) -> None:
    """Refresh managed objectives while retaining repository-owned objective sections."""

    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if MANAGED_MARKER not in existing:
            return
        if not overwrite_managed_files:
            return
        content = _merge_objectives(existing, content)
        content = _preserve_timestamp_only_change(existing, content)
        if existing == content:
            return
    path.write_text(content, encoding="utf-8")
    changed.append(_github_relative(path))


def _merge_objectives(existing: str, fresh: str) -> str:
    """Move user-owned title, objectives, and agent map into a fresh template."""

    # These sections express target-repository intent and remain user-owned across managed refreshes.
    existing_title = re.search(r"^#\s+.+$", existing, re.M)
    if existing_title:
        fresh = re.sub(r"^#\s+.+$", existing_title.group(0), fresh, count=1, flags=re.M)
    if existing_title and existing_title.group(0) != "# Repository Objectives":
        for heading in ["Aspirational Objectives", "Agent Map"]:
            existing_section = _extract_markdown_section(existing, heading)
            if existing_section:
                fresh = _replace_markdown_section(fresh, heading, existing_section)
    return fresh


def _preserve_timestamp_only_change(existing: str, fresh: str) -> str:
    """Keep existing managed content when only generated timestamps differ."""

    timestamp_pattern = r"(?i)(Last (?:modified|refreshed):\s*)[0-9]{4}-[0-9]{2}-[0-9]{2}T[^\s]+"
    normalize = lambda content: re.sub(timestamp_pattern, r"\1<TIMESTAMP>", content)
    return existing if normalize(existing) == normalize(fresh) else fresh


def _remove_managed(path: Path, changed: list[str]) -> None:
    """Remove an obsolete fully managed file while preserving user-owned files."""

    if not path.exists() or MANAGED_MARKER not in _read_optional(path):
        return
    path.unlink()
    changed.append(_github_relative(path))


def _apply_existing_agent_loops(
    github: Path,
    timestamp: str,
    overwrite_managed_files: bool,
    changed: list[str],
) -> list[str]:
    """Add managed loops and non-destructive current insight ledgers to user-owned agents."""

    if not overwrite_managed_files:
        return []
    improvements: list[str] = []
    for agent_name in _list_existing_agent_names(github):
        agent_path = github / "agents" / f"{agent_name}.agent.md"
        existing = _read_optional(agent_path)
        updated = _merge_agent_loop(
            existing,
            _existing_agent_loop_template(timestamp, agent_name, _agent_can_write(existing)),
        )
        updated = _preserve_timestamp_only_change(existing, updated)
        if updated != existing:
            agent_path.write_text(updated, encoding="utf-8")
            changed.append(_github_relative(agent_path))
            improvements.append(f"Added managed improvement loop to .github/agents/{agent_name}.agent.md.")
        _write_managed(
            github / "insights" / f"{agent_name}.md",
            _insight_ledger_template(timestamp, agent_name),
            False,
            changed,
        )
    return improvements


def _agent_can_write(content: str) -> bool:
    """Return whether the agent's declared tool list permits it to write its own insight file."""

    tools = re.search(r"^tools:\s*\[(?P<tools>[^]]*)\]", content, re.M | re.I)
    if not tools:
        return False
    declared_tools = {tool.strip().strip("'\"").lower() for tool in tools.group("tools").split(",")}
    return bool({"edit", "editfiles", "write", "runcommands"} & declared_tools)


def _merge_agent_loop(existing: str, loop: str) -> str:
    """Replace an existing managed agent-loop suffix or append one after user-owned guidance."""

    managed_suffix = rf"(?m)^[ \t]*{re.escape(AGENT_LOOP_MARKER)}[ \t]*(?:\r?\n|$)[\s\S]*\Z"
    if re.search(managed_suffix, existing):
        return re.sub(managed_suffix, lambda _: loop, existing)
    return f"{existing.rstrip()}\n\n{loop}"


def _existing_agent_loop_template(timestamp: str, agent_name: str, can_write: bool) -> str:
    """Render a small repeatable loop that preserves an existing agent's stated mission."""

    insight_path = f".github/insights/{agent_name}.md"
    insight_action = (
        f"Overwrite `{insight_path}` with the current verified learning before finishing."
        if can_write
        else f"Return a ready-to-write current insight record for `{insight_path}` so the conductor can overwrite it."
    )
    return f"""{AGENT_LOOP_MARKER}

## Improvement Loop

Last refreshed: {timestamp}

1. Read the shared repository mission in `.github/objectives.md` and the current `{insight_path}` before starting.
2. Apply this agent's existing mission to one concrete file, artifact, or rendered surface in service of the repository mission.
3. State the evidence used, how the finding or change advances the repository mission, and the nearest relevant validation.
4. {insight_action}
5. Feed reusable learning and any needed agent or canonical-file improvement back to the conductor.
"""


def _extract_markdown_section(content: str, heading: str) -> str:
    """Return one level-two Markdown section without trailing whitespace."""

    match = re.search(rf"^## {re.escape(heading)}\n[\s\S]*?(?=^## |\Z)", content, re.M)
    return match.group(0).rstrip() if match else ""


def _replace_markdown_section(content: str, heading: str, replacement: str) -> str:
    """Replace one level-two Markdown section while preserving surrounding content."""

    return re.sub(rf"^## {re.escape(heading)}\n[\s\S]*?(?=^## |\Z)", f"{replacement}\n\n", content, count=1, flags=re.M)


def _improve_copilot_instructions(content: str, github: Path) -> tuple[str, list[str]]:
    """Consolidate command summaries whose canonical prompt or closeout rule already exists."""

    canonical_prompts = {
        path.name.removesuffix(".prompt.md")
        for path in (github / "prompts").glob("*.prompt.md")
    }
    improvements: list[str] = []
    section_pattern = re.compile(
        rf"^## Reusable prompt commands\s*\n(?P<body>[\s\S]*?)(?=^## |^[ \t]*{re.escape(MANAGED_MARKER)}[ \t]*$|\Z)",
        re.M,
    )
    command_pattern = re.compile(r"^### /(?P<slug>[a-z0-9-]+)\s*\n[\s\S]*?(?=^### /|\Z)", re.M | re.I)

    def improve_section(section_match: re.Match[str]) -> str:
        """Remove only command blocks with a verified canonical replacement."""

        def improve_command(command_match: re.Match[str]) -> str:
            """Keep unknown commands and report every deterministic removal."""

            slug = command_match.group("slug").lower()
            if slug in canonical_prompts:
                improvements.append(
                    f"Removed /{slug} summary because .github/prompts/{slug}.prompt.md is canonical."
                )
                return ""
            if slug == "end-session":
                improvements.append(
                    "Removed legacy /end-session automation because Git closeout requires explicit authorization."
                )
                return ""
            return command_match.group(0).rstrip() + "\n\n"

        body = command_pattern.sub(improve_command, section_match.group("body")).strip()
        return f"## Reusable prompt commands\n\n{body}\n\n" if body else ""

    return section_pattern.sub(improve_section, content).rstrip() + "\n", improvements


def _set_last_modified_header(content: str, timestamp: str) -> str:
    """Add or refresh the canonical modification header after a substantive instruction change."""

    header = f"<!-- Last modified: {timestamp} -->"
    if re.match(r"^<!-- Last modified:.*?-->\s*", content, re.I):
        return re.sub(r"^<!-- Last modified:.*?-->", header, content, count=1, flags=re.I)
    return f"{header}\n\n{content.lstrip()}"


def _merge_managed_block(existing: str, block: str) -> str:
    """Replace generated instruction suffixes, collapsing orphaned or duplicate contracts."""

    if not existing.strip():
        return block
    generated_starts = [
        match.start()
        for pattern in [
            rf"(?m)^[ \t]*{re.escape(MANAGED_MARKER)}[ \t]*$",
            r"(?m)^## Loop Architecture Contract\r?$",
        ]
        if (match := re.search(pattern, existing))
    ]
    if generated_starts:
        user_guidance = existing[: min(generated_starts)].rstrip()
        return f"{user_guidance}\n\n{block}" if user_guidance else block
    return f"{existing.rstrip()}\n\n{block}"


def _github_relative(path: Path) -> str:
    """Return a path beginning at .github for stable changed-file responses."""

    parts = path.parts
    if ".github" not in parts:
        return _to_posix(path)
    index = parts.index(".github")
    return _to_posix(Path(*parts[index:]))


def _to_posix(path: Path) -> str:
    """Render a path with forward slashes so MCP responses are platform-independent."""

    return path.as_posix()


def _now_iso() -> str:
    """Return the current UTC time in the timestamp format used by managed files."""

    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _copilot_managed_block(timestamp: str) -> str:
    """Render the durable loop contract appended to Copilot instructions."""

    return f"""{MANAGED_MARKER}

## Loop Architecture Contract

Last refreshed: {timestamp}

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
"""


def _objectives_template(timestamp: str, summary: dict[str, Any]) -> str:
    """Render repository objectives from the analyzer's detected profile and rubric."""

    expectations = _format_expectations(summary["outcomeExpectations"])
    objectives = "\n".join(f"{index}. {objective}" for index, objective in enumerate(_profile_objectives(summary["primaryKind"]), start=1))
    specialists = summary["existingSpecialists"]
    existing_agents = summary["existingAgents"]
    specialist_map = (
        f"- Existing specialist agents ({', '.join(specialists)}): serve the shared repository mission through recurring domain expertise for the detected profile."
        if specialists
        else f"- repo-specialist-agent: {summary['specialistMission']}"
    )
    agent_loop_map = (
        f"- Existing agent loops ({', '.join(existing_agents)}): preserve each agent's mission, contribute specialized evidence to the shared repository mission, and maintain a matching current insight."
        if existing_agents
        else ""
    )
    validation_commands = "\n".join(f"- `{command}`" for command in summary["validationCommands"])
    if not validation_commands:
        validation_commands = "- Use the nearest repository-provided executable check for the changed behavior."
    return f"""<!-- Last modified: {timestamp} -->
{MANAGED_MARKER}

# Repository Objectives

Use this file for the shared repository mission: what the repo is trying to become, what quality means here, and how specialized loops contribute to that mission.

## Working Profile

- Detected profile: {summary['primaryKind']}
- Suggested specialist: {summary['suggestedSpecialist']}

## Aspirational Objectives

{objectives}

## Agent Map

- loop-improver-mcp: owns README/Copilot/objectives hygiene and decides which managed surfaces should exist.
{specialist_map}
{agent_loop_map}

## Outcome Expectations

{expectations}

## Verification

Each loop pass should name the changed behavior, run the cheapest relevant check, capture evidence, and record what improved in .github/insights/.

Detected commands:

{validation_commands}
"""


def _profile_objectives(primary_kind: RepoKind) -> list[str]:
    """Return deterministic objectives that reflect the detected repository work."""

    if primary_kind == "blog":
        return [
            "Publish useful articles with a consistent voice and clear audience value.",
            "Keep article visuals, layouts, and navigation effective across supported viewports.",
            "Verify the site build and rendered experience before publishing.",
            "Keep collaboration guidance concise and route recurring editorial work through existing specialists.",
        ]
    if primary_kind == "python":
        return [
            "Keep the Python capability deterministic, readable, and stable at its public interfaces.",
            "Cover behavior changes with focused tests and configured quality checks.",
            "Remove dead or duplicated code after verifying references and framework usage.",
            "Keep collaboration guidance concise and create specialist surfaces only for recurring work.",
        ]
    if primary_kind == "typescript":
        return [
            "Keep product behavior type-safe, testable, and stable across supported runtimes.",
            "Preserve clear component and module boundaries as the product evolves.",
            "Run configured tests, lint, type checks, or builds before delivery.",
            "Keep collaboration guidance concise and create specialist surfaces only for recurring work.",
        ]
    if primary_kind == "rust":
        return [
            "Keep Rust behavior correct, explicit, and stable at library or CLI boundaries.",
            "Use focused tests and configured lint checks to verify changes.",
            "Prune dead code and unnecessary complexity after checking references.",
            "Keep collaboration guidance concise and create specialist surfaces only for recurring work.",
        ]
    if primary_kind == "bicep":
        return [
            "Keep infrastructure templates minimal, repeatable, and explicit about environment assumptions.",
            "Validate syntax and planned deployment changes before applying infrastructure.",
            "Keep parameters, modules, and operational guidance aligned with active environments.",
            "Keep collaboration guidance concise and create specialist surfaces only for recurring work.",
        ]
    if primary_kind == "docs":
        return [
            "Keep documentation accurate, navigable, concise, and useful to its intended audience.",
            "Verify examples, links, and commands against current repository behavior.",
            "Remove duplicated or stale guidance when canonical ownership is clear.",
            "Keep collaboration guidance concise and create specialist surfaces only for recurring work.",
        ]
    return [
        "Keep the repository's primary capability aligned with its documented audience and outcomes.",
        "Make focused changes that preserve readability, validation, and maintainability.",
        "Keep collaboration guidance concise and create specialist surfaces only for recurring work.",
    ]


def _format_expectations(expectations: dict[str, list[str]]) -> str:
    """Render grouped outcome expectations as nested Markdown bullets."""

    sections: list[str] = []
    for path, bullets in expectations.items():
        rendered = "\n".join(f"  - {bullet}" for bullet in bullets)
        sections.append(f"- {path}\n{rendered}")
    return "\n".join(sections)


def _specialist_agent_template(timestamp: str, summary: dict[str, Any]) -> str:
    """Render the specialist agent that runs recurring repository improvement loops."""

    practices = "\n".join(f"- {practice}" for practice in _profile_practices(summary["primaryKind"]))
    return f"""<!-- Last modified: {timestamp} -->
{MANAGED_MARKER}
---
description: '{summary['suggestedSpecialist']}. Run repo-specific improvement loops tied to .github/objectives.md.'
tools: ['codebase', 'search', 'usages', 'editFiles', 'runCommands', 'runTests', 'problems']
---

# repo-specialist-agent

You are the repo-specific improvement agent. Read .github/objectives.md and the newest insights before changing files.
Treat the detected technology profile as starting context. Derive domain-specific loops from this repository's objectives, source, tests, and existing guidance.

## Detected Mission

{summary['specialistMission']}

## Working Standard

{practices}
- Search existing files and guidance before adding a parallel helper, document, prompt, or dependency.
- Prefer intention-revealing names, small focused changes, and direct control flow.
- Check references before removing or replacing existing behavior.
- Use the detected commands in `.github/objectives.md`; do not invent validation that the repository does not provide.
- Prune stale or duplicated material only when its ownership and replacement are clear.

## Loop

1. Use the opening exchange to establish a concise session title, direction, and agreed endpoint.
2. Identify one repo-specific improvement that advances the shared repository mission.
3. Use analyze_github_loop attention guidance only as evidence for choosing a concrete focus area.
4. Read the owning files, existing specialist guidance, and nearest validation surface.
5. Make the smallest change that improves the chosen outcome, including pruning when appropriate.
6. Run the cheapest relevant detected command and inspect behavior-specific output when available.
7. Write durable notes by overwriting the current insight in .github/insights/repo-specialist-agent.md.
8. Review the final diff and working tree, separating unrelated changes before closeout.
9. Commit only the loop's intended changes with a meaningful message after the user has authorized it.
10. Push only when the user has authorized it and the branch is safe to update.

If validation fails, unrelated changes cannot be separated, or pushing is not authorized, do not claim the loop is complete; leave an explicit handoff with the repository status, remaining check, and exact next Git action.

If the repo profile is wrong, update .github/objectives.md and this agent before doing specialized work.
"""


def _profile_practices(primary_kind: RepoKind) -> list[str]:
    """Return practical quality checks for a generated specialist's detected profile."""

    practices: dict[RepoKind, list[str]] = {
        "blog": [
            "Preserve the author's voice, intended audience, and factual boundaries.",
            "Check article structure, transitions, visual opportunities, and publish readiness.",
            "Build the site and inspect rendered output when layout or visuals change.",
        ],
        "docs": [
            "Keep the documented behavior accurate, navigable, concise, and useful to its intended reader.",
            "Verify examples, links, and commands against the repository when practical.",
        ],
        "bicep": [
            "Keep templates minimal, parameter intent explicit, and environment assumptions documented.",
            "Validate deployment syntax and inspect planned changes before applying infrastructure.",
        ],
        "rust": [
            "Keep ownership, error handling, public interfaces, and CLI behavior explicit.",
            "Run focused tests and configured lint or formatting checks for changed crates.",
        ],
        "python": [
            "Keep interfaces typed where the repository expects typing and make responsibilities clear in code.",
            "Run focused tests plus configured lint and dead-code checks for changed modules.",
        ],
        "typescript": [
            "Preserve type safety, runtime behavior, and the repository's component or module boundaries.",
            "Run configured tests, lint, type checks, or builds for the changed package.",
        ],
        "generic": [
            "Derive quality criteria from the repository's README, objectives, tests, and existing guidance.",
            "Verify changed behavior through the nearest repository-provided executable check.",
        ],
    }
    return practices[primary_kind]

def _insights_readme_template(timestamp: str) -> str:
    """Render instructions for maintaining one current insight per loop surface."""

    return f"""<!-- Last modified: {timestamp} -->
{MANAGED_MARKER}

# Current insights

Each MCP or specialist pass overwrites the matching insight file after focused work. These files capture current reusable learning, not a permanent history.

Use this block:

```text
## <ISO-8601 UTC timestamp, ms> - <short title>
**Mission:** <loop architecture | repo specialist | named objective>
**Improved:** <what got better and how it was verified>
**Prune candidates:** <dead code / stale docs / empty dirs / unused symbols, or none>
**Reusable learnings:** <fact, pattern, or gotcha worth reusing, or none>
**Agent self-improvement:** <agent/instruction/objectives edit that would help next time, or none>
```
"""


def _insight_ledger_template(timestamp: str, agent_name: str) -> str:
    """Render an empty current-insight file for one agent or MCP surface."""

    return f"""<!-- Last modified: {timestamp} -->
{MANAGED_MARKER}

# {agent_name} insight

Current focused learning for this surface.
"""