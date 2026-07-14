# Last modified: 2026-07-14T00:00:00.000Z

"""Inspect repositories and create the managed files used by their improvement loops.

The public functions analyze a repository, install its loop foundation, and record
the latest learning. Private helpers handle file discovery, hygiene checks, profile
selection, safe updates to managed content, and rendering the generated Markdown.
"""

from __future__ import annotations

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
    has_insights = any(file.startswith("insights/") for file in github_files)

    signals = [
        "readme" if readme else "no-readme",
        "copilot-instructions" if copilot else "no-copilot-instructions",
        "objectives" if objectives else "no-objectives",
        "repo-specialist-agent" if has_specialist else "no-repo-specialist-agent",
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
        "" if has_specialist else ".github/agents/repo-specialist-agent.agent.md",
        "" if has_insights else ".github/insights/README.md",
        *[f"README hygiene: {finding}" for finding in readme_hygiene.findings],
        *[f"Copilot hygiene: {finding}" for finding in copilot_hygiene.findings],
        *[f"Objectives hygiene: {finding}" for finding in objectives_hygiene.findings],
    ]
    missing = [item for item in missing if item]

    recommendation = (
        f"Run improve_loop to install the modernization foundation, then tune {profile.suggested_specialist} around the repo's objectives."
        if missing
        else f"Modernization foundation is present; use {profile.suggested_specialist} for domain work and record insights after each pass."
    )

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
        "outcomeExpectations": _outcome_expectations(profile),
        "readmeSignals": readme_hygiene.signals,
        "copilotSignals": copilot_hygiene.signals,
        "objectivesSignals": objectives_hygiene.signals,
        "primaryKind": profile.primary_kind,
        "suggestedSpecialist": profile.suggested_specialist,
        "specialistMission": profile.specialist_mission,
    }


