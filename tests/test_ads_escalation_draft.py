#!/usr/bin/env python3
"""Tests for ADS escalation draft generation."""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_escalation_draft


TASK_CONTENT = """\
    # 任务：确认联机同步方案

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260326-001` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | TechLead |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | |
    | **coordination_model** | `direct` |
    | **trace_id** | `TRACE-20260326-001` |
    | **updated_at** | `2026-03-26T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `src/netcode/` — 联机同步代码
    - **forbidden_paths**（禁止改动）：
      - `infra/` — 基础设施

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    明确联机同步方案。

    ## 验收标准（可勾选）

    - [ ] 明确同步策略

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `src/netcode/sync.ts` | 同步实现 |

    ## Memory refs（可选）

    无

    ## 证据期望（完成时必须附上）

    npm run test

    ## Freshness

    - **stale_after**（可选）：`P2D`
    - **最后更新时间说明**：等待同步策略

    ---

    **状态**：`blocked`
"""


HANDOFF_BLOCKED = """\
    # ADS Handoff — `TASK-20260326-001`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **From** | Backend @ Codex |
    | **To** | Integration |
    | **task_id** | TASK-20260326-001 |
    | **Priority** | High |
    | **Timestamp** | 2026-03-26T11:00:00Z |
    | **trace_id** | TRACE-20260326-001 |
    | **updated_at** | 2026-03-26T11:00:00Z |
    | **stale_after** | `P2D` |
    | **handoff_status** | `BLOCKED` |
    | **blocked_reason** | `Need sync authority decision` |
    | **spec_update_status** | `in_progress` |

    ## Context

    **当前状态**：联机同步实现暂停，等待主从权威方案结论。

    ## Deliverable request

    **需要什么**：确认同步 authority 模式。

    ## Evidence expectation

    **必须提供的证明**：test

    **已附证据**：

    | evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
    |---------------|-------------|-------------|--------|----------------|---------------|
    | `test` | Backend @ Codex | 2026-03-26T10:50:00Z | pass | `artifacts/test.txt` | pending |

    ## Handoff to next

    **下一棒**：Integration
    **建议下一动作**：升级给 TechLead 决策后继续。
"""


HANDOFF_NEEDS_CONTEXT = HANDOFF_BLOCKED.replace("`BLOCKED`", "`NEEDS_CONTEXT`").replace(
    "Need sync authority decision",
    "Need missing replay context",
)


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestAdsEscalationDraft:
    def test_build_escalation_draft_uses_handoff_context_and_artifacts(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        handoff_path = write_file(tmp_path, ".ai/handoffs/TASK-20260326-001.md", HANDOFF_BLOCKED)

        draft = ads_escalation_draft.build_escalation_draft(
            task_path=task_path,
            repo_root=tmp_path,
            handoff_path=handoff_path,
        )

        assert "# ADS Escalation — `TASK-20260326-001`" in draft
        assert re.search(r"\| \*\*escalation_id\*\* \| `ESC-\d{8}-001` \|", draft)
        assert "| **source_handoff** | `.ai/handoffs/TASK-20260326-001.md` |" in draft
        assert "| **escalation_type** | `needs_human_decision` |" in draft
        assert "| **decision_owner** | TechLead |" in draft
        assert "**当前阻塞**：Need sync authority decision" in draft
        assert "- `artifacts/test.txt`" in draft
        assert "| `src/netcode/sync.ts` | 同步实现 |" in draft

    def test_build_escalation_draft_infers_needs_context_from_handoff_status(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        handoff_path = write_file(tmp_path, ".ai/handoffs/TASK-20260326-001.md", HANDOFF_NEEDS_CONTEXT)

        draft = ads_escalation_draft.build_escalation_draft(
            task_path=task_path,
            repo_root=tmp_path,
            handoff_path=handoff_path,
            requested_by="Backend @ CLI",
        )

        assert "| **escalation_type** | `needs_context` |" in draft
        assert "| **requested_by** | Backend @ CLI |" in draft
        assert "当前 handoff 状态为 `NEEDS_CONTEXT`" in draft
