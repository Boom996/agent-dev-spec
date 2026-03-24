#!/usr/bin/env python3
"""Capture ADS Innovation Briefs from task execution context."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


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


def parse_task(task_path: Path) -> dict[str, str]:
    text = read_text(task_path)
    return {
        "task_id": extract_table_value(text, "task_id") or task_path.stem,
        "owner_role": extract_table_value(text, "owner_role") or "unknown",
        "parent_change_id": extract_table_value(text, "parent_change_id") or "",
    }


def next_innovation_id(directory: Path, today: str) -> str:
    existing_numbers: list[int] = []
    pattern = re.compile(rf"^INV-{re.escape(today)}-(\d{{3}})$")
    if directory.exists():
        for path in directory.glob("INV-*.md"):
            match = pattern.match(path.stem)
            if match:
                existing_numbers.append(int(match.group(1)))
    next_number = max(existing_numbers, default=0) + 1
    return f"INV-{today}-{next_number:03d}"


def render_innovation_brief(
    innovation_id: str,
    title: str,
    submitted_by: str,
    submitted_at: str,
    context_task: str,
    context_change: str,
    summary: str,
    trigger: str,
    judgement: str,
    urgency: str = "medium",
    impact_estimate: str = "medium",
    status: str = "proposed",
) -> str:
    lines = [
        f"# Innovation Brief — `{innovation_id}`",
        "",
        "> 任务执行过程中产生的创新想法捕获。保存为 `.ai/innovations/<innovation-id>.md`。",
        "> 低门槛提交，不阻断当前任务；正式变更通过 Change Proposal 启动。",
        "",
        "## Metadata",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| **innovation_id** | `{innovation_id}` |",
        f"| **title** | {title} |",
        f"| **submitted_by** | `{submitted_by}` |",
        f"| **submitted_at** | `{submitted_at}` |",
        f"| **context_task** | `{context_task}` |",
        f"| **context_change** | `{context_change}` |" if context_change else "| **context_change** |  |",
        f"| **status** | `{status}` |",
        f"| **urgency** | `{urgency}` |",
        f"| **impact_estimate** | `{impact_estimate}` |",
        "| **triage_by** | `architect` |",
        f"| **triage_deadline** | `{submitted_at[:10]}` |",
        "| **promoted_to** |  |",
        "",
        "## 想法摘要",
        "",
        summary,
        "",
        "## 触发背景",
        "",
        trigger,
        "",
        "## 提交者的初步判断",
        "",
        judgement,
        "",
    ]
    return "\n".join(lines)


def capture_innovation(
    task_path: Path,
    title: str,
    summary: str,
    trigger: str,
    judgement: str,
    output_path: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> Path:
    task = parse_task(task_path)
    submitted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if output_path is None:
        directory = repo_root / ".ai" / "innovations"
        directory.mkdir(parents=True, exist_ok=True)
        innovation_id = next_innovation_id(directory, submitted_at[:10].replace("-", ""))
        output_path = directory / f"{innovation_id}.md"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        stem_match = re.search(r"(INV-\d{8}-\d{3})", output_path.stem)
        innovation_id = stem_match.group(1) if stem_match else next_innovation_id(output_path.parent, submitted_at[:10].replace("-", ""))

    content = render_innovation_brief(
        innovation_id=innovation_id,
        title=title,
        submitted_by=task["owner_role"],
        submitted_at=submitted_at,
        context_task=task["task_id"],
        context_change=task["parent_change_id"],
        summary=summary,
        trigger=trigger,
        judgement=judgement,
    )
    output_path.write_text(content, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture an ADS Innovation Brief from a task context.")
    parser.add_argument("task_path", help="Path to the ADS task markdown file")
    parser.add_argument("--title", required=True, help="Innovation title")
    parser.add_argument("--summary", required=True, help="Innovation summary")
    parser.add_argument("--trigger", required=True, help="What triggered this innovation")
    parser.add_argument("--judgement", required=True, help="Submitter's initial judgement")
    parser.add_argument("--output", help="Optional output path")
    args = parser.parse_args()

    task_path = Path(args.task_path).resolve()
    output_path = Path(args.output).resolve() if args.output else None
    written = capture_innovation(
        task_path,
        title=args.title,
        summary=args.summary,
        trigger=args.trigger,
        judgement=args.judgement,
        output_path=output_path,
        repo_root=REPO_ROOT,
    )
    print(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
