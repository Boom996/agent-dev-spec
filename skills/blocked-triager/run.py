#!/usr/bin/env python3
"""Triage blocked ADS tasks and optionally draft shared change requests."""

from __future__ import annotations

import argparse
import fnmatch
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath, Path


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


def extract_subsection_bullets(section: str, label: str) -> list[str]:
    label_prefix = f"- **{label}**"
    active = False
    items: list[str] = []
    for line in section.splitlines():
        if line.startswith(label_prefix):
            active = True
            continue
        if active and line.startswith("- **"):
            break
        if active and line.strip().startswith("- "):
            item = strip_code(line.strip()[2:].split(" — ", 1)[0].strip()) or ""
            if item:
                items.append(item)
    return items


def normalize_rule(rule: str) -> str:
    return rule.strip().strip("`")


def path_matches_rule(path: str, rule: str) -> bool:
    path = path.strip().strip("`")
    rule = normalize_rule(rule)
    pure_path = PurePosixPath(path)
    if any(char in rule for char in "*?[]"):
        return fnmatch.fnmatch(path, rule) or pure_path.match(rule)
    if rule.endswith("/"):
        return path == rule.rstrip("/") or path.startswith(rule)
    return path == rule or path.startswith(rule.rstrip("/") + "/")


def parse_task(task_path: Path) -> dict[str, object]:
    text = read_text(task_path)
    single_writer = find_section(text, "单写者范围")
    return {
        "task_id": extract_table_value(text, "task_id") or task_path.stem,
        "owner_role": extract_table_value(text, "owner_role") or "unknown",
        "approval_owner": extract_table_value(text, "approval_owner") or "unknown",
        "trace_id": extract_table_value(text, "trace_id") or "unknown",
        "updated_at": extract_table_value(text, "updated_at") or "unknown",
        "locked_paths": extract_subsection_bullets(single_writer, "locked_paths"),
        "forbidden_paths": extract_subsection_bullets(single_writer, "forbidden_paths"),
    }


def detect_block_type(summary: str, target_paths: list[str], locked_paths: list[str], forbidden_paths: list[str]) -> tuple[str, list[str], list[str]]:
    reasons: list[str] = []
    shared_paths: list[str] = []
    lowered = summary.lower()

    for path in target_paths:
        if any(path_matches_rule(path, rule) for rule in forbidden_paths):
            reasons.append(f"`{path}` 落在 forbidden_paths 中")
            shared_paths.append(path)
            continue
        if locked_paths and not any(path_matches_rule(path, rule) for rule in locked_paths):
            reasons.append(f"`{path}` 不在当前 task 的 locked_paths 中")
            shared_paths.append(path)

    if shared_paths:
        return "ESCALATE_SHARED_CHANGE_REQUEST", reasons, shared_paths

    needs_context_keywords = [
        "need context",
        "missing context",
        "unclear",
        "unknown",
        "not sure",
        "need details",
        "缺少",
        "不清楚",
        "未知",
        "需要上下文",
    ]
    blocked_keywords = [
        "blocked",
        "waiting",
        "approval",
        "dependency",
        "credential",
        "external",
        "access",
        "审批",
        "等待",
        "依赖",
        "凭证",
        "卡住",
    ]

    if any(keyword in lowered for keyword in needs_context_keywords):
        reasons.append("摘要更像上下文缺失，而不是执行被外部依赖卡住")
        return "NEEDS_CONTEXT", reasons, []

    if any(keyword in lowered for keyword in blocked_keywords):
        reasons.append("摘要显示当前依赖外部批准、资源或前置条件")
        return "BLOCKED", reasons, []

    reasons.append("未发现越界改动，也没有明显的上下文缺失或外部阻塞")
    return "CONTINUE", reasons, []


def derive_request_id(task_id: str) -> str:
    match = re.search(r"TASK-(\d{8})-(\d+)", task_id)
    if match:
        return f"SCR-{match.group(1)}-{match.group(2).zfill(3)}"
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"SCR-{today}-001"


