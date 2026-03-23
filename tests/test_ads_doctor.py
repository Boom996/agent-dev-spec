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
