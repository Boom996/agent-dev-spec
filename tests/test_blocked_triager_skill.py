#!/usr/bin/env python3
"""Tests for the blocked-triager operational skill."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "skills" / "blocked-triager" / "run.py"
SPEC = importlib.util.spec_from_file_location("blocked_triager_run", MODULE_PATH)
assert SPEC and SPEC.loader
blocked_triager = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = blocked_triager
SPEC.loader.exec_module(blocked_triager)


TASK_CONTENT = """\
    # 任务：阻塞分类测试

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260324-101` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | Architect |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | |
    | **coordination_model** | `direct` |
    | **trace_id** | `TRACE-20260324-101` |
    | **updated_at** | `2026-03-24T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `backend/` — 后端路径
    - **forbidden_paths**（禁止改动）：
      - `ops/**` — 运维路径

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    测试 triager。

    ## 验收标准（可勾选）

    - [ ] 测试通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `backend/src/service.py` | 主实现 |

    ## Memory refs（可选）

    无

    ## 证据期望（完成时必须附上）

    pytest

    ## Freshness

    - **stale_after**（可选）：`P2D`
    - **最后更新时间说明**：创建

    ---

    **状态**：`in-progress`
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestBlockedTriagerSkill:
    def test_triager_escalates_shared_change_request(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        task = blocked_triager.parse_task(task_path)
        triage = blocked_triager.build_triage_report(
            task,
            "Need to modify shared contract outside current task scope.",
            ["shared/contracts/approval_event.ts"],
        )

        assert triage["decision"] == "ESCALATE_SHARED_CHANGE_REQUEST"
        assert "shared/contracts/approval_event.ts" in triage["shared_paths"]

        request_text = blocked_triager.render_shared_change_request(
            task,
            "Need to modify shared contract outside current task scope.",
            triage["shared_paths"],
            "SCR-20260324-101",
        )
        assert "`TASK-20260324-101`" in request_text
        assert "`shared/contracts/approval_event.ts`" in request_text

    def test_triager_marks_external_wait_as_blocked(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        task = blocked_triager.parse_task(task_path)
        triage = blocked_triager.build_triage_report(
            task,
            "Waiting for architect approval before continuing.",
            ["backend/src/service.py"],
        )

        assert triage["decision"] == "BLOCKED"

    def test_triager_marks_missing_details_as_needs_context(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        task = blocked_triager.parse_task(task_path)
        triage = blocked_triager.build_triage_report(
            task,
            "Need context for the API payload shape before implementation.",
            ["backend/src/service.py"],
        )

        assert triage["decision"] == "NEEDS_CONTEXT"
