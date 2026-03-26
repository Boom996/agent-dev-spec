#!/usr/bin/env python3
"""Generate a handoff draft from task metadata and current git state."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
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


def extract_checkbox_lines(section: str) -> list[str]:
    return re.findall(r"^- \[[ xX]\] .+$", section, flags=re.MULTILINE)


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


def parse_related_path_descriptions(text: str) -> dict[str, str]:
    section = find_section(text, "相关路径")
    mapping: dict[str, str] = {}
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        if "------" in line or "路径" in line:
            continue
        parts = [part.strip() for part in line.split("|")[1:-1]]
        if len(parts) >= 2 and parts[0]:
            mapping[strip_code(parts[0]) or ""] = parts[1]
    return mapping


def extract_freshness_stale_after(text: str) -> str:
    freshness = find_section(text, "Freshness")
    match = re.search(r"\*\*stale_after\*\*.*?：\s*`?([^`\n]+)`?", freshness)
    return match.group(1).strip() if match else "P2D"


def load_identity(identity_path: Path | None) -> dict:
    if not identity_path or not identity_path.exists():
        return {}
    return json.loads(identity_path.read_text(encoding="utf-8"))


def run_git(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def discover_changed_paths(repo_root: Path) -> list[str]:
    changed = run_git(repo_root, ["diff", "--name-only", "--relative", "HEAD", "--"])
    untracked = run_git(repo_root, ["ls-files", "--others", "--exclude-standard"])
    paths = [line.strip() for line in (changed.splitlines() + untracked.splitlines()) if line.strip()]
    return sorted(dict.fromkeys(paths))


def git_diff_summary(repo_root: Path) -> str:
    summary = run_git(repo_root, ["diff", "--stat", "--relative", "HEAD", "--"])
    if summary:
        return summary
    untracked = discover_changed_paths(repo_root)
    if untracked:
        return "Untracked files:\n" + "\n".join(f" {path}" for path in untracked)
    return "No git diff detected."


def git_branch(repo_root: Path) -> str:
    branch = run_git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    return branch or "unknown"


def infer_evidence_items(identity: dict, explicit_items: list[str]) -> list[str]:
    if explicit_items:
        return explicit_items
    commands = identity.get("standard_verify_commands", {})
    if isinstance(commands, dict) and commands:
        return [str(key) for key in commands.keys()]
    return ["test"]


def infer_spec_update_status(changed_paths: list[str]) -> str:
    return "updated" if any(path.startswith(".ai/specs/") for path in changed_paths) else "not_started"


def build_handoff_draft(
    task_path: Path,
    repo_root: Path = REPO_ROOT,
    handoff_to: str | None = None,
    from_actor: str | None = None,
    handoff_status: str = "DONE",
    blocked_reason: str = "",
    evidence_items: list[str] | None = None,
    identity_path: Path | None = None,
) -> str:
    task_text = read_text(task_path)
    task_id = extract_table_value(task_text, "task_id") or task_path.stem
    priority = extract_table_value(task_text, "priority") or "Medium"
    trace_id = extract_table_value(task_text, "trace_id") or "unknown"
    approval_owner = extract_table_value(task_text, "approval_owner") or "unknown"
    team_pattern_id = extract_table_value(task_text, "team_pattern_id") or ""
    task_handoff_to = extract_table_value(task_text, "handoff_to") or "Integration"
    stale_after = extract_freshness_stale_after(task_text)
    acceptance_lines = extract_checkbox_lines(find_section(task_text, "验收标准（可勾选）"))
    related_descriptions = parse_related_path_descriptions(task_text)
    memory_refs = parse_memory_refs(task_text)
    evidence_expectation = find_section(task_text, "证据期望（完成时必须附上）")

    changed_paths = discover_changed_paths(repo_root)
    path_rows = changed_paths or sorted(related_descriptions.keys())
    diff_summary = git_diff_summary(repo_root)
    identity = load_identity(identity_path)
    evidence_names = infer_evidence_items(identity, evidence_items or [])
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    target_actor = handoff_to or task_handoff_to
    current_actor = from_actor or f"{extract_table_value(task_text, 'owner_role') or 'Developer'} @ CLI"
    spec_update_status = infer_spec_update_status(changed_paths)

    lines = [
        f"# ADS Handoff — `{task_id}`",
        "",
        "## Metadata",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| **From** | {current_actor} |",
        f"| **To** | {target_actor} |",
        f"| **task_id** | {task_id} |",
        f"| **Priority** | {priority} |",
        f"| **Timestamp** | {now} |",
        f"| **trace_id** | {trace_id} |",
        f"| **updated_at** | {now} |",
        f"| **stale_after** | `{stale_after}` |",
        f"| **handoff_status** | `{handoff_status}` |",
        f"| **blocked_reason** | {blocked_reason} |",
        f"| **spec_update_status** | `{spec_update_status}` |",
        f"| **team_pattern_id** | `{team_pattern_id}` |" if team_pattern_id else "| **team_pattern_id** |  |",
        "",
        "## Context",
        "",
        f"**当前状态**：已根据当前 worktree 生成 handoff 草稿；变更文件数 {len(changed_paths)}，当前分支 `{git_branch(repo_root)}`。",
        "",
        "**相关路径**：",
        "",
        "| 路径 | 内容说明 |",
        "|------|----------|",
    ]

    for path in path_rows:
        description = related_descriptions.get(path, "Changed in current worktree")
        lines.append(f"| `{path}` | {description} |")

    lines.extend(
        [
            "",
            "**依赖**：按 task 合同继续确认依赖是否已满足",
            "**约束**：遵守 task 中的 locked_paths / forbidden_paths 与 Constitution",
            "",
            "## Memory refs（可选）",
            "",
        ]
    )
    lines.extend(f"- `{item}`" if not item.startswith("`") else f"- {item}" for item in (memory_refs or ["无"]))

    lines.extend(
        [
            "",
            "## Deliverable request",
            "",
            f"**需要什么**：由 {target_actor} 基于当前 diff、验收标准和证据要求继续推进或复核。",
            "",
            "**验收标准**（可勾选）：",
            "",
        ]
    )
    lines.extend(acceptance_lines or ["- [ ] 补充任务验收标准"])
    lines.extend(
        [
            "",
            f"**参考资料**：`{task_path.relative_to(repo_root)}`",
            "",
            "## Evidence expectation",
            "",
            "**必须提供的证明**：",
            evidence_expectation or "按 task 中的证据期望补齐验证命令、日志或截图。",
            "",
            "**已附证据**：（本任务主责已填）",
            "",
            "| evidence_item | executed_by | executed_at | result | artifact_paths | review_status |",
            "|---------------|-------------|-------------|--------|----------------|---------------|",
        ]
    )
    for item in evidence_names:
        artifact_path = f"`artifacts/{item}.txt`"
        lines.append(f"| `{item}` | {current_actor} |  | pending | {artifact_path} | pending |")

    lines.extend(
        [
            "",
            "**Evidence telemetry**：（可选，补充 cost / latency / retry）",
            "",
            "| evidence_item | duration_ms | cost_usd | retry_count |",
            "|---------------|-------------|----------|-------------|",
        ]
    )
    for item in evidence_names:
        lines.append(f"| `{item}` |  |  |  |")

    lines.extend(
        [
            "",
            "**附加说明**：",
            "",
            f"- Branch: `{git_branch(repo_root)}`",
            "- Diff summary:",
        ]
    )
    for diff_line in diff_summary.splitlines():
        lines.append(f"- {diff_line}")

    lines.extend(
        [
            "",
            "## Approval",
            "",
            f"**approval_owner**：{approval_owner}",
            "**approval_status**：`pending`",
            "",
            "## Handoff to next",
            "",
            f"**下一棒**：{target_actor}",
            f"**建议下一动作**：先核对 diff 与证据，再决定是否将 `handoff_status` 更新为 `pending_resume`、`DONE` 或 `DONE_WITH_CONCERNS`。",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an ADS handoff draft from task metadata and git diff.")
    parser.add_argument("task", help="Path to the task markdown file")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root used for git inspection")
    parser.add_argument("--to", help="Override handoff target")
    parser.add_argument("--from-actor", help="Override current actor, e.g. `Backend @ Codex`")
    parser.add_argument("--status", default="DONE", help="handoff_status value")
    parser.add_argument("--blocked-reason", default="", help="Reason when status is BLOCKED or NEEDS_CONTEXT")
    parser.add_argument("--evidence-item", action="append", default=[], help="Evidence item label, repeatable")
    parser.add_argument(
        "--identity",
        default=str(REPO_ROOT / ".agent" / "identity.json.example"),
        help="Path to identity.json or example identity file",
    )
    parser.add_argument("--output", help="Write draft to file instead of stdout")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    task_path = Path(args.task).resolve()
    identity_path = Path(args.identity).resolve() if args.identity else None
    draft = build_handoff_draft(
        task_path,
        repo_root=repo_root,
        handoff_to=args.to,
        from_actor=args.from_actor,
        handoff_status=args.status,
        blocked_reason=args.blocked_reason,
        evidence_items=args.evidence_item,
        identity_path=identity_path,
    )

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(draft, encoding="utf-8")
    else:
        print(draft, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
