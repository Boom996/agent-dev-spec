#!/usr/bin/env python3
"""Tests for the handoff-writer operational skill."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "skills" / "handoff-writer" / "run.py"
SPEC = importlib.util.spec_from_file_location("handoff_writer_run", MODULE_PATH)
assert SPEC and SPEC.loader
handoff_writer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = handoff_writer
SPEC.loader.exec_module(handoff_writer)


TASK_CONTENT = """\
    # 任务：交接测试

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260323-300` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | TechLead |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | |
    | **coordination_model** | `direct` |
    | **trace_id** | `TRACE-20260323-300` |
    | **updated_at** | `2026-03-23T11:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `src/state.py` — 状态逻辑
    - **forbidden_paths**（禁止改动）：
      - `ops/` — 运维

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    生成交接文件。

    ## 验收标准（可勾选）

    - [ ] 状态逻辑完成

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `src/state.py` | 状态逻辑 |

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


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def run_git(repo_root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)


class TestHandoffWriterSkill:
    def test_write_handoff_writes_default_output_file(self, tmp_path):
        run_git(tmp_path, "init")
        run_git(tmp_path, "config", "user.email", "test@example.com")
        run_git(tmp_path, "config", "user.name", "Test User")
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        write_file(tmp_path, "src/state.py", "STATE = {}\n")
        run_git(tmp_path, "add", ".")
        run_git(tmp_path, "commit", "-m", "baseline")
        write_file(tmp_path, "src/state.py", "STATE = {'hp': 100}\n")

        output_path = handoff_writer.write_handoff(
            task_path,
            repo_root=tmp_path,
            from_actor="Backend @ Codex",
            handoff_status="DONE_WITH_CONCERNS",
            evidence_items=["test"],
            identity_path=REPO_ROOT / ".agent" / "identity.json.example",
        )

        assert output_path == tmp_path / ".ai" / "handoffs" / "TASK-20260323-300.md"
        content = output_path.read_text(encoding="utf-8")
        assert "| **From** | Backend @ Codex |" in content
        assert "| **handoff_status** | `DONE_WITH_CONCERNS` |" in content
        assert "| `src/state.py` | 状态逻辑 |" in content
