#!/usr/bin/env python3
"""Check whether an adopted ADS workspace is structurally healthy."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Finding:
    level: str
    code: str
    message: str


@dataclass
class TaskRecord:
    path: Path
    task_id: str
    updated_at: str
    status: str


@dataclass
class HandoffRecord:
    path: Path
    task_id: str
    updated_at: str


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_table_value(text: str, label: str) -> str:
    pattern = rf"\|\s*\*\*{re.escape(label)}\*\*\s*\|\s*(.*?)\s*\|"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def strip_code(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def parse_iso8601(value: str) -> datetime | None:
    value = strip_code(value)
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def discover(repo_root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in repo_root.glob(pattern) if path.is_file())


def parse_task(path: Path) -> TaskRecord:
    text = read_text(path)
    status_match = re.search(r"\*\*状态\*\*[:：]\s*`?([^`\n]+)`?", text)
    return TaskRecord(
        path=path,
        task_id=strip_code(extract_table_value(text, "task_id")) or path.stem,
        updated_at=strip_code(extract_table_value(text, "updated_at")),
        status=(status_match.group(1).strip() if status_match else "unknown"),
    )


def parse_handoff(path: Path) -> HandoffRecord:
    text = read_text(path)
    return HandoffRecord(
        path=path,
        task_id=strip_code(extract_table_value(text, "task_id")) or path.stem,
        updated_at=strip_code(extract_table_value(text, "updated_at")),
    )


def load_toolset(repo_root: Path) -> dict:
    toolset_path = repo_root / "tools" / "toolset.json"
    if not toolset_path.exists():
        return {}
    return json.loads(read_text(toolset_path))


def load_skill_manifests(repo_root: Path) -> list[tuple[Path, dict]]:
    manifests: list[tuple[Path, dict]] = []
    for path in discover(repo_root, "skills/**/manifest.json"):
        manifests.append((path, json.loads(read_text(path))))
    return manifests


def check_required_files(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    required_files = [
        ("fail", "missing_readme_agent", repo_root / "README_AGENT.md"),
        ("fail", "missing_constitution", repo_root / ".agent" / "constitution.md"),
        ("warn", "missing_identity", repo_root / ".agent" / "identity.json"),
        ("warn", "missing_start_here", repo_root / ".ai" / "START_HERE.md"),
        ("warn", "missing_validate_ads", repo_root / "scripts" / "validate_ads.py"),
        ("warn", "missing_toolset", repo_root / "tools" / "toolset.json"),
    ]
    for level, code, path in required_files:
        if not path.exists():
            findings.append(Finding(level, code, f"missing `{path.relative_to(repo_root)}`"))
    return findings


def check_task_handoff_alignment(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    task_files = [path for path in discover(repo_root, ".ai/tasks/**/*.md") if path.name != ".gitkeep"]
    handoff_files = [path for path in discover(repo_root, ".ai/handoffs/**/*.md") if path.name != ".gitkeep"]

    tasks = [parse_task(path) for path in task_files]
    handoffs = [parse_handoff(path) for path in handoff_files]
    handoff_by_task = {record.task_id: record for record in handoffs}
    task_ids = {record.task_id for record in tasks}

    for task in tasks:
        task_updated = parse_iso8601(task.updated_at)
        handoff = handoff_by_task.get(task.task_id)
        if task.status in {"in-progress", "blocked", "review", "done"} and not handoff:
            findings.append(
                Finding(
                    "warn",
                    "missing_handoff",
                    f"task `{task.task_id}` is `{task.status}` but has no matching `.ai/handoffs/{task.task_id}.md`",
                )
            )
            continue
        if handoff:
            handoff_updated = parse_iso8601(handoff.updated_at)
            if task_updated and handoff_updated and handoff_updated < task_updated:
                findings.append(
                    Finding(
                        "warn",
                        "stale_handoff",
                        f"handoff `{handoff.path.relative_to(repo_root)}` is older than task `{task.task_id}`",
                    )
                )
            if task.updated_at and not task_updated:
                findings.append(Finding("warn", "invalid_task_timestamp", f"task `{task.task_id}` has invalid updated_at `{task.updated_at}`"))
            if handoff.updated_at and not handoff_updated:
                findings.append(
                    Finding(
                        "warn",
                        "invalid_handoff_timestamp",
                        f"handoff `{handoff.path.relative_to(repo_root)}` has invalid updated_at `{handoff.updated_at}`",
                    )
                )

    for handoff in handoffs:
        if handoff.task_id not in task_ids:
            findings.append(
                Finding(
                    "warn",
                    "orphan_handoff",
                    f"handoff `{handoff.path.relative_to(repo_root)}` references missing task `{handoff.task_id}`",
                )
            )

    return findings


def check_toolset_drift(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    toolset = load_toolset(repo_root)
    if not toolset:
        return findings

    tool_entries = {}
    for entry in toolset.get("tools", []):
        if not isinstance(entry, dict):
            continue
        tool_id = str(entry.get("tool_id", "")).strip()
        if tool_id:
            tool_entries[tool_id] = entry

    manifests = load_skill_manifests(repo_root)
    manifest_tool_ids: set[str] = set()

    for path, manifest in manifests:
        tool_id = str(manifest.get("tool_id", "")).strip()
        version = str(manifest.get("version", "")).strip()
        manifest_tool_ids.add(tool_id)
        if not tool_id:
            findings.append(Finding("warn", "manifest_missing_tool_id", f"manifest `{path.relative_to(repo_root)}` missing `tool_id`"))
            continue

        tool_entry = tool_entries.get(tool_id)
        if not tool_entry:
            findings.append(Finding("warn", "tool_missing_from_toolset", f"manifest tool `{tool_id}` is not registered in `tools/toolset.json`"))
            continue

        manifest_rel = str(path.relative_to(repo_root))
        declared_manifest = str(tool_entry.get("manifest", "")).strip()
        if declared_manifest and declared_manifest != manifest_rel:
            findings.append(
                Finding(
                    "warn",
                    "manifest_path_drift",
                    f"tool `{tool_id}` points to `{declared_manifest}` but manifest lives at `{manifest_rel}`",
                )
            )
        declared_version = str(tool_entry.get("version", "")).strip()
        if declared_version and version and declared_version != version:
            findings.append(
                Finding(
                    "warn",
                    "tool_version_drift",
                    f"tool `{tool_id}` version mismatch: toolset=`{declared_version}` manifest=`{version}`",
                )
            )

    for tool_id, entry in tool_entries.items():
        manifest_rel = str(entry.get("manifest", "")).strip()
        if manifest_rel and not (repo_root / manifest_rel).exists():
            findings.append(Finding("warn", "missing_manifest_path", f"tool `{tool_id}` declares missing manifest `{manifest_rel}`"))
        if tool_id not in manifest_tool_ids and manifest_rel:
            findings.append(Finding("warn", "toolset_orphan_entry", f"`tools/toolset.json` registers `{tool_id}` without a matching skill manifest"))

    return findings


def run_doctor(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(check_required_files(repo_root))
    findings.extend(check_task_handoff_alignment(repo_root))
    findings.extend(check_toolset_drift(repo_root))
    return findings


def render_report(repo_root: Path, findings: list[Finding]) -> str:
    fail_count = sum(1 for finding in findings if finding.level == "fail")
    warn_count = sum(1 for finding in findings if finding.level == "warn")
    status = "fail" if fail_count else "warn" if warn_count else "pass"

    lines = [
        "# ADS Doctor Report",
        "",
        f"- repo_root: {repo_root}",
        f"- generated_at: {datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"- status: {status}",
        f"- failures: {fail_count}",
        f"- warnings: {warn_count}",
        "",
        "## Findings",
    ]
    if not findings:
        lines.append("- none")
    else:
        for finding in findings:
            lines.append(f"- [{finding.level}] {finding.code}: {finding.message}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run health checks for an ADS workspace.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="ADS repository root to inspect")
    parser.add_argument("--output", help="Optional markdown output path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    findings = run_doctor(repo_root)
    report = render_report(repo_root, findings)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 1 if any(finding.level == "fail" for finding in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
