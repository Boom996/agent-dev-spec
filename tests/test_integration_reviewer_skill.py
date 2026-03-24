#!/usr/bin/env python3
"""Tests for the integration-reviewer operational skill."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "skills" / "integration-reviewer" / "run.py"
SPEC = importlib.util.spec_from_file_location("integration_reviewer_run", MODULE_PATH)
assert SPEC and SPEC.loader
integration_reviewer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = integration_reviewer
SPEC.loader.exec_module(integration_reviewer)


TASK_CONTENT = """\
    # 任务：集成复核测试

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260324-301` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | `frontend-backend-integration` |
    | **approval_owner** | Integration |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | |
    | **coordination_model** | `direct` |
    | **trace_id** | `TRACE-20260324-301` |
    | **updated_at** | `2026-03-24T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `backend/src/service.py` — 服务实现
    - **forbidden_paths**（禁止改动）：
      - `ops/**` — 运维路径

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    集成复核 skill 测试。

    ## 验收标准（可勾选）

    - [ ] 服务逻辑完成
    - [ ] 验证通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `backend/src/service.py` | 服务实现 |

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


HANDOFF_PASS = """\
    # ADS Handoff — `TASK-20260324-301`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **From** | Backend @ Codex |
    | **To** | Integration |
    | **task_id** | TASK-20260324-301 |
    | **Priority** | High |
    | **Timestamp** | 2026-03-24T11:00:00Z |
    | **trace_id** | TRACE-20260324-301 |
    | **updated_at** | 2026-03-24T11:00:00Z |
    | **stale_after** | `P2D` |
    | **handoff_status** | `DONE` |
    | **blocked_reason** |  |
    | **spec_update_status** | `updated` |
    | **team_pattern_id** | `frontend-backend-integration` |

    ## Context

    **当前状态**：实现完成，等待 Integration 复核。

    **相关路径**：

    | 路径 | 内容说明 |
    |------|----------|
    | `backend/src/service.py` | 服务实现 |

    **依赖**：无
    **约束**：无

    ## Memory refs（可选）

    无

    ## Deliverable request

    **需要什么**：Integration 复核。

    **验收标准**（可勾选）：

    - [x] 服务逻辑完成
    - [x] 验证通过

    **参考资料**：无

    ## Evidence expectation

    **必须提供的证明**：pytest

    **已附证据**：（本任务主责已填）

    | evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
    |---------------|-------------|-------------|--------|----------------|---------------|
    | `spec_compliance: auth spec updated` | Backend @ Codex | 2026-03-24T10:50:00Z | pass | `artifacts/spec.txt` | reviewed |
    | `test` | Backend @ Codex | 2026-03-24T10:55:00Z | pass | `artifacts/test.txt` | reviewed |

    **附加说明**：

    - none

    ## Approval

    **approval_owner**：Integration
    **approval_status**：`approved`

    ## Handoff to next

    **下一棒**：Integration
    **建议下一动作**：完成 QA 并合并。
"""


HANDOFF_FAIL = HANDOFF_PASS.replace(
    "| `spec_compliance: auth spec updated` | Backend @ Codex | 2026-03-24T10:50:00Z | pass | `artifacts/spec.txt` | reviewed |\n"
    "| `test` | Backend @ Codex | 2026-03-24T10:55:00Z | pass | `artifacts/test.txt` | reviewed |",
    "| `test` | Backend @ Codex | 2026-03-24T10:55:00Z | fail | `artifacts/test.txt` | pending |",
).replace("| **spec_update_status** | `updated` |", "| **spec_update_status** | `not_started` |")


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestIntegrationReviewerSkill:
    def test_review_pass_generates_pass_qa_file(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        handoff_path = write_file(tmp_path, ".ai/handoffs/TASK-20260324-301.md", HANDOFF_PASS)

        result, output_path = integration_reviewer.write_review(
            task_path,
            handoff_path,
            qa_actor="Integration @ Codex",
            repo_root=tmp_path,
        )

        assert result["passed"] is True
        assert output_path.name == "TASK-20260324-301-pass.md"
        content = output_path.read_text(encoding="utf-8")
        assert "# QA 结论：PASS" in content

    def test_review_fail_generates_fail_qa_file(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        handoff_path = write_file(tmp_path, ".ai/handoffs/TASK-20260324-301.md", HANDOFF_FAIL)

        result, output_path = integration_reviewer.write_review(
            task_path,
            handoff_path,
            qa_actor="Integration @ Codex",
            repo_root=tmp_path,
        )

        assert result["passed"] is False
        content = output_path.read_text(encoding="utf-8")
        assert "# QA 结论：FAIL" in content
        assert "spec compliance evidence" in content or "spec_compliance" in content
