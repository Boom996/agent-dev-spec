#!/usr/bin/env python3
"""Build a minimal ADS knowledge pack from task, handoff, and memory objects."""

from __future__ import annotations

import argparse
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


def extract_bullets(section: str) -> list[str]:
    items: list[str] = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            item = line[2:].split(" — ", 1)[0].strip()
            item = strip_code(item) or ""
            if item and item != "无":
                items.append(item)
    return items


def parse_memory_refs(text: str) -> list[str]:
    section = find_section(text, "Memory refs（可选）")
    return extract_bullets(section)


def parse_memory(path: Path) -> dict:
    text = read_text(path)
    summary = find_section(text, "Summary")
    details = find_section(text, "Details")
    links = find_section(text, "Links")
    related_tasks_match = re.search(r"\*\*related_tasks\*\*：\n((?:\n?- .+)+)", links)
    related_paths_match = re.search(r"\*\*related_paths\*\*：\n((?:\n?- .+)+)", links)
    return {
        "path": path,
        "memory_id": extract_table_value(text, "memory_id") or path.stem,
        "type": extract_table_value(text, "type") or "unknown",
        "title": extract_table_value(text, "title") or path.stem,
        "scope": extract_table_value(text, "scope") or "unknown",
        "owner": extract_table_value(text, "owner") or "unknown",
        "review_after": extract_table_value(text, "review_after") or "",
        "trace_id": extract_table_value(text, "trace_id") or "unknown",
        "updated_at": extract_table_value(text, "updated_at") or "unknown",
        "summary": summary,
        "details": details,
        "related_tasks": extract_bullets(related_tasks_match.group(1)) if related_tasks_match else [],
        "related_paths": extract_bullets(related_paths_match.group(1)) if related_paths_match else [],
    }


def resolve_memory_paths(task_path: Path, handoff_path: Path | None, explicit_paths: list[str]) -> list[Path]:
    refs: list[str] = []
    refs.extend(explicit_paths)
    refs.extend(parse_memory_refs(read_text(task_path)))
    if handoff_path and handoff_path.exists():
        refs.extend(parse_memory_refs(read_text(handoff_path)))

    resolved: list[Path] = []
    for ref in refs:
        candidate = (REPO_ROOT / ref).resolve()
        if candidate.exists():
            resolved.append(candidate)
    return sorted(set(resolved))


def build_pack(task_path: Path, handoff_path: Path | None, memory_paths: list[Path]) -> str:
    task_text = read_text(task_path)
    task_id = extract_table_value(task_text, "task_id") or task_path.stem
    owner_role = extract_table_value(task_text, "owner_role") or "unknown"
    trace_id = extract_table_value(task_text, "trace_id") or "unknown"
    acceptance = find_section(task_text, "验收标准（可勾选）")
    related_paths = find_section(task_text, "相关路径")

    acceptance_items = [
        match.group(1).strip()
        for match in re.finditer(r"^- \[[ xX]\] (.+)$", acceptance, flags=re.MULTILINE)
    ]
    related_path_items = []
    for line in related_paths.splitlines():
        if line.strip().startswith("|") and "------" not in line and "路径" not in line:
            parts = [part.strip() for part in line.split("|")[1:-1]]
            if parts and parts[0]:
                related_path_items.append(strip_code(parts[0]) or "")

    memories = [parse_memory(path) for path in memory_paths]
    lines = [
        f"# ADS Knowledge Pack — {task_id}",
        "",
        f"- task_id: {task_id}",
        f"- owner_role: {owner_role}",
        f"- trace_id: {trace_id}",
        "",
        "## Acceptance Snapshot",
    ]
    lines.extend(f"- {item}" for item in (acceptance_items or ["none"]))
    lines.append("")
    lines.append("## Related Paths")
    lines.extend(f"- {item}" for item in (related_path_items or ["none"]))

    if handoff_path and handoff_path.exists():
        handoff_text = read_text(handoff_path)
        status_match = re.search(r"\*\*当前状态\*\*：(.*)", handoff_text)
        lines.append("")
        lines.append("## Handoff Status")
        lines.append(status_match.group(1).strip() if status_match else "none")

    lines.append("")
    lines.append("## Memory Objects")
    if not memories:
        lines.append("- none")
    for memory in memories:
        lines.append(f"- {memory['memory_id']} ({memory['type']}) — {memory['title']}")
        lines.append(
            f"  owner: {memory['owner']}, scope: {memory['scope']}, updated_at: {memory['updated_at']}, review_after: {memory['review_after'] or 'n/a'}"
        )
        if memory["summary"]:
            lines.append(f"  summary: {memory['summary'].replace(chr(10), ' ')}")
        if memory["related_paths"]:
            lines.append(f"  related_paths: {', '.join(memory['related_paths'])}")

    lines.append("")
    lines.append("## Source Files")
    lines.append(f"- {task_path.relative_to(REPO_ROOT)}")
    if handoff_path and handoff_path.exists():
        lines.append(f"- {handoff_path.relative_to(REPO_ROOT)}")
    lines.extend(f"- {path.relative_to(REPO_ROOT)}" for path in memory_paths)
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an ADS knowledge pack.")
    parser.add_argument("task", help="Task markdown file path")
    parser.add_argument("--handoff", help="Optional handoff markdown file path")
    parser.add_argument("--memory", action="append", default=[], help="Optional memory object path, repeatable")
    parser.add_argument("--output", help="Output file path. Defaults to stdout.")
    args = parser.parse_args()

    task_path = Path(args.task).resolve()
    handoff_path = Path(args.handoff).resolve() if args.handoff else None
    memory_paths = resolve_memory_paths(task_path, handoff_path, args.memory)
    pack = build_pack(task_path, handoff_path, memory_paths)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(pack, encoding="utf-8")
    else:
        print(pack, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
