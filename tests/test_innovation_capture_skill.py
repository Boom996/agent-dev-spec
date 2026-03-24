#!/usr/bin/env python3
"""Tests for the innovation-capture operational skill."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "skills" / "innovation-capture" / "run.py"
SPEC = importlib.util.spec_from_file_location("innovation_capture_run", MODULE_PATH)
assert SPEC and SPEC.loader
innovation_capture = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = innovation_capture
SPEC.loader.exec_module(innovation_capture)


TASK_CONTENT = """\
    # 任务：创新捕获测试

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260324-401` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | Architect |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | `change-20260324-010` |
    | **coordination_model** | `direct` |
    | **trace_id** | `TRACE-20260324-401` |
    | **updated_at** | `2026-03-24T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `backend/src/cache/` — 缓存逻辑
    - **forbidden_paths**（禁止改动）：
      - `ops/**` — 运维路径

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    创新捕获测试。

    ## 验收标准（可勾选）

    - [ ] 测试通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `backend/src/cache/service.py` | 缓存逻辑 |

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


class TestInnovationCaptureSkill:
    def test_capture_innovation_writes_brief(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        output_path = tmp_path / ".ai/innovations/INV-20260324-001.md"

        written = innovation_capture.capture_innovation(
            task_path,
            title="Use Redis for distributed cache",
            summary="Current cache is process-local and does not scale.",
            trigger="Observed cache misses during multi-replica testing.",
            judgement="Medium cost, high scalability upside.",
            output_path=output_path,
            repo_root=tmp_path,
        )

        assert written == output_path
        content = written.read_text(encoding="utf-8")
        assert "# Innovation Brief" in content
        assert "`TASK-20260324-401`" in content
        assert "`change-20260324-010`" in content
        assert "Use Redis for distributed cache" in content
