#!/usr/bin/env python3
"""Tests for ADS Phase 3 validations."""
from __future__ import annotations
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "tests"))
import validate_ads
from conftest import write_file


# --- Minimal valid change proposal helper ---
MINIMAL_PROPOSAL = """\
    # Change Proposal — `change-20260322-001`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **change_id** | `change-20260322-001` |
    | **title** | 测试变更 |
    | **status** | `approved` |
    | **proposed_by** | `architect` |
    | **trace_id** | `TRACE-20260322-001` |
    | **updated_at** | `2026-03-22T10:00:00+08:00` |

    ## What & Why
    测试。

    ## Scope
    Layer 1.

    ## Impact
    - TASK-001
"""

MINIMAL_SPEC_DELTA = """\
    # Spec Delta — `change-20260322-001`

    ## 本次变更影响的 Spec 文档

    | Spec 文件 | 变更类型 | 变更摘要 |
    |----------|---------|---------|
    | `.ai/specs/placeholder.md` | 新增 | 测试 |

    ## 更新责任
    Developer 负责更新。
"""


class TestChangeProposalPhase3:
    def test_executing_proposal_without_human_checkpoint_returns_error(self, tmp_ads_repo):
        content = MINIMAL_PROPOSAL.replace("| **status** | `approved` |",
                                           "| **status** | `executing` |")
        path = write_file(tmp_ads_repo, "proposal.md", content)
        errors = validate_ads.validate_change_proposal(path)
        assert any("human_checkpoint" in e for e in errors)

    def test_executing_proposal_with_design_approved_ok(self, tmp_ads_repo):
        content = MINIMAL_PROPOSAL.replace(
            "| **status** | `approved` |",
            "| **status** | `executing` |"
        ).replace(
            "| **updated_at** | `2026-03-22T10:00:00+08:00` |",
            "| **updated_at** | `2026-03-22T10:00:00+08:00` |\n    | **human_checkpoint** | `design_approved` |"
        )
        path = write_file(tmp_ads_repo, "proposal.md", content)
        errors = validate_ads.validate_change_proposal(path)
        assert not any("human_checkpoint" in e for e in errors)

    def test_approved_proposal_no_human_checkpoint_required(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, "proposal.md", MINIMAL_PROPOSAL)
        errors = validate_ads.validate_change_proposal(path)
        assert not any("human_checkpoint" in e for e in errors)


class TestSpecDeltaValidation:
    def test_spec_delta_with_existing_path_ok(self, tmp_ads_repo, monkeypatch):
        (tmp_ads_repo / ".ai" / "specs").mkdir(parents=True, exist_ok=True)
        (tmp_ads_repo / ".ai" / "specs" / "auth.md").write_text("# spec", encoding="utf-8")
        content = MINIMAL_SPEC_DELTA.replace(
            "| `.ai/specs/placeholder.md` | 新增 | 测试 |",
            "| `.ai/specs/auth.md` | 新增 | 测试 |"
        )
        path = write_file(tmp_ads_repo, "spec-delta.md", content)
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        errors = validate_ads.validate_spec_delta(path)
        assert errors == []

    def test_spec_delta_with_missing_path_returns_error(self, tmp_ads_repo, monkeypatch):
        content = MINIMAL_SPEC_DELTA.replace(
            "| `.ai/specs/placeholder.md` | 新增 | 测试 |",
            "| `.ai/specs/nonexistent.md` | 新增 | 测试 |"
        )
        path = write_file(tmp_ads_repo, "spec-delta.md", content)
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        errors = validate_ads.validate_spec_delta(path)
        assert any("nonexistent.md" in e for e in errors)

    def test_spec_delta_with_placeholder_skips_check(self, tmp_ads_repo, monkeypatch):
        # Path containing '...' or '<' is a placeholder — skip existence check
        path = write_file(tmp_ads_repo, "spec-delta.md", MINIMAL_SPEC_DELTA)
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        errors = validate_ads.validate_spec_delta(path)
        assert errors == []

    def test_empty_spec_delta_table_has_no_path_errors(self, tmp_ads_repo, monkeypatch):
        content = """\
            # Spec Delta — `change-test`

            ## 本次变更影响的 Spec 文档

            | Spec 文件 | 变更类型 | 变更摘要 |
            |----------|---------|---------|

            ## 更新责任
            无。
        """
        path = write_file(tmp_ads_repo, "spec-delta.md", textwrap.dedent(content))
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        errors = validate_ads.validate_spec_delta(path)
        assert errors == []


