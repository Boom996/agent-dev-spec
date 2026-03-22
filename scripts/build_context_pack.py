#!/usr/bin/env python3
"""Build an ADS CLI context pack from a task and optional handoff."""

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
            items.append(strip_code(line.strip()[2:].split(" — ", 1)[0].strip()) or "")
    return [item for item in items if item]


def extract_checkbox_texts(section: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^- \[[ xX]\] (.+)$", section, flags=re.MULTILINE)]


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


def load_constitution_mission(repo_root: Path) -> str:
    """Extract first non-empty line of Mission section from constitution.md."""
    constitution_path = repo_root / ".agent" / "constitution.md"
    if not constitution_path.exists():
        return ""
    text = read_text(constitution_path)
    mission = find_section(text, "Mission")
    for line in mission.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def load_change_info(parent_change_id: str, repo_root: Path) -> tuple[str, str] | None:
    """Return (title, status) from change proposal, or None if not found."""
    proposal_path = repo_root / ".ai" / "changes" / parent_change_id / "proposal.md"
    if not proposal_path.exists():
        return None
    text = read_text(proposal_path)
    title = extract_table_value(text, "title") or ""
    status = extract_table_value(text, "status") or ""
    return (title, status) if title else None


def _truncate_section(lines: list[str], marker: str, max_items: int) -> list[str]:
    """Truncate a section starting with marker to at most max_items bullet lines."""
    result = []
    in_section = False
    item_count = 0
    for line in lines:
        if line == marker:
            in_section = True
            result.append(line)
            item_count = 0
            continue
        if in_section:
            if line.startswith("[") and line.endswith("]"):
                in_section = False
                result.append(line)
                continue
            if line.startswith("- "):
                item_count += 1
                if item_count <= max_items:
                    result.append(line)
                # else skip
                continue
        result.append(line)
    return result


def infer_handoff(task_id: str) -> Path | None:
    candidate = REPO_ROOT / ".ai" / "handoffs" / f"{task_id}.md"
    return candidate if candidate.exists() else None


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


def load_identity(identity_path: Path | None) -> dict:
    if not identity_path or not identity_path.exists():
        return {}
    return json.loads(identity_path.read_text(encoding="utf-8"))


def build_pack(task_path: Path, handoff_path: Path | None, identity_path: Path | None, project_name: str | None, mode: str = "default") -> str:
    task_text = read_text(task_path)
    task_id = extract_table_value(task_text, "task_id") or task_path.stem
    owner_role = extract_table_value(task_text, "owner_role") or "unknown"
    trace_id = extract_table_value(task_text, "trace_id") or "unknown"

    single_writer = find_section(task_text, "单写者范围")
    acceptance = find_section(task_text, "验收标准（可勾选）")
    related_paths = find_section(task_text, "相关路径")

    locked_paths = extract_subsection_bullets(single_writer, "locked_paths")
    forbidden_paths = extract_subsection_bullets(single_writer, "forbidden_paths")
    acceptance_items = extract_checkbox_texts(acceptance)
    related_path_items = extract_table_first_column(related_paths)
    memory_refs = parse_memory_refs(task_text)

    identity = load_identity(identity_path)
    verify_commands = [str(v) for v in identity.get("standard_verify_commands", {}).values()]
    if not project_name:
        project_name = identity.get("project_name", "unknown-project")

    lines = [
        f"# ADS CLI 上下文包 — {task_id}",
        "# 用途：粘贴到 Codex CLI / 无状态 Agent 单轮任务（勿当生产密钥使用）",
        "",
        f"[PROJECT] {project_name}",
        "[ADS] Agent Development Specification",
        f"[TASK_ID] {task_id}",
        f"[OWNER_ROLE] {owner_role}",
        f"[TRACE_ID] {trace_id}",
        "[LOCKED_PATHS]",
    ]
    lines.extend(f"- {item}" for item in (locked_paths or ["(none declared)"]))
    lines.append("[FORBIDDEN_PATHS]")
    lines.extend(f"- {item}" for item in (forbidden_paths or ["(none declared)"]))
    lines.append("[ACCEPTANCE]")
    lines.extend(f"- {item}" for item in (acceptance_items or ["(none declared)"]))
    lines.append("[RELATED_PATHS]")
    lines.extend(f"- {item}" for item in (related_path_items or ["(none declared)"]))
    lines.append("[VERIFY]")
    lines.extend(verify_commands or ["(no standard verify commands found)"])
    lines.append("[CONTEXT_FILES]")
    lines.append(f"- {task_path.relative_to(REPO_ROOT)} (full task contract)")
    lines.append("- README_AGENT.md (repo root)")

    if handoff_path and handoff_path.exists():
        handoff_text = read_text(handoff_path)
        status_match = re.search(r"\*\*当前状态\*\*：(.*)", handoff_text)
        memory_refs.extend(parse_memory_refs(handoff_text))
        lines.append(f"- {handoff_path.relative_to(REPO_ROOT)} (latest handoff)")
        lines.append("[HANDOFF_STATUS]")
        lines.append(status_match.group(1).strip() if status_match else "(status not found)")

    if memory_refs:
        lines.append("[MEMORY_REFS]")
        lines.extend(f"- {item}" for item in sorted(set(memory_refs)))

    if mode == "cli":
        mission = load_constitution_mission(REPO_ROOT)
        if mission:
            lines.append("[CONSTITUTION]")
            lines.append(mission)

        parent_change_id = extract_table_value(task_text, "parent_change_id")
        if parent_change_id:
            change_info = load_change_info(parent_change_id, REPO_ROOT)
            if change_info:
                title, status = change_info
                lines.append("[CHANGE_INFO]")
                lines.append(f"change: {parent_change_id}")
                lines.append(f"title: {title}")
                lines.append(f"status: {status}")

        coordination_model = extract_table_value(task_text, "coordination_model")
        if coordination_model:
            lines.append("[COORDINATION]")
            lines.append(coordination_model)

        # Enforce ≤120 lines
        if len(lines) > 118:  # reserve 2 for [OUTPUT] lines
            lines = _truncate_section(lines, "[RELATED_PATHS]", 5)
            lines = _truncate_section(lines, "[MEMORY_REFS]", 5)

    lines.append("[OUTPUT]")
    lines.append("- Implement or review only within LOCKED_PATHS")
    lines.append("- Summarize files changed + verification output")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an ADS CLI context pack.")
    parser.add_argument("task", help="Path to the task markdown file")
    parser.add_argument("--handoff", help="Optional handoff markdown file")
    parser.add_argument(
        "--identity",
        default=str(REPO_ROOT / ".agent" / "identity.json.example"),
        help="Path to identity.json or example identity file",
    )
    parser.add_argument("--project-name", help="Optional project name override")
    parser.add_argument("--output", help="Write pack to file instead of stdout")
    parser.add_argument("--mode", choices=["default", "cli"], default="default", help="Output mode")
    args = parser.parse_args()

    task_path = Path(args.task).resolve()
    task_text = read_text(task_path)
    task_id = extract_table_value(task_text, "task_id") or task_path.stem
    handoff_path = Path(args.handoff).resolve() if args.handoff else infer_handoff(task_id)
    identity_path = Path(args.identity).resolve() if args.identity else None

    pack = build_pack(task_path, handoff_path, identity_path, args.project_name, mode=args.mode)
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(pack, encoding="utf-8")
    else:
        print(pack, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
