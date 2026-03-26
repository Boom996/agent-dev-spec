#!/usr/bin/env python3
"""Generate an ADS escalation draft from task and handoff artifacts."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
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


def infer_handoff(task_id: str, repo_root: Path) -> Path | None:
    candidate = repo_root / ".ai" / "handoffs" / f"{task_id}.md"
    return candidate if candidate.exists() else None


def discover_artifact_paths(handoff_text: str) -> list[str]:
    table = find_section(handoff_text, "Evidence expectation")
    return sorted(set(re.findall(r"`([^`]+)`", table)))


def build_escalation_draft(
    task_path: Path,
    repo_root: Path = REPO_ROOT,
    handoff_path: Path | None = None,
    requested_by: str | None = None,
    decision_owner: str | None = None,
    escalation_type: str | None = None,
    urgency: str = "high",
) -> str:
    task_text = read_text(task_path)
    task_id = extract_table_value(task_text, "task_id") or task_path.stem
    trace_id = extract_table_value(task_text, "trace_id") or "unknown"
    owner_role = extract_table_value(task_text, "owner_role") or "Developer"
    approval_owner = extract_table_value(task_text, "approval_owner") or "HumanOwner"
    handoff_to = extract_table_value(task_text, "handoff_to") or "Integration"
    related_paths = find_section(task_text, "相关路径")

    if handoff_path is None:
        handoff_path = infer_handoff(task_id, repo_root)

    handoff_status = "BLOCKED"
    blocked_reason = "Need explicit unblock decision"
    current_status = "任务阻塞，需升级处理。"
    artifact_paths: list[str] = []
    if handoff_path and handoff_path.exists():
        handoff_text = read_text(handoff_path)
        handoff_status = extract_table_value(handoff_text, "handoff_status") or handoff_status
        blocked_reason = extract_table_value(handoff_text, "blocked_reason") or blocked_reason
        status_match = re.search(r"\*\*当前状态\*\*[:：](.*)", handoff_text)
        current_status = status_match.group(1).strip() if status_match else current_status
        artifact_paths = discover_artifact_paths(handoff_text)

    inferred_type = escalation_type or ("needs_context" if handoff_status == "NEEDS_CONTEXT" else "needs_human_decision")
    actor = requested_by or f"{owner_role} @ CLI"
    decision_owner_value = decision_owner or approval_owner
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    escalation_id = f"ESC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-001"
    handoff_rel = handoff_path.relative_to(repo_root).as_posix() if handoff_path and handoff_path.exists() else f".ai/handoffs/{task_id}.md"

    lines = [
        f"# ADS Escalation — `{task_id}`",
        "",
        "## Metadata",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| **escalation_id** | `{escalation_id}` |",
        f"| **task_id** | `{task_id}` |",
        f"| **source_handoff** | `{handoff_rel}` |",
        f"| **escalation_type** | `{inferred_type}` |",
        f"| **requested_by** | {actor} |",
        f"| **decision_owner** | {decision_owner_value} |",
        f"| **urgency** | `{urgency}` |",
        "| **status** | `pending` |",
        f"| **trace_id** | `{trace_id}` |",
        f"| **updated_at** | {now} |",
        "",
        "## Current Block",
        "",
        f"**当前阻塞**：{blocked_reason}",
        "",
        f"**为什么普通 handoff 不够**：当前 handoff 状态为 `{handoff_status}`，下一棒 `{handoff_to}` 需要额外决策或上下文才能继续。当前状态：{current_status}",
        "",
        "## Decision Request",
        "",
        f"**需要谁做什么决定**：由 {decision_owner_value} 明确阻塞处理方式，并回写到 task / handoff / escalation。",
        "",
        "**建议选项**：",
        "",
        "- 选项 A：补齐缺失上下文或审批，允许当前任务继续",
        "- 选项 B：重定向到新 task / shared change / 跨仓库协调流程",
        "- 选项 C：明确取消或延后当前任务，避免继续空转",
        "",
        "**推荐路径**：优先做最小阻塞解除，并要求结论回写到 `.ai/handoffs/` 与本 escalation 文件。",
        "",
        "## Impact",
        "",
        "**影响的任务 / 仓库 / 团队**：",
        "",
        f"- `{task_id}`",
        f"- `{handoff_to}`",
        "",
        "**如果不处理会怎样**：",
        "",
        "- 阻塞信息继续停留在聊天里，后续 Agent 无法可靠恢复",
        "- 任务状态会长期停在 blocked / needs_context，影响交付节奏",
        "",
        "## Evidence & Context",
        "",
        "**相关证据**：",
        "",
        f"- `{task_path.relative_to(repo_root).as_posix()}`",
        f"- `{handoff_rel}`",
    ]
    for artifact in artifact_paths:
        lines.append(f"- `{artifact}`")

    lines.extend(
        [
            "",
            "**补充上下文**：",
            "",
            "- task 中的相关路径与验收标准应作为决策依据",
            "- 如需跨仓库 / 权限处理，应明确新的 owner 与回写位置",
            "",
            "## Resolution",
            "",
            "**决策结果**：",
            "",
            "（待填写）",
            "",
            "**后续动作**：",
            "",
            "- 谁回写 handoff / task",
            "- 谁继续执行",
        ]
    )
    if "| 路径 | 说明 |" in related_paths:
        lines.extend(["", "## Related Paths Snapshot", "", related_paths])

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task", type=Path, help="task markdown path")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="repository root")
    parser.add_argument("--handoff", type=Path, help="optional handoff markdown path")
    parser.add_argument("--requested-by", help="override requested_by")
    parser.add_argument("--decision-owner", help="override decision owner")
    parser.add_argument("--type", dest="escalation_type", help="override escalation type")
    parser.add_argument("--urgency", default="high", help="override urgency")
    parser.add_argument("--output", type=Path, help="write escalation markdown to a file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    draft = build_escalation_draft(
        task_path=args.task.resolve(),
        repo_root=args.repo_root.resolve(),
        handoff_path=args.handoff.resolve() if args.handoff else None,
        requested_by=args.requested_by,
        decision_owner=args.decision_owner,
        escalation_type=args.escalation_type,
        urgency=args.urgency,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(draft, encoding="utf-8")
    print(draft)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
