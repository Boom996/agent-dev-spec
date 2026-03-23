#!/usr/bin/env python3
"""Infer impacted specs for an ADS task and optionally write spec-delta."""

from __future__ import annotations

import argparse
import re
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


def find_section(text: str, title: str) -> str:
    pattern = rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_related_paths(task_text: str) -> list[str]:
    section = find_section(task_text, "相关路径")
    paths: list[str] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "------" in line or "路径" in line:
            continue
        parts = [part.strip() for part in line.split("|")[1:-1]]
        if parts and parts[0]:
            value = strip_code(parts[0]) or ""
            if value:
                paths.append(value)
    return paths


def parse_simple_frontmatter(text: str) -> dict[str, list[str] | str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict[str, list[str] | str] = {}
    current_list_key: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("  - ") and current_list_key:
            existing = data.setdefault(current_list_key, [])
            if isinstance(existing, list):
                existing.append(line[4:].strip())
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if value:
                data[key] = value
                current_list_key = None
            else:
                data[key] = []
                current_list_key = key
    return data


def parse_task(task_path: Path) -> dict[str, object]:
    text = read_text(task_path)
    return {
        "task_id": extract_table_value(text, "task_id") or task_path.stem,
        "parent_change_id": extract_table_value(text, "parent_change_id") or "",
        "trace_id": extract_table_value(text, "trace_id") or "unknown",
        "updated_at": extract_table_value(text, "updated_at") or "unknown",
        "related_paths": extract_related_paths(text),
    }


def tokenise(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-zA-Z0-9]+", value.lower()) if len(token) >= 3}


def discover_specs(repo_root: Path) -> list[dict[str, object]]:
    specs: list[dict[str, object]] = []
    for path in sorted(repo_root.glob(".ai/specs/**/*.md")):
        text = read_text(path)
        frontmatter = parse_simple_frontmatter(text)
        title_match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
        title = title_match.group(1).strip() if title_match else path.stem
        specs.append(
            {
                "path": path,
                "frontmatter": frontmatter,
                "title": title,
                "tokens": tokenise(path.stem) | tokenise(title),
            }
        )
    return specs


def infer_impacted_specs(task: dict[str, object], changed_paths: list[str], repo_root: Path = REPO_ROOT) -> list[dict[str, str]]:
    task_id = str(task["task_id"])
    parent_change_id = str(task["parent_change_id"])
    path_hints = set(changed_paths or [str(path) for path in task["related_paths"]])
    hint_tokens: set[str] = set()
    for path in path_hints:
        hint_tokens |= tokenise(path)

    impacted: dict[str, dict[str, str]] = {}
    direct_spec_changes = {path for path in path_hints if path.startswith(".ai/specs/")}

    for path in direct_spec_changes:
        impacted[path] = {
            "path": path,
            "change_type": "修改",
            "summary": "当前任务或工作树已直接修改 spec 文件",
        }

    for spec in discover_specs(repo_root):
        rel_path = str(Path(spec["path"]).relative_to(repo_root))
        frontmatter = spec["frontmatter"]
        related_changes = frontmatter.get("related_changes", [])
        related_tasks = frontmatter.get("related_tasks", [])
        if isinstance(related_changes, str):
            related_changes = [related_changes]
        if isinstance(related_tasks, str):
            related_tasks = [related_tasks]

        matched = False
        summary = ""
        if parent_change_id and parent_change_id in related_changes:
            matched = True
            summary = f"spec frontmatter 已关联变更 `{parent_change_id}`"
        elif task_id and task_id in related_tasks:
            matched = True
            summary = f"spec frontmatter 已关联任务 `{task_id}`"
        elif hint_tokens and hint_tokens & set(spec["tokens"]):
            matched = True
            summary = "spec 文件名或标题与当前变更路径存在关键词重叠"

        if matched and rel_path not in impacted:
            impacted[rel_path] = {
                "path": rel_path,
                "change_type": "修改",
                "summary": summary,
            }

    return [impacted[key] for key in sorted(impacted.keys())]


def infer_spec_update_status(impacted_specs: list[dict[str, str]], changed_paths: list[str]) -> str:
    if any(path.startswith(".ai/specs/") for path in changed_paths):
        return "updated"
    if impacted_specs:
        return "in_progress"
    return "not_applicable"


def render_spec_delta(change_id: str, impacted_specs: list[dict[str, str]]) -> str:
    lines = [
        f"# Spec Delta — `{change_id}`",
        "",
        "## 本次变更影响的 Spec 文档",
        "",
    ]
    if not impacted_specs:
        lines.extend(["无", ""])
    else:
        lines.extend(
            [
                "| Spec 文件 | 变更类型 | 变更摘要 |",
                "|----------|---------|---------|",
            ]
        )
        for spec in impacted_specs:
            lines.append(f"| `{spec['path']}` | {spec['change_type']} | {spec['summary']} |")
        lines.append("")

    lines.extend(
        [
            "## 更新责任",
            "",
            "Developer 角色在将 `handoff_status` 设置为 `DONE` 或 `DONE_WITH_CONCERNS` 之前，",
            "必须完成上述 spec 文档的更新，并在 handoff evidence_items 的 `spec_compliance`",
            "阶段的 notes 中注明\"spec-delta.md 引用的 spec 文档已更新\"。",
            "",
            "## 若无 Spec 影响",
            "",
            "写 `无` — 明确声明本次变更不影响任何 Spec 文档。",
            "",
        ]
    )
    return "\n".join(lines)


def build_report(task: dict[str, object], impacted_specs: list[dict[str, str]], changed_paths: list[str]) -> dict[str, object]:
    status = infer_spec_update_status(impacted_specs, changed_paths)
    lines = [
        f"# ADS Spec Sync — {task['task_id']}",
        "",
        f"- spec_update_status: {status}",
        f"- parent_change_id: {task['parent_change_id'] or 'none'}",
        "",
        "## Changed Path Hints",
    ]
    lines.extend(f"- `{path}`" for path in (changed_paths or [str(path) for path in task["related_paths"]] or ["none"]))
    lines.append("")
    lines.append("## Impacted Specs")
    if impacted_specs:
        for spec in impacted_specs:
            lines.append(f"- `{spec['path']}` — {spec['change_type']} — {spec['summary']}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Recommended Next Action")
    if status == "updated":
        lines.append("- 在 handoff 中将 `spec_update_status` 标记为 `updated`，并引用已修改的 spec。")
    elif status == "in_progress":
        lines.append("- 先更新或确认这些 spec，再将 handoff 标记为完成。")
    else:
        lines.append("- 当前没有明显 spec 影响，可在 spec-delta 中写 `无`。")
    return {
        "status": status,
        "report": "\n".join(lines) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Infer impacted specs for an ADS task.")
    parser.add_argument("task_path", help="Path to ADS task markdown file")
    parser.add_argument("--changed-path", action="append", default=[], help="Explicit changed path hint")
    parser.add_argument("--output", help="Optional report output path")
    parser.add_argument("--spec-delta-output", help="Optional spec-delta output path")
    args = parser.parse_args()

    task_path = Path(args.task_path).resolve()
    task = parse_task(task_path)
    changed_paths = args.changed_path
    impacted_specs = infer_impacted_specs(task, changed_paths, repo_root=REPO_ROOT)
    report = build_report(task, impacted_specs, changed_paths)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report["report"], encoding="utf-8")
    else:
        print(report["report"], end="")

    if args.spec_delta_output and task["parent_change_id"]:
        spec_delta_text = render_spec_delta(str(task["parent_change_id"]), impacted_specs)
        spec_delta_path = Path(args.spec_delta_output).resolve()
        spec_delta_path.parent.mkdir(parents=True, exist_ok=True)
        spec_delta_path.write_text(spec_delta_text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
