#!/usr/bin/env python3
"""Tests for ADS resume context generation."""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_resume


TASK_WITH_CHANGE = """\
    # 任务：恢复 JWT 工作

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260323-010` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | TechLead |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | `change-20260323-001` |
    | **coordination_model** | `direct` |
    | **autonomy_level** | `semi-autonomous` |
    | **trace_id** | `TRACE-20260323-010` |
    | **updated_at** | `2026-03-23T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `backend/src/auth/` — 认证逻辑
    - **forbidden_paths**（禁止改动）：
      - `infra/` — 基础设施

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    恢复 JWT 任务上下文。

    ## 验收标准（可勾选）

    - [ ] JWT 生成逻辑可运行
    - [ ] 测试通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `backend/src/auth/jwt.py` | JWT 主逻辑 |

    ## Memory refs（可选）

    - `.ai/memory/auth-risk.md` — 历史风险

    ## 证据期望（完成时必须附上）

    pytest

    ## Freshness

    - **stale_after**（可选）：`P2D`
    - **最后更新时间说明**：恢复上下文

    ---

    **状态**：`in-progress`
"""


HANDOFF_BLOCKED = """\
    # ADS Handoff — `TASK-20260323-010`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **From** | Backend @ Codex |
    | **To** | Integration |
    | **task_id** | TASK-20260323-010 |
    | **Priority** | High |
    | **Timestamp** | 2026-03-23T12:00:00Z |
    | **trace_id** | TRACE-20260323-010 |
    | **updated_at** | 2026-03-23T12:00:00Z |
    | **stale_after** | `P2D` |
    | **handoff_status** | `BLOCKED` |
    | **blocked_reason** | `Need prod signing key decision` |
    | **spec_update_status** | `in_progress` |

    ## Context

    **当前状态**：JWT 实现基本完成，但签名 key 策略未定。

    **相关路径**：

    | 路径 | 内容说明 |
    |------|----------|
    | `backend/src/auth/jwt.py` | JWT 主逻辑 |

    **依赖**：等待安全组确认  
    **约束**：不要提交真实密钥

    ## Memory refs（可选）

    - `.ai/memory/auth-risk.md` — 历史风险

    ## Deliverable request

    **需要什么**：确认签名 key 决策并继续任务。

    **验收标准**（可勾选）：

    - [ ] 确认 key 策略

    **参考资料**：proposal

    ## Evidence expectation

    **必须提供的证明**：pytest

    **已附证据**：（本任务主责已填）

    | evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
    |---------------|-------------|-------------|--------|----------------|---------------|
    | `test` | Backend @ Codex | 2026-03-23T11:50:00Z | pass | `artifacts/test.txt` | pending |

    **附加说明**：

    - none

    ## Approval

    **approval_owner**：TechLead
    **approval_status**：`pending`

    ## Handoff to next

    **下一棒**：Integration
    **建议下一动作**：先确认签名 key 决策，再继续实现。
"""


CONSTITUTION = """\
    # Project Constitution

    ## Mission
    Build a reliable auth system for the game backend.

    ## Non-Negotiable Principles
    - No secrets in git
    - Every task needs evidence
"""


CHANGE_PROPOSAL = """\
    # Change Proposal — `change-20260323-001`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **change_id** | `change-20260323-001` |
    | **title** | 为认证能力加入 JWT |
    | **status** | `approved` |
    | **proposed_by** | architect |
    | **approval_owner** | TechLead |
    | **trace_id** | `TRACE-20260323-010` |
    | **updated_at** | `2026-03-23T09:00:00+08:00` |

    ## What & Why

    JWT.

    ## Scope

    **影响层级**：Layer 1-2

    **影响路径**：

    - `backend/src/auth/` — auth logic

    ## Impact

    **关联任务**：

    - `TASK-20260323-010`
"""


ESCALATION = """\
    # ADS Escalation — `TASK-20260323-010`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **escalation_id** | `ESC-20260323-001` |
    | **task_id** | `TASK-20260323-010` |
    | **source_handoff** | `.ai/handoffs/TASK-20260323-010.md` |
    | **escalation_type** | `needs_human_decision` |
    | **requested_by** | Backend @ Codex |
    | **decision_owner** | TechLead |
    | **urgency** | `high` |
    | **status** | `pending` |
    | **trace_id** | `TRACE-20260323-010` |
    | **updated_at** | 2026-03-23T12:10:00Z |

    ## Current Block

    **当前阻塞**：Need prod signing key decision

    ## Decision Request

    - 由 TechLead 明确 key 策略

    ## Impact

    - `TASK-20260323-010`
    - `Integration`

    ## Evidence & Context

    - `.ai/tasks/active/task.md`
    - `.ai/handoffs/TASK-20260323-010.md`

    ## Resolution

    （待填写）
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestAdsResume:
    def test_build_resume_includes_constitution_change_and_handoff(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_WITH_CHANGE)
        write_file(tmp_path, ".ai/handoffs/TASK-20260323-010.md", HANDOFF_BLOCKED)
        write_file(tmp_path, ".ai/escalations/TASK-20260323-010.md", ESCALATION)
        write_file(tmp_path, ".agent/constitution.md", CONSTITUTION)
        write_file(tmp_path, ".ai/changes/change-20260323-001/proposal.md", CHANGE_PROPOSAL)
        write_file(tmp_path, ".ai/memory/auth-risk.md", "# Memory Object\n")
        identity_path = write_file(
            tmp_path,
            ".agent/identity.json",
            json.dumps(
                {
                    "project_name": "game-server",
                    "standard_verify_commands": {"test": "python3 -m pytest -q"},
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )

        resume_text = ads_resume.build_resume(task_path, None, identity_path, None, repo_root=tmp_path)

        assert "# ADS Resume — TASK-20260323-010" in resume_text
        assert "Build a reliable auth system for the game backend." in resume_text
        assert "为认证能力加入 JWT" in resume_text
        assert "handoff_status: BLOCKED" in resume_text
        assert "blocked_reason: Need prod signing key decision" in resume_text
        assert "next_action: 先确认签名 key 决策，再继续实现。" in resume_text
        assert "## Active Escalation" in resume_text
        assert "path: .ai/escalations/TASK-20260323-010.md" in resume_text
        assert "decision_owner: TechLead" in resume_text
        assert "current_block: Need prod signing key decision" in resume_text
        assert "python3 -m pytest -q" in resume_text

    def test_build_resume_handles_missing_handoff(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK_WITH_CHANGE.replace("`change-20260323-001`", ""))
        identity_path = write_file(tmp_path, ".agent/identity.json", '{"project_name":"game-client"}\n')

        resume_text = ads_resume.build_resume(task_path, None, identity_path, None, repo_root=tmp_path)

        assert "handoff_status: missing" in resume_text
        assert "No handoff found. Resume from task contract and current worktree." in resume_text
