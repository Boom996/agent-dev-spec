#!/usr/bin/env python3
"""Review ADS task and handoff artifacts and write a QA PASS/FAIL result."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_ads


@dataclass
class EvidenceRow:
    item: str
    executed_by: str
    executed_at: str
    result: str
    artifact_paths: str
    review_status: str


@dataclass
class ReviewIssue:
    severity: str
    description: str
    expected: str
    actual: str
    evidence: str
    fix_instruction: str
    involved_paths: str


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


def parse_task(task_path: Path) -> dict[str, object]:
    text = read_text(task_path)
    title_match = re.match(r"^# 任务：(.+)$", text, flags=re.MULTILINE)
    return {
        "task_id": extract_table_value(text, "task_id") or task_path.stem,
        "title": title_match.group(1).strip() if title_match else task_path.stem,
        "owner_role": extract_table_value(text, "owner_role") or "unknown",
        "team_pattern_id": extract_table_value(text, "team_pattern_id") or "",
        "acceptance_items": extract_checkbox_texts(find_section(text, "验收标准（可勾选）")),
    }


def parse_handoff(handoff_path: Path) -> dict[str, object]:
    text = read_text(handoff_path)
    return {
        "to": extract_table_value(text, "To") or "unknown",
        "from": extract_table_value(text, "From") or "unknown",
        "task_id": extract_table_value(text, "task_id") or handoff_path.stem,
        "approval_owner": extract_table_value(text, "approval_owner") or "",
        "approval_status": re.search(r"\*\*approval_status\*\*[:：]\s*`?([^`\n]+)`?", find_section(text, "Approval")).group(1).strip()
        if re.search(r"\*\*approval_status\*\*[:：]\s*`?([^`\n]+)`?", find_section(text, "Approval"))
        else "unknown",
        "spec_update_status": extract_table_value(text, "spec_update_status") or "unknown",
        "handoff_status": extract_table_value(text, "handoff_status") or "unknown",
        "evidence_rows": parse_evidence_rows(find_section(text, "Evidence expectation")),
    }


def parse_evidence_rows(section: str) -> list[EvidenceRow]:
    rows: list[EvidenceRow] = []
    row_pattern = re.compile(
        r"^\|\s*`?([^|`]+)`?\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|$",
        re.MULTILINE,
    )
    for match in row_pattern.finditer(section):
        item, executed_by, executed_at, result, artifact_paths, review_status = [part.strip() for part in match.groups()]
        if item == "evidence_item":
            continue
        rows.append(EvidenceRow(item, executed_by, executed_at, result, artifact_paths, review_status))
    return rows


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def review(task_path: Path, handoff_path: Path, repo_root: Path = REPO_ROOT) -> dict[str, object]:
    task = parse_task(task_path)
    handoff = parse_handoff(handoff_path)
    issues: list[ReviewIssue] = []

    validation_errors = validate_ads.validate_handoff(handoff_path)
    for error in validation_errors:
        issues.append(
            ReviewIssue(
                severity="High",
                description="Handoff artifact does not satisfy ADS validation.",
                expected="handoff should pass ADS structural validation",
                actual=error,
                evidence=f"`{display_path(handoff_path, repo_root)}`",
                fix_instruction="补齐 handoff 缺失字段或 evidence 结构后重新提交评审。",
                involved_paths=display_path(handoff_path, repo_root),
            )
        )

    evidence_rows: list[EvidenceRow] = handoff["evidence_rows"]  # type: ignore[assignment]
    has_spec_compliance = any("spec_compliance" in row.item for row in evidence_rows)
    non_spec_rows = [row for row in evidence_rows if "spec_compliance" not in row.item]
    fail_rows = [row for row in evidence_rows if row.result.lower() == "fail"]
    pending_rows = [row for row in evidence_rows if row.result.lower() == "pending" or row.review_status.lower() == "pending"]
    pass_rows = [row for row in non_spec_rows if row.result.lower() == "pass"]

    if task["team_pattern_id"] and not has_spec_compliance:
        issues.append(
            ReviewIssue(
                severity="High",
                description="Missing spec compliance evidence for a team-pattern task.",
                expected="handoff should contain at least one `spec_compliance:` evidence row",
                actual=f"team_pattern_id={task['team_pattern_id']} but no spec_compliance row found",
                evidence=f"`{display_path(handoff_path, repo_root)}`",
                fix_instruction="补充 spec_compliance 阶段 evidence，并说明规格核对结果。",
                involved_paths=display_path(handoff_path, repo_root),
            )
        )

    if str(handoff["spec_update_status"]) in {"not_started", "in_progress"} and has_spec_compliance:
        issues.append(
            ReviewIssue(
                severity="Medium",
                description="Spec update status and spec compliance evidence are inconsistent.",
                expected="spec_update_status should be `updated` or `not_applicable` when spec_compliance is reviewed",
                actual=f"spec_update_status={handoff['spec_update_status']}",
                evidence=f"`{display_path(handoff_path, repo_root)}`",
                fix_instruction="确认 spec 是否已同步；如已同步，更新 handoff 的 spec_update_status。",
                involved_paths=display_path(handoff_path, repo_root),
            )
        )

    for row in fail_rows:
        issues.append(
            ReviewIssue(
                severity="High",
                description="Evidence row reports a failing verification result.",
                expected="all required verification rows should pass before integration QA passes",
                actual=f"{row.item} -> {row.result}",
                evidence=row.artifact_paths or row.executed_at or "handoff evidence row",
                fix_instruction="修复失败验证，再更新 handoff evidence 与结果。",
                involved_paths=display_path(handoff_path, repo_root),
            )
        )

    if not pass_rows:
        issues.append(
            ReviewIssue(
                severity="Medium",
                description="No code-quality style pass evidence found.",
                expected="handoff should include at least one passing non-spec evidence row such as lint/test/build",
                actual="no non-spec evidence row with `pass` result",
                evidence=f"`{display_path(handoff_path, repo_root)}`",
                fix_instruction="至少补一条通过的 lint/test/build 类验证 evidence。",
                involved_paths=display_path(handoff_path, repo_root),
            )
        )

    if pending_rows and not fail_rows:
        issues.append(
            ReviewIssue(
                severity="Medium",
                description="Evidence rows are still pending review or execution.",
                expected="evidence rows should be fully executed and reviewed before PASS",
                actual=", ".join(row.item for row in pending_rows),
                evidence=f"`{display_path(handoff_path, repo_root)}`",
                fix_instruction="执行并回填 pending evidence，或将 handoff_status 保持在待恢复/待复核状态。",
                involved_paths=display_path(handoff_path, repo_root),
            )
        )

    passed = len(issues) == 0
    return {
        "passed": passed,
        "task": task,
        "handoff": handoff,
        "issues": issues,
    }


def render_pass(result: dict[str, object], qa_actor: str) -> str:
    task = result["task"]
    handoff = result["handoff"]
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [
        f"# QA 结论：PASS — `{task['task_id']}`",
        "",
        "## 任务",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| **task_id** | {task['task_id']} |",
        f"| **描述** | {task['title']} |",
        f"| **Developer** | {handoff['from']} |",
        f"| **QA** | {qa_actor} |",
        f"| **Timestamp** | {timestamp} |",
        "",
        "## 结论：PASS",
        "",
        "## 证据摘要",
        "",
        "- 验收标准核对：task 与 handoff 结构满足当前 ADS 要求",
        "- 命令/测试结果：handoff evidence 中至少一条非 spec 验证已通过，且未发现 fail",
        f"- 其他说明：handoff_status={handoff['handoff_status']}，spec_update_status={handoff['spec_update_status']}",
        "",
        "## 下一动作",
        "",
        "→ Integration：合并 / 关闭任务 / 更新 backlog",
        "",
    ]
    return "\n".join(lines)


def render_fail(result: dict[str, object], qa_actor: str) -> str:
    task = result["task"]
    handoff = result["handoff"]
    issues: list[ReviewIssue] = result["issues"]  # type: ignore[assignment]
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    lines = [
        f"# QA 结论：FAIL — `{task['task_id']}`",
        "",
        "## 任务",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| **task_id** | {task['task_id']} |",
        f"| **描述** | {task['title']} |",
        f"| **Developer** | {handoff['from']} |",
        f"| **QA** | {qa_actor} |",
        "| **Attempt** | 第 1 次 |",
        f"| **Timestamp** | {timestamp} |",
        "",
        "## 结论：FAIL",
        "",
        "## 问题列表",
        "",
    ]
    for index, issue in enumerate(issues, start=1):
        lines.extend(
            [
                f"### Issue {index} — 严重级别：{issue.severity}",
                "",
                "| 项 | 内容 |",
                "|----|------|",
                f"| **描述** | {issue.description} |",
                f"| **期望** | {issue.expected} |",
                f"| **实际** | {issue.actual} |",
                f"| **证据** | {issue.evidence} |",
                f"| **修复指令** | {issue.fix_instruction} |",
                f"| **涉及路径** | {issue.involved_paths} |",
                "",
            ]
        )
    lines.extend(
        [
            "## 下一动作",
            "",
            f"→ Developer：按修复指令修改后更新 `.ai/handoffs/{task['task_id']}.md` 并重新提交评审",
            "",
        ]
    )
    return "\n".join(lines)


def default_output_path(result: dict[str, object], repo_root: Path = REPO_ROOT) -> Path:
    task_id = result["task"]["task_id"]
    suffix = "pass" if result["passed"] else "fail"
    return repo_root / ".ai" / "qa" / f"{task_id}-{suffix}.md"


def write_review(task_path: Path, handoff_path: Path, qa_actor: str = "Integration", output_path: Path | None = None, repo_root: Path = REPO_ROOT) -> tuple[dict[str, object], Path]:
    result = review(task_path, handoff_path, repo_root=repo_root)
    rendered = render_pass(result, qa_actor) if result["passed"] else render_fail(result, qa_actor)
    if output_path is None:
        output_path = default_output_path(result, repo_root=repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return result, output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Review ADS task and handoff artifacts into a QA result.")
    parser.add_argument("task_path", help="Path to ADS task markdown file")
    parser.add_argument("handoff_path", help="Path to ADS handoff markdown file")
    parser.add_argument("--qa-actor", default="Integration", help="Reviewer label shown in the QA result")
    parser.add_argument("--output", help="Optional output path")
    args = parser.parse_args()

    task_path = Path(args.task_path).resolve()
    handoff_path = Path(args.handoff_path).resolve()
    output_path = Path(args.output).resolve() if args.output else None
    result, written_path = write_review(task_path, handoff_path, qa_actor=args.qa_actor, output_path=output_path, repo_root=REPO_ROOT)
    print(written_path)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
