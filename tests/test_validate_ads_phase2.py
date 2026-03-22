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