# --- Minimal valid handoff helpers ---
MINIMAL_HANDOFF_NO_PATTERN = """\
    # ADS Handoff — `TASK-20260322-001`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **From** | Backend |
    | **To** | Integration |
    | **task_id** | `TASK-20260322-001` |
    | **Priority** | High |
    | **Timestamp** | `2026-03-22T10:00:00+08:00` |
    | **trace_id** | `TRACE-20260322-001` |
    | **updated_at** | `2026-03-22T10:00:00+08:00` |
    | **stale_after** | `P7D` |

    ## Context

    **当前状态**：已完成

    **相关路径**：

    | 路径 | 内容说明 |
    |------|----------|
    | `src/` | 主要代码 |

    ## Memory refs（可选）

    无

    ## Deliverable request

    **需要什么**：集成测试

    **验收标准**（可勾选）：

    - [ ] 测试通过

    ## Evidence expectation

    **已附证据**：

    | evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
    |---------------|-------------|-------------|--------|----------------|---------------|
    | `build` | backend | 2026-03-22T10:00:00+08:00 | pass | | pending |

    ## Approval

    **approval_owner**：tech-lead
    **approval_status**：`pending`
"""

MINIMAL_HANDOFF_WITH_PATTERN = MINIMAL_HANDOFF_NO_PATTERN.replace(
    "| **stale_after** | `P7D` |",
    "| **stale_after** | `P7D` |\n    | **team_pattern_id** | `frontend-backend-integration` |"
)

MINIMAL_HANDOFF_WITH_PATTERN_AND_SPEC_COMPLIANCE = MINIMAL_HANDOFF_WITH_PATTERN.replace(
    "| `build` | backend | 2026-03-22T10:00:00+08:00 | pass | | pending |",
    "| `spec_compliance: all criteria met` | qa-agent | 2026-03-22T10:00:00+08:00 | pass | | reviewed |\n    | `build` | backend | 2026-03-22T10:00:00+08:00 | pass | | pending |"
)


class TestHandoffPhase3:
    def test_handoff_with_team_pattern_missing_spec_compliance_returns_error(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, "handoff.md", MINIMAL_HANDOFF_WITH_PATTERN)
        errors = validate_ads.validate_handoff(path)
        assert any("spec_compliance" in e for e in errors)

    def test_handoff_with_team_pattern_and_spec_compliance_ok(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, "handoff.md", MINIMAL_HANDOFF_WITH_PATTERN_AND_SPEC_COMPLIANCE)
        errors = validate_ads.validate_handoff(path)
        assert not any("spec_compliance" in e for e in errors)

    def test_handoff_without_team_pattern_no_spec_compliance_required(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, "handoff.md", MINIMAL_HANDOFF_NO_PATTERN)
        errors = validate_ads.validate_handoff(path)
        assert not any("spec_compliance" in e for e in errors)


MINIMAL_INNOVATION = """\
    # Innovation Brief — `INV-20260322-001`

    ## Metadata

    | 字段 | 值 |
    |------|-----|
    | **innovation_id** | `INV-20260322-001` |
    | **title** | 用 Redis 替代内存缓存以支持水平扩展 |
    | **submitted_by** | `developer-agent` |
    | **submitted_at** | `2026-03-22T10:00:00+08:00` |
    | **status** | `proposed` |
    | **urgency** | `low` |

    ## 想法摘要

    发现当前内存缓存方案在水平扩展时存在数据不一致问题，建议迁移到 Redis 解决此问题。

    ## 触发背景

    在执行 TASK-20260322-001 时发现负载测试失败。

    ## 提交者的初步判断

    中等优先级，不阻断当前任务，建议下个 sprint 评估。
"""


