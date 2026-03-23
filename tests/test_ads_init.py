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
        assert (target_root / "README_AGENT.md").exists()
        assert (target_root / ".agent" / "constitution.md").exists()
        assert (target_root / ".agent" / "docs" / "00-overview.md").exists()
        assert (target_root / ".agent" / "docs" / "guides" / "client-adapters" / "codex-cli.md").exists()
        assert (target_root / ".ai" / "START_HERE.md").exists()
        assert (target_root / "tools" / "toolset.json").exists()
        assert (target_root / "tools" / "mcp" / "ads-server.json.example").exists()
        assert (target_root / "scripts" / "ads_doctor.py").exists()
        assert (target_root / "scripts" / "sync-tools.py").exists()

        identity = json.loads((target_root / ".agent" / "identity.json").read_text(encoding="utf-8"))
        assert identity["project_name"] == "space-game"
        assert identity["standard_verify_commands"]["test"] == "TODO: add your standard verify command"

        toolset = json.loads((target_root / "tools" / "toolset.json").read_text(encoding="utf-8"))
        tool_ids = {tool["tool_id"] for tool in toolset["tools"]}
        assert "ads.doctor" in tool_ids
        assert "ads.sync_tools" in tool_ids

        readme_agent = (target_root / "README_AGENT.md").read_text(encoding="utf-8")
        assert ".agent/docs/00-overview.md" in readme_agent

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
