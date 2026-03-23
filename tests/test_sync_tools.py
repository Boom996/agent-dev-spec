#!/usr/bin/env python3
"""Tests for ADS tool registry synchronization."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC_TOOLS_PATH = REPO_ROOT / "scripts" / "sync-tools.py"
SPEC = importlib.util.spec_from_file_location("sync_tools", SYNC_TOOLS_PATH)
assert SPEC and SPEC.loader
sync_tools = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync_tools)


def write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


class TestSyncTools:
    def test_sync_toolset_writes_core_and_skill_entries(self, tmp_path):
        write_json(
            tmp_path / "skills" / "game-runner" / "manifest.json",
            {
                "tool_id": "game-runner",
                "name": "game-runner",
                "version": "2.0.0",
                "description": "Run game workflows.",
            },
        )
        write_json(
            tmp_path / "tools" / "toolset.json",
            {
                "version": "1.0",
                "registry": "project-local",
                "tools": [
                    {
                        "tool_id": "game-runner",
                        "title": "Game Runner",
                        "owner": "gameplay",
                        "risk_level": "medium",
                        "version": "1.5.0",
                        "source": "skill",
                        "manifest": "skills/game-runner/manifest.json",
                    }
                ],
                "mcp_servers": [{"id": "custom-server", "config_path": "tools/mcp/custom.json"}],
            },
        )

        toolset = sync_tools.sync_toolset(tmp_path)

        tool_ids = {tool["tool_id"] for tool in toolset["tools"]}
        assert "ads.resume" in tool_ids
        assert "ads.sync_tools" in tool_ids
        assert "game-runner" in tool_ids

        game_runner = next(tool for tool in toolset["tools"] if tool["tool_id"] == "game-runner")
        assert game_runner["owner"] == "gameplay"
        assert game_runner["risk_level"] == "medium"
        assert game_runner["version"] == "2.0.0"
        assert toolset["mcp_servers"] == [{"id": "custom-server", "config_path": "tools/mcp/custom.json"}]

    def test_check_toolset_detects_drift(self, tmp_path):
        write_json(
            tmp_path / "skills" / "alpha" / "manifest.json",
            {
                "tool_id": "alpha",
                "name": "alpha",
                "version": "1.0.0",
                "description": "Alpha tool.",
            },
        )

        sync_tools.sync_toolset(tmp_path)
        assert sync_tools.check_toolset(tmp_path) is True

        toolset_path = tmp_path / "tools" / "toolset.json"
        data = json.loads(toolset_path.read_text(encoding="utf-8"))
        data["tools"] = [tool for tool in data["tools"] if tool["tool_id"] != "alpha"]
        toolset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        assert sync_tools.check_toolset(tmp_path) is False
