# tests/test_validate_ads_phase2.py
"""Tests for ADS Phase 2 validations: Change Proposal."""
from __future__ import annotations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))
import validate_ads  # noqa: E402
from conftest import write_file


VALID_PROPOSAL = """\
# Change Proposal — `change-20260322-001`

## Metadata

| 字段 | 值 |
|------|-----|
| **change_id** | `change-20260322-001` |
| **title** | 实现用户认证功能 |
| **status** | `approved` |
| **proposed_by** | PM |
| **approval_owner** | HumanOwner |
| **trace_id** | `TRACE-20260322-001` |
| **updated_at** | 2026-03-22T10:00:00+08:00 |

## What & Why

本次变更实现用户认证功能，解决系统缺乏安全访问控制的问题。

## Scope

**影响层级**：Layer 1-2

**影响路径**：

- `src/auth.ts` — 认证模块

## Impact

**关联任务**：

- `TASK-001`

**风险说明**：

- 可能影响现有会话管理

**回滚方案**：

还原 auth.ts 到上一版本。
"""


class TestChangeProposalValidation:
    def test_valid_proposal_has_no_errors(self, tmp_ads_repo):
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", VALID_PROPOSAL
        )
        errors = validate_ads.validate_change_proposal(path)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_missing_change_id_returns_error(self, tmp_ads_repo):
        content = VALID_PROPOSAL.replace(
            "| **change_id** | `change-20260322-001` |",
            "| **change_id** |  |",
        )
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", content
        )
        errors = validate_ads.validate_change_proposal(path)
        assert any("change_id" in e for e in errors)

    def test_missing_title_returns_error(self, tmp_ads_repo):
        content = VALID_PROPOSAL.replace(
            "| **title** | 实现用户认证功能 |",
            "| **title** |  |",
        )
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", content
        )
        errors = validate_ads.validate_change_proposal(path)
        assert any("title" in e for e in errors)

    def test_missing_status_returns_error(self, tmp_ads_repo):
        content = VALID_PROPOSAL.replace(
            "| **status** | `approved` |",
            "| **status** |  |",
        )
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", content
        )
        errors = validate_ads.validate_change_proposal(path)
        assert any("status" in e for e in errors)

    def test_missing_proposed_by_returns_error(self, tmp_ads_repo):
        content = VALID_PROPOSAL.replace(
            "| **proposed_by** | PM |",
            "| **proposed_by** |  |",
        )
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", content
        )
        errors = validate_ads.validate_change_proposal(path)
        assert any("proposed_by" in e for e in errors)

    def test_missing_updated_at_returns_error(self, tmp_ads_repo):
        content = VALID_PROPOSAL.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |",
            "| **updated_at** |  |",
        )
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", content
        )
        errors = validate_ads.validate_change_proposal(path)
        assert any("updated_at" in e for e in errors)

    def test_missing_what_and_why_section_returns_error(self, tmp_ads_repo):
        content = VALID_PROPOSAL.replace("## What & Why", "## WhatAndWhy_REMOVED")
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", content
        )
        errors = validate_ads.validate_change_proposal(path)
        assert any("What & Why" in e for e in errors)

    def test_missing_scope_section_returns_error(self, tmp_ads_repo):
        content = VALID_PROPOSAL.replace("## Scope", "## Scope_REMOVED")
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", content
        )
        errors = validate_ads.validate_change_proposal(path)
        assert any("Scope" in e for e in errors)

    def test_missing_impact_section_returns_error(self, tmp_ads_repo):
        content = VALID_PROPOSAL.replace("## Impact", "## Impact_REMOVED")
        path = write_file(
            tmp_ads_repo, ".ai/changes/change-20260322-001/proposal.md", content
        )
        errors = validate_ads.validate_change_proposal(path)
        assert any("Impact" in e for e in errors)


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


