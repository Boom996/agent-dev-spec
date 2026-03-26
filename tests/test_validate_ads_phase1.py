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
    """Tests for Phase 1 new handoff fields: handoff_status, spec_update_status."""

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


class TestEscalationValidation:
    VALID_ESCALATION = """\
        # ADS Escalation — `TASK-001`

        ## Metadata

        | 字段 | 值 |
        |------|-----|
        | **escalation_id** | `ESC-20260326-001` |
        | **task_id** | `TASK-001` |
        | **source_handoff** | `.ai/handoffs/TASK-001.md` |
        | **escalation_type** | `needs_human_decision` |
        | **requested_by** | Backend @ Codex |
        | **decision_owner** | TechLead |
        | **urgency** | `high` |
        | **status** | `pending` |
        | **trace_id** | `TRACE-001` |
        | **updated_at** | `2026-03-26T12:00:00Z` |

        ## Current Block

        **当前阻塞**：Need signing key strategy

        ## Decision Request

        - 明确签名 key 策略
        - 回写 task / handoff / escalation

        ## Impact

        - `TASK-001`
        - `Integration`

        ## Evidence & Context

        - `.ai/tasks/active/task.md`
        - `.ai/handoffs/TASK-001.md`

        ## Resolution

        （待填写）
    """

    def test_valid_escalation_passes(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".ai/handoffs/TASK-001.md", "# ADS Handoff — `TASK-001`\n")
        path = write_file(tmp_ads_repo, ".ai/escalations/TASK-001.md", self.VALID_ESCALATION)
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_escalation(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert errors == [], f"Unexpected errors: {errors}"

    def test_invalid_escalation_type_returns_error(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".ai/handoffs/TASK-001.md", "# ADS Handoff — `TASK-001`\n")
        content = self.VALID_ESCALATION.replace(
            "| **escalation_type** | `needs_human_decision` |",
            "| **escalation_type** | `wrong_type` |",
        )
        path = write_file(tmp_ads_repo, ".ai/escalations/TASK-001.md", content)
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_escalation(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert any("escalation_type" in e for e in errors)

    def test_missing_source_handoff_returns_error(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, ".ai/escalations/TASK-001.md", self.VALID_ESCALATION)
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_escalation(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert any("source_handoff" in e for e in errors)


class TestToolsetValidation:
    def test_script_toolset_entry_without_manifest_passes(self, tmp_ads_repo):
        path = write_file(
            tmp_ads_repo,
            "tools/toolset.json",
            """\
            {
              "version": "1.0",
              "registry": "project-local",
              "tools": [
                {
                  "tool_id": "ads.resume",
                  "owner": "platform",
                  "risk_level": "low",
                  "version": "1.0.0",
                  "source": "script",
                  "entrypoint": "scripts/ads_resume.py"
                }
              ]
            }
            """,
        )
        write_file(tmp_ads_repo, "scripts/ads_resume.py", "#!/usr/bin/env python3\n")
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_toolset(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert errors == [], f"Unexpected errors: {errors}"

    def test_script_toolset_entry_missing_entrypoint_returns_error(self, tmp_ads_repo):
        path = write_file(
            tmp_ads_repo,
            "tools/toolset.json",
            """\
            {
              "version": "1.0",
              "registry": "project-local",
              "tools": [
                {
                  "tool_id": "ads.resume",
                  "owner": "platform",
                  "risk_level": "low",
                  "version": "1.0.0",
                  "source": "script"
                }
              ]
            }
            """,
        )
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_toolset(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert any("entrypoint" in e for e in errors)


class TestTaskPhase1Fields:
    """Tests for Phase 1 new task fields: coordination_model."""

    def test_invalid_coordination_model_returns_error(self, tmp_ads_repo):
        content = """\
            # 任务：测试任务

            ## 元数据

            | 字段 | 值 |
            |------|-----|
            | **task_id** | `TASK-20260322-001` |
            | **owner_role** | Developer |
            | **owner** | test |
            | **priority** | High |
            | **deps** | `[]` |
            | **handoff_to** | Integration |
            | **team_pattern_id** | |
            | **approval_owner** | HumanOwner |
            | **allowed_agents** | `[]` |
            | **trace_id** | TRACE-001 |
            | **updated_at** | 2026-03-22T10:00:00+08:00 |
            | **coordination_model** | invalid-value |

            ## 单写者范围

            - **locked_paths**（本任务周期内仅主责可改）：
              - `src/` — 说明
            - **forbidden_paths**（禁止改动）：
              - `.agent/` — 说明

            ## 共享改动升级（可选）

            无

            ## 背景与目标

            测试任务

            ## 验收标准（可勾选）

            - [ ] 测试通过

            ## 相关路径

            | 路径 | 说明 |
            |------|------|
            | `src/` | 源码 |

            ## Memory refs（可选）

            无

            ## 证据期望（完成时必须附上）

            测试输出

            ## Freshness

            - **stale_after**：P7D
            - **最后更新时间说明**：初始创建

            **状态**：`backlog`
        """
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-001.md", content)
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_task(path)
        finally:
            validate_ads.REPO_ROOT = original
        assert any("coordination_model" in e for e in errors)

    def test_absent_coordination_model_passes(self, tmp_ads_repo):
        """当 task 完全不含 coordination_model 字段时，validate_task() 不应报错。"""
        content = (
            "# 任务：测试任务\n\n"
            "## 元数据\n\n"
            "| 字段 | 值 |\n"
            "|------|-----|\n"
            "| **task_id** | `TASK-20260322-001` |\n"
            "| **owner_role** | Developer |\n"
            "| **owner** | test |\n"
            "| **priority** | High |\n"
            "| **deps** | `[]` |\n"
            "| **handoff_to** | Integration |\n"
            "| **team_pattern_id** | |\n"
            "| **approval_owner** | HumanOwner |\n"
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
        path = write_file(tmp_ads_repo, ".ai/tasks/active/TASK-absent.md", content)
        original = validate_ads.REPO_ROOT
        validate_ads.REPO_ROOT = tmp_ads_repo
        try:
            errors = validate_ads.validate_task(path)
        finally:
            validate_ads.REPO_ROOT = original
        coord_errors = [e for e in errors if "coordination_model" in e]
        assert coord_errors == [], f"absent field should not trigger error, got: {coord_errors}"

    def test_valid_coordination_model_passes(self, tmp_ads_repo):
        for model in ["direct", "orchestrated", "peer-parallel"]:
            content = (
                "# 任务：测试任务\n\n"
                "## 元数据\n\n"
                "| 字段 | 值 |\n"
                "|------|-----|\n"
                "| **task_id** | `TASK-20260322-001` |\n"
                "| **owner_role** | Developer |\n"
                "| **owner** | test |\n"
                "| **priority** | High |\n"
                "| **deps** | `[]` |\n"
                "| **handoff_to** | Integration |\n"
                "| **team_pattern_id** | |\n"
                "| **approval_owner** | HumanOwner |\n"
                "| **allowed_agents** | `[]` |\n"
                "| **trace_id** | TRACE-001 |\n"
                "| **updated_at** | 2026-03-22T10:00:00+08:00 |\n"
                f"| **coordination_model** | {model} |\n\n"
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
            path = write_file(
                tmp_ads_repo, f".ai/tasks/active/TASK-{model}.md", content
            )
            original = validate_ads.REPO_ROOT
            validate_ads.REPO_ROOT = tmp_ads_repo
            try:
                errors = validate_ads.validate_task(path)
            finally:
                validate_ads.REPO_ROOT = original
            coord_errors = [e for e in errors if "coordination_model" in e]
            assert coord_errors == [], f"model={model} got errors: {coord_errors}"


class TestConstitutionIntegration:
    """Test that validate_constitution() is callable and returns expected results."""

    def test_main_warns_missing_constitution(self, tmp_ads_repo):
        # validate_constitution 返回非空错误列表（constitution.md 不存在）
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert len(errors) > 0
        assert "constitution.md" in errors[0]

    def test_main_passes_with_valid_constitution(self, tmp_ads_repo):
        (tmp_ads_repo / ".agent" / "constitution.md").write_text(
            "# C\n\n## Mission\nBuild.\n\n## Non-Negotiable Principles\n- X\n\n"
            "## Role Definitions\n- Dev\n\n## Agent Governance\n- Human approves\n",
            encoding="utf-8",
        )
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert errors == []
