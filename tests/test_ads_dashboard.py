#!/usr/bin/env python3
"""Tests for ADS local dashboard."""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_dashboard
import ads_init


TASK_CONTENT = """\
    # 任务：实现存档系统

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260326-401` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | HumanOwner |
    | **allowed_agents** | `[]` |
    | **trace_id** | `TRACE-20260326-401` |
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


HANDOFF_CONTENT = """\
    # ADS Handoff — `TASK-20260326-401`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **From** | Backend @ Codex |
    | **To** | Integration |
    | **task_id** | TASK-20260326-401 |
    | **Priority** | High |
    | **Timestamp** | 2026-03-26T10:30:00Z |
    | **trace_id** | TRACE-20260326-401 |
    | **updated_at** | 2026-03-26T10:30:00Z |
    | **stale_after** | `P2D` |
    | **handoff_status** | `DONE_WITH_CONCERNS` |
    | **blocked_reason** |  |
    | **spec_update_status** | `updated` |

    ## Context

    **当前状态**：实现完成，等待集成验证。

    | 路径 | 内容说明 |
    |------|----------|
    | `src/save/store.py` | 存档主逻辑 |

    ## Memory refs（可选）

    无

    ## Deliverable request

    **需要什么**：继续验收

    **验收标准**（可勾选）：

    - [ ] 测试通过

    ## Evidence expectation

    **必须提供的证明**：pytest

    **已附证据**：（本任务主责已填）

    | evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
    |---------------|-------------|-------------|--------|----------------|---------------|
    | `test` | Backend @ Codex | 2026-03-26T10:28:00Z | pass | `artifacts/test.txt` | reviewed |

    **Evidence telemetry**：（可选，补充 cost / latency / retry）

    | evidence_item | duration_ms | cost_usd | retry_count |
    |---------------|-------------|----------|-------------|
    | `test` | `1532` | `0.012500` | `1` |

    ## Approval

    **approval_owner**：HumanOwner
    **approval_status**：`pending`

    ## Handoff to next

    **下一棒**：Integration
    **建议下一动作**：执行集成验证
"""


ESCALATION_CONTENT = """\
    # ADS Escalation — `TASK-20260326-401`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **escalation_id** | `ESC-20260326-001` |
    | **task_id** | `TASK-20260326-401` |
    | **source_handoff** | `.ai/handoffs/TASK-20260326-401.md` |
    | **escalation_type** | `needs_human_decision` |
    | **requested_by** | Backend @ Codex |
    | **decision_owner** | HumanOwner |
    | **urgency** | `high` |
    | **status** | `pending` |
    | **trace_id** | `TRACE-20260326-401` |
    | **updated_at** | 2026-03-26T10:40:00Z |

    ## Current Block

    **当前阻塞**：Need release decision

    ## Decision Request

    - 需要人工批准

    ## Impact

    - `TASK-20260326-401`

    ## Evidence & Context

    - `.ai/tasks/active/task.md`

    ## Resolution

    （待填写）