class TestInnovationBriefValidation:
    def test_valid_innovation_has_no_errors(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, "innovation.md", MINIMAL_INNOVATION)
        errors = validate_ads.validate_innovation(path)
        assert errors == []

    def test_missing_innovation_id_returns_error(self, tmp_ads_repo):
        content = MINIMAL_INNOVATION.replace("| **innovation_id** | `INV-20260322-001` |\n    ", "")
        path = write_file(tmp_ads_repo, "innovation.md", content)
        errors = validate_ads.validate_innovation(path)
        assert any("innovation_id" in e for e in errors)

    def test_missing_submitted_at_returns_error(self, tmp_ads_repo):
        content = MINIMAL_INNOVATION.replace("| **submitted_at** | `2026-03-22T10:00:00+08:00` |\n    ", "")
        path = write_file(tmp_ads_repo, "innovation.md", content)
        errors = validate_ads.validate_innovation(path)
        assert any("submitted_at" in e for e in errors)

    def test_invalid_status_returns_error(self, tmp_ads_repo):
        content = MINIMAL_INNOVATION.replace("| **status** | `proposed` |",
                                              "| **status** | `invalid-status` |")
        path = write_file(tmp_ads_repo, "innovation.md", content)
        errors = validate_ads.validate_innovation(path)
        assert any("status" in e for e in errors)

    def test_missing_summary_section_returns_error(self, tmp_ads_repo):
        # Remove the 想法摘要 section
        content = MINIMAL_INNOVATION.replace("## 想法摘要\n\n    发现当前内存缓存方案在水平扩展时存在数据不一致问题，建议迁移到 Redis 解决此问题。\n\n    ", "")
        path = write_file(tmp_ads_repo, "innovation.md", content)
        errors = validate_ads.validate_innovation(path)
        assert any("想法摘要" in e for e in errors)


class TestInnovationIntegration:
    def test_valid_example_innovation_has_no_errors(self):
        example_path = REPO_ROOT / "examples" / "case-innovation-brief.md"
        assert example_path.exists(), f"Example file not found: {example_path}"
        errors = validate_ads.validate_innovation(example_path)
        assert errors == [], f"Unexpected errors: {errors}"


# ---------------------------------------------------------------------------
# Phase 3-4: autonomy_level / token_budget task fields
# ---------------------------------------------------------------------------

MINIMAL_TASK_BASE = (
    "# 任务：测试任务\n\n"
    "## 元数据\n\n"
    "| 字段 | 值 |\n"
    "|------|-----|\n"
    "| **task_id** | `TASK-20260322-001` |\n"
    "| **owner_role** | Developer |\n"
    "| **priority** | High |\n"
    "| **deps** | `[]` |\n"
    "| **handoff_to** | |\n"
    "| **team_pattern_id** | |\n"
    "| **approval_owner** | |\n"
    "| **allowed_agents** | `[]` |\n"
    "| **trace_id** | TRACE-001 |\n"
    "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n\n"
    "## 单写者范围\n\n"
    "- **locked_paths**（本任务周期内仅主责可改）：\n"
    "  - `src/` — 说明\n"
    "- **forbidden_paths**（禁止改动）：\n"
    "  - `.agent/` — 说明\n\n"
    "## 共享改动升级（可选）\n\n无\n\n"
    "## 背景与目标\n\n测试\n\n"
    "## 验收标准（可勾选）\n\n- [ ] 通过\n\n"
    "## 相关路径\n\n"
    "| 路径 | 说明 |\n|------|------|\n| `src/` | 源码 |\n\n"
    "## Memory refs（可选）\n\n无\n\n"
    "## 证据期望（完成时必须附上）\n\n测试输出\n\n"
    "## Freshness\n\n"
    "- **stale_after**：P7D\n"
    "- **最后更新时间说明**：初始创建\n\n"
    "**状态**：`backlog`\n"
)


