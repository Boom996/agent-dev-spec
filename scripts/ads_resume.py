#!/usr/bin/env python3
"""Generate a resume-oriented ADS context summary from task and handoff artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_code(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def extract_table_value(text: str, label: str) -> str | None:
    pattern = rf"\|\s*\*\*{re.escape(label)}\*\*\s*\|\s*(.*?)\s*\|"
    match = re.search(pattern, text)
    return strip_code(match.group(1).strip()) if match else None


def find_section(text: str, title: str) -> str:
    pattern = rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_checkbox_texts(section: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^- \[[ xX]\] (.+)$", section, flags=re.MULTILINE)]


def extract_subsection_bullets(section: str, label: str) -> list[str]:
    lines = section.splitlines()
    label_prefix = f"- **{label}**"
    active = False
    items: list[str] = []
    for line in lines:
        if line.startswith(label_prefix):
            active = True
            continue
        if active and line.startswith("- **"):
            break
        if active and line.strip().startswith("- "):
            value = strip_code(line.strip()[2:].split(" — ", 1)[0].strip()) or ""
            if value:
                items.append(value)
    return items


def extract_table_first_column(section: str) -> list[str]:
    rows: list[str] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "------" in line or "路径" in line:
            continue
        parts = [part.strip() for part in line.split("|")[1:-1]]
        if parts and parts[0]:
            rows.append(strip_code(parts[0]) or "")
    return rows


def parse_memory_refs(text: str) -> list[str]:
    section = find_section(text, "Memory refs（可选）")
    refs: list[str] = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            item = strip_code(line[2:].split(" — ", 1)[0].strip()) or ""
            if item and item != "无":
                refs.append(item)
    return refs


def infer_handoff(task_id: str, repo_root: Path) -> Path | None:
    candidate = repo_root / ".ai" / "handoffs" / f"{task_id}.md"
    return candidate if candidate.exists() else None


def infer_escalation(task_id: str, repo_root: Path) -> Path | None:
    candidate = repo_root / ".ai" / "escalations" / f"{task_id}.md"
    return candidate if candidate.exists() else None


def load_identity(identity_path: Path | None) -> dict:
    if not identity_path or not identity_path.exists():
        return {}
    return json.loads(identity_path.read_text(encoding="utf-8"))


def load_constitution(repo_root: Path) -> tuple[str, list[str]]:
    path = repo_root / ".agent" / "constitution.md"
    if not path.exists():
        return "", []
    text = read_text(path)
    mission = ""
    for line in find_section(text, "Mission").splitlines():
        line = line.strip()
        if line:
            mission = line
            break
    principles = [line.strip()[2:].strip() for line in find_section(text, "Non-Negotiable Principles").splitlines() if line.strip().startswith("- ")]
    return mission, principles


def load_change_info(parent_change_id: str, repo_root: Path) -> dict[str, object] | None:
    proposal_path = repo_root / ".ai" / "changes" / parent_change_id / "proposal.md"
    if not proposal_path.exists():
        return None
    text = read_text(proposal_path)
    scope_section = find_section(text, "Scope")
    impact_section = find_section(text, "Impact")
    return {
        "change_id": parent_change_id,
        "title": extract_table_value(text, "title") or "",
        "status": extract_table_value(text, "status") or "",
        "impact_paths": [line[2:].strip() for line in scope_section.splitlines() if line.strip().startswith("- ")],
        "related_tasks": [line[2:].strip() for line in impact_section.splitlines() if line.strip().startswith("- ")],
    }


def load_escalation_info(task_id: str, repo_root: Path) -> dict[str, str] | None:
    path = infer_escalation(task_id, repo_root)
    if not path or not path.exists():
        return None
    text = read_text(path)
    current_block = ""
    for line in find_section(text, "Current Block").splitlines():
        line = line.strip()
        if line.startswith("**当前阻塞**"):
            current_block = line.split("：", 1)[-1].strip()
            break
    return {
        "path": str(path.relative_to(repo_root)),
        "escalation_type": extract_table_value(text, "escalation_type") or "unknown",
        "status": extract_table_value(text, "status") or "unknown",
        "decision_owner": extract_table_value(text, "decision_owner") or "unknown",
        "current_block": current_block or "unknown",
    }


def build_resume(task_path: Path, handoff_path: Path | None, identity_path: Path | None, project_name: str | None, repo_root: Path = REPO_ROOT) -> str:
    task_text = read_text(task_path)
    task_id = extract_table_value(task_text, "task_id") or task_path.stem
    owner_role = extract_table_value(task_text, "owner_role") or "unknown"
    priority = extract_table_value(task_text, "priority") or "unknown"
    trace_id = extract_table_value(task_text, "trace_id") or "unknown"
    updated_at = extract_table_value(task_text, "updated_at") or "unknown"
    handoff_to = extract_table_value(task_text, "handoff_to") or "unknown"
    coordination_model = extract_table_value(task_text, "coordination_model") or "direct"
    autonomy_level = extract_table_value(task_text, "autonomy_level") or "unspecified"
    approval_owner = extract_table_value(task_text, "approval_owner") or "unknown"
    parent_change_id = extract_table_value(task_text, "parent_change_id") or ""

    single_writer = find_section(task_text, "单写者范围")
    acceptance = find_section(task_text, "验收标准（可勾选）")
    related_paths = find_section(task_text, "相关路径")
    locked_paths = extract_subsection_bullets(single_writer, "locked_paths")
    forbidden_paths = extract_subsection_bullets(single_writer, "forbidden_paths")
    acceptance_items = extract_checkbox_texts(acceptance)
    related_path_items = extract_table_first_column(related_paths)
    memory_refs = parse_memory_refs(task_text)

    identity = load_identity(identity_path)
    if not project_name:
        project_name = identity.get("project_name", repo_root.name)
    verify_commands = [str(v) for v in identity.get("standard_verify_commands", {}).values()]

    mission, principles = load_constitution(repo_root)
    change_info = load_change_info(parent_change_id, repo_root) if parent_change_id else None
    escalation_info = load_escalation_info(task_id, repo_root)

    if handoff_path is None:
        handoff_path = infer_handoff(task_id, repo_root)

    if handoff_path and handoff_path.exists():
        handoff_text = read_text(handoff_path)
        handoff_status = extract_table_value(handoff_text, "handoff_status") or "unknown"
        blocked_reason = extract_table_value(handoff_text, "blocked_reason") or ""
        spec_update_status = extract_table_value(handoff_text, "spec_update_status") or "unknown"
        current_status_match = re.search(r"\*\*当前状态\*\*[:：](.*)", handoff_text)
        next_actor_match = re.search(r"\*\*下一棒\*\*[:：](.*)", handoff_text)
        next_action_match = re.search(r"\*\*建议下一动作\*\*[:：](.*)", handoff_text)
        current_status = current_status_match.group(1).strip() if current_status_match else "unknown"
        next_actor = next_actor_match.group(1).strip() if next_actor_match else handoff_to
        next_action = next_action_match.group(1).strip() if next_action_match else "Review latest handoff and continue the task."
        memory_refs.extend(parse_memory_refs(handoff_text))
    else:
        handoff_status = "missing"
        blocked_reason = ""
        spec_update_status = "unknown"
        current_status = "No handoff found. Resume from task contract and current worktree."
        next_actor = handoff_to
        next_action = "Reconstruct current state from the task and repository diff before making edits."

    lines = [
        f"# ADS Resume — {task_id}",
        "",
        f"- project: {project_name}",
        f"- task_id: {task_id}",
        f"- owner_role: {owner_role}",
        f"- priority: {priority}",
        f"- trace_id: {trace_id}",
        f"- updated_at: {updated_at}",
        "",
        "## Mission",
        mission or "unknown",
    ]

    if principles:
        lines.append("")
        lines.append("## Non-Negotiable Principles")
        lines.extend(f"- {item}" for item in principles[:5])

    if change_info:
        lines.append("")
        lines.append("## Active Change")
        lines.append(f"- change_id: {change_info['change_id']}")
        lines.append(f"- title: {change_info['title'] or 'unknown'}")
        lines.append(f"- status: {change_info['status'] or 'unknown'}")
        impact_paths = change_info["impact_paths"] if isinstance(change_info["impact_paths"], list) else []
        related_tasks = change_info["related_tasks"] if isinstance(change_info["related_tasks"], list) else []
        if impact_paths:
            lines.append("- impact_paths:")
            lines.extend(f"  {item}" for item in impact_paths)
        if related_tasks:
            lines.append("- related_tasks:")
            lines.extend(f"  {item}" for item in related_tasks)

    lines.extend(
        [
            "",
            "## Task Snapshot",
            f"- handoff_to: {handoff_to}",
            f"- coordination_model: {coordination_model}",
            f"- autonomy_level: {autonomy_level}",
            f"- approval_owner: {approval_owner}",
            "",
            "### Acceptance",
        ]
    )
    lines.extend(f"- {item}" for item in (acceptance_items or ["none declared"]))
    lines.append("")
    lines.append("### Locked Paths")
    lines.extend(f"- {item}" for item in (locked_paths or ["none declared"]))
    lines.append("")
    lines.append("### Forbidden Paths")
    lines.extend(f"- {item}" for item in (forbidden_paths or ["none declared"]))
    lines.append("")
    lines.append("### Related Paths")
    lines.extend(f"- {item}" for item in (related_path_items or ["none declared"]))

    lines.extend(
        [
            "",
            "## Latest Handoff",
            f"- handoff_status: {handoff_status}",
            f"- spec_update_status: {spec_update_status}",
            f"- current_status: {current_status}",
        ]
    )
    if blocked_reason:
        lines.append(f"- blocked_reason: {blocked_reason}")
    lines.append(f"- next_actor: {next_actor}")
    lines.append(f"- next_action: {next_action}")

    lines.append("")
    lines.append("## Memory Refs")
    lines.extend(f"- {item}" for item in (sorted(set(memory_refs)) or ["none"]))

    if escalation_info:
        lines.extend(
            [
                "",
                "## Active Escalation",
                f"- path: {escalation_info['path']}",
                f"- escalation_type: {escalation_info['escalation_type']}",
                f"- status: {escalation_info['status']}",
                f"- decision_owner: {escalation_info['decision_owner']}",
                f"- current_block: {escalation_info['current_block']}",
            ]
        )

    lines.append("")
    lines.append("## Resume Checklist")
    lines.append("- Re-open README.md and the task contract before editing.")
    lines.append("- Stay inside LOCKED_PATHS and avoid FORBIDDEN_PATHS.")
    if verify_commands:
        lines.append("- Standard verify commands:")
        lines.extend(f"  {command}" for command in verify_commands)
    else:
        lines.append("- No standard verify commands declared in identity.json.")
    lines.append("- Refresh or rewrite the handoff when context changes materially.")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a resume-oriented ADS context summary.")
    parser.add_argument("task", help="Path to the task markdown file")
    parser.add_argument("--handoff", help="Optional handoff markdown file")
    parser.add_argument(
        "--identity",
        default=str(REPO_ROOT / ".agent" / "identity.json.example"),
        help="Path to identity.json or example identity file",
    )
    parser.add_argument("--project-name", help="Optional project name override")
    parser.add_argument("--output", help="Write resume summary to file instead of stdout")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root used to resolve ADS files")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    task_path = Path(args.task).resolve()
    task_text = read_text(task_path)
    task_id = extract_table_value(task_text, "task_id") or task_path.stem
    handoff_path = Path(args.handoff).resolve() if args.handoff else infer_handoff(task_id, repo_root)
    identity_path = Path(args.identity).resolve() if args.identity else None

    resume_text = build_resume(task_path, handoff_path, identity_path, args.project_name, repo_root=repo_root)
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(resume_text, encoding="utf-8")
    else:
        print(resume_text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
