#!/usr/bin/env python3
"""Validate core ADS task and handoff artifacts."""

from __future__ import annotations

import argparse
import re
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
TASK_GLOBS = [".ai/tasks/**/*.md", "examples/case-task-*.md"]
HANDOFF_GLOBS = [".ai/handoffs/**/*.md", "examples/case-handoff-*.md"]
MEMORY_GLOBS = [".ai/memory/**/*.md", "examples/case-memory-*.md"]
REQUEST_GLOBS = [".ai/requests/**/*.md", "examples/case-shared-change-request*.md"]
QA_GLOBS = [".ai/qa/**/*.md", "examples/case-qa-*.md"]
PATTERN_GLOBS = [".ai/patterns/*.md"]
CHANGE_GLOBS = [".ai/changes/**/proposal.md", "examples/case-change-proposal/proposal.md"]
TOOLSET_PATHS = [REPO_ROOT / "tools" / "toolset.json", REPO_ROOT / "tools" / "toolset.json.example"]
VALID_HANDOFF_STATUSES = {"DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED", "pending_resume"}
VALID_SPEC_UPDATE_STATUSES = {"not_started", "in_progress", "updated", "not_applicable"}
VALID_COORDINATION_MODELS = {"direct", "orchestrated", "peer-parallel"}
VALID_CHANGE_STATUSES = {"pending_approval", "approved", "in_progress", "done", "cancelled"}


def is_iso8601ish(value: str) -> bool:
    value = value.strip()
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$", value))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def find_section(text: str, title: str) -> str:
    pattern = rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_table_value(text: str, label: str) -> str | None:
    pattern = rf"\|\s*\*\*{re.escape(label)}\*\*\s*\|\s*(.*?)\s*\|"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def strip_code(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def extract_checkbox_lines(section: str) -> list[str]:
    return re.findall(r"^- \[[ xX]\] .+$", section, flags=re.MULTILINE)


def extract_bullets(section: str) -> list[str]:
    return [line.strip() for line in section.splitlines() if line.strip().startswith("- ")]


def extract_memory_refs(section: str) -> list[str]:
    refs: list[str] = []
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            item = strip_code(line[2:].split(" — ", 1)[0].strip()) or ""
            if item and item != "无":
                refs.append(item)
    return refs


def discover_files(globs: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in globs:
        files.extend(path for path in REPO_ROOT.glob(pattern) if path.is_file())
    return sorted(set(files))


def detect_kind(path: Path) -> str | None:
    text = read_text(path)
    if text.startswith("# 任务："):
        return "task"
    if text.startswith("# ADS Handoff"):
        return "handoff"
    if text.startswith("# Memory Object"):
        return "memory"
    if text.startswith("# Shared Change Request"):
        return "request"
    if text.startswith("# QA 结论：PASS"):
        return "qa_pass"
    if text.startswith("# QA 结论：FAIL"):
        return "qa_fail"
    if text.startswith("# Team Pattern"):
        return "pattern"
    if text.startswith("# Change Proposal"):
        return "change_proposal"
    return None


def validate_task(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []

    for field in [
        "task_id",
        "owner_role",
        "priority",
        "deps",
        "trace_id",
        "updated_at",
    ]:
        if not extract_table_value(text, field):
            errors.append(f"missing metadata field `{field}`")

    for field in ["team_pattern_id", "approval_owner", "allowed_agents", "handoff_to"]:
        if extract_table_value(text, field) is None:
            errors.append(f"missing metadata row `{field}`")

    team_pattern_id = strip_code(extract_table_value(text, "team_pattern_id"))
    if team_pattern_id:
        pattern_path = REPO_ROOT / ".ai" / "patterns" / f"{team_pattern_id}.md"
        if not pattern_path.exists():
            errors.append(f"declared team pattern `{team_pattern_id}` does not exist")

    updated_at = extract_table_value(text, "updated_at")
    if updated_at and "ISO8601" not in updated_at and not is_iso8601ish(updated_at):
        errors.append("`updated_at` is not ISO8601-like")

    single_writer = find_section(text, "单写者范围")
    if "locked_paths" not in single_writer:
        errors.append("missing `locked_paths` block")
    if "forbidden_paths" not in single_writer:
        errors.append("missing `forbidden_paths` block")

    if not find_section(text, "共享改动升级（可选）"):
        errors.append("missing `共享改动升级（可选）` section")

    if not extract_checkbox_lines(find_section(text, "验收标准（可勾选）")):
        errors.append("acceptance criteria must contain checkbox items")

    related_paths = find_section(text, "相关路径")
    if "| 路径 | 说明 |" not in related_paths:
        errors.append("missing related paths table")

    if not find_section(text, "证据期望（完成时必须附上）"):
        errors.append("missing evidence expectation section")

    memory_refs = extract_memory_refs(find_section(text, "Memory refs（可选）"))
    for ref in memory_refs:
        if not (REPO_ROOT / ref).exists():
            errors.append(f"referenced memory object does not exist: {ref}")

    freshness = find_section(text, "Freshness")
    if not freshness:
        errors.append("missing freshness section")
    elif "stale_after" not in freshness:
        errors.append("missing `stale_after` in freshness section")

    # Phase 1：coordination_model 为可选字段；有值时校验枚举范围
    coordination_model = strip_code(extract_table_value(text, "coordination_model"))
    if coordination_model and coordination_model not in VALID_COORDINATION_MODELS:
        errors.append(
            f"`coordination_model` must be one of {sorted(VALID_COORDINATION_MODELS)}, "
            f"got '{coordination_model}'"
        )

    # Phase 2: parent_change_id 存在时检查变更目录
    parent_change_id = strip_code(extract_table_value(text, "parent_change_id"))
    if parent_change_id:
        change_dir = REPO_ROOT / ".ai" / "changes" / parent_change_id
        if not change_dir.is_dir():
            errors.append(f"declared parent_change_id `{parent_change_id}` directory does not exist: {change_dir.relative_to(REPO_ROOT)}")

    # Phase 2: orchestrated 任务必须有 Sub-Tasks Detail 节
    if coordination_model == "orchestrated" and not find_section(text, "Sub-Tasks Detail"):
        errors.append("orchestrated task must have a `## Sub-Tasks Detail` section")

    return errors


def validate_handoff(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []

    for field in [
        "From",
        "To",
        "task_id",
        "Priority",
        "Timestamp",
        "trace_id",
        "updated_at",
        "stale_after",
    ]:
        if not extract_table_value(text, field):
            errors.append(f"missing metadata field `{field}`")

    for field in ("Timestamp", "updated_at"):
        value = extract_table_value(text, field)
        if value and "ISO8601" not in value and not is_iso8601ish(value):
            errors.append(f"`{field}` is not ISO8601-like")

    context = find_section(text, "Context")
    if "当前状态" not in context:
        errors.append("missing current status in context")
    if "| 路径 | 内容说明 |" not in context:
        errors.append("missing related paths table in context")

    if not extract_checkbox_lines(find_section(text, "Deliverable request")):
        errors.append("deliverable request must contain checkbox acceptance items")

    evidence = find_section(text, "Evidence expectation")
    if "| evidence_item | executed_by | executed_at | result | artifact_paths | review_status |" not in evidence:
        errors.append("missing structured evidence table")

    approval = find_section(text, "Approval")
    if "approval_owner" not in approval:
        errors.append("missing `approval_owner` in approval section")
    if "approval_status" not in approval:
        errors.append("missing `approval_status` in approval section")

    memory_refs = extract_memory_refs(find_section(text, "Memory refs（可选）"))
    for ref in memory_refs:
        if not (REPO_ROOT / ref).exists():
            errors.append(f"referenced memory object does not exist: {ref}")

    # Phase 1：handoff_status 为可选字段；有值时校验枚举范围
    handoff_status = strip_code(extract_table_value(text, "handoff_status"))
    if handoff_status and handoff_status not in VALID_HANDOFF_STATUSES:
        errors.append(
            f"`handoff_status` must be one of {sorted(VALID_HANDOFF_STATUSES)}, got '{handoff_status}'"
        )

    # Phase 1：spec_update_status 为可选字段；有值时校验枚举范围
    spec_update_status = strip_code(extract_table_value(text, "spec_update_status"))
    if spec_update_status and spec_update_status not in VALID_SPEC_UPDATE_STATUSES:
        errors.append(
            f"`spec_update_status` must be one of {sorted(VALID_SPEC_UPDATE_STATUSES)}, got '{spec_update_status}'"
        )

    return errors


def validate_memory(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []

    for field in [
        "memory_id",
        "type",
        "title",
        "scope",
        "owner",
        "status",
        "freshness",
        "review_after",
        "trace_id",
        "updated_at",
    ]:
        if not extract_table_value(text, field):
            errors.append(f"missing metadata field `{field}`")

    updated_at = extract_table_value(text, "updated_at")
    if updated_at and "ISO8601" not in updated_at and not is_iso8601ish(strip_code(updated_at) or ""):
        errors.append("`updated_at` is not ISO8601-like")

    review_after = strip_code(extract_table_value(text, "review_after") or "")
    if review_after and not re.match(r"^P\d+D$", review_after):
        errors.append("`review_after` must look like `P7D`")

    links = find_section(text, "Links")
    if "**related_tasks**" not in links:
        errors.append("missing `related_tasks` links block")
    if "**related_paths**" not in links:
        errors.append("missing `related_paths` links block")
    if "**source**" not in links:
        errors.append("missing `source` field")

    if not find_section(text, "Summary"):
        errors.append("missing summary section")

    return errors


def validate_request(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []

    for field in [
        "request_id",
        "task_id",
        "requested_by",
        "approval_owner",
        "trace_id",
        "updated_at",
    ]:
        if not extract_table_value(text, field):
            errors.append(f"missing metadata field `{field}`")

    updated_at = extract_table_value(text, "updated_at")
    if updated_at and "ISO8601" not in updated_at and not is_iso8601ish(strip_code(updated_at) or ""):
        errors.append("`updated_at` is not ISO8601-like")

    requested_change = find_section(text, "Requested change")
    if "**目标文件 / 目录**" not in requested_change:
        errors.append("missing target files block in requested change section")
    elif not extract_bullets(requested_change):
        errors.append("requested change should list at least one target path or proposed change bullet")
    if "**为什么不能留在当前 locked_paths 内解决**" not in requested_change:
        errors.append("missing locked_paths rationale in requested change section")
    if "**拟议改动**" not in requested_change:
        errors.append("missing proposed changes block in requested change section")

    impact = find_section(text, "Impact")
    if "**可能影响的任务**" not in impact:
        errors.append("missing impacted tasks block in impact section")
    elif not extract_bullets(impact):
        errors.append("impact section should contain bullet items")
    if "**风险说明**" not in impact:
        errors.append("missing risk notes block in impact section")

    decision = find_section(text, "Decision")
    decision_match = re.search(r"\*\*结论\*\*：`?(pending|approved|rejected)`?", decision)
    if not decision_match:
        errors.append("decision must be one of `pending`, `approved`, `rejected`")
    if "**批准备注**" not in decision:
        errors.append("missing approval notes block")
    if "**后续动作**" not in decision:
        errors.append("missing follow-up actions block")
    elif not extract_bullets(decision):
        errors.append("decision section should contain follow-up action bullets")

    return errors


def validate_qa_pass(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []

    for field in ["task_id", "描述", "Developer", "QA", "Timestamp"]:
        if not extract_table_value(text, field):
            errors.append(f"missing metadata field `{field}`")

    timestamp = extract_table_value(text, "Timestamp")
    if timestamp and "ISO8601" not in timestamp and not is_iso8601ish(strip_code(timestamp) or ""):
        errors.append("`Timestamp` is not ISO8601-like")

    evidence = find_section(text, "证据摘要")
    if len(extract_bullets(evidence)) < 2:
        errors.append("evidence summary should contain at least two bullet items")

    next_actions = find_section(text, "下一动作")
    if not next_actions.strip():
        errors.append("missing next action section content")

    return errors


def validate_qa_fail(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []

    for field in ["task_id", "描述", "Developer", "QA", "Attempt", "Timestamp"]:
        if not extract_table_value(text, field):
            errors.append(f"missing metadata field `{field}`")

    timestamp = extract_table_value(text, "Timestamp")
    if timestamp and "ISO8601" not in timestamp and not is_iso8601ish(strip_code(timestamp) or ""):
        errors.append("`Timestamp` is not ISO8601-like")

    if not re.findall(r"^### Issue .+$", text, flags=re.MULTILINE):
        errors.append("qa fail report must contain at least one issue block")
    if "| **描述** |" not in text or "| **修复指令** |" not in text:
        errors.append("issue block must include description and fix instructions")

    next_actions = find_section(text, "下一动作")
    if not next_actions.strip():
        errors.append("missing next action section content")

    return errors


REQUIRED_CONSTITUTION_SECTIONS = [
    "Mission",
    "Non-Negotiable Principles",
    "Role Definitions",
    "Agent Governance",
]


def validate_constitution(repo_root: Path) -> list[str]:
    """Validate .agent/constitution.md exists and has required non-empty sections."""
    constitution_path = repo_root / ".agent" / "constitution.md"
    if not constitution_path.exists():
        return ["constitution.md not found at .agent/constitution.md"]

    text = read_text(constitution_path)
    errors: list[str] = []
    for section in REQUIRED_CONSTITUTION_SECTIONS:
        content = find_section(text, section)
        if not content.strip():
            errors.append(f"constitution.md: section '{section}' is missing or empty")
    return errors


def validate_pattern(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []

    for field in ["team_pattern_id", "version", "updated_at"]:
        if not extract_table_value(text, field):
            errors.append(f"missing metadata field `{field}`")

    updated_at = extract_table_value(text, "updated_at")
    if updated_at and "ISO8601" not in updated_at and not is_iso8601ish(strip_code(updated_at) or ""):
        errors.append("`updated_at` is not ISO8601-like")

    # Phase 2: coordination_model 为必填字段（team-pattern 须声明默认协调模式）
    if not extract_table_value(text, "coordination_model"):
        errors.append("missing metadata field `coordination_model`")
    else:
        cm = strip_code(extract_table_value(text, "coordination_model"))
        if cm and cm not in VALID_COORDINATION_MODELS:
            errors.append(
                f"`coordination_model` must be one of {sorted(VALID_COORDINATION_MODELS)}, "
                f"got '{cm}'"
            )

    for title in [
        "Description",
        "Roles",
        "Entry Conditions",
        "Shared Context Scope",
        "Handoff Rules",
        "Approval Flow",
        "Integration Gate",
        "State Model",
    ]:
        if not find_section(text, title):
            errors.append(f"missing `{title}` section")

    if not extract_bullets(find_section(text, "Roles")):
        errors.append("roles section must contain bullet items")
    if not extract_bullets(find_section(text, "State Model")):
        errors.append("state model must contain bullet items")

    return errors


def has_spec_delta_entry(text: str) -> bool:
    """Return True if spec-delta text has at least one non-header table row."""
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| Spec") or stripped.startswith("|-------"):
            in_table = True
            continue
        if in_table and stripped.startswith("|") and stripped.endswith("|"):
            # Not a separator row
            if not re.match(r"^\|[-| ]+\|$", stripped):
                return True
    return False


def validate_change_proposal(path: Path) -> list[str]:
    text = read_text(path)
    errors: list[str] = []

    for field in ["change_id", "title", "status", "proposed_by", "updated_at"]:
        if not extract_table_value(text, field):
            errors.append(f"missing metadata field `{field}`")

    updated_at = extract_table_value(text, "updated_at")
    if updated_at and "ISO8601" not in updated_at and not is_iso8601ish(strip_code(updated_at) or ""):
        errors.append("`updated_at` is not ISO8601-like")

    status = strip_code(extract_table_value(text, "status"))
    if status and status not in VALID_CHANGE_STATUSES:
        errors.append(
            f"`status` must be one of {sorted(VALID_CHANGE_STATUSES)}, got '{status}'"
        )

    if not find_section(text, "What & Why"):
        errors.append("missing `What & Why` section")

    scope = find_section(text, "Scope")
    if not scope.strip():
        errors.append("missing `Scope` section")

    if not find_section(text, "Impact"):
        errors.append("missing `Impact` section")

    return errors


def validate_toolset(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    tools = data.get("tools", [])
    if not isinstance(tools, list):
        return ["`tools` must be a list"]

    for index, tool in enumerate(tools, start=1):
        if not isinstance(tool, dict):
            errors.append(f"tool #{index} must be an object")
            continue
        for field in ("tool_id", "owner", "risk_level", "version", "manifest"):
            if not tool.get(field):
                errors.append(f"tool #{index} missing `{field}`")
        manifest = tool.get("manifest")
        if manifest:
            manifest_path = (REPO_ROOT / manifest).resolve()
            if not manifest_path.exists():
                errors.append(f"tool #{index} manifest does not exist: {manifest}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ADS collaboration markdown files.")
    parser.add_argument("--paths", nargs="*", help="Optional explicit files or directories to validate.")
    args = parser.parse_args()

    files: list[Path] = []
    if args.paths:
        for raw in args.paths:
            candidate = Path(raw).resolve()
            if candidate.is_dir():
                files.extend(path for path in candidate.rglob("*.md") if path.is_file())
            elif candidate.is_file():
                files.append(candidate)
    else:
        files.extend(discover_files(TASK_GLOBS))
        files.extend(discover_files(HANDOFF_GLOBS))
        files.extend(discover_files(MEMORY_GLOBS))
        files.extend(discover_files(REQUEST_GLOBS))
        files.extend(discover_files(QA_GLOBS))
        files.extend(discover_files(PATTERN_GLOBS))
        files.extend(discover_files(CHANGE_GLOBS))

    failures = 0

    # Phase 1：校验 constitution（始终针对 REPO_ROOT）
    constitution_errors = validate_constitution(REPO_ROOT)
    if constitution_errors:
        failures += 1
        print("[FAIL] constitution: .agent/constitution.md")
        for error in constitution_errors:
            print(f"  - {error}")
    else:
        if (REPO_ROOT / ".agent" / "constitution.md").exists():
            print("[OK] constitution: .agent/constitution.md")

    files = sorted(set(files))
    if not files:
        print("No ADS markdown files found to validate.")
        return 1 if failures else 0
    for path in files:
        rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
        kind = detect_kind(path)
        if kind is None:
            continue
        if kind == "handoff":
            errors = validate_handoff(path)
        elif kind == "task":
            errors = validate_task(path)
        elif kind == "memory":
            errors = validate_memory(path)
        elif kind == "request":
            errors = validate_request(path)
        elif kind == "qa_pass":
            errors = validate_qa_pass(path)
        elif kind == "qa_fail":
            errors = validate_qa_fail(path)
        elif kind == "change_proposal":
            errors = validate_change_proposal(path)
        else:
            errors = validate_pattern(path)
        if errors:
            failures += 1
            print(f"[FAIL] {kind}: {rel}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[OK] {kind}: {rel}")

    for toolset_path in TOOLSET_PATHS:
        if not toolset_path.exists():
            continue
        rel = toolset_path.relative_to(REPO_ROOT)
        errors = validate_toolset(toolset_path)
        if errors:
            failures += 1
            print(f"[FAIL] toolset: {rel}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[OK] toolset: {rel}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