def render_shared_change_request(task: dict[str, object], summary: str, shared_paths: list[str], request_id: str) -> str:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [
        f"# Shared Change Request — `{request_id}`",
        "",
        "## Metadata",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| **request_id** | `{request_id}` |",
        f"| **task_id** | `{task['task_id']}` |",
        f"| **requested_by** | {task['owner_role']} @ blocked-triager |",
        f"| **approval_owner** | {task['approval_owner']} |",
        f"| **trace_id** | `{task['trace_id']}` |",
        f"| **updated_at** | {timestamp} |",
        "",
        "## Requested change",
        "",
        "**目标文件 / 目录**：",
        "",
    ]
    lines.extend(f"- `{path}` — 当前任务需要修改但不在 locked_paths 内" for path in shared_paths)
    lines.extend(
        [
            "",
            "**为什么不能留在当前 locked_paths 内解决**：",
            "",
            summary or "当前改动跨出任务单写者边界，需要通过 shared-change-request 升级处理。",
            "",
            "**拟议改动**：",
            "",
            "- 评审这些共享路径是否应由当前任务接管或拆成新任务",
            "- 批准后由指定 owner 在共享路径上完成改动并回写 handoff / QA",
            "",
            "## Impact",
            "",
            "**可能影响的任务**：",
            "",
            f"- `{task['task_id']}`",
            "",
            "**风险说明**：",
            "",
            "- 若直接修改共享路径，可能绕过单写者原则并引发并行冲突",
            "",
            "## Decision",
            "",
            "**结论**：`pending`",
            "",
            "**批准备注**：",
            "",
            "待审批。",
            "",
            "**后续动作**：",
            "",
            "- Approval owner 评估是否批准该共享改动",
            "- 批准后更新 task / handoff 并回填最终决策",
            "",
        ]
    )
    return "\n".join(lines)


def build_triage_report(task: dict[str, object], summary: str, target_paths: list[str]) -> dict[str, object]:
    decision, reasons, shared_paths = detect_block_type(
        summary,
        target_paths,
        task["locked_paths"],
        task["forbidden_paths"],
    )
    report_lines = [
        f"# ADS Blocked Triage — {task['task_id']}",
        "",
        f"- decision: {decision}",
        f"- owner_role: {task['owner_role']}",
        f"- approval_owner: {task['approval_owner']}",
        "",
        "## Summary",
        summary or "No explicit blocker summary provided.",
        "",
        "## Reasons",
    ]
    report_lines.extend(f"- {reason}" for reason in reasons)
    if not reasons:
        report_lines.append("- none")
    report_lines.append("")
    report_lines.append("## Target Paths")
    report_lines.extend(f"- `{path}`" for path in (target_paths or ["none"]))
    report_lines.append("")
    report_lines.append("## Recommended Next Action")
    if decision == "ESCALATE_SHARED_CHANGE_REQUEST":
        report_lines.append("- 起草 shared-change-request，并在审批前停止修改这些共享路径。")
    elif decision == "BLOCKED":
        report_lines.append("- 将 handoff_status 标记为 `BLOCKED`，并明确外部依赖或审批条件。")
    elif decision == "NEEDS_CONTEXT":
        report_lines.append("- 将 handoff_status 标记为 `NEEDS_CONTEXT`，请求缺失设计/规格/输入。")
    else:
        report_lines.append("- 继续在当前 locked_paths 内推进实现。")

    return {
        "decision": decision,
        "shared_paths": shared_paths,
        "report": "\n".join(report_lines) + "\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage blocked ADS tasks.")
    parser.add_argument("task_path", help="Path to ADS task markdown file")
    parser.add_argument("--summary", default="", help="Short summary of the blocker or uncertainty")
    parser.add_argument("--target-path", action="append", default=[], help="Path the current actor wants to touch")
    parser.add_argument("--output", help="Optional triage report output path")
    parser.add_argument("--request-output", help="Optional shared-change-request output path")
    args = parser.parse_args()

    task_path = Path(args.task_path).resolve()
    task = parse_task(task_path)
    triage = build_triage_report(task, args.summary, args.target_path)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(triage["report"], encoding="utf-8")
    else:
        print(triage["report"], end="")

    if triage["decision"] == "ESCALATE_SHARED_CHANGE_REQUEST" and args.request_output:
        request_id = derive_request_id(str(task["task_id"]))
        request_text = render_shared_change_request(task, args.summary, triage["shared_paths"], request_id)
        request_path = Path(args.request_output).resolve()
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(request_text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
