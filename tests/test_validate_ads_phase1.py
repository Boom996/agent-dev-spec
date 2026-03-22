# tests/test_validate_ads_phase1.py
"""Tests for ADS Phase 1 new validations."""
from __future__ import annotations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))
import validate_ads  # noqa: E402
from conftest import write_file


class TestConstitutionValidation:
    def test_missing_constitution_returns_error(self, tmp_ads_repo):
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert any("constitution.md" in e for e in errors)

    def test_empty_mission_returns_error(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".agent/constitution.md", """\
            # Project Constitution

            ## Mission

            ## Non-Negotiable Principles
            - No breaking changes

            ## Role Definitions
            - Developer: writes code

            ## Agent Governance
            - Humans approve
        """)
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert any("Mission" in e for e in errors)

    def test_empty_non_negotiable_principles_returns_error(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".agent/constitution.md", """\
            # Project Constitution

            ## Mission
            Build something great.

            ## Non-Negotiable Principles

            ## Role Definitions
            - Developer: writes code

            ## Agent Governance
            - Humans approve
        """)
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert any("Non-Negotiable Principles" in e for e in errors)

    def test_empty_role_definitions_returns_error(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".agent/constitution.md", """\
            # Project Constitution

            ## Mission
            Build something great.

            ## Non-Negotiable Principles
            - No breaking changes

            ## Role Definitions

            ## Agent Governance
            - Humans approve
        """)
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert any("Role Definitions" in e for e in errors)

    def test_empty_agent_governance_returns_error(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".agent/constitution.md", """\
            # Project Constitution

            ## Mission
            Build something great.

            ## Non-Negotiable Principles
            - No breaking changes

            ## Role Definitions
            - Developer: writes code

            ## Agent Governance
        """)
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert any("Agent Governance" in e for e in errors)

    def test_valid_constitution_passes(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".agent/constitution.md", """\
            # Project Constitution

            ## Mission
            Build the best ADS-compatible project.

            ## Non-Negotiable Principles
            - No breaking API changes without migration guide

            ## Tech Stack Principles
            - Python 3.11+

            ## Role Definitions
            - PM: defines changes
            - Developer: implements tasks

            ## Agent Governance
            - Humans approve constitution changes

            ## Approval Hierarchy
            - Constitution: human only
        """)
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert errors == []


class TestHandoffPhase1Fields:
    """Tests for Phase 1 new handoff fields: handoff_status, blocked_reason, spec_update_status."""

    VALID_HANDOFF_BASE = """\
        # ADS Handoff — `TASK-001`

        ## Metadata

        | 字段 | 值 |
        |------|-----|
        | **From** | Developer |
        | **To** | Integration |
        | **task_id** | TASK-001 |
        | **Priority** | High |
        | **Timestamp** | 2026-03-22T10:00:00+08:00 |
        | **trace_id** | TRACE-001 |
        | **updated_at** | 2026-03-22T10:00:00+08:00 |
        | **stale_after** | P2D |
        | **handoff_status** | DONE |
        | **spec_update_status** | not_applicable |

        ## Context

        **当前状态**：完成

        | 路径 | 内容说明 |
        |------|----------|
        | src/auth.ts | 认证模块 |

        **依赖**：无
        **约束**：无

        ## Memory refs（可选）

        无

        ## Deliverable request

        **需要什么**：集成验证

        **验收标准**（可勾选）：

        - [ ] 所有测试通过

        **参考资料**：无

        ## Evidence expectation

        **必须提供的证明**：测试输出

        **已附证据**：

        | evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
        |---------------|-------------|-------------|--------|----------------|---------------|
        | `test` | developer | 2026-03-22T10:00:00+08:00 | pass | | reviewed |

        **附加说明**：无

        ## Approval

        **approval_owner**：HumanOwner
        **approval_status**：`approved`

        ## Handoff to next

        **下一棒**：Integration
        **建议下一动作**：运行集成测试
    """

    def test_valid_handoff_with_new_fields_passes(self, tmp_ads_repo):
        path = write_file(
            tmp_ads_repo, ".ai/handoffs/TASK-001.md", self.VALID_HANDOFF_BASE
        )
        # Temporarily patch REPO_ROOT
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_handoff(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert errors == [], f"Unexpected errors: {errors}"

    def test_invalid_handoff_status_returns_error(self, tmp_ads_repo):
        content = self.VALID_HANDOFF_BASE.replace(
            "| **handoff_status** | DONE |",
            "| **handoff_status** | INVALID_VALUE |",
        )
        path = write_file(tmp_ads_repo, ".ai/handoffs/TASK-002.md", content)
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_handoff(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert any("handoff_status" in e for e in errors)

    def test_invalid_spec_update_status_returns_error(self, tmp_ads_repo):
        content = self.VALID_HANDOFF_BASE.replace(
            "| **spec_update_status** | not_applicable |",
            "| **spec_update_status** | WRONG |",
        )
        path = write_file(tmp_ads_repo, ".ai/handoffs/TASK-003.md", content)
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_handoff(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert any("spec_update_status" in e for e in errors)
