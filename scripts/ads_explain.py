#!/usr/bin/env python3
"""Generate a user-facing ADS first-run brief for a repository."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_section(text: str, title: str) -> str:
    pattern = rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def first_nonempty_line(section: str) -> str:
    for line in section.splitlines():
        value = line.strip()
        if value:
            return value
    return ""


def discover(repo_root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in repo_root.glob(pattern) if path.is_file() and path.name != ".gitkeep")


def infer_workspace_status(repo_root: Path) -> str:
    required = [
        repo_root / "README_AGENT.md",
        repo_root / ".ai" / "START_HERE.md",
        repo_root / ".agent" / "constitution.md",
    ]
    present = sum(1 for path in required if path.exists())
    if present == len(required):
        return "ads_ready"
    if present:
        return "partial_ads"
    return "needs_bootstrap"


def load_project_name(repo_root: Path) -> str:
    identity = repo_root / ".agent" / "identity.json"
    if identity.exists():
        match = re.search(r'"project_name"\s*:\s*"([^"]+)"', read_text(identity))
        if match:
            return match.group(1)
    return repo_root.name


def load_docs_entry(repo_root: Path) -> dict[str, str]:
    identity = repo_root / ".agent" / "identity.json"
    if not identity.exists():
        return {}
    text = read_text(identity)
    docs_entry_match = re.search(r'"docs_entry"\s*:\s*\{(.*?)\n\s*\}', text, flags=re.DOTALL)
    if not docs_entry_match:
        return {}
    block = docs_entry_match.group(1)
    entries: dict[str, str] = {}
    for key in ("readme_agent", "ai_context", "project_brief", "start_here"):
        match = re.search(rf'"{key}"\s*:\s*"([^"]+)"', block)
        if match:
            entries[key] = match.group(1)
    return entries


def load_mission(repo_root: Path) -> str:
    constitution = repo_root / ".agent" / "constitution.md"
    if not constitution.exists():
        return "unknown"
    mission = first_nonempty_line(find_section(read_text(constitution), "Mission"))
    if "一句话" in mission or "存在的意义" in mission:
        return "unknown"
    return mission or "unknown"


def load_current_stage(repo_root: Path) -> str:
    start_here = repo_root / ".ai" / "START_HERE.md"
    if not start_here.exists():
        return "unknown"
    stage = first_nonempty_line(find_section(read_text(start_here), "当前阶段目标"))
    return stage or "unknown"


def build_explanation(repo_root: Path = REPO_ROOT) -> str:
    workspace_status = infer_workspace_status(repo_root)
    project_name = load_project_name(repo_root)
    docs_entry = load_docs_entry(repo_root)
    mission = load_mission(repo_root)
    current_stage = load_current_stage(repo_root)
    active_tasks = discover(repo_root, ".ai/tasks/active/*.md")
    handoffs = discover(repo_root, ".ai/handoffs/*.md")
    escalations = discover(repo_root, ".ai/escalations/*.md")
    requests = discover(repo_root, ".ai/requests/*.md")
    qas = discover(repo_root, ".ai/qa/*.md")

    lines = [
        "# ADS Project Brief",
        "",
        f"- project: {project_name}",
        f"- workspace_status: {workspace_status}",
        f"- current_stage: {current_stage}",
        "",
        "## Mission",
        mission,
        "",
        "## Why ADS Exists Here",
        "ADS is the repo-native control plane for this project: tasks, handoffs, evidence, governance, and recovery should live in files instead of chat history alone.",
        "",
        "## Collaboration Snapshot",
        f"- active_tasks: {len(active_tasks)}",
        f"- handoffs: {len(handoffs)}",
        f"- active_escalations: {len(escalations)}",
        f"- shared_requests: {len(requests)}",
        f"- qa_records: {len(qas)}",
        "",
        "## Read This First",
        "- README_AGENT.md",
        "- .ai/START_HERE.md" if (repo_root / ".ai" / "START_HERE.md").exists() else "- .ai/START_HERE.md (missing)",
        "- .agent/constitution.md" if (repo_root / ".agent" / "constitution.md").exists() else "- .agent/constitution.md (missing)",
    ]
    if docs_entry.get("project_brief"):
        lines.append(f"- {docs_entry['project_brief']}")
    if docs_entry.get("ai_context"):
        lines.append(f"- {docs_entry['ai_context']}")

    if active_tasks:
        lines.append(f"- {active_tasks[0].relative_to(repo_root).as_posix()}")
    if handoffs:
        lines.append(f"- {handoffs[0].relative_to(repo_root).as_posix()}")

    lines.extend(["", "## Next Commands"])
    if workspace_status == "needs_bootstrap":
        lines.append("- Run ADS bootstrap before expecting structured collaboration.")
        lines.append("- Suggested: `python3 scripts/ads_init.py /path/to/your-project` or `python3 scripts/ads_adopt.py /path/to/your-project --apply`")
    else:
        lines.append("- `python3 scripts/ads_doctor.py`")
        lines.append("- `python3 scripts/validate_ads.py`")
        lines.append("- `python3 scripts/ads_health_report.py`")
        if active_tasks:
            lines.append(f"- `python3 scripts/ads_resume.py {active_tasks[0].relative_to(repo_root).as_posix()}`")

    lines.extend(
        [
            "",
            "## User Guidance",
            "- If you are new to the repo, understand the mission and current stage before opening code.",
            "- If you are continuing work, resume from the active task and latest handoff instead of reconstructing context from chat.",
            "- If the work is blocked, check `.ai/escalations/` before guessing.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root to explain")
    parser.add_argument("--output", help="Optional output markdown path")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    text = build_explanation(repo_root)
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
