#!/usr/bin/env python3
"""Tests for the task-decomposer operational skill."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "skills" / "task-decomposer" / "run.py"
SPEC = importlib.util.spec_from_file_location("task_decomposer_run", MODULE_PATH)
assert SPEC and SPEC.loader
task_decomposer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = task_decomposer
SPEC.loader.exec_module(task_decomposer)


CHANGE_PROPOSAL = """\
    # Change Proposal — `change-20260323-200`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **change_id** | `change-20260323-200` |
    | **title** | 为玩家资料页加入存档同步 |
    | **status** | `approved` |
    | **proposed_by** | architect |
    | **approval_owner** | TechLead |
    | **trace_id** | `TRACE-20260323-200` |
    | **updated_at** | `2026-03-23T10:00:00+08:00` |

    ## What & Why

    Sync player save data.

    ## Scope

    **影响层级**：Layer 1-2

    **影响路径**：

    - `frontend/src/pages/Profile.tsx` — 资料页入口
    - `backend/src/save_sync/service.py` — 同步服务
    - `.ai/specs/save-sync.md` — 规格补充

    ## Impact

    **关联任务**：

    - `TASK-20260323-001`
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestTaskDecomposerSkill:
    def test_generate_tasks_splits_change_by_role(self, tmp_path):
        change_path = write_file(tmp_path, ".ai/changes/change-20260323-200/proposal.md", CHANGE_PROPOSAL)

        written_paths = task_decomposer.generate_tasks(change_path, output_dir=tmp_path / "out")

        assert len(written_paths) == 3
        contents = [path.read_text(encoding="utf-8") for path in written_paths]
        assert any("owner_role** | Frontend" in content for content in contents)
        assert any("owner_role** | Backend" in content for content in contents)
        assert any("owner_role** | Architect" in content for content in contents)
        assert all("parent_change_id** | `change-20260323-200`" in content for content in contents)

    def test_generate_tasks_refuses_to_overwrite_without_force(self, tmp_path):
        change_path = write_file(tmp_path, ".ai/changes/change-20260323-200/proposal.md", CHANGE_PROPOSAL)
        output_dir = tmp_path / "out"

        task_decomposer.generate_tasks(change_path, output_dir=output_dir)

        try:
            task_decomposer.generate_tasks(change_path, output_dir=output_dir)
            raised = False
        except FileExistsError:
            raised = True

        assert raised is True