def apply_github_loop(repo_path: str, overwrite_managed_files: bool = True) -> dict[str, Any]:
    """Create or refresh managed loop files while preserving user-owned guidance."""

    repo = Path(repo_path)
    before = analyze_github_loop(str(repo))
    timestamp = _now_iso()
    github = repo / ".github"
    for directory in [github, github / "agents", github / "insights"]:
        directory.mkdir(parents=True, exist_ok=True)

    changed: list[str] = []
    copilot_path = github / "copilot-instructions.md"
    existing_copilot = _read_optional(copilot_path)
    next_copilot = _merge_managed_block(existing_copilot, _copilot_managed_block(timestamp))
    if next_copilot != existing_copilot:
        copilot_path.write_text(next_copilot, encoding="utf-8")
        changed.append(".github/copilot-instructions.md")

    _write_objectives(github / "objectives.md", _objectives_template(timestamp, before), overwrite_managed_files, changed)
    _write_managed(github / "agents" / "repo-specialist-agent.agent.md", _specialist_agent_template(timestamp, before), overwrite_managed_files, changed)
    _write_managed(github / "insights" / "README.md", _insights_readme_template(timestamp), overwrite_managed_files, changed)
    _write_managed(github / "insights" / "loop-improver-mcp.md", _insight_ledger_template(timestamp, "loop-improver-mcp"), False, changed)
    _write_managed(github / "insights" / "repo-specialist-agent.md", _insight_ledger_template(timestamp, "repo-specialist-agent"), False, changed)

    return {"before": before, "after": analyze_github_loop(str(repo)), "changed": changed}


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
            "instruction": "No timestamp attention items surfaced. Choose an objective from .github/objectives.md based on current repo work.",
            "objectiveCandidates": [],
            "focusFolders": [],
        }
    return {
        "instruction": "Use these attention items to choose one objective for the session, then focus on the highest-signal folder or file cluster before editing.",
        "objectiveCandidates": [
            "Review files missing Last modified timestamps and decide whether they are durable enough to keep, update, move, or prune.",
            "Review stale timestamp files and refresh only the files whose content still serves an active objective.",
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
    """Return whether timestamp checks would be meaningless for a file or cache path."""

    ignored_prefixes = (".git/", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/")
    ignored_suffixes = (".json", ".lock", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".zip", ".gz", ".pdf")
    return file.startswith(ignored_prefixes) or file.endswith(ignored_suffixes)


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
    signals = [
        "has-brand-heading" if re.search(r"^#\s+\S", content, re.M) else "no-brand-heading",
        "explains-capability" if re.search(r"what|capability|purpose|why|use", content, re.I) else "thin-capability-story",
        "has-usage-entry" if re.search(r"quickstart|setup|install|usage", content, re.I) else "no-usage-entry",
        "concise" if len(content) <= 5000 else "too-long-for-human-orientation",
        "mentions-ai-surface" if re.search(r"copilot|agent|mcp|prompt", content, re.I) else "human-first",
    ]
    findings = [
        "" if re.search(r"^#\s+\S", content, re.M) else "needs a clear repo brand heading",
        "" if re.search(r"what|capability|purpose|why|use", content, re.I) else "should explain the repo capability in human terms",
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
    if _any_path_matches(files, r"(^|/)(content|src/content|posts|blog)/") or "astro.config.mjs" in file_set:
        return RepoProfile("blog", ["profile-blog"], "Voice and editor specialist", "Improve article quality, voice consistency, publish readiness, and editorial insight loops.")
    if "package.json" in file_set or _any_file_ends_with(files, ".ts") or _any_file_ends_with(files, ".tsx"):
        return RepoProfile("typescript", ["profile-typescript"], "TypeScript product hygiene specialist", "Keep the TypeScript surface small, tested, typed, and aligned to the repo objectives.")
    if _any_file_ends_with(files, ".bicep") or _any_file_ends_with(files, ".bicepparam"):
        return RepoProfile("bicep", ["profile-bicep"], "Infrastructure validation specialist", "Keep deployment templates minimal, validated, and aligned to the repo's environment objectives.")
    markdown_count = sum(1 for file in files if file.endswith(".md"))
    if markdown_count >= max(3, len(files) / 2):
        return RepoProfile("docs", ["profile-docs"], "Documentation clarity specialist", "Keep documentation concise, human-readable, accurate, and free of duplicated operational guidance.")
    return RepoProfile("generic", ["profile-generic"], "Repository specialist", "Identify the repo's recurring work and create small verified improvement loops around it.")


def _any_file_ends_with(files: list[str], suffix: str) -> bool:
    """Return whether any repository file has the requested suffix."""

    return any(file.endswith(suffix) for file in files)


def _any_path_matches(files: list[str], pattern: str) -> bool:
    """Return whether a regular expression matches any repository-relative path."""

    return any(re.search(pattern, file) for file in files)


def _outcome_expectations(profile: RepoProfile) -> dict[str, list[str]]:
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
            "States the repo-specific outcomes that should improve over time.",
            "Maps each active loop or specialist surface to the outcomes it serves.",
            "Defines evidence or verification that shows an improvement actually landed.",
        ],
        "Last modified hygiene": [
            "Surfaces text files without a Last modified timestamp as attention candidates.",
            "Surfaces text files with timestamps older than the configured stale threshold, defaulting to 30 days.",
            "Uses timestamp age to help the session choose one objective and focus folder, not as proof that a file is wrong.",
        ],
        ".github/agents/repo-specialist-agent.agent.md": [
            f"Focuses on recurring domain work for the detected {profile.primary_kind} profile.",
            f"Uses this mission as its default lens: {profile.specialist_mission}",
            "Reads objectives and latest insights before changing files, then records reusable learnings after focused passes.",
        ],
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
    for heading in ["Aspirational Objectives", "Agent Map"]:
        existing_section = _extract_markdown_section(existing, heading)
        if existing_section:
            fresh = _replace_markdown_section(fresh, heading, existing_section)
    return fresh


def _extract_markdown_section(content: str, heading: str) -> str:
    """Return one level-two Markdown section without trailing whitespace."""

    match = re.search(rf"^## {re.escape(heading)}\n[\s\S]*?(?=^## |\Z)", content, re.M)
    return match.group(0).rstrip() if match else ""


def _replace_markdown_section(content: str, heading: str, replacement: str) -> str:
    """Replace one level-two Markdown section while preserving surrounding content."""

    return re.sub(rf"^## {re.escape(heading)}\n[\s\S]*?(?=^## |\Z)", f"{replacement}\n\n", content, count=1, flags=re.M)


def _merge_managed_block(existing: str, block: str) -> str:
    """Replace the managed instruction suffix or append one to user-owned content."""

    if not existing.strip():
        return block
    managed_suffix = rf"(?m)^[ \t]*{re.escape(MANAGED_MARKER)}[ \t]*(?:\r?\n|$)[\s\S]*\Z"
    if re.search(managed_suffix, existing):
        # The marker owns only the generated suffix, preserving instructions written before it.
        return re.sub(managed_suffix, block.rstrip(), existing)
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
- .github/objectives.md names the repo's aspirational objectives and maps them to active loops.
- .github/agents/ contains repo-specialist agents only when they help recurring work.
- .github/insights/ records the current learning for each loop surface and what should improve next.

### Ground Rules

- Start with README and Copilot hygiene before adding new agents.
- Use the opening exchange to establish a concise session title, direction, and agreed endpoint before starting a loop.
- Identify objectives from the repo's actual files, tests, docs, and recurring work.
- Let this MCP server own loop architecture; deploy repo agents only for recurring domain work.
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
- Objectives map to active loops and verification methods.
- Agent passes produce insights that improve future passes.
- Completed loop changes are committed and pushed, or an explicit Git handoff records why they are not.
"""


def _objectives_template(timestamp: str, summary: dict[str, Any]) -> str:
    """Render repository objectives from the analyzer's detected profile and rubric."""

    expectations = _format_expectations(summary["outcomeExpectations"])
    return f"""<!-- Last modified: {timestamp} -->
{MANAGED_MARKER}

# Repository Objectives

Use this file for the repo's aspirational objectives: what the repo is trying to become, what quality means here, and which loops keep it improving.

## Working Profile

- Detected profile: {summary['primaryKind']}
- Suggested specialist: {summary['suggestedSpecialist']}

## Aspirational Objectives

1. Make the README a clear, concise capability page for the repo.
2. Keep Copilot instructions focused on durable rules, validation, and cleanup expectations.
3. Create missing `.github` collaboration surfaces when older repos do not have them.
4. Use repo agents only for recurring domain work that benefits from a dedicated instruction surface.
5. Tune repo-specialist guidance around the repo's actual language, content, product, or infrastructure work.

## Agent Map

- loop-improver-mcp: owns README/Copilot/objectives hygiene and decides which managed surfaces should exist.
- repo-specialist-agent: {summary['specialistMission']}

## Outcome Expectations

{expectations}

## Verification

Each loop pass should name the changed behavior, run the cheapest relevant check, capture evidence, and record what improved in .github/insights/.
"""


def _format_expectations(expectations: dict[str, list[str]]) -> str:
    """Render grouped outcome expectations as nested Markdown bullets."""

    sections: list[str] = []
    for path, bullets in expectations.items():
        rendered = "\n".join(f"  - {bullet}" for bullet in bullets)
        sections.append(f"- {path}\n{rendered}")
    return "\n".join(sections)


def _specialist_agent_template(timestamp: str, summary: dict[str, Any]) -> str:
    """Render the specialist agent that runs recurring repository improvement loops."""

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

## Code Standard

- Write for a reader who is still learning the language or repository.
- Give each source file a brief header description of its role and how it fits into the system.
- Give functions and classes concise docstrings that explain their responsibility and important inputs or results.
- Prefer intention-revealing names, small single-purpose units, and direct control flow.
- Comment only when rationale, invariants, constraints, or non-obvious tradeoffs cannot be made clear in code.
- Remove comments that narrate the code, repeat names, or no longer match behavior.
- Treat a need for explanatory prose as a signal to simplify the code first.
- Review source comments in every changed code file.
- Add or update focused comments where the code cannot preserve purpose, rationale, invariants, or constraints by itself.

## Code Audit

- Search for existing code before adding a new helper, type, module, or dependency.
- Check references to changed and nearby symbols before deciding they are still needed.
- Run the repository's dead-code tooling when available, and verify uncertain findings with reference searches.
- Remove unused functions, classes, imports, tests, and comments when their behavior is no longer part of an active objective.

## Loop

1. Use the opening exchange to establish a concise session title, direction, and agreed endpoint.
2. Identify one repo-specific improvement tied to an objective.
3. Review analyze_github_loop attention guidance and choose one objective plus one focus folder or file cluster for the session.
4. Read the owning files, nearest validation surface, and usages of the symbols likely to change.
5. Prune dead code, stale docs, duplicated guidance, or unnecessary verbosity when that is the smallest useful improvement.
6. Review changed code and source comments against the Code Standard; simplify first, then add focused comments where needed.
7. Complete the Code Audit for changed and nearby symbols.
8. Run the cheapest relevant executable check.
9. Write durable notes before closing the loop by overwriting the current insight in .github/insights/repo-specialist-agent.md.
10. Review the final diff and working tree, separating unrelated changes before closeout.
11. Commit only the loop's intended changes with a meaningful message.
12. Push the commit when the user has authorized it and the branch is safe to update.

If validation fails, unrelated changes cannot be separated, or pushing is not authorized, do not claim the loop is complete; leave an explicit handoff with the repository status, remaining check, and exact next Git action.

If the repo profile is wrong, update .github/objectives.md and this agent before doing specialized work.
"""

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