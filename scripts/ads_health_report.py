#!/usr/bin/env python3
"""Generate a minimal ADS collaboration health report."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TASK_GLOBS = [".ai/tasks/**/*.md", "examples/case-task-*.md"]
DEFAULT_HANDOFF_GLOBS = [".ai/handoffs/**/*.md", "examples/case-handoff-*.md"]
DEFAULT_MEMORY_GLOBS = [".ai/memory/**/*.md", "examples/case-memory-*.md"]
DEFAULT_REQUEST_GLOBS = [".ai/requests/**/*.md", "examples/case-shared-change-request*.md"]
DEFAULT_QA_GLOBS = [".ai/qa/**/*.md", "examples/case-qa-*.md"]
DEFAULT_TOOLSET_PATHS = [REPO_ROOT / "tools" / "toolset.json", REPO_ROOT / "tools" / "toolset.json.example"]


@dataclass
class TaskRecord:
    path: Path
    task_id: str
    owner_role: str
    updated_at: str
    stale_after: str
    team_pattern_id: str
    approval_owner: str


@dataclass
class HandoffRecord:
    path: Path
    task_id: str
    updated_at: str
    evidence_complete: bool
    telemetry_complete: bool
    approval_status: str


@dataclass
class ToolRecord:
    tool_id: str
    owner: str
    risk_level: str
    version: str


@dataclass
class MemoryRecord:
    memory_id: str
    freshness: str
    updated_at: str
    review_after: str


@dataclass
class RequestRecord:
    path: Path
    request_id: str
    task_id: str
    updated_at: str
    decision: str
    approval_owner: str


@dataclass
class QaRecord:
    path: Path
    task_id: str
    result: str
    timestamp: str


@dataclass
class PatternHealth:
    pattern_id: str
    task_count: int = 0
    missing_handoff: int = 0
    missing_evidence: int = 0
    pending_approvals: int = 0
    missing_qa: int = 0
    failed_qas: int = 0
    pending_requests: int = 0
    rejected_requests: int = 0


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def discover(globs: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in globs:
        files.extend(path for path in REPO_ROOT.glob(pattern) if path.is_file())
    return sorted(set(files))


def extract_table_value(text: str, label: str) -> str:
    pattern = rf"\|\s*\*\*{re.escape(label)}\*\*\s*\|\s*(.*?)\s*\|"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def strip_code(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        return value[1:-1].strip()
    return value


def find_section(text: str, title: str) -> str:
    pattern = rf"^## {re.escape(title)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, flags=re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def detect_kind(path: Path) -> str | None:
    text = read_text(path)
    if text.startswith("# 任务："):
        return "task"
    if text.startswith("# ADS Handoff"):
        return "handoff"
    if text.startswith("# Shared Change Request"):
        return "request"
    if text.startswith("# QA 结论：PASS"):
        return "qa_pass"
    if text.startswith("# QA 结论：FAIL"):
        return "qa_fail"
    return None


def parse_task(path: Path) -> TaskRecord | None:
    text = read_text(path)
    if detect_kind(path) != "task":
        return None
    freshness = find_section(text, "Freshness")
    stale_match = re.search(r"\*\*stale_after\*\*.*?：(.+)", freshness)
    return TaskRecord(
        path=path,
        task_id=strip_code(extract_table_value(text, "task_id")) or path.stem,
        owner_role=strip_code(extract_table_value(text, "owner_role")) or "unknown",
        updated_at=strip_code(extract_table_value(text, "updated_at")),
        stale_after=strip_code(stale_match.group(1).strip()) if stale_match else "",
        team_pattern_id=strip_code(extract_table_value(text, "team_pattern_id")),
        approval_owner=strip_code(extract_table_value(text, "approval_owner")),
    )


def parse_handoff(path: Path) -> HandoffRecord | None:
    text = read_text(path)
    if detect_kind(path) != "handoff":
        return None
    evidence = find_section(text, "Evidence expectation")
    row_pattern = re.compile(
        r"^\|\s*`?([^|`]+)`?\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|$",
        re.MULTILINE,
    )
    evidence_complete = False
    telemetry_pattern = re.compile(
        r"^\|\s*`?([^|`]+)`?\s*\|\s*`?([^|`]*)`?\s*\|\s*`?([^|`]*)`?\s*\|\s*`?([^|`]*)`?\s*\|$",
        re.MULTILINE,
    )
    for match in row_pattern.finditer(evidence):
        item, executed_by, executed_at, result, artifact_paths, review_status = [part.strip() for part in match.groups()]
        if item == "evidence_item":
            continue
        if executed_by and executed_at and result not in {"", "pass / fail"} and artifact_paths and review_status not in {"", "pending / reviewed"}:
            evidence_complete = True
            break
    telemetry_complete = False
    if "Evidence telemetry" in evidence:
        for match in telemetry_pattern.finditer(evidence):
            item, duration_ms, cost_usd, retry_count = [part.strip() for part in match.groups()]
            if item == "evidence_item":
                continue
            if duration_ms or cost_usd or retry_count:
                telemetry_complete = True
                break
    return HandoffRecord(
        path=path,
        task_id=strip_code(extract_table_value(text, "task_id")) or path.stem,
        updated_at=strip_code(extract_table_value(text, "updated_at")),
        evidence_complete=evidence_complete,
        telemetry_complete=telemetry_complete,
        approval_status=strip_code(re.search(r"\*\*approval_status\*\*：(.+)", find_section(text, "Approval")).group(1).strip())
        if re.search(r"\*\*approval_status\*\*：(.+)", find_section(text, "Approval"))
        else "",
    )


def parse_toolset(path: Path) -> list[ToolRecord]:
    if not path.exists():
        return []
    data = json.loads(read_text(path))
    records: list[ToolRecord] = []
    for tool in data.get("tools", []):
        if not isinstance(tool, dict):
            continue
        records.append(
            ToolRecord(
                tool_id=str(tool.get("tool_id", "")),
                owner=str(tool.get("owner", "")),
                risk_level=str(tool.get("risk_level", "")),
                version=str(tool.get("version", "")),
            )
        )
    return records


def parse_memory(path: Path) -> MemoryRecord | None:
    text = read_text(path)
    if not text.startswith("# Memory Object"):
        return None
    return MemoryRecord(
        memory_id=strip_code(extract_table_value(text, "memory_id")) or path.stem,
        freshness=strip_code(extract_table_value(text, "freshness")) or "durable",
        updated_at=strip_code(extract_table_value(text, "updated_at")),
        review_after=strip_code(extract_table_value(text, "review_after")),
    )


def parse_request(path: Path) -> RequestRecord | None:
    text = read_text(path)
    if detect_kind(path) != "request":
        return None
    decision_section = find_section(text, "Decision")
    decision_match = re.search(r"\*\*结论\*\*：`?(pending|approved|rejected)`?", decision_section)
    return RequestRecord(
        path=path,
        request_id=strip_code(extract_table_value(text, "request_id")) or path.stem,
        task_id=strip_code(extract_table_value(text, "task_id")) or "unknown",
        updated_at=strip_code(extract_table_value(text, "updated_at")),
        decision=decision_match.group(1) if decision_match else "unknown",
        approval_owner=strip_code(extract_table_value(text, "approval_owner")) or "unknown",
    )


def parse_qa(path: Path) -> QaRecord | None:
    text = read_text(path)
    kind = detect_kind(path)
    if kind not in {"qa_pass", "qa_fail"}:
        return None
    return QaRecord(
        path=path,
        task_id=strip_code(extract_table_value(text, "task_id")) or path.stem,
        result="pass" if kind == "qa_pass" else "fail",
        timestamp=strip_code(extract_table_value(text, "Timestamp")),
    )


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
    value = value.strip()
    match = re.match(r"^P(\d+)D$", value)
    if not match:
        return None
    return timedelta(days=int(match.group(1)))


def is_stale(updated_at: str, stale_after: str, now: datetime) -> bool:
    updated = parse_iso8601(updated_at)
    duration = parse_duration(stale_after)
    if not updated or not duration:
        return False
    return updated + duration < now


def build_report(
    tasks: list[TaskRecord],
    handoffs: list[HandoffRecord],
    tools: list[ToolRecord],
    memories: list[MemoryRecord],
    requests: list[RequestRecord],
    qas: list[QaRecord],
    now: datetime,
) -> str:
    handoff_by_task = {record.task_id: record for record in handoffs}
    task_by_id = {task.task_id: task for task in tasks}
    missing_handoff = [task for task in tasks if task.task_id not in handoff_by_task]
    missing_evidence = [
        task for task in tasks
        if task.task_id in handoff_by_task and not handoff_by_task[task.task_id].evidence_complete
    ]
    missing_telemetry = [
        task for task in tasks
        if task.task_id in handoff_by_task and not handoff_by_task[task.task_id].telemetry_complete
    ]
    handoffs_with_telemetry = [handoff for handoff in handoffs if handoff.telemetry_complete]
    stale_tasks = [task for task in tasks if is_stale(task.updated_at, task.stale_after, now)]
    pending_approvals = [
        task for task in tasks
        if task.task_id in handoff_by_task and handoff_by_task[task.task_id].approval_status == "pending"
    ]
    pending_requests = [request for request in requests if request.decision == "pending"]
    rejected_requests = [request for request in requests if request.decision == "rejected"]
    high_risk_tools = [tool for tool in tools if tool.risk_level.lower() in {"high", "critical"}]
    stale_memories = []
    for memory in memories:
        updated = parse_iso8601(memory.updated_at)
        review_after = parse_duration(memory.review_after)
        if updated and review_after and updated + review_after < now:
            stale_memories.append(memory)
    qa_by_task: dict[str, list[QaRecord]] = {}
    for qa in qas:
        qa_by_task.setdefault(qa.task_id, []).append(qa)
    missing_qa = [task for task in tasks if task.task_id not in qa_by_task]
    failed_qas = [qa for qa in qas if qa.result == "fail"]
    passed_qas = [qa for qa in qas if qa.result == "pass"]
    pattern_health: dict[str, PatternHealth] = {}

    def get_pattern_health(task: TaskRecord | None) -> PatternHealth:
        pattern_id = task.team_pattern_id if task and task.team_pattern_id else "unpatterned"
        if pattern_id not in pattern_health:
            pattern_health[pattern_id] = PatternHealth(pattern_id=pattern_id)
        return pattern_health[pattern_id]

    for task in tasks:
        get_pattern_health(task).task_count += 1
    for task in missing_handoff:
        get_pattern_health(task).missing_handoff += 1
    for task in missing_evidence:
        get_pattern_health(task).missing_evidence += 1
    for task in pending_approvals:
        get_pattern_health(task).pending_approvals += 1
    for task in missing_qa:
        get_pattern_health(task).missing_qa += 1
    for qa in failed_qas:
        get_pattern_health(task_by_id.get(qa.task_id)).failed_qas += 1
    for request in pending_requests:
        get_pattern_health(task_by_id.get(request.task_id)).pending_requests += 1
    for request in rejected_requests:
        get_pattern_health(task_by_id.get(request.task_id)).rejected_requests += 1

    lines = [
        "# ADS Health Report",
        "",
        f"- generated_at: {now.isoformat().replace('+00:00', 'Z')}",
        f"- total_tasks: {len(tasks)}",
        f"- total_handoffs: {len(handoffs)}",
        f"- total_requests: {len(requests)}",
        f"- total_qas: {len(qas)}",
        f"- missing_handoff: {len(missing_handoff)}",
        f"- missing_evidence: {len(missing_evidence)}",
        f"- handoffs_with_telemetry: {len(handoffs_with_telemetry)}",
        f"- missing_telemetry: {len(missing_telemetry)}",
        f"- stale_tasks: {len(stale_tasks)}",
        f"- stale_memories: {len(stale_memories)}",
        f"- pending_approvals: {len(pending_approvals)}",
        f"- pending_requests: {len(pending_requests)}",
        f"- rejected_requests: {len(rejected_requests)}",
        f"- missing_qa: {len(missing_qa)}",
        f"- failed_qas: {len(failed_qas)}",
        f"- high_risk_tools: {len(high_risk_tools)}",
        "",
        "## Missing Handoff",
    ]
    lines.extend(
        f"- {task.task_id} ({task.owner_role}) — {task.path.relative_to(REPO_ROOT)}"
        for task in (missing_handoff or [])
    )
    if not missing_handoff:
        lines.append("- none")

    lines.append("")
    lines.append("## Missing Evidence")
    lines.extend(
        f"- {task.task_id} — handoff exists but structured evidence is incomplete"
        for task in (missing_evidence or [])
    )
    if not missing_evidence:
        lines.append("- none")

    lines.append("")
    lines.append("## Evidence Telemetry Coverage")
    lines.extend(
        f"- {task.task_id} — handoff exists but telemetry is still empty"
        for task in (missing_telemetry or [])
    )
    if not missing_telemetry:
        lines.append("- none")

    lines.append("")
    lines.append("## Stale Tasks")
    lines.extend(
        f"- {task.task_id} — updated_at={task.updated_at}, stale_after={task.stale_after}"
        for task in (stale_tasks or [])
    )
    if not stale_tasks:
        lines.append("- none")

    lines.append("")
    lines.append("## Stale Memories")
    lines.extend(
        f"- {memory.memory_id} — updated_at={memory.updated_at}, review_after={memory.review_after}"
        for memory in (stale_memories or [])
    )
    if not stale_memories:
        lines.append("- none")

    lines.append("")
    lines.append("## Pending Approvals")
    lines.extend(
        f"- {task.task_id} — approval_owner={task.approval_owner or 'unknown'}"
        for task in (pending_approvals or [])
    )
    if not pending_approvals:
        lines.append("- none")

    lines.append("")
    lines.append("## Pending Requests")
    lines.extend(
        f"- {request.request_id} -> {request.task_id} — approval_owner={request.approval_owner}"
        for request in (pending_requests or [])
    )
    if not pending_requests:
        lines.append("- none")

    lines.append("")
    lines.append("## Rejected Requests")
    lines.extend(
        f"- {request.request_id} -> {request.task_id} — {request.path.relative_to(REPO_ROOT)}"
        for request in (rejected_requests or [])
    )
    if not rejected_requests:
        lines.append("- none")

    lines.append("")
    lines.append("## Missing QA")
    lines.extend(
        f"- {task.task_id} ({task.owner_role}) — no QA result found"
        for task in (missing_qa or [])
    )
    if not missing_qa:
        lines.append("- none")

    lines.append("")
    lines.append("## QA Results")
    lines.extend(
        f"- PASS {qa.task_id} — {qa.path.relative_to(REPO_ROOT)}"
        for qa in passed_qas
    )
    lines.extend(
        f"- FAIL {qa.task_id} — {qa.path.relative_to(REPO_ROOT)}"
        for qa in failed_qas
    )
    if not qas:
        lines.append("- none")

    lines.append("")
    lines.append("## Team Patterns")
    for task in tasks:
        if task.team_pattern_id:
            lines.append(f"- {task.task_id} -> {task.team_pattern_id}")
    if not any(task.team_pattern_id for task in tasks):
        lines.append("- none declared")

    lines.append("")
    lines.append("## Team Pattern Health")
    for pattern_id in sorted(pattern_health):
        health = pattern_health[pattern_id]
        blockers = []
        if health.missing_handoff:
            blockers.append(f"missing_handoff={health.missing_handoff}")
        if health.missing_evidence:
            blockers.append(f"missing_evidence={health.missing_evidence}")
        if health.pending_approvals:
            blockers.append(f"pending_approvals={health.pending_approvals}")
        if health.pending_requests:
            blockers.append(f"pending_requests={health.pending_requests}")
        if health.rejected_requests:
            blockers.append(f"rejected_requests={health.rejected_requests}")
        if health.missing_qa:
            blockers.append(f"missing_qa={health.missing_qa}")
        if health.failed_qas:
            blockers.append(f"failed_qas={health.failed_qas}")
        blocker_text = ", ".join(blockers) if blockers else "clear"
        lines.append(f"- {pattern_id}: tasks={health.task_count}, blockers={blocker_text}")
    if not pattern_health:
        lines.append("- none")

    lines.append("")
    lines.append("## High Risk Tools")
    lines.extend(
        f"- {tool.tool_id} — owner={tool.owner}, version={tool.version}, risk={tool.risk_level}"
        for tool in (high_risk_tools or [])
    )
    if not high_risk_tools:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a minimal ADS collaboration health report.")
    parser.add_argument("--output", help="Optional markdown output path")
    parser.add_argument("--paths", nargs="*", help="Optional files or directories to scan")
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
        files.extend(discover(DEFAULT_TASK_GLOBS))
        files.extend(discover(DEFAULT_HANDOFF_GLOBS))
        files.extend(discover(DEFAULT_REQUEST_GLOBS))
        files.extend(discover(DEFAULT_QA_GLOBS))

    tasks = [record for path in sorted(set(files)) if (record := parse_task(path))]
    handoffs = [record for path in sorted(set(files)) if (record := parse_handoff(path))]
    requests = [record for path in sorted(set(files)) if (record := parse_request(path))]
    qas = [record for path in sorted(set(files)) if (record := parse_qa(path))]
    tools: list[ToolRecord] = []
    for path in DEFAULT_TOOLSET_PATHS:
        if path.exists():
            tools = parse_toolset(path)
            break
    memories = [record for path in discover(DEFAULT_MEMORY_GLOBS) if (record := parse_memory(path))]
    now = datetime.now(timezone.utc)
    report = build_report(tasks, handoffs, tools, memories, requests, qas, now)

    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
