#!/usr/bin/env python3
"""Tests for ADS first-run explanation output."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_explain
import ads_init


TASK_CONTENT = """\
    # 任务：实现存档系统

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260326-301` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | HumanOwner |
    | **allowed_agents** | `[]` |
    | **trace_id** | `TRACE-20260326-301` |
    | **updated_at** | `2026-03-26T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `src/save/` — 存档代码
    - **forbidden_paths**（禁止改动）：
      - `infra/` — 基础设施

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    完成存档系统。

    ## 验收标准（可勾选）

    - [ ] 测试通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `src/save/store.py` | 存档主逻辑 |

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


ESCALATION_CONTENT = """\
    # ADS Escalation — `TASK-20260326-301`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **escalation_id** | `ESC-20260326-001` |
    | **task_id** | `TASK-20260326-301` |
    | **source_handoff** | `.ai/handoffs/TASK-20260326-301.md` |
    | **escalation_type** | `needs_human_decision` |
    | **requested_by** | Backend @ Codex |
    | **decision_owner** | HumanOwner |
    | **urgency** | `high` |
    | **status** | `pending` |
    | **trace_id** | `TRACE-20260326-301` |
    | **updated_at** | 2026-03-26T10:20:00Z |

    ## Current Block

    **当前阻塞**：Need release decision

    ## Decision Request

    - 需要人工批准

    ## Impact

    - `TASK-20260326-301`

    ## Evidence & Context

    - `.ai/tasks/active/task.md`

    ## Resolution

    （待填写）
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestAdsExplain:
    def test_build_explanation_summarizes_project_purpose_and_next_steps(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT, project_name="AgentGames")
        write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        write_file(tmp_path, ".ai/escalations/TASK-20260326-301.md", ESCALATION_CONTENT)
        start_here = tmp_path / ".ai" / "START_HERE.md"
        start_here.write_text(
            start_here.read_text(encoding="utf-8").replace("（例如：MVP Week 1 — 基础 UI 与布局）", "MVP Week 3 — Save System"),
            encoding="utf-8",
        )

        text = ads_explain.build_explanation(tmp_path)

        assert "# ADS Project Brief" in text
        assert "- project: AgentGames" in text
        assert "- workspace_status: ads_ready" in text
        assert "Build a reliable" in text or "Mission" in text
        assert "MVP Week 3 — Save System" in text
        assert "- active_tasks: 1" in text
        assert "- active_escalations: 1" in text
        assert "README.md" in text
        assert "python3 scripts/ads_doctor.py" in text
        assert "python3 scripts/ads_resume.py .ai/tasks/active/task.md" in text

    def test_build_explanation_reports_bootstrap_needed_for_plain_repo(self, tmp_path):
        (tmp_path / "README.md").write_text("# Plain Repo\n", encoding="utf-8")

        text = ads_explain.build_explanation(tmp_path)

        assert "- workspace_status: needs_bootstrap" in text
        assert "Run ADS bootstrap before expecting structured collaboration." in text
