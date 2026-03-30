#!/usr/bin/env python3
"""Serve a lightweight local ADS dashboard."""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import ads_explain
import ads_health_report
import ads_resume


REPO_ROOT = Path(__file__).resolve().parent.parent
JSON = dict[str, Any]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def discover(repo_root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in repo_root.glob(pattern) if path.is_file() and path.name != ".gitkeep")


def parse_iso8601(value: str) -> datetime | None:
    if not value:
        return None
    raw = value.strip().strip("`")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def sort_paths_by_updated(paths: list[Path], updated_getter: callable) -> list[Path]:
    return sorted(paths, key=lambda path: updated_getter(path) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)


def parse_task(path: Path, repo_root: Path) -> JSON:
    text = read_text(path)
    title_match = re.search(r"^# 任务：(.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    task_id = ads_resume.extract_table_value(text, "task_id") or path.stem
    owner_role = ads_resume.extract_table_value(text, "owner_role") or "unknown"
    updated_at = ads_resume.extract_table_value(text, "updated_at") or ""
    goal = ads_resume.find_section(text, "背景与目标").splitlines()[0].strip() if ads_resume.find_section(text, "背景与目标") else "unknown"
    related_paths = ads_resume.extract_table_first_column(ads_resume.find_section(text, "相关路径"))
    return {
        "task_id": task_id,
        "title": title,
        "owner_role": owner_role,
        "updated_at": updated_at,
        "goal": goal,
        "path": path.relative_to(repo_root).as_posix(),
        "related_paths": related_paths,
    }


def parse_handoff(path: Path, repo_root: Path) -> JSON:
    text = read_text(path)
    record = ads_health_report.parse_handoff(path)
    next_action_match = re.search(r"\*\*建议下一动作\*\*[:：](.*)", text)
    current_status_match = re.search(r"\*\*当前状态\*\*[:：](.*)", text)
    telemetry_rows = re.findall(
        r"^\|\s*`?([^|`]+)`?\s*\|\s*`?([^|`]*)`?\s*\|\s*`?([^|`]*)`?\s*\|\s*`?([^|`]*)`?\s*\|$",
        ads_resume.find_section(text, "Evidence expectation"),
        flags=re.MULTILINE,
    )
    populated_telemetry = [
        {"item": item.strip(), "duration_ms": duration.strip(), "cost_usd": cost.strip(), "retry_count": retry.strip()}
        for item, duration, cost, retry in telemetry_rows
        if item.strip() != "evidence_item" and any(part.strip() for part in (duration, cost, retry))
    ]
    return {
        "task_id": record.task_id if record else path.stem,
        "updated_at": record.updated_at if record else "",
        "approval_status": record.approval_status if record else "unknown",
        "evidence_complete": bool(record and record.evidence_complete),
        "telemetry_complete": bool(record and record.telemetry_complete),
        "next_action": next_action_match.group(1).strip() if next_action_match else "Review latest handoff.",
        "current_status": current_status_match.group(1).strip() if current_status_match else "unknown",
        "path": path.relative_to(repo_root).as_posix(),
        "telemetry": populated_telemetry,
    }


def parse_escalation(path: Path, repo_root: Path) -> JSON:
    text = read_text(path)
    current_block = ""
    for line in ads_resume.find_section(text, "Current Block").splitlines():
        stripped = line.strip()
        if stripped.startswith("**当前阻塞**"):
            current_block = stripped.split("：", 1)[-1].strip()
            break
    return {
        "task_id": ads_resume.extract_table_value(text, "task_id") or path.stem,
        "status": ads_resume.extract_table_value(text, "status") or "unknown",
        "decision_owner": ads_resume.extract_table_value(text, "decision_owner") or "unknown",
        "updated_at": ads_resume.extract_table_value(text, "updated_at") or "",
        "current_block": current_block or "unknown",
        "path": path.relative_to(repo_root).as_posix(),
    }


def parse_qa(path: Path, repo_root: Path) -> JSON:
    record = ads_health_report.parse_qa(path)
    return {
        "task_id": record.task_id if record else path.stem,
        "result": record.result if record else "unknown",
        "timestamp": record.timestamp if record else "",
        "path": path.relative_to(repo_root).as_posix(),
    }


def telemetry_coverage(handoffs: list[JSON]) -> int:
    if not handoffs:
        return 0
    covered = sum(1 for handoff in handoffs if handoff["telemetry_complete"])
    return int(round(covered * 100 / len(handoffs)))


def latest(items: list[JSON], key: str) -> JSON | None:
    if not items:
        return None
    return sorted(items, key=lambda item: parse_iso8601(str(item.get(key, ""))) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[0]


def workspace_label(status: str) -> str:
    return {
        "ads_ready": "ADS 已接入",
        "partial_ads": "ADS 部分接入",
        "needs_bootstrap": "尚未接入 ADS",
    }.get(status, status)


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            items.append(cleaned)
    return items


def build_guidance(
    repo_root: Path,
    docs_entry: JSON,
    workspace_status: str,
    primary_task: JSON | None,
) -> JSON:
    install_report = str(docs_entry.get("install_report", "")).strip()
    read_this_first = unique_strings(
        [
            str(docs_entry.get("readme", "README.md")),
            ".ai/START_HERE.md" if (repo_root / ".ai" / "START_HERE.md").exists() else "",
            ".agent/constitution.md" if (repo_root / ".agent" / "constitution.md").exists() else "",
            str(docs_entry.get("project_brief", "")),
            install_report,
            str(docs_entry.get("ai_context", "")),
        ]
    )

    if workspace_status == "needs_bootstrap":
        next_commands = [
            "python3 scripts/ads_init.py /path/to/your-project",
            "python3 scripts/ads_adopt.py /path/to/your-project --apply",
        ]
    else:
        next_commands = [
            "python3 scripts/ads_explain.py",
            "python3 scripts/ads_dashboard.py",
            "python3 scripts/ads_doctor.py",
            "python3 scripts/validate_ads.py",
        ]
        if primary_task:
            next_commands.append(f"python3 scripts/ads_resume.py {primary_task['path']}")

    return {
        "workspace_label": workspace_label(workspace_status),
        "read_this_first": read_this_first,
        "next_commands": next_commands,
        "first_step": (
            "先读 README.md 和 ADS install report，再从 backlog 选择第一个真实任务。"
            if install_report and not primary_task
            else "先读 README.md，确认当前任务和下一步动作。"
        ),
        "empty_state": "当前仓库还没有 active task，建议先从 backlog 激活一个真实任务。"
        if not primary_task
        else "",
        "backlog_hint": ".ai/tasks/backlog/",
    }


def build_homepage(project: JSON, metrics: JSON, focus: JSON) -> JSON:
    pending_block = bool(focus.get("escalation"))
    return {
        "project_home_title": "项目首页",
        "project_home_summary": "先理解项目使命与阶段，再进入具体代码与任务细节。",
        "control_panel_title": "今日控制台",
        "control_panel_summary": "这里汇总当前最重要任务、下一步动作、阻塞和审批状态。",
        "ads_role": "ADS 是这个仓库的协作控制面：任务、交接、证据、审批和恢复都应落在仓库文件里，而不是只存在聊天记录中。",
        "status_lines": [
            f"总体状态：{project['overall_status']}",
            f"待审批：{metrics['pending_approvals']}",
            f"阻塞数：{metrics['active_escalations']}",
            "当前存在人工决策阻塞，请优先处理。" if pending_block else "当前没有人工决策阻塞，可以继续推进。",
        ],
    }


def build_snapshot(repo_root: Path = REPO_ROOT) -> JSON:
    docs_entry = ads_explain.load_docs_entry(repo_root)
    active_task_paths = sort_paths_by_updated(
        discover(repo_root, ".ai/tasks/active/*.md"),
        lambda path: parse_iso8601(ads_resume.extract_table_value(read_text(path), "updated_at") or ""),
    )
    backlog_task_paths = discover(repo_root, ".ai/tasks/backlog/*.md")
    handoff_paths = sort_paths_by_updated(
        discover(repo_root, ".ai/handoffs/*.md"),
        lambda path: parse_iso8601(ads_resume.extract_table_value(read_text(path), "updated_at") or ""),
    )
    escalation_paths = sort_paths_by_updated(
        discover(repo_root, ".ai/escalations/*.md"),
        lambda path: parse_iso8601(ads_resume.extract_table_value(read_text(path), "updated_at") or ""),
    )
    qa_paths = sort_paths_by_updated(
        discover(repo_root, ".ai/qa/*.md"),
        lambda path: parse_iso8601(ads_health_report.parse_qa(path).timestamp if ads_health_report.parse_qa(path) else ""),
    )

    tasks = [parse_task(path, repo_root) for path in active_task_paths]
    handoffs = [parse_handoff(path, repo_root) for path in handoff_paths]
    escalations = [parse_escalation(path, repo_root) for path in escalation_paths]
    qas = [parse_qa(path, repo_root) for path in qa_paths]

    primary_task = tasks[0] if tasks else None
    primary_handoff = next((handoff for handoff in handoffs if primary_task and handoff["task_id"] == primary_task["task_id"]), latest(handoffs, "updated_at"))
    primary_escalation = next((item for item in escalations if primary_task and item["task_id"] == primary_task["task_id"]), latest(escalations, "updated_at"))
    latest_qa = latest(qas, "timestamp")
    latest_handoff = latest(handoffs, "updated_at")

    metrics = {
        "active_tasks": len(tasks),
        "active_escalations": len([item for item in escalations if item["status"] == "pending"]),
        "pending_approvals": len([item for item in handoffs if item["approval_status"] == "pending"]),
        "recent_qa_status": latest_qa["result"].upper() if latest_qa else "NONE",
        "telemetry_coverage": telemetry_coverage(handoffs),
        "last_updated": latest_handoff["updated_at"] if latest_handoff else (primary_task["updated_at"] if primary_task else "unknown"),
    }

    if primary_escalation and primary_escalation["status"] == "pending":
        overall_status = "阻塞中"
    elif metrics["pending_approvals"] or metrics["active_escalations"]:
        overall_status = "需要关注"
    else:
        overall_status = "正常推进"

    focus = {
        "task_id": primary_task["task_id"] if primary_task else "none",
        "title": primary_task["title"] if primary_task else "当前没有进行中任务",
        "owner_role": primary_task["owner_role"] if primary_task else "unknown",
        "goal": primary_task["goal"] if primary_task else "请从 backlog 中选择任务开始推进。",
        "next_action": (
            primary_handoff["next_action"]
            if primary_handoff
            else ("先生成或更新当前 task 的 handoff。" if primary_task else "先从 backlog 选择一个任务，再补当前 handoff。")
        ),
        "path": primary_task["path"] if primary_task else "",
        "escalation": primary_escalation,
        "related_paths": primary_task["related_paths"] if primary_task else [],
    }

    recent_progress = {
        "latest_handoff": latest_handoff,
        "latest_qa": latest_qa,
        "latest_telemetry": (latest_handoff["telemetry"][0] if latest_handoff and latest_handoff["telemetry"] else None),
    }

    actions = [
        {"label": "进入当前任务", "href": "/detail?mode=task"},
        {"label": "查看阻塞项", "href": "/detail?mode=risk"},
        {"label": "查看健康报告", "href": "/detail?mode=health"},
        {"label": "刷新页面", "href": "/"},
    ]

    return {
        "project": {
            "name": ads_explain.load_project_name(repo_root),
            "mission": ads_explain.load_mission(repo_root),
            "current_stage": ads_explain.load_current_stage(repo_root),
            "overall_status": overall_status,
            "workspace_status": ads_explain.infer_workspace_status(repo_root),
            "docs_entry": docs_entry,
        },
        "metrics": metrics,
        "homepage": build_homepage(
            {
                "name": ads_explain.load_project_name(repo_root),
                "mission": ads_explain.load_mission(repo_root),
                "current_stage": ads_explain.load_current_stage(repo_root),
                "overall_status": overall_status,
            },
            metrics,
            focus,
        ),
        "focus": focus,
        "recent_progress": recent_progress,
        "guidance": build_guidance(repo_root, docs_entry, ads_explain.infer_workspace_status(repo_root), primary_task),
        "actions": actions,
        "collections": {
            "tasks": tasks,
            "backlog_tasks": [path.relative_to(repo_root).as_posix() for path in backlog_task_paths],
            "handoffs": handoffs,
            "escalations": escalations,
            "qas": qas,
        },
    }


def metric_card(label: str, value: Any, href: str) -> str:
    return f"""
    <a class="metric-card" href="{html.escape(href)}">
      <span class="metric-label">{html.escape(str(label))}</span>
      <strong class="metric-value">{html.escape(str(value))}</strong>
    </a>
    """


def render_layout(title: str, subtitle: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #f4f7f6;
      --panel: #ffffff;
      --line: #dce6e3;
      --ink: #152321;
      --muted: #617775;
      --brand: #0d5c63;
      --accent: #1f8a70;
      --warn: #d95d39;
      --soft: #e8f2f0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "SF Pro SC","PingFang SC","Noto Sans SC",sans-serif;
      background:
        radial-gradient(circle at top left, rgba(31,138,112,0.10), transparent 32%),
        linear-gradient(180deg, #f8fbfa 0%, var(--bg) 100%);
      color: var(--ink);
    }}
    a {{ color: inherit; text-decoration: none; }}
    .page {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 28px 20px 44px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.6fr 0.9fr;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .panel {{
      background: rgba(255,255,255,0.88);
      backdrop-filter: blur(8px);
      border: 1px solid var(--line);
      border-radius: 24px;
      padding: 22px;
      box-shadow: 0 18px 40px rgba(24, 46, 43, 0.08);
    }}
    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--brand);
      margin-bottom: 12px;
    }}
    h1, h2, h3, p {{ margin: 0; }}
    h1 {{
      font-size: clamp(32px, 5vw, 56px);
      line-height: 0.98;
      margin-bottom: 12px;
      letter-spacing: -0.04em;
    }}
    .subtitle {{
      font-size: 18px;
      line-height: 1.6;
      color: var(--muted);
      max-width: 60ch;
    }}
    .status-badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      padding: 10px 14px;
      background: var(--soft);
      color: var(--brand);
      font-weight: 700;
      margin-bottom: 16px;
    }}
    .status-badge.warn {{
      background: rgba(217,93,57,0.12);
      color: var(--warn);
    }}
    .meta-list, .stack-list {{
      display: grid;
      gap: 10px;
      margin-top: 18px;
      color: var(--muted);
      font-size: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 18px;
    }}
    .span-12 {{ grid-column: span 12; }}
    .span-7 {{ grid-column: span 7; }}
    .span-5 {{ grid-column: span 5; }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-top: 16px;
    }}
    .metric-card {{
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 16px;
      border-radius: 18px;
      background: linear-gradient(180deg, #fcfefd 0%, #f3f8f7 100%);
      border: 1px solid var(--line);
      transition: transform 0.18s ease, box-shadow 0.18s ease;
    }}
    .metric-card:hover {{
      transform: translateY(-2px);
      box-shadow: 0 10px 24px rgba(24, 46, 43, 0.08);
    }}
    .metric-label {{
      font-size: 13px;
      color: var(--muted);
    }}
    .metric-value {{
      font-size: 30px;
      letter-spacing: -0.04em;
    }}
    .section-title {{
      font-size: 20px;
      margin-bottom: 14px;
      letter-spacing: -0.03em;
    }}
    .focus-card {{
      display: grid;
      gap: 14px;
    }}
    .focus-head {{
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
    }}
    .focus-title {{
      font-size: 28px;
      line-height: 1.1;
      letter-spacing: -0.04em;
    }}
    .focus-meta, .list {{
      display: grid;
      gap: 10px;
      color: var(--muted);
      font-size: 14px;
    }}
    .attention {{
      padding: 14px 16px;
      border-radius: 18px;
      border: 1px solid rgba(217,93,57,0.25);
      background: rgba(217,93,57,0.07);
      color: #7f2d1b;
    }}
    .progress-card {{
      display: grid;
      gap: 14px;
    }}
    .progress-item {{
      padding: 14px 16px;
      border-radius: 18px;
      background: #f8fbfa;
      border: 1px solid var(--line);
    }}
    .action-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 14px;
      margin-top: 12px;
    }}
    .action-card {{
      padding: 16px 18px;
      border-radius: 18px;
      background: linear-gradient(160deg, rgba(13,92,99,0.10), rgba(31,138,112,0.08));
      border: 1px solid rgba(13,92,99,0.18);
      font-weight: 700;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--soft);
      color: var(--brand);
      font-size: 12px;
      font-weight: 700;
    }}
    .nav {{
      display: flex;
      gap: 10px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }}
    .nav a {{
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(13,92,99,0.08);
      color: var(--brand);
      font-weight: 700;
    }}
    pre {{
      margin: 0;
      padding: 14px 16px;
      border-radius: 18px;
      background: #f8fbfa;
      border: 1px solid var(--line);
      white-space: pre-wrap;
      word-break: break-word;
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 13px;
      color: #244340;
    }}
    @media (max-width: 900px) {{
      .hero, .grid {{ grid-template-columns: 1fr; }}
      .span-7, .span-5, .span-12 {{ grid-column: span 1; }}
      .metric-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .action-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 640px) {{
      .page {{ padding: 18px 14px 28px; }}
      .metric-grid, .action-grid {{ grid-template-columns: 1fr; }}
      h1 {{ font-size: 34px; }}
      .focus-title {{ font-size: 24px; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <div class="nav">
      <a href="/">概览</a>
      <a href="/detail?mode=task">详情：任务</a>
      <a href="/detail?mode=risk">详情：风险</a>
      <a href="/detail?mode=health">详情：健康</a>
    </div>
    {body}
  </main>
</body>
</html>"""


def render_overview_page(snapshot: JSON) -> str:
    project = snapshot["project"]
    metrics = snapshot["metrics"]
    homepage = snapshot["homepage"]
    focus = snapshot["focus"]
    recent = snapshot["recent_progress"]
    guidance = snapshot["guidance"]
    status_class = "warn" if project["overall_status"] != "正常推进" else ""
    latest_handoff = recent["latest_handoff"]
    latest_qa = recent["latest_qa"]
    latest_telemetry = recent["latest_telemetry"]
    read_list = "".join(f"<span>{html.escape(item)}</span>" for item in guidance["read_this_first"])
    command_text = html.escape("\n".join(guidance["next_commands"]))
    mission_text = project["mission"] if project["mission"] != "unknown" else "请先在 .agent/constitution.md 中补充项目使命。"
    stage_text = project["current_stage"] if project["current_stage"] != "unknown" else "请在 .ai/START_HERE.md 中声明当前阶段。"
    empty_state = (
        f"<div class='attention'><strong>空状态提示：</strong>{html.escape(guidance['empty_state'])}<br><span>建议先查看 {html.escape(guidance['backlog_hint'])}</span></div>"
        if guidance["empty_state"]
        else ""
    )
    first_step_card = (
        f"""
          <div class="progress-item">
            <strong>接入后第一步</strong>
            <div class="list" style="margin-top:10px;">
              <span>{html.escape(guidance['first_step'])}</span>
              <span>{html.escape(project['docs_entry'].get('install_report', 'README.md'))}</span>
            </div>
          </div>
        """
        if guidance["empty_state"]
        else ""
    )
    body = f"""
    <section class="hero">
      <div class="panel">
        <div class="eyebrow">ADS Local Dashboard</div>
        <h1>{html.escape(homepage['project_home_title'])}</h1>
        <p class="subtitle">{html.escape(project['name'])} · {html.escape(mission_text)}</p>
        <div class="meta-list">
          <span>当前阶段：{html.escape(stage_text)}</span>
          <span>工作区状态：{html.escape(guidance['workspace_label'])}</span>
          <span>{html.escape(homepage['project_home_summary'])}</span>
          <span>{html.escape(homepage['ads_role'])}</span>
        </div>
      </div>
      <div class="panel">
        <div class="eyebrow">Today Control</div>
        <h2 class="section-title" style="margin-bottom:10px;">{html.escape(homepage['control_panel_title'])}</h2>
        <div class="status-badge {status_class}">{html.escape(project['overall_status'])}</div>
        <div class="stack-list">
          <span>{html.escape(homepage['control_panel_summary'])}</span>
          <span>当前重点：{html.escape(focus['title'])}</span>
          <span>下一步动作：{html.escape(focus['next_action'])}</span>
          <span>最近更新时间：{html.escape(str(metrics['last_updated']))}</span>
          <span>项目简报：{html.escape(project['docs_entry'].get('project_brief', '未声明'))}</span>
          <span>主上下文：{html.escape(project['docs_entry'].get('ai_context', '未声明'))}</span>
          {"".join(f"<span>{html.escape(line)}</span>" for line in homepage['status_lines'])}
        </div>
      </div>
    </section>

    <section class="panel" style="margin-top:18px;">
      <h2 class="section-title">项目全局概览</h2>
      <div class="list">
        <span>这是一个以仓库为中心的人机协作控制面首页，而不是传统 admin dashboard。</span>
        <span>目标是让新成员先理解项目，再让续做成员直接进入任务推进。</span>
      </div>
    </section>

    <section class="grid" style="margin-top:18px;">
      <div class="panel span-7">
        <h2 class="section-title">快速上手</h2>
        <div class="progress-card">
          <div class="progress-item">
            <strong>1. 先读这些文档</strong>
            <div class="list" style="margin-top:10px;">
              {read_list}
            </div>
          </div>
          <div class="progress-item">
            <strong>2. 当前 ADS 状态</strong>
            <div class="list" style="margin-top:10px;">
              <span>{html.escape(guidance['workspace_label'])}</span>
              <span>项目当前阶段：{html.escape(stage_text)}</span>
              <span>项目总状态：{html.escape(project['overall_status'])}</span>
            </div>
          </div>
          {first_step_card}
          <div class="progress-item">
            <strong>3. 建议命令</strong>
            <pre>{command_text}</pre>
          </div>
        </div>
      </div>
      <div class="panel span-5">
        <h2 class="section-title">使用建议</h2>
        <div class="progress-card">
          <div class="progress-item">
            <strong>新成员入口</strong>
            <div class="list" style="margin-top:10px;">
              <span>先理解项目使命、当前阶段、主上下文，再进入代码。</span>
              <span>优先使用结构化 task / handoff，不要从聊天记录倒推状态。</span>
            </div>
          </div>
          <div class="progress-item">
            <strong>续做成员入口</strong>
            <div class="list" style="margin-top:10px;">
              <span>从 active task 和最近 handoff 恢复上下文。</span>
              <span>如果卡住，先看 `.ai/escalations/`，不要自行猜测决策。</span>
            </div>
          </div>
          {empty_state}
        </div>
      </div>
    </section>

    <section class="panel">
      <h2 class="section-title">关键指标</h2>
      <div class="metric-grid">
        {metric_card("活跃任务数", metrics["active_tasks"], "/detail?mode=task")}
        {metric_card("阻塞数", metrics["active_escalations"], "/detail?mode=risk")}
        {metric_card("待审批数", metrics["pending_approvals"], "/detail?mode=risk")}
        {metric_card("最近 QA", metrics["recent_qa_status"], "/detail?mode=health")}
        {metric_card("Telemetry 覆盖率", f"{metrics['telemetry_coverage']}%", "/detail?mode=health")}
        {metric_card("工作区状态", project["workspace_status"], "/detail?mode=health")}
      </div>
    </section>

    <section class="grid" style="margin-top:18px;">
      <div class="panel span-7">
        <h2 class="section-title">当前重点</h2>
        <div class="focus-card">
          <div class="focus-head">
            <div>
              <div class="pill">{html.escape(focus['task_id'])}</div>
              <div class="focus-title" style="margin-top:10px;">{html.escape(focus['title'])}</div>
            </div>
            <div class="pill">{html.escape(focus['owner_role'])}</div>
          </div>
          <p class="subtitle">{html.escape(focus['goal'])}</p>
          <div class="focus-meta">
            <span>下一步动作：{html.escape(focus['next_action'])}</span>
            <span>相关路径：{html.escape(", ".join(focus['related_paths']) or '无')}</span>
            <span>任务文件：{html.escape(focus['path'] or '无')}</span>
          </div>
          {f"<div class='attention'><strong>当前阻塞：</strong>{html.escape(focus['escalation']['current_block'])}<br><span>决策 owner：{html.escape(focus['escalation']['decision_owner'])}</span></div>" if focus['escalation'] else ""}
        </div>
      </div>
      <div class="panel span-5">
        <h2 class="section-title">最近进展</h2>
        <div class="progress-card">
          <div class="progress-item">
            <strong>最近 Handoff</strong>
            <div class="list" style="margin-top:10px;">
              <span>{html.escape(latest_handoff['current_status']) if latest_handoff else '暂无'}</span>
              <span>{html.escape(latest_handoff['next_action']) if latest_handoff else '暂无下一步'}</span>
            </div>
          </div>
          <div class="progress-item">
            <strong>最近 QA</strong>
            <div class="list" style="margin-top:10px;">
              <span>{html.escape(latest_qa['result'].upper()) if latest_qa else 'NONE'}</span>
              <span>{html.escape(latest_qa['path']) if latest_qa else '暂无 QA 记录'}</span>
            </div>
          </div>
          <div class="progress-item">
            <strong>最近 Telemetry</strong>
            <div class="list" style="margin-top:10px;">
              <span>duration_ms: {html.escape(latest_telemetry['duration_ms']) if latest_telemetry else '无'}</span>
              <span>cost_usd: {html.escape(latest_telemetry['cost_usd']) if latest_telemetry else '无'}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="panel" style="margin-top:18px;">
      <h2 class="section-title">行动入口</h2>
      <div class="action-grid">
        {"".join(f"<a class='action-card' href='{html.escape(action['href'])}'>{html.escape(action['label'])}</a>" for action in snapshot['actions'])}
      </div>
    </section>
    """
    return render_layout("ADS Dashboard", "项目全局概览", body)


def render_detail_page(snapshot: JSON, mode: str = "task") -> str:
    focus = snapshot["focus"]
    collections = snapshot["collections"]
    metrics = snapshot["metrics"]
    if mode == "risk":
        section_title = "阻塞与风险"
        if collections["escalations"]:
            content = "".join(
                f"<div class='progress-item'><strong>{html.escape(item['task_id'])}</strong><div class='list' style='margin-top:10px;'><span>{html.escape(item['current_block'])}</span><span>decision_owner: {html.escape(item['decision_owner'])}</span><span>{html.escape(item['path'])}</span></div></div>"
                for item in collections["escalations"]
            )
        else:
            content = "<div class='progress-item'>当前没有 active escalation。</div>"
    elif mode == "health":
        section_title = "健康与验证"
        content = f"""
        <div class='progress-item'>
          <strong>Telemetry 覆盖率</strong>
          <div class='list' style='margin-top:10px;'>
            <span>{metrics['telemetry_coverage']}%</span>
            <span>最近 QA：{html.escape(metrics['recent_qa_status'])}</span>
            <span>待审批数：{metrics['pending_approvals']}</span>
          </div>
        </div>
        <div class='progress-item'>
          <strong>建议命令</strong>
          <pre>python3 scripts/ads_doctor.py
python3 scripts/ads_health_report.py
python3 scripts/validate_ads.py</pre>
        </div>
        """
    else:
        section_title = "当前任务详情"
        content = f"""
        <div class='progress-item'>
          <strong>{html.escape(focus['task_id'])} · {html.escape(focus['title'])}</strong>
          <div class='list' style='margin-top:10px;'>
            <span>owner_role: {html.escape(focus['owner_role'])}</span>
            <span>goal: {html.escape(focus['goal'])}</span>
            <span>next_action: {html.escape(focus['next_action'])}</span>
            <span>path: {html.escape(focus['path'] or '无')}</span>
          </div>
        </div>
        <div class='progress-item'>
          <strong>相关路径</strong>
          <pre>{html.escape(chr(10).join(focus['related_paths']) or '无')}</pre>
        </div>
        """

    body = f"""
    <section class="panel">
      <div class="eyebrow">ADS Detail</div>
      <h1>{html.escape(section_title)}</h1>
      <p class="subtitle">统一详情页承接首页点击后的进一步查看，保持导航简单。</p>
    </section>
    <section class="panel" style="margin-top:18px;">
      <h2 class="section-title">{html.escape(section_title)}</h2>
      <div class="progress-card">{content}</div>
    </section>
    """
    return render_layout(f"ADS Dashboard - {section_title}", section_title, body)


def route_request(raw_path: str, repo_root: Path = REPO_ROOT) -> JSON:
    parsed = urlparse(raw_path)
    snapshot = build_snapshot(repo_root)
    if parsed.path in {"", "/"}:
        body = render_overview_page(snapshot)
        return {"status": 200, "content_type": "text/html; charset=utf-8", "body": body}
    if parsed.path == "/detail":
        mode = parse_qs(parsed.query).get("mode", ["task"])[0]
        body = render_detail_page(snapshot, mode=mode)
        return {"status": 200, "content_type": "text/html; charset=utf-8", "body": body}
    if parsed.path == "/snapshot.json":
        return {
            "status": 200,
            "content_type": "application/json; charset=utf-8",
            "body": json.dumps(snapshot, ensure_ascii=False, indent=2),
        }
    return {"status": 404, "content_type": "text/plain; charset=utf-8", "body": "Not Found"}


def serve(repo_root: Path, host: str, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            response = route_request(self.path, repo_root)
            body = response["body"].encode("utf-8")
            self.send_response(int(response["status"]))
            self.send_header("Content-Type", str(response["content_type"]))
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(f"[ads_dashboard] serving {repo_root}")
    print(f"[ads_dashboard] open {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root to visualize")
    parser.add_argument("--host", default="127.0.0.1", help="Host for the local web server")
    parser.add_argument("--port", type=int, default=8765, help="Port for the local web server")
    parser.add_argument("--output", help="Write the overview HTML to a file instead of serving")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_overview_page(build_snapshot(repo_root)), encoding="utf-8")
        print(f"[ads_dashboard] wrote {output}")
        return 0

    serve(repo_root, args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
