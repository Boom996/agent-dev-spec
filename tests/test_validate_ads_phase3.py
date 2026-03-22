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
