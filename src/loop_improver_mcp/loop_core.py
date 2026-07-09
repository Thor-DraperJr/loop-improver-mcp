# Last modified: 2026-07-09T21:10:00.420Z

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from typing import Any, Literal


RepoKind = Literal["rust", "python", "typescript", "blog", "docs", "bicep", "security-demo", "teams-live", "generic"]

MANAGED_MARKER = "<!-- Managed by loop-improver-mcp -->"


@dataclass(frozen=True)
class RepoProfile:
    primary_kind: RepoKind
    signals: list[str]
    suggested_specialist: str
    specialist_mission: str


@dataclass(frozen=True)
class Hygiene:
    signals: list[str]
    findings: list[str]


def analyze_github_loop(repo_path: str, stale_after_days: int = 30, now: datetime | None = None) -> dict[str, Any]:
    repo = Path(repo_path)
    github = repo / ".github"
    github_files = _list_relative_files(github) if github.exists() else []
    repo_files = _list_repo_files(repo)
    profile = _infer_repo_profile(repo, repo_files)

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
    return sorted(_to_posix(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def _list_repo_files(root: Path) -> list[str]:
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
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _read_text_optional(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _analyze_file_timestamps(repo: Path, files: list[str], stale_after_days: int, now: datetime) -> dict[str, list[dict[str, str]] | list[str]]:
    missing: list[str] = []
    stale: list[dict[str, str]] = []
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


def _attention_session_guidance(timestamp_hygiene: dict[str, list[dict[str, str]] | list[str]]) -> dict[str, Any]:
    missing = [str(path) for path in timestamp_hygiene["missingLastModified"]]
    stale = [str(item["path"]) for item in timestamp_hygiene["staleLastModified"]]  # type: ignore[index]
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
    counts: dict[str, int] = {}
    for file in files:
        folder = file.split("/", 1)[0] if "/" in file else "."
        counts[folder] = counts.get(folder, 0) + 1
    return [
        {"folder": folder, "attentionCount": count}
        for folder, count in sorted(counts.items(), key=lambda item: (-item[1], item[0] == ".", item[0]))
    ]


def _skip_timestamp_scan(file: str) -> bool:
    ignored_prefixes = (".git/", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/")
    ignored_suffixes = (".json", ".lock", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".zip", ".gz", ".pdf")
    return file.startswith(ignored_prefixes) or file.endswith(ignored_suffixes)


def _extract_last_modified(content: str) -> datetime | None:
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
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _analyze_readme(content: str) -> Hygiene:
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
    if not content.strip():
        return Hygiene(["missing"], ["missing durable agent ground rules"])
    signals = [
        "has-ground-rules" if re.search(r"ground rules|definition of done|validation", content, re.I) else "thin-ground-rules",
        "names-canonical-files" if re.search(r"README\.md|objectives\.md|canonical", content, re.I) else "no-canonical-file-map",
        "has-learning-loop" if re.search(r"insights|learning|reusable", content, re.I) else "no-learning-loop",
        "has-pruning-rule" if re.search(r"prun(e|ing)|dead code|stale", content, re.I) else "no-pruning-rule",
        "concise" if len(content) <= 7000 else "possible-prompt-warehouse",
    ]
    findings = [
        "" if re.search(r"ground rules|definition of done|validation", content, re.I) else "needs durable ground rules and validation expectations",
        "" if re.search(r"README\.md|objectives\.md|canonical", content, re.I) else "should name README, objectives, agents, and insights as separate canonical surfaces",
        "" if re.search(r"insights|learning|reusable", content, re.I) else "should require an insight loop after focused passes",
        "" if re.search(r"prun(e|ing)|dead code|stale", content, re.I) else "should include pruning and stale-reference cleanup",
        "" if len(content) <= 7000 else "may contain primary prompts that belong in prompts, skills, or agents",
    ]
    return Hygiene(signals, [finding for finding in findings if finding])


def _analyze_objectives(content: str) -> Hygiene:
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


def _infer_repo_profile(repo: Path, files: list[str]) -> RepoProfile:
    has = set(files).__contains__
    has_ext = lambda suffix: any(file.endswith(suffix) for file in files)
    has_path = lambda pattern: any(re.search(pattern, file) for file in files)
    profile_override = _profile_from_objectives(repo / ".github" / "objectives.md")
    if profile_override:
        return profile_override
    repo_context = _repo_profile_context(repo, files)

    if has("scout/loops/security-se-loop.json") or has("docs/a365-eval.md") or has_path(r"(^|/)security-solution-engineer/"):
        return RepoProfile("security-demo", ["profile-security-demo"], "Security demo infrastructure specialist", "Keep Microsoft security demo infrastructure, validation evidence, Scout loops, and customer-ready narratives aligned to the repo objectives.")
    if re.search(r"teams\.live\.com|msgapi\.teams\.live\.com|chatsvc/consumer|teams live", repo_context, re.I):
        return RepoProfile("teams-live", ["profile-teams-live"], "Teams Live shim agent", "Keep the consumer Teams Live browser-session/private-endpoint bridge isolated, consent-based, auditable, and aligned to the repo objectives.")
    if has("Cargo.toml") or has_ext(".rs"):
        return RepoProfile("rust", ["profile-rust"], "Rust hygiene specialist", "Prune dead Rust code, reduce unnecessary verbosity, and keep tests or CLI behavior aligned with the repo objectives.")
    if has("pyproject.toml") or has_ext(".py"):
        return RepoProfile("python", ["profile-python"], "Python MCP hygiene specialist", "Keep the Python MCP tool surface small, typed, tested, deterministic, and aligned to the repo objectives.")
    if has_path(r"(^|/)(content|src/content|posts|blog)/") or has("astro.config.mjs"):
        return RepoProfile("blog", ["profile-blog"], "Voice and editor specialist", "Improve article quality, voice consistency, publish readiness, and editorial insight loops.")
    if has("package.json") or has_ext(".ts") or has_ext(".tsx"):
        return RepoProfile("typescript", ["profile-typescript"], "TypeScript product hygiene specialist", "Keep the TypeScript surface small, tested, typed, and aligned to the repo objectives.")
    if has_ext(".bicep") or has_ext(".bicepparam"):
        return RepoProfile("bicep", ["profile-bicep"], "Infrastructure validation specialist", "Keep deployment templates minimal, validated, and aligned to the repo's environment objectives.")
    markdown_count = sum(1 for file in files if file.endswith(".md"))
    if markdown_count >= max(3, len(files) / 2):
        return RepoProfile("docs", ["profile-docs"], "Documentation clarity specialist", "Keep documentation concise, human-readable, accurate, and free of duplicated operational guidance.")
    return RepoProfile("generic", ["profile-generic"], "Repository specialist", "Identify the repo's recurring work and create small verified improvement loops around it.")


def _profile_from_objectives(path: Path) -> RepoProfile | None:
    content = _read_text_optional(path)
    if not content:
        return None
    match = re.search(r"^-\s*Detected profile:\s*(.+)$", content, re.M)
    if not match:
        return None
    detected = match.group(1).strip()
    if re.search(r"teams live|teams-live|chatsvc/consumer|msgapi\.teams\.live\.com", detected, re.I):
        return RepoProfile("teams-live", ["profile-teams-live", "profile-from-objectives"], "Teams Live shim agent", "Keep the consumer Teams Live browser-session/private-endpoint bridge isolated, consent-based, auditable, and aligned to the repo objectives.")
    return None


def _repo_profile_context(repo: Path, files: list[str]) -> str:
    candidate_files = [
        file
        for file in files
        if file in {"README.md", ".github/objectives.md"} or file.startswith("docs/") and file.endswith(".md")
    ]
    chunks: list[str] = []
    for file in candidate_files[:20]:
        content = _read_text_optional(repo / file)
        if content:
            chunks.append(content[:5000])
    return "\n".join(chunks)


def _outcome_expectations(profile: RepoProfile) -> dict[str, list[str]]:
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
    existing_title = re.search(r"^#\s+.+$", existing, re.M)
    if existing_title:
        fresh = re.sub(r"^#\s+.+$", existing_title.group(0), fresh, count=1, flags=re.M)
    for heading in ["Aspirational Objectives", "Agent Map"]:
        existing_section = _extract_markdown_section(existing, heading)
        if existing_section:
            fresh = _replace_markdown_section(fresh, heading, existing_section)
    return fresh


def _extract_markdown_section(content: str, heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\n[\s\S]*?(?=^## |\Z)", content, re.M)
    return match.group(0).rstrip() if match else ""


def _replace_markdown_section(content: str, heading: str, replacement: str) -> str:
    return re.sub(rf"^## {re.escape(heading)}\n[\s\S]*?(?=^## |\Z)", f"{replacement}\n\n", content, count=1, flags=re.M)


def _merge_managed_block(existing: str, block: str) -> str:
    if not existing.strip():
        return block
    if MANAGED_MARKER in existing:
        return re.sub(f"{re.escape(MANAGED_MARKER)}[\\s\\S]*$", block.rstrip(), existing)
    return f"{existing.rstrip()}\n\n{block}"


def _github_relative(path: Path) -> str:
    parts = path.parts
    if ".github" not in parts:
        return _to_posix(path)
    index = parts.index(".github")
    return _to_posix(Path(*parts[index:]))


def _to_posix(path: Path) -> str:
    return path.as_posix()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _copilot_managed_block(timestamp: str) -> str:
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
- Identify objectives from the repo's actual files, tests, docs, and recurring work.
- Let this MCP server own loop architecture; deploy repo agents only for recurring domain work.
- Each agent must end passes by recording insights and applying obvious agent/doc improvements directly.
- Each agent must keep the insights loop current by overwriting its current insight after focused passes.
- Prefer pruning, moving, or merging stale code and docs over adding parallel surfaces.
- When files are moved or removed, delete empty directories and check for stale references.

### Definition Of Done

- README remains human-facing and concise.
- Copilot instructions remain durable ground rules, not a primary prompt warehouse.
- Objectives map to active loops and verification methods.
- Agent passes produce insights that improve future passes.
"""


def _objectives_template(timestamp: str, summary: dict[str, Any]) -> str:
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
    sections: list[str] = []
    for path, bullets in expectations.items():
        rendered = "\n".join(f"  - {bullet}" for bullet in bullets)
        sections.append(f"- {path}\n{rendered}")
    return "\n".join(sections)


def _specialist_agent_template(timestamp: str, summary: dict[str, Any]) -> str:
    return f"""<!-- Last modified: {timestamp} -->
{MANAGED_MARKER}
---
description: '{summary['suggestedSpecialist']}. Run repo-specific improvement loops tied to .github/objectives.md.'
tools: ['codebase', 'search', 'usages', 'editFiles', 'runCommands', 'runTests', 'problems']
---

# repo-specialist-agent

You are the repo-specific improvement agent. Read .github/objectives.md and the newest insights before changing files.

## Detected Mission

{summary['specialistMission']}

## Loop

1. Identify one repo-specific improvement tied to an objective.
2. Review analyze_github_loop attention guidance and choose one objective plus one focus folder or file cluster for the session.
3. Read the owning files and nearest validation surface.
4. Prune dead code, stale docs, duplicated guidance, or unnecessary verbosity when that is the smallest useful improvement.
5. Run the cheapest relevant executable check.
6. Overwrite the current insight in .github/insights/repo-specialist-agent.md.

If the repo profile is wrong, update .github/objectives.md and this agent before doing specialized work.
"""

def _insights_readme_template(timestamp: str) -> str:
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
    return f"""<!-- Last modified: {timestamp} -->
{MANAGED_MARKER}

# {agent_name} insight

Current focused learning for this surface.
"""