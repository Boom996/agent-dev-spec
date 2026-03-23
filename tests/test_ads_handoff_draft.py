#!/usr/bin/env python3
"""Tests for ADS handoff draft generation."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_handoff_draft


TASK_CONTENT = """\
    # 任务：实现玩家状态存储

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260323-020` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | `frontend-backend-integration` |
    | **approval_owner** | TechLead |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | |
    | **coordination_model** | `direct` |
    | **trace_id** | `TRACE-20260323-020` |
    | **updated_at** | `2026-03-23T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `src/` — 游戏状态代码
    - **forbidden_paths**（禁止改动）：
      - `ops/` — 运维目录

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    实现玩家状态存储。

    ## 验收标准（可勾选）

    - [ ] 玩家状态可持久化
    - [ ] 测试通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `src/state.py` | 玩家状态存储 |
    | `tests/test_state.py` | 状态测试 |

    ## Memory refs（可选）

    - `.ai/memory/state-risk.md` — 存储风险

    ## 证据期望（完成时必须附上）

    - pytest
    - lint

    ## Freshness

    - **stale_after**（可选）：`P3D`
    - **最后更新时间说明**：开始实现

    ---

    **状态**：`review`
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def run_git(repo_root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)


class TestAdsHandoffDraft:
    def test_handoff_draft_uses_git_diff_and_identity_commands(self, tmp_path):
        run_git(tmp_path, "init")
        run_git(tmp_path, "config", "user.email", "test@example.com")
        run_git(tmp_path, "config", "user.name", "Test User")

        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        write_file(
            tmp_path,
            ".agent/identity.json",
            json.dumps(
                {
                    "standard_verify_commands": {"lint": "ruff check .", "test": "python3 -m pytest -q"},
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )
        write_file(tmp_path, ".ai/memory/state-risk.md", "# Memory Object\n")
        write_file(tmp_path, "src/state.py", "STATE = {}\n")
        write_file(tmp_path, "tests/test_state.py", "def test_state():\n    assert True\n")
        run_git(tmp_path, "add", ".")
        run_git(tmp_path, "commit", "-m", "baseline")

        write_file(tmp_path, "src/state.py", "STATE = {'hp': 100}\n")
        write_file(tmp_path, "notes.txt", "todo\n")

        draft = ads_handoff_draft.build_handoff_draft(
            task_path,
            repo_root=tmp_path,
            identity_path=tmp_path / ".agent" / "identity.json",
        )

        assert "# ADS Handoff — `TASK-20260323-020`" in draft
        assert "| `src/state.py` | 玩家状态存储 |" in draft
        assert "| `notes.txt` | Changed in current worktree |" in draft
        assert "| `lint` | Backend @ CLI |  | pending | `artifacts/lint.txt` | pending |" in draft
        assert "| `test` | Backend @ CLI |  | pending | `artifacts/test.txt` | pending |" in draft
        assert "| **spec_update_status** | `not_started` |" in draft

    def test_handoff_draft_honors_explicit_status_and_block_reason(self, tmp_path):
        run_git(tmp_path, "init")
        run_git(tmp_path, "config", "user.email", "test@example.com")
        run_git(tmp_path, "config", "user.name", "Test User")

        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        run_git(tmp_path, "add", ".")
        run_git(tmp_path, "commit", "-m", "baseline")

        draft = ads_handoff_draft.build_handoff_draft(
            task_path,
            repo_root=tmp_path,
            handoff_status="BLOCKED",
            blocked_reason="Need API schema decision",
            evidence_items=["integration-test"],
        )

        assert "| **handoff_status** | `BLOCKED` |" in draft
        assert "| **blocked_reason** | Need API schema decision |" in draft
        assert "| `integration-test` | Backend @ CLI |  | pending | `artifacts/integration-test.txt` | pending |" in draft