"""


QA_PASS = """\
    # QA 结论：PASS

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260326-401` |
    | **qa_id** | `QA-20260326-001` |
    | **result** | `pass` |
    | **timestamp** | `2026-03-26T11:00:00Z` |
    | **trace_id** | `TRACE-20260326-401` |

    ## 证据摘要

    - 集成验证通过
    - 证据齐全

    ## Next Action

    继续发布
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestAdsDashboard:
    def test_build_snapshot_collects_overview_metrics_and_focus(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT, project_name="AgentGames")
        write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        write_file(tmp_path, ".ai/handoffs/TASK-20260326-401.md", HANDOFF_CONTENT)
        write_file(tmp_path, ".ai/escalations/TASK-20260326-401.md", ESCALATION_CONTENT)
        write_file(tmp_path, ".ai/qa/TASK-20260326-401-pass.md", QA_PASS)

        snapshot = ads_dashboard.build_snapshot(tmp_path)

        assert snapshot["project"]["name"] == "AgentGames"
        assert snapshot["metrics"]["active_tasks"] == 1
        assert snapshot["metrics"]["active_escalations"] == 1
        assert snapshot["metrics"]["pending_approvals"] == 1
        assert snapshot["metrics"]["telemetry_coverage"] == 100
        assert snapshot["focus"]["task_id"] == "TASK-20260326-401"
        assert snapshot["focus"]["next_action"] == "执行集成验证"
        assert snapshot["guidance"]["workspace_label"] == "ADS 已接入"
        assert "README.md" in snapshot["guidance"]["read_this_first"]
        assert "python3 scripts/ads_dashboard.py" in snapshot["guidance"]["next_commands"]
        assert snapshot["homepage"]["project_home_title"] == "项目首页"
        assert snapshot["homepage"]["control_panel_title"] == "今日控制台"

    def test_render_overview_page_contains_dashboard_sections(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT, project_name="AgentGames")
        write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        write_file(tmp_path, ".ai/handoffs/TASK-20260326-401.md", HANDOFF_CONTENT)

        html = ads_dashboard.render_overview_page(ads_dashboard.build_snapshot(tmp_path))

        assert "项目全局概览" in html
        assert "关键指标" in html
        assert "当前重点" in html
        assert "最近进展" in html
        assert "快速上手" in html
        assert "项目首页" in html
        assert "今日控制台" in html
        assert "新成员入口" in html
        assert "续做成员入口" in html
        assert "README.md" in html
        assert "python3 scripts/ads_doctor.py" in html
        assert "行动入口" in html
        assert "AgentGames" in html

    def test_render_detail_page_switches_by_mode(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT, project_name="AgentGames")
        write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)
        write_file(tmp_path, ".ai/handoffs/TASK-20260326-401.md", HANDOFF_CONTENT)
        write_file(tmp_path, ".ai/escalations/TASK-20260326-401.md", ESCALATION_CONTENT)

        snapshot = ads_dashboard.build_snapshot(tmp_path)
        risk_html = ads_dashboard.render_detail_page(snapshot, mode="risk")
        task_html = ads_dashboard.render_detail_page(snapshot, mode="task")
        health_html = ads_dashboard.render_detail_page(snapshot, mode="health")

        assert "阻塞与风险" in risk_html
        assert "Need release decision" in risk_html
        assert "当前任务详情" in task_html
        assert "实现存档系统" in task_html
        assert "健康与验证" in health_html
        assert "Telemetry 覆盖率" in health_html

    def test_route_request_returns_two_page_html(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT)
        write_file(tmp_path, ".ai/tasks/active/task.md", TASK_CONTENT)

        overview = ads_dashboard.route_request("/", tmp_path)
        detail = ads_dashboard.route_request("/detail?mode=task", tmp_path)

        assert overview["status"] == 200
        assert overview["content_type"] == "text/html; charset=utf-8"
        assert "项目全局概览" in overview["body"]
        assert detail["status"] == 200
        assert "当前任务详情" in detail["body"]

    def test_build_snapshot_without_active_task_returns_empty_state_guidance(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT, project_name="AgentGames")

        snapshot = ads_dashboard.build_snapshot(tmp_path)

        assert snapshot["focus"]["title"] == "当前没有进行中任务"
        assert snapshot["focus"]["next_action"] == "先从 backlog 选择一个任务，再补当前 handoff。"
        assert snapshot["guidance"]["empty_state"] == "当前仓库还没有 active task，建议先从 backlog 激活一个真实任务。"
        assert snapshot["guidance"]["first_step"] == "先读 README.md 和 ADS install report，再从 backlog 选择第一个真实任务。"

    def test_render_overview_page_shows_empty_state_actions_when_no_active_task(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT, project_name="AgentGames")
        write_file(
            tmp_path,
            ".agent/docs/guides/ads-install-report.md",
            "# ADS Install Report\n\n- ready\n",
        )

        html = ads_dashboard.render_overview_page(ads_dashboard.build_snapshot(tmp_path))

        assert "当前没有进行中任务" in html
        assert "先从 backlog 选择一个任务" in html
        assert ".ai/tasks/backlog/" in html
        assert "接入后第一步" in html
        assert "先读 README.md 和 ADS install report" in html
        assert ".agent/docs/guides/ads-install-report.md" in html
