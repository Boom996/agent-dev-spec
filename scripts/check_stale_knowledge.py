#!/usr/bin/env python3
"""Check whether ADS memory objects are stale relative to review windows and linked artifacts."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
TASK_GLOBS = [".ai/tasks/**/*.md", "examples/case-task-*.md"]
HANDOFF_GLOBS = [".ai/handoffs/**/*.md", "examples/case-handoff-*.md"]
MEMORY_GLOBS = [".ai/memory/**/*.md", "examples/case-memory-*.md"]


@dataclass
class TaskRef:
    task_id: str
    updated_at: str
    memory_refs: list[str]


@dataclass
class HandoffRef:
    task_id: str
    updated_at: str
    memory_refs: list[str]


@dataclass
class MemoryRecord:
    path: Path
    memory_id: str
    freshness: str
    updated_at: str
    review_after: str
    related_paths: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def discover(globs: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in globs:
        files.extend(path for path in REPO_ROOT.glob(pattern) if path.is_file())
    return sorted(set(files))


def strip_code(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def extract_table_value(text: str, label: str) -> str:
    pattern = rf"\|\s*\*\*{re.escape(label)}\*\*\s*\|\s*(.*?)\s*\|"
    match = re.search(pattern, text)
    return strip_code(match.group(1).strip()) if match else ""


def find_section(text: str, title: str) -> str:
    pattern = rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_bullets(section: str) -> list[str]:
    items: list[str] = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            item = strip_code(line[2:].split(" — ", 1)[0].strip()) or ""
            if item and item != "无":
                items.append(item)
    return items


def parse_iso8601(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_duration(value: str) -> timedelta | None:
    match = re.match(r"^P(\d+)D$", value.strip())
    if not match:
        return None
    return timedelta(days=int(match.group(1)))


def parse_memory_refs(text: str) -> list[str]:
    return extract_bullets(find_section(text, "Memory refs（可选）"))


def parse_task(path: Path) -> TaskRef:
    text = read_text(path)
    return TaskRef(
        task_id=extract_table_value(text, "task_id") or path.stem,
        updated_at=extract_table_value(text, "updated_at"),
        memory_refs=parse_memory_refs(text),
    )


def parse_handoff(path: Path) -> HandoffRef:
    text = read_text(path)
    return HandoffRef(
        task_id=extract_table_value(text, "task_id") or path.stem,
        updated_at=extract_table_value(text, "updated_at"),
        memory_refs=parse_memory_refs(text),
    )


def parse_memory(path: Path) -> MemoryRecord:
    text = read_text(path)
    links = find_section(text, "Links")
    related_paths_match = re.search(r"\*\*related_paths\*\*：\n((?:\n?- .+)+)", links)
    return MemoryRecord(
        path=path,
        memory_id=extract_table_value(text, "memory_id") or path.stem,
        freshness=extract_table_value(text, "freshness") or "durable",
        updated_at=extract_table_value(text, "updated_at"),
        review_after=extract_table_value(text, "review_after"),
        related_paths=extract_bullets(related_paths_match.group(1)) if related_paths_match else [],
    )


def check_stale(tasks: list[TaskRef], handoffs: list[HandoffRef], memories: list[MemoryRecord], now: datetime) -> str:
    memory_by_path = {str(record.path.relative_to(REPO_ROOT)): record for record in memories}
    stale_lines: list[str] = []

    for memory in memories:
        updated = parse_iso8601(memory.updated_at)
        review_after = parse_duration(memory.review_after)
        rel = memory.path.relative_to(REPO_ROOT)

        if not updated:
            stale_lines.append(f"- {rel}: invalid or missing updated_at")
            continue

        if review_after and updated + review_after < now:
            stale_lines.append(f"- {rel}: review window exceeded (updated_at={memory.updated_at}, review_after={memory.review_after})")

        if "examples" not in str(rel):
            for related_path in memory.related_paths:
                if not (REPO_ROOT / related_path).exists():
                    stale_lines.append(f"- {rel}: related path does not exist -> {related_path}")

    for task in tasks:
        task_updated = parse_iso8601(task.updated_at)
        for ref in task.memory_refs:
            memory = memory_by_path.get(ref)
            if not memory:
                stale_lines.append(f"- task:{task.task_id}: referenced memory missing -> {ref}")
                continue
            memory_updated = parse_iso8601(memory.updated_at)
            if memory.freshness == "operational" and task_updated and memory_updated and task_updated > memory_updated:
                stale_lines.append(
                    f"- {ref}: older than referencing task {task.task_id} (task updated_at={task.updated_at}, memory updated_at={memory.updated_at})"
                )

    for handoff in handoffs:
        handoff_updated = parse_iso8601(handoff.updated_at)
        for ref in handoff.memory_refs:
            memory = memory_by_path.get(ref)
            if not memory:
                stale_lines.append(f"- handoff:{handoff.task_id}: referenced memory missing -> {ref}")
                continue
            memory_updated = parse_iso8601(memory.updated_at)
            if memory.freshness == "operational" and handoff_updated and memory_updated and handoff_updated > memory_updated:
                stale_lines.append(
                    f"- {ref}: older than referencing handoff {handoff.task_id} (handoff updated_at={handoff.updated_at}, memory updated_at={memory.updated_at})"
                )

    lines = [
        "# ADS Stale Knowledge Report",
        "",
        f"- generated_at: {now.isoformat().replace('+00:00', 'Z')}",
        f"- total_memories: {len(memories)}",
        f"- stale_findings: {len(stale_lines)}",
        "",
        "## Findings",
    ]
    lines.extend(stale_lines or ["- none"])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check stale ADS knowledge and memory objects.")
    parser.add_argument("--output", help="Optional markdown output path")
    args = parser.parse_args()

    tasks = [parse_task(path) for path in discover(TASK_GLOBS)]
    handoffs = [parse_handoff(path) for path in discover(HANDOFF_GLOBS)]
    memories = [parse_memory(path) for path in discover(MEMORY_GLOBS)]
    now = datetime.now(timezone.utc)
    report = check_stale(tasks, handoffs, memories, now)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