class TestTaskGovernanceFields:
    def test_invalid_autonomy_level_returns_error(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        content = MINIMAL_TASK_BASE.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
            "| **autonomy_level** | `invalid-value` |\n",
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p34-autonomy-bad.md", content)
        errors = validate_ads.validate_task(path)
        assert any("autonomy_level" in e for e in errors), f"Expected autonomy_level error, got: {errors}"

    def test_valid_autonomy_level_ok(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        content = MINIMAL_TASK_BASE.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
            "| **autonomy_level** | `supervised` |\n",
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p34-autonomy-ok.md", content)
        errors = validate_ads.validate_task(path)
        autonomy_errors = [e for e in errors if "autonomy_level" in e]
        assert autonomy_errors == [], f"Unexpected autonomy_level errors: {autonomy_errors}"

    def test_invalid_token_budget_returns_error(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        content = MINIMAL_TASK_BASE.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
            "| **token_budget** | `not-a-number` |\n",
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p34-budget-bad.md", content)
        errors = validate_ads.validate_task(path)
        assert any("token_budget" in e for e in errors), f"Expected token_budget error, got: {errors}"

    def test_valid_token_budget_ok(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        content = MINIMAL_TASK_BASE.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
            "| **token_budget** | `50000` |\n",
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p34-budget-ok.md", content)
        errors = validate_ads.validate_task(path)
        budget_errors = [e for e in errors if "token_budget" in e]
        assert budget_errors == [], f"Unexpected token_budget errors: {budget_errors}"


# ---------------------------------------------------------------------------
# Phase 3-4: review_cadence pattern field
# ---------------------------------------------------------------------------

MINIMAL_PATTERN_WITH_REVIEW_CADENCE = """\
# Team Pattern

## Metadata

| 字段 | 值 |
|------|-----|
| **team_pattern_id** | `test-pattern-p34` |
| **version** | `1` |
| **updated_at** | `2026-03-22T00:00:00Z` |
| **coordination_model** | `peer-parallel` |
| **review_cadence** | `per_task` |

## Description

Test description.

## Roles

- `RoleA`

## Entry Conditions

- Condition one

## Shared Context Scope

Default scope.

## Handoff Rules

- Handoff rule one

## Approval Flow

Approval description.

## Integration Gate

Gate description.

## State Model

- `planned`
- `done`
"""

MINIMAL_PATTERN_NO_REVIEW_CADENCE = """\
# Team Pattern

## Metadata

| 字段 | 值 |
|------|-----|
| **team_pattern_id** | `test-pattern-p34` |
| **version** | `1` |
| **updated_at** | `2026-03-22T00:00:00Z` |
| **coordination_model** | `peer-parallel` |

## Description

Test description.

## Roles

- `RoleA`

## Entry Conditions

- Condition one

## Shared Context Scope

Default scope.

## Handoff Rules

- Handoff rule one

## Approval Flow

Approval description.

## Integration Gate

Gate description.

## State Model

- `planned`
- `done`
"""


class TestPatternReviewCadence:
    def test_invalid_review_cadence_returns_error(self, tmp_ads_repo):
        content = MINIMAL_PATTERN_WITH_REVIEW_CADENCE.replace(
            "| **review_cadence** | `per_task` |",
            "| **review_cadence** | `invalid` |",
        )
        path = write_file(tmp_ads_repo, ".ai/patterns/test-pattern-p34.md", content)
        errors = validate_ads.validate_pattern(path)
        assert any("review_cadence" in e for e in errors), f"Expected review_cadence error, got: {errors}"

    def test_valid_review_cadence_ok(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, ".ai/patterns/test-pattern-p34.md", MINIMAL_PATTERN_WITH_REVIEW_CADENCE)
        errors = validate_ads.validate_pattern(path)
        cadence_errors = [e for e in errors if "review_cadence" in e]
        assert cadence_errors == [], f"Unexpected review_cadence errors: {cadence_errors}"

    def test_absent_review_cadence_ok(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, ".ai/patterns/test-pattern-p34.md", MINIMAL_PATTERN_NO_REVIEW_CADENCE)
        errors = validate_ads.validate_pattern(path)
        cadence_errors = [e for e in errors if "review_cadence" in e]
        assert cadence_errors == [], f"Unexpected review_cadence errors: {cadence_errors}"
