#!/usr/bin/env python3
"""Tests for the spec-syncer operational skill."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "skills" / "spec-syncer" / "run.py"
SPEC = importlib.util.spec_from_file_location("spec_syncer_run", MODULE_PATH)
assert SPEC and SPEC.loader
spec_syncer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = spec_syncer
SPEC.loader.exec_module(spec_syncer)


TASK_CONTENT = """\
    # 任务：同步认证 spec

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260324-201` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | Architect |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | `change-20260324-001` |
    | **coordination_model** | `direct` |
    | **trace_id** | `TRACE-20260324-201` |
    | **updated_at** | `2026-03-24T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `backend/src/auth/` — 认证代码
    - **forbidden_paths**（禁止改动）：
      - `ops/**` — 运维路径

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    需要判断 spec 是否同步。

    ## 验收标准（可勾选）

    - [ ] 测试通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `backend/src/auth/jwt.py` | JWT 逻辑 |

    ## Memory refs（可选）

    无

    ## 证据期望（完成时必须附上）

    pytest

    ## Freshness

    - **stale_after**（可选）：`P2D`
    - **最后更新时间说明**：创建

    ---

    **状态**：`review`
"""


SPEC_CONTENT = """\
    ---
    spec_id: auth-capability
    version: 1.0.0
    status: active
    owned_by: architect
    related_changes:
      - change-20260324-001
    related_tasks:
      - TASK-20260324-201
    updated_at: 2026-03-24
    stale_after: 2026-09-24
    ---

    # Auth 能力

    ## 能力概述

    JWT。
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestSpecSyncerSkill:
    def test_spec_syncer_infers_impacted_spec_from_change_links(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        write_file(tmp_path, ".ai/specs/auth-capability.md", SPEC_CONTENT)
        task = spec_syncer.parse_task(task_path)

        impacted_specs = spec_syncer.infer_impacted_specs(task, ["backend/src/auth/jwt.py"], repo_root=tmp_path)
        report = spec_syncer.build_report(task, impacted_specs, ["backend/src/auth/jwt.py"])

        assert any(spec["path"] == ".ai/specs/auth-capability.md" for spec in impacted_specs)
        assert report["status"] == "in_progress"

        spec_delta = spec_syncer.render_spec_delta("change-20260324-001", impacted_specs)
        assert "`.ai/specs/auth-capability.md`" in spec_delta

    def test_spec_syncer_marks_updated_when_spec_file_changed(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        write_file(tmp_path, ".ai/specs/auth-capability.md", SPEC_CONTENT)
        task = spec_syncer.parse_task(task_path)

        impacted_specs = spec_syncer.infer_impacted_specs(task, [".ai/specs/auth-capability.md"], repo_root=tmp_path)
        report = spec_syncer.build_report(task, impacted_specs, [".ai/specs/auth-capability.md"])

        assert report["status"] == "updated"

    def test_spec_syncer_marks_not_applicable_without_matching_specs(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT.replace("`change-20260324-001`", ""))
        task = spec_syncer.parse_task(task_path)

        impacted_specs = spec_syncer.infer_impacted_specs(task, ["backend/src/profile/avatar.py"], repo_root=tmp_path)
        report = spec_syncer.build_report(task, impacted_specs, ["backend/src/profile/avatar.py"])

        assert impacted_specs == []
        assert report["status"] == "not_applicable"
