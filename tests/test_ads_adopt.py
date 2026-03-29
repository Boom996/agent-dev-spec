#!/usr/bin/env python3
"""Tests for ADS brownfield adoption automation."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_adopt
import ads_doctor


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def build_brownfield_repo(tmp_path: Path) -> Path:
    target_root = tmp_path / "AgentGames"
    (target_root / ".git").mkdir(parents=True)
    write_file(target_root, ".golutra/workspace.json", '{"members":[]}\n')
    write_file(target_root, "docs/superpowers/plans/HANDOFF.md", "# Legacy handoff\n")
    write_file(
        target_root,
        "docs/superpowers/specs/2026-03-24-agent-maze-project-guide.md",
        "# Agent迷宫世界项目导读\n\n> Web 端 2D、多 Agent 羁绊驱动的异步观察 RPG\n",
    )

    code_root = target_root / "agentgames"
    (code_root / ".git").mkdir(parents=True)
    (code_root / "apps").mkdir(parents=True)
    (code_root / "packages").mkdir(parents=True)
    write_file(code_root, "turbo.json", '{ "tasks": {} }\n')
    write_file(
        code_root,
        "package.json",
        json.dumps(
            {
                "name": "agentgames",
                "private": True,
                "packageManager": "pnpm@10.30.3",
                "scripts": {
                    "lint": "turbo lint",
                    "test": "turbo test",
                    "build": "turbo build",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    return target_root


class TestAdsAdopt:
    def test_build_report_detects_primary_code_root_and_legacy_systems(self, tmp_path):
        target_root = build_brownfield_repo(tmp_path)

        report = ads_adopt.build_report(target_root)

        assert report.project_name == "AgentGames"
        assert report.workspace_root_name == "AgentGames"
        assert report.primary_code_root == "agentgames"
        assert report.verify_commands == {
            "lint": "pnpm --dir agentgames lint",
            "test": "pnpm --dir agentgames test",
            "build": "pnpm --dir agentgames build",
        }
        assert "golutra_workspace" in report.existing_systems
        assert "agentgames" in report.nested_git_roots
        assert report.context_docs[0] == "docs/superpowers/specs/2026-03-24-agent-maze-project-guide.md"
        assert report.vision_one_liner == "Web 端 2D、多 Agent 羁绊驱动的异步观察 RPG"
        assert report.adoption_fit == "recommended"
        assert report.recommended_mode == "report_then_apply"
        assert report.trial_path[0].startswith("先阅读")
        assert "python3 scripts/ads_adopt.py" in report.apply_next_commands[0]

    def test_build_report_accepts_project_name_override(self, tmp_path):
        target_root = build_brownfield_repo(tmp_path)

        report = ads_adopt.build_report(target_root, project_name="AgentGames")

        assert report.project_name == "AgentGames"

    def test_apply_adoption_bootstraps_custom_project_files(self, tmp_path):
        target_root = build_brownfield_repo(tmp_path)

        report, result = ads_adopt.apply_adoption(target_root, force=False)

        assert result.created
        assert report.primary_code_root == "agentgames"
        assert (target_root / "README.md").exists()
        assert (target_root / ".agent" / "identity.json").exists()
        assert (target_root / ".agent" / "adoption-report.json").exists()
        assert (target_root / ".agent" / "docs" / "guides" / "project-brief.md").exists()
        assert (target_root / ".agent" / "docs" / "guides" / "project-adoption-report.md").exists()
        assert (target_root / ".agent" / "docs" / "guides" / "legacy-workspace-mapping.md").exists()
        assert (target_root / ".ai" / "tasks" / "backlog" / "TASK-00000000-001-ads-adoption.md").exists()

        identity = json.loads((target_root / ".agent" / "identity.json").read_text(encoding="utf-8"))
        assert identity["vision_one_liner"] == "Web 端 2D、多 Agent 羁绊驱动的异步观察 RPG"
        assert identity["standard_verify_commands"]["test"] == "pnpm --dir agentgames test"
        assert identity["docs_entry"]["ai_context"] == "docs/superpowers/specs/2026-03-24-agent-maze-project-guide.md"
        assert identity["docs_entry"]["project_brief"] == ".agent/docs/guides/project-brief.md"

        readme = (target_root / "README.md").read_text(encoding="utf-8")
        assert "ADS Agent Quick Start" in readme
        assert "agentgames" in readme
        assert ".agent/docs/guides/project-brief.md" in readme
        assert ".agent/docs/guides/legacy-workspace-mapping.md" in readme

        project_brief = (target_root / ".agent" / "docs" / "guides" / "project-brief.md").read_text(encoding="utf-8")
        assert "# ADS Project Brief" in project_brief
        assert "- project: AgentGames" in project_brief
        assert "docs/superpowers/specs/2026-03-24-agent-maze-project-guide.md" in project_brief
        assert "python3 scripts/ads_doctor.py" in project_brief

        findings = ads_doctor.run_doctor(target_root)
        assert findings == []

        summary = ads_adopt.render_apply_summary(report)
        assert "## Trial Ready Summary" in summary
        assert "python3 scripts/ads_doctor.py" in summary
        assert "README.md" in summary

    def test_write_report_files_emits_markdown_and_json(self, tmp_path):
        target_root = build_brownfield_repo(tmp_path)
        report = ads_adopt.build_report(target_root, project_name="AgentGames")
        markdown_path = tmp_path / "reports" / "adoption.md"
        json_path = tmp_path / "reports" / "adoption.json"

        written = ads_adopt.write_report_files(report, markdown_path, json_path)

        assert markdown_path in written
        assert json_path in written
        assert "## Next Commands" in markdown_path.read_text(encoding="utf-8")
        assert "## Trial Summary" in markdown_path.read_text(encoding="utf-8")
        assert "## Recommended Mode" in markdown_path.read_text(encoding="utf-8")
        assert "## Minimal Trial Path" in markdown_path.read_text(encoding="utf-8")
        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["project_name"] == "AgentGames"
        assert data["workspace_root_name"] == "AgentGames"
        assert data["adoption_fit"] == "recommended"
