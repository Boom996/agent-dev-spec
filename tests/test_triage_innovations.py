#!/usr/bin/env python3
"""Tests for triage_innovations.py."""
from __future__ import annotations
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import triage_innovations


def make_innovation(tmp_path: Path, status: str, triage_deadline: str | None,
                    inv_id: str = "INV-001") -> Path:
    deadline_line = f"triage_deadline: {triage_deadline}" if triage_deadline else ""
    content = f"""\
---
innovation_id: {inv_id}
title: 测试想法
submitted_by: developer
submitted_at: 2026-03-22T10:00:00+08:00
status: {status}
urgency: low
{deadline_line}
---

## 想法摘要
测试。
"""
    path = tmp_path / f"{inv_id}.md"
    path.write_text(content, encoding="utf-8")
    return path


def make_markdown_innovation(tmp_path: Path, status: str, triage_deadline: str | None,
                             inv_id: str = "INV-002") -> Path:
    deadline_cell = f"`{triage_deadline}`" if triage_deadline else ""
    content = f"""\
# Innovation Brief — `{inv_id}`

## Metadata

| 字段 | 值 |
|------|-----|
| **innovation_id** | `{inv_id}` |
| **title** | 测试想法 |
| **submitted_by** | `developer` |
| **submitted_at** | `2026-03-22T10:00:00+08:00` |
| **context_task** | `TASK-001` |
| **context_change** | `change-001` |
| **status** | `{status}` |
| **urgency** | `low` |
| **impact_estimate** | `medium` |
| **triage_by** | `architect` |
| **triage_deadline** | {deadline_cell} |
| **promoted_to** |  |

## 想法摘要
测试。
"""
    path = tmp_path / f"{inv_id}.md"
    path.write_text(content, encoding="utf-8")
    return path


class TestTriageInnovations:
    def test_overdue_proposed_brief_detected(self, tmp_path):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        path = make_innovation(tmp_path, status="proposed", triage_deadline=yesterday)
        msg, status = triage_innovations.check_innovation(path, date.today(), warn_days=7)
        assert status == "OVERDUE"

    def test_ok_promoted_brief_not_flagged(self, tmp_path):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        path = make_innovation(tmp_path, status="promoted", triage_deadline=yesterday)
        msg, status = triage_innovations.check_innovation(path, date.today(), warn_days=7)
        assert status == "OK"

    def test_soon_proposed_brief_flagged_as_warn(self, tmp_path):
        soon = (date.today() + timedelta(days=5)).isoformat()
        path = make_innovation(tmp_path, status="proposed", triage_deadline=soon)
        msg, status = triage_innovations.check_innovation(path, date.today(), warn_days=7)
        assert status == "SOON"

    def test_proposed_without_deadline_is_ok(self, tmp_path):
        path = make_innovation(tmp_path, status="proposed", triage_deadline=None)
        msg, status = triage_innovations.check_innovation(path, date.today(), warn_days=7)
        assert status == "OK"

    def test_markdown_metadata_innovation_is_supported(self, tmp_path):
        soon = (date.today() + timedelta(days=3)).isoformat()
        path = make_markdown_innovation(tmp_path, status="proposed", triage_deadline=soon)
        msg, status = triage_innovations.check_innovation(path, date.today(), warn_days=7)
        assert status == "SOON"
