#!/usr/bin/env python3
"""Tests for ADS repo bootstrap scaffolding."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_init


class TestAdsInit:
    def test_init_repo_creates_bootstrap_files(self, tmp_path):
        target_root = tmp_path / "space-game"

        result = ads_init.init_repo(target_root, source_root=REPO_ROOT)

        assert result.created
        assert (target_root / "README.md").exists()
        assert (target_root / ".agent" / "constitution.md").exists()
        assert (target_root / ".agent" / "docs" / "00-overview.md").exists()
        assert (target_root / ".agent" / "docs" / "08-harness-landscape-and-recovery.md").exists()
        assert (target_root / ".agent" / "docs" / "guides" / "adoption-playbook.md").exists()
        assert (target_root / ".agent" / "docs" / "guides" / "client-adapters" / "codex-cli.md").exists()
        assert (target_root / ".agent" / "docs" / "guides" / "client-adapters" / "cursor.md").exists()
        assert (target_root / ".agent" / "docs" / "guides" / "client-adapters" / "opencode.md").exists()
        assert (target_root / ".agent" / "docs" / "research" / "README.md").exists()
        assert (target_root / ".ai" / "START_HERE.md").exists()
        assert (target_root / ".ai" / "escalations").exists()
        assert (target_root / ".ai" / "innovations").exists()
        assert (target_root / ".github" / "workflows" / "ads-checks.yml.example").exists()
        assert (target_root / "tools" / "toolset.json").exists()
        assert (target_root / "tools" / "mcp" / "ads-server.json.example").exists()
        assert (target_root / "scripts" / "ads_dashboard.py").exists()
        assert (target_root / "scripts" / "ads_doctor.py").exists()
        assert (target_root / "scripts" / "ads_explain.py").exists()
        assert (target_root / "scripts" / "ads_escalation_draft.py").exists()
        assert (target_root / "scripts" / "ads_mcp_server.py").exists()
        assert (target_root / "scripts" / "sync-tools.py").exists()

        identity = json.loads((target_root / ".agent" / "identity.json").read_text(encoding="utf-8"))
        assert identity["project_name"] == "space-game"
        assert identity["standard_verify_commands"]["test"] == "TODO: add your standard verify command"

        toolset = json.loads((target_root / "tools" / "toolset.json").read_text(encoding="utf-8"))
        tool_ids = {tool["tool_id"] for tool in toolset["tools"]}
        assert "ads.dashboard" in tool_ids
        assert "ads.doctor" in tool_ids
        assert "ads.explain" in tool_ids
        assert "ads.escalation_draft" in tool_ids
        assert "ads.sync_tools" in tool_ids

        readme = (target_root / "README.md").read_text(encoding="utf-8")
        assert "ADS Agent Quick Start" in readme
        assert ".ai/START_HERE.md" in readme
        assert ".agent/docs/guides/adoption-playbook.md" in readme

    def test_init_repo_merges_ads_quick_start_into_existing_readme(self, tmp_path):
        target_root = tmp_path / "existing-readme"
        target_root.mkdir(parents=True)
        (target_root / "README.md").write_text("# Existing Project\n\nOriginal content.\n", encoding="utf-8")

        ads_init.init_repo(target_root, source_root=REPO_ROOT)

        readme = (target_root / "README.md").read_text(encoding="utf-8")
        assert "ADS Agent Quick Start" in readme
        assert "Original content." in readme

    def test_init_repo_infers_node_verify_commands(self, tmp_path):
        target_root = tmp_path / "arcade"
        target_root.mkdir(parents=True)
        (target_root / "package.json").write_text('{"name":"arcade"}\n', encoding="utf-8")

        ads_init.init_repo(target_root, source_root=REPO_ROOT)

        identity = json.loads((target_root / ".agent" / "identity.json").read_text(encoding="utf-8"))
        assert identity["standard_verify_commands"] == {
            "lint": "npm run lint",
            "test": "npm run test",
            "build": "npm run build",
        }

    def test_init_repo_skips_existing_files_without_force(self, tmp_path):
        target_root = tmp_path / "existing-repo"
        target_root.mkdir(parents=True)
        existing_identity = target_root / ".agent" / "identity.json"
        existing_identity.parent.mkdir(parents=True, exist_ok=True)
        existing_identity.write_text('{"project_name":"keep-me"}\n', encoding="utf-8")

        result = ads_init.init_repo(target_root, source_root=REPO_ROOT, force=False)

        assert existing_identity in result.skipped
        identity = json.loads(existing_identity.read_text(encoding="utf-8"))
        assert identity["project_name"] == "keep-me"

    def test_init_repo_overwrites_existing_files_with_force(self, tmp_path):
        target_root = tmp_path / "overwrite-repo"
        target_root.mkdir(parents=True)
        existing_identity = target_root / ".agent" / "identity.json"
        existing_identity.parent.mkdir(parents=True, exist_ok=True)
        existing_identity.write_text('{"project_name":"old"}\n', encoding="utf-8")

        result = ads_init.init_repo(target_root, source_root=REPO_ROOT, force=True, project_name="new-name")

        assert existing_identity in result.overwritten
        identity = json.loads(existing_identity.read_text(encoding="utf-8"))
        assert identity["project_name"] == "new-name"
