#!/usr/bin/env python3
"""Tests for build_context_pack.py Phase 2 --mode cli extension."""
from __future__ import annotations
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import build_context_pack


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


MINIMAL_TASK = """\
    # 任务：测试任务

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260322-001` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | |
    | **team_pattern_id** | |
    | **approval_owner** | |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | |
    | **coordination_model** | |
    | **trace_id** | `TRACE-20260322-001` |
    | **updated_at** | `2026-03-22T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `src/` — 说明
    - **forbidden_paths**（禁止改动）：
      - `config/` — 说明

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    测试任务背景。

    ## 验收标准（可勾选）

    - [ ] 标准 1

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `src/index.ts` | 入口文件 |

    ## Memory refs（可选）

    无

    ## 证据期望（完成时必须附上）

    npm test 通过。

    ## Freshness

    - **stale_after**: P7D
    - **最后更新时间说明**: 初始创建
"""

MINIMAL_CONSTITUTION = """\
    # Project Constitution

    ## Mission
    Build reliable multi-agent collaboration tooling.

    ## Non-Negotiable Principles
    - No breaking changes without approval

    ## Role Definitions
    - Developer: writes code

    ## Agent Governance
    - Humans approve major changes
"""


class TestCLIMode:
    def test_cli_mode_includes_constitution_section(self, tmp_path, monkeypatch):
        task_path = write_file(tmp_path, "task.md", MINIMAL_TASK)
        write_file(tmp_path, ".agent/constitution.md", MINIMAL_CONSTITUTION)
        monkeypatch.setattr(build_context_pack, "REPO_ROOT", tmp_path)
        pack = build_context_pack.build_pack(task_path, None, None, None, mode="cli")
        assert "[CONSTITUTION]" in pack

    def test_cli_mode_includes_change_info_when_available(self, tmp_path, monkeypatch):
        # Task with parent_change_id
        task_content = MINIMAL_TASK.replace(
            "| **parent_change_id** | |",
            "| **parent_change_id** | `change-20260322-001` |"
        )
        task_path = write_file(tmp_path, "task.md", task_content)
        write_file(tmp_path, ".agent/constitution.md", MINIMAL_CONSTITUTION)
        write_file(tmp_path, ".ai/changes/change-20260322-001/proposal.md", """\
            # Change Proposal — `change-20260322-001`

            ## Metadata

            | 字段 | 值 |
            |------|-----|
            | **change_id** | `change-20260322-001` |
            | **title** | 实现 JWT 令牌支持 |
            | **status** | `approved` |
            | **proposed_by** | `architect` |
            | **trace_id** | `TRACE-20260322-001` |
            | **updated_at** | `2026-03-22T10:00:00+08:00` |

            ## What & Why
            测试变更。

            ## Scope
            Layer 1-2.

            ## Impact
            - TASK-001
        """)
        monkeypatch.setattr(build_context_pack, "REPO_ROOT", tmp_path)
        pack = build_context_pack.build_pack(task_path, None, None, None, mode="cli")
        assert "[CHANGE_INFO]" in pack

    def test_cli_mode_skips_change_info_when_absent(self, tmp_path, monkeypatch):
        task_path = write_file(tmp_path, "task.md", MINIMAL_TASK)
        write_file(tmp_path, ".agent/constitution.md", MINIMAL_CONSTITUTION)
        monkeypatch.setattr(build_context_pack, "REPO_ROOT", tmp_path)
        pack = build_context_pack.build_pack(task_path, None, None, None, mode="cli")
        assert "[CHANGE_INFO]" not in pack

    def test_cli_mode_output_within_120_lines(self, tmp_path, monkeypatch):
        task_path = write_file(tmp_path, "task.md", MINIMAL_TASK)
        write_file(tmp_path, ".agent/constitution.md", MINIMAL_CONSTITUTION)
        monkeypatch.setattr(build_context_pack, "REPO_ROOT", tmp_path)
        pack = build_context_pack.build_pack(task_path, None, None, None, mode="cli")
        assert len(pack.splitlines()) <= 120

    def test_default_mode_unchanged(self, tmp_path, monkeypatch):
        task_path = write_file(tmp_path, "task.md", MINIMAL_TASK)
        monkeypatch.setattr(build_context_pack, "REPO_ROOT", tmp_path)
        pack_default = build_context_pack.build_pack(task_path, None, None, None, mode="default")
        pack_no_mode = build_context_pack.build_pack(task_path, None, None, None)
        assert "[CONSTITUTION]" not in pack_default
        assert pack_default == pack_no_mode
