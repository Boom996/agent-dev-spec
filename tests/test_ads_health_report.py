#!/usr/bin/env python3
"""Tests for ADS health report telemetry coverage."""

from __future__ import annotations

import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_health_report


TASK = """\
    # 任务：健康报告测试

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260326-201` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | HumanOwner |
    | **allowed_agents** | `[]` |
    | **trace_id** | `TRACE-20260326-201` |
    | **updated_at** | `2026-03-26T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `src/` — 业务代码
    - **forbidden_paths**（禁止改动）：
      - `ops/` — 运维

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    健康报告测试。

    ## 验收标准（可勾选）

    - [ ] 测试通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `src/main.py` | 主入口 |

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


HANDOFF_WITH_TELEMETRY = """\
    # ADS Handoff — `TASK-20260326-201`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **From** | Backend @ Codex |
    | **To** | Integration |
    | **task_id** | TASK-20260326-201 |
    | **Priority** | High |
    | **Timestamp** | 2026-03-26T10:10:00Z |
    | **trace_id** | TRACE-20260326-201 |
    | **updated_at** | 2026-03-26T10:10:00Z |
    | **stale_after** | `P2D` |

    ## Context

    **当前状态**：完成

    | 路径 | 内容说明 |
    |------|----------|
    | `src/main.py` | 主入口 |

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
    | `test` | Backend @ Codex | 2026-03-26T10:09:00Z | pass | `artifacts/test.txt` | reviewed |

    **Evidence telemetry**：（可选，补充 cost / latency / retry）

    | evidence_item | duration_ms | cost_usd | retry_count |
    |---------------|-------------|----------|-------------|
    | `test` | `1532` | `0.012500` | `1` |

    ## Approval

    **approval_owner**：HumanOwner
    **approval_status**：`approved`

    ## Handoff to next

    **下一棒**：Integration
    **建议下一动作**：继续验收
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


class TestAdsHealthReport:
    def test_health_report_counts_handoffs_with_telemetry(self, tmp_path):
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", TASK)
        handoff_path = write_file(tmp_path, ".ai/handoffs/TASK-20260326-201.md", HANDOFF_WITH_TELEMETRY)

        original_root = ads_health_report.REPO_ROOT
        ads_health_report.REPO_ROOT = tmp_path
        try:
            report = ads_health_report.build_report(
                tasks=[ads_health_report.parse_task(task_path)],
                handoffs=[ads_health_report.parse_handoff(handoff_path)],
                tools=[],
                memories=[],
                requests=[],
                qas=[],
                now=datetime(2026, 3, 26, 12, 0, tzinfo=timezone.utc),
            )
        finally:
            ads_health_report.REPO_ROOT = original_root

        assert "- handoffs_with_telemetry: 1" in report
        assert "- missing_telemetry: 0" in report
