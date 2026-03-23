#!/usr/bin/env python3
"""Generate ADS task drafts from a change proposal."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class ChangeProposal:
    change_id: str
    title: str
    approval_owner: str
    trace_id: str
    updated_at: str
    impact_paths: list[tuple[str, str]]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_table_value(text: str, label: str) -> str:
    pattern = rf"\|\s*\*\*{re.escape(label)}\*\*\s*\|\s*(.*?)\s*\|"
    match = re.search(pattern, text)
    if not match:
        return ""
    value = match.group(1).strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def find_section(text: str, title: str) -> str:
    pattern = rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_impact_paths(scope_section: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in scope_section.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        raw = line[2:].strip()
        if " — " in raw:
            path, description = raw.split(" — ", 1)
        else:
            path, description = raw, "Impacted by change proposal"
        path = path.strip().strip("`")
        description = description.strip()
        if path:
            rows.append((path, description))
    return rows


def parse_change_proposal(path: Path) -> ChangeProposal:
    text = read_text(path)
    scope = find_section(text, "Scope")
    return ChangeProposal(
        change_id=extract_table_value(text, "change_id") or path.parent.name,
        title=extract_table_value(text, "title") or path.parent.name,
        approval_owner=extract_table_value(text, "approval_owner") or "unknown",
        trace_id=extract_table_value(text, "trace_id") or "unknown",
        updated_at=extract_table_value(text, "updated_at") or "unknown",
        impact_paths=parse_impact_paths(scope),
    )


def infer_role(path: str) -> str:
    lower = path.lower()
    if any(token in lower for token in ("frontend/", "/ui", "components", "pages", "hooks")):
        return "Frontend"
    if any(token in lower for token in ("backend/", "/api", "/server", "/auth", "/db", "/models")):
        return "Backend"
    if any(token in lower for token in (".ai/specs/", "specs/", "architecture", "design", "docs/")):
        return "Architect"
    if any(token in lower for token in ("tests/", "qa/", "e2e", ".github/", "ci", "release", "integration")):
        return "Integration"
    return "AgentImplementer"


def slugify(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in slug.split("-") if part)


def derive_date_token(change: ChangeProposal) -> str:
    for candidate in (change.change_id, change.updated_at):
        digits = "".join(ch for ch in candidate if ch.isdigit())
        if len(digits) >= 8:
            return digits[:8]
    return "00000000"


def group_paths_by_role(change: ChangeProposal) -> dict[str, list[tuple[str, str]]]:
    groups: dict[str, list[tuple[str, str]]] = {}
    for path, description in change.impact_paths:
        role = infer_role(path)
        groups.setdefault(role, []).append((path, description))
    if not groups:
        groups["AgentImplementer"] = [("src/", "Primary implementation area to be refined manually")]
    return groups


def render_task(change: ChangeProposal, role: str, grouped_paths: list[tuple[str, str]], index: int) -> str:
    date_token = derive_date_token(change)
    task_id = f"TASK-{date_token}-{index:03d}"
    title = f"{change.title}（{role}）"
    acceptance = [
        f"- [ ] {role} 范围内的相关路径已完成预期改动",
        "- [ ] 不修改本任务 forbidden_paths 中声明的路径",
        "- [ ] 补齐对应验证命令与 handoff 证据",
    ]

    lines = [
        f"# 任务：{title}",
        "",
        "## 元数据",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| **task_id** | `{task_id}` |",
        f"| **owner_role** | {role} |",
        "| **owner** | |",
        "| **priority** | High |",
        "| **deps** | `[]` |",
        "| **handoff_to** | Integration |",
        "| **team_pattern_id** | |",
        f"| **approval_owner** | {change.approval_owner} |",
        "| **allowed_agents** | `[]` |",
        f"| **parent_change_id** | `{change.change_id}` |",
        "| **coordination_model** | `direct` |",
        "| **autonomy_level** | `semi-autonomous` |",
        f"| **trace_id** | `{change.trace_id}` |",
        f"| **updated_at** | `{change.updated_at}` |",
        "",
        "## 单写者范围",
        "",
        "- **locked_paths**（本任务周期内仅主责可改）：",
    ]
    lines.extend(f"  - `{path}` — {description}" for path, description in grouped_paths)
    lines.extend(
        [
            "- **forbidden_paths**（禁止改动）：",
            "  - `docs/00-overview.md` — 协议总览不应在任务执行中随意修改",
            "",
            "## 共享改动升级（可选）",
            "",
            "无",
            "",
            "## 背景与目标",
            "",
            f"本任务由变更提案 `{change.change_id}` 自动拆分生成，负责 `{role}` 侧的交付面。",
            "开始执行前应补充更细的背景、依赖和非目标说明。",
            "",
            "## 验收标准（可勾选）",
            "",
        ]
    )
    lines.extend(acceptance)
    lines.extend(
        [
            "",
            "## 相关路径",
            "",
            "| 路径 | 说明 |",
            "|------|------|",
        ]
    )
    lines.extend(f"| `{path}` | {description} |" for path, description in grouped_paths)
    lines.extend(
        [
            "",
            "## Memory refs（可选）",
            "",
            "无",
            "",
            "## 证据期望（完成时必须附上）",
            "",
            "- 标准验证命令输出",
            "- 对应 handoff 中的 evidence 表格行",
            "",
            "## Freshness",
            "",
            "- **stale_after**（可选）：`P2D`",
            "- **最后更新时间说明**：由 task-decomposer 自动生成初稿",
            "",
            "---",
            "",
            "**状态**：`backlog`",
            "",
        ]
    )
    return "\n".join(lines)


def generate_tasks(change_path: Path, output_dir: Path | None = None, force: bool = False) -> list[Path]:
    change = parse_change_proposal(change_path)
    groups = group_paths_by_role(change)
    if output_dir is None:
        output_dir = REPO_ROOT / ".ai" / "tasks" / "generated" / change.change_id
    output_dir.mkdir(parents=True, exist_ok=True)

    written_paths: list[Path] = []
    for index, role in enumerate(sorted(groups.keys()), start=1):
        content = render_task(change, role, groups[role], index)
        filename = f"{index:02d}-{slugify(role)}.md"
        path = output_dir / filename
        if path.exists() and not force:
            raise FileExistsError(f"task draft already exists: {path}")
        path.write_text(content, encoding="utf-8")
        written_paths.append(path)
    return written_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ADS task drafts from a change proposal.")
    parser.add_argument("change_path", help="Path to change proposal markdown")
    parser.add_argument("--output-dir", help="Optional output directory for generated task files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated task files")
    args = parser.parse_args()

    change_path = Path(args.change_path).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    written_paths = generate_tasks(change_path, output_dir=output_dir, force=args.force)
    for path in written_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