class TestTaskPhase2Validations:
    def test_parent_change_id_missing_dir_returns_error(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        content = MINIMAL_TASK_BASE.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
            "| **parent_change_id** | `change-20260322-001` |\n",
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p2-parent-missing.md", content)
        errors = validate_ads.validate_task(path)
        assert any("parent_change_id" in e for e in errors), f"Expected parent_change_id error, got: {errors}"

    def test_parent_change_id_existing_dir_ok(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        (tmp_ads_repo / ".ai" / "changes" / "change-20260322-001").mkdir(parents=True, exist_ok=True)
        content = MINIMAL_TASK_BASE.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
            "| **parent_change_id** | `change-20260322-001` |\n",
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p2-parent-exists.md", content)
        errors = validate_ads.validate_task(path)
        parent_errors = [e for e in errors if "parent_change_id" in e]
        assert parent_errors == [], f"Unexpected parent_change_id errors: {parent_errors}"

    def test_orchestrated_task_missing_subtasks_section_returns_error(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        content = MINIMAL_TASK_BASE.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
            "| **coordination_model** | `orchestrated` |\n",
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p2-orch-nosub.md", content)
        errors = validate_ads.validate_task(path)
        assert any("Sub-Tasks Detail" in e for e in errors), f"Expected Sub-Tasks Detail error, got: {errors}"

    def test_orchestrated_task_with_subtasks_section_ok(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        content = (
            MINIMAL_TASK_BASE.replace(
                "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
                "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
                "| **coordination_model** | `orchestrated` |\n",
            ).rstrip()
            + "\n\n## Sub-Tasks Detail\n\n"
            "| sub_task_id | 描述 | 负责角色 | 状态 |\n"
            "|-------------|------|---------|------|\n"
            "| `TASK-001` | 子任务 | Developer | pending |\n"
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p2-orch-withsub.md", content)
        errors = validate_ads.validate_task(path)
        sub_errors = [e for e in errors if "Sub-Tasks Detail" in e]
        assert sub_errors == [], f"Unexpected Sub-Tasks Detail errors: {sub_errors}"

    def test_direct_task_no_subtasks_section_ok(self, tmp_ads_repo, monkeypatch):
        monkeypatch.setattr(validate_ads, "REPO_ROOT", tmp_ads_repo)
        content = MINIMAL_TASK_BASE.replace(
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n",
            "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
            "| **coordination_model** | `direct` |\n",
        )
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-p2-direct.md", content)
        errors = validate_ads.validate_task(path)
        sub_errors = [e for e in errors if "Sub-Tasks Detail" in e]
        assert sub_errors == [], f"Unexpected Sub-Tasks Detail errors: {sub_errors}"


MINIMAL_PATTERN_NO_CM = """\
# Team Pattern

## Metadata

| 字段 | 值 |
|------|-----|
| **team_pattern_id** | `test-pattern` |
| **version** | `1` |
| **updated_at** | `2026-03-22T00:00:00Z` |

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

MINIMAL_PATTERN_WITH_CM = """\
# Team Pattern

## Metadata

| 字段 | 值 |
|------|-----|
| **team_pattern_id** | `test-pattern` |
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

MINIMAL_PATTERN_INVALID_CM = """\
# Team Pattern

## Metadata

| 字段 | 值 |
|------|-----|
| **team_pattern_id** | `test-pattern` |
| **version** | `1` |
| **updated_at** | `2026-03-22T00:00:00Z` |
| **coordination_model** | `invalid-value` |

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


class TestPatternPhase2Validations:
    def test_pattern_missing_coordination_model_returns_error(self, tmp_ads_repo):
        path = write_file(
            tmp_ads_repo, ".ai/patterns/test-pattern.md", MINIMAL_PATTERN_NO_CM
        )
        errors = validate_ads.validate_pattern(path)
        assert any("coordination_model" in e for e in errors), (
            f"Expected coordination_model error, got: {errors}"
        )

    def test_pattern_with_coordination_model_ok(self, tmp_ads_repo):
        path = write_file(
            tmp_ads_repo, ".ai/patterns/test-pattern.md", MINIMAL_PATTERN_WITH_CM
        )
        errors = validate_ads.validate_pattern(path)
        assert errors == [], f"Unexpected errors: {errors}"

    def test_pattern_invalid_coordination_model_returns_error(self, tmp_ads_repo):
        path = write_file(
            tmp_ads_repo, ".ai/patterns/test-pattern.md", MINIMAL_PATTERN_INVALID_CM
        )
        errors = validate_ads.validate_pattern(path)
        assert any("coordination_model" in e for e in errors), (
            f"Expected coordination_model enum error, got: {errors}"
        )


class TestHasSpecDeltaEntry:
    def test_empty_text_returns_false(self):
        assert validate_ads.has_spec_delta_entry("") is False

    def test_text_with_table_row_returns_true(self):
        text = """\
## 本次变更影响的 Spec 文档

| Spec 文件 | 变更类型 | 变更摘要 |
|----------|---------|---------|
| `.ai/specs/auth.md` | 新增 | 新增用户认证规范 |
"""
        assert validate_ads.has_spec_delta_entry(text) is True

    def test_text_with_only_header_returns_false(self):
        text = """\
## 本次变更影响的 Spec 文档

| Spec 文件 | 变更类型 | 变更摘要 |
|----------|---------|---------|
"""
        assert validate_ads.has_spec_delta_entry(text) is False
