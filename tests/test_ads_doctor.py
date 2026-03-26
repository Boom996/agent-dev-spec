#!/usr/bin/env python3
"""Tests for ADS doctor health checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_doctor
import ads_init


MINIMAL_TASK = """\
    # 任务：接入任务

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260323-001` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | HumanOwner |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | |
    | **coordination_model** | |
    | **trace_id** | `TRACE-20260323-001` |
    | **updated_at** | `2026-03-23T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `src/` — 业务代码
    - **forbidden_paths**（禁止改动）：
      - `infra/` — 基础设施

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    完成 ADS 接入。

    ## 验收标准（可勾选）

    - [ ] 接入完成

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `src/game.ts` | 游戏入口 |

    ## Memory refs（可选）

    无

    ## 证据期望（完成时必须附上）

    npm run test

    ## Freshness

    - **stale_after**（可选）：`P2D`
    - **最后更新时间说明**：创建任务

    ---

    **状态**：`in-progress`
"""


BLOCKED_HANDOFF = """\
    # ADS Handoff — `TASK-20260323-001`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **From** | Backend @ Codex |
    | **To** | Integration |
    | **task_id** | TASK-20260323-001 |
    | **Priority** | High |
    | **Timestamp** | 2026-03-23T11:00:00Z |
    | **trace_id** | TRACE-20260323-001 |
    | **updated_at** | 2026-03-23T11:00:00Z |
    | **stale_after** | `P2D` |
    | **handoff_status** | `BLOCKED` |
    | **blocked_reason** | `Need API decision` |
    | **spec_update_status** | `in_progress` |

    ## Context

    **当前状态**：实现暂停，等待接口方案。

    ## Deliverable request

    **需要什么**：确认 API 设计。

    ## Evidence expectation

    **必须提供的证明**：npm run test

    **已附证据**：

    | evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
    |---------------|-------------|-------------|--------|----------------|---------------|
    | `test` | Backend @ Codex | 2026-03-23T10:50:00Z | pass | `artifacts/test.txt` | pending |

    ## Approval

    **approval_owner**：HumanOwner
    **approval_status**：`pending`

    ## Handoff to next

    **下一棒**：Integration
    **建议下一动作**：升级并等待决策。
"""


ESCALATION = """\
    # ADS Escalation — `TASK-20260323-001`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **escalation_id** | `ESC-20260323-001` |
    | **task_id** | `TASK-20260323-001` |
    | **source_handoff** | `.ai/handoffs/TASK-20260323-001.md` |
    | **escalation_type** | `needs_human_decision` |
    | **requested_by** | Backend @ Codex |
    | **decision_owner** | HumanOwner |
    | **urgency** | `high` |
    | **status** | `pending` |
    | **trace_id** | `TRACE-20260323-001` |
    | **updated_at** | 2026-03-23T11:05:00Z |

    ## Current Block

    **当前阻塞**：Need API decision

    ## Decision Request

    - 需要 HumanOwner 决策 API 方案

    ## Impact

    - `TASK-20260323-001`
    - `Integration`

    ## Evidence & Context

    - `.ai/tasks/active/task.md`
    - `.ai/handoffs/TASK-20260323-001.md`

    ## Resolution

    （待填写）
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestAdsDoctor:
    def test_doctor_passes_on_bootstrapped_repo(self, tmp_path):
        target_root = tmp_path / "game-project"
        ads_init.init_repo(target_root, source_root=REPO_ROOT)

        findings = ads_doctor.run_doctor(target_root)

        assert findings == []

    def test_doctor_reports_missing_constitution(self, tmp_path):
        target_root = tmp_path / "broken-project"
        ads_init.init_repo(target_root, source_root=REPO_ROOT)
        (target_root / ".agent" / "constitution.md").unlink()

        findings = ads_doctor.run_doctor(target_root)

        assert any(f.level == "fail" and f.code == "missing_constitution" for f in findings)

    def test_doctor_reports_missing_handoff_for_active_task(self, tmp_path):
        target_root = tmp_path / "workflow-project"
        ads_init.init_repo(target_root, source_root=REPO_ROOT)
        write_file(target_root, ".ai/tasks/active/task.md", MINIMAL_TASK)

        findings = ads_doctor.run_doctor(target_root)

        assert any(f.code == "missing_handoff" for f in findings)

    def test_doctor_reports_missing_escalation_for_blocked_handoff(self, tmp_path):
        target_root = tmp_path / "blocked-project"
        ads_init.init_repo(target_root, source_root=REPO_ROOT)
        write_file(target_root, ".ai/tasks/active/task.md", MINIMAL_TASK)
        write_file(target_root, ".ai/handoffs/TASK-20260323-001.md", BLOCKED_HANDOFF)

        findings = ads_doctor.run_doctor(target_root)

        assert any(f.code == "missing_escalation" for f in findings)

    def test_doctor_accepts_blocked_handoff_when_escalation_exists(self, tmp_path):
        target_root = tmp_path / "escalated-project"
        ads_init.init_repo(target_root, source_root=REPO_ROOT)
        write_file(target_root, ".ai/tasks/active/task.md", MINIMAL_TASK)
        write_file(target_root, ".ai/handoffs/TASK-20260323-001.md", BLOCKED_HANDOFF)
        write_file(target_root, ".ai/escalations/TASK-20260323-001.md", ESCALATION)

        findings = ads_doctor.run_doctor(target_root)

        assert not any(f.code == "missing_escalation" for f in findings)

    def test_doctor_reports_toolset_drift(self, tmp_path):
        target_root = tmp_path / "tool-project"
        ads_init.init_repo(target_root, source_root=REPO_ROOT)
        manifest_path = write_file(
            target_root,
            "skills/game-runner/manifest.json",
            json.dumps(
                {
                    "tool_id": "game-runner",
                    "name": "game-runner",
                    "version": "1.0.0",
                    "description": "Run game workflows.",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        )

        findings = ads_doctor.run_doctor(target_root)

        assert manifest_path.exists()
        assert any(f.code == "tool_missing_from_toolset" for f in findings)
