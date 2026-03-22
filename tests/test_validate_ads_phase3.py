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
