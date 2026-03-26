#!/usr/bin/env python3
"""Tests for ADS MCP server helpers."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_init
import ads_explain
import ads_mcp_server


MINIMAL_TASK = """\
    # 任务：MCP 测试任务

    ## 元数据

    | 字段 | 值 |
    |------|-----|
    | **task_id** | `TASK-20260324-501` |
    | **owner_role** | Backend |
    | **priority** | High |
    | **deps** | `[]` |
    | **handoff_to** | Integration |
    | **team_pattern_id** | |
    | **approval_owner** | HumanOwner |
    | **allowed_agents** | `[]` |
    | **parent_change_id** | |
    | **coordination_model** | `direct` |
    | **trace_id** | `TRACE-20260324-501` |
    | **updated_at** | `2026-03-24T10:00:00+08:00` |

    ## 单写者范围

    - **locked_paths**（本任务周期内仅主责可改）：
      - `src/` — 业务代码
    - **forbidden_paths**（禁止改动）：
      - `ops/` — 运维

    ## 共享改动升级（可选）

    无

    ## 背景与目标

    测试 MCP server。

    ## 验收标准（可勾选）

    - [ ] 测试通过

    ## 相关路径

    | 路径 | 说明 |
    |------|------|
    | `src/main.py` | 主入口 |

    ## Memory refs（可选）

    无

    ## 证据期望（完成时必须附上）

    pytest

    ## Freshness

    - **stale_after**（可选）：`P2D`
    - **最后更新时间说明**：创建

    ---

    **状态**：`in-progress`
"""


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


class TestAdsMcpServer:
    def test_build_evidence_capture_args_supports_telemetry_fields(self):
        args = ads_mcp_server.build_evidence_capture_args(
            {
                "item": "test",
                "command": "python3 -m pytest -q",
                "retry_count": 2,
                "cost_usd": "0.125000",
            },
            repo_root=REPO_ROOT,
        )

        assert "--retry-count" in args
        assert "2" in args
        assert "--cost-usd" in args
        assert "0.125000" in args

    def test_tools_list_exposes_core_ads_tools(self):
        response = ads_mcp_server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, repo_root=REPO_ROOT)
        assert response is not None
        tools = response["result"]["tools"]
        tool_names = {tool["name"] for tool in tools}
        assert "ads.resume" in tool_names
        assert "ads.doctor" in tool_names
        assert "ads.explain" in tool_names
        assert "ads.integration_reviewer" in tool_names

    def test_tools_call_runs_ads_explain(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT)
        response = ads_mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {"name": "ads.explain", "arguments": {"repo_root": str(tmp_path)}},
            },
            repo_root=REPO_ROOT,
        )
        assert response is not None
        assert response["result"]["isError"] is False
        assert "# ADS Project Brief" in response["result"]["content"][0]["text"]

    def test_tools_call_runs_ads_doctor(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT)
        response = ads_mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "ads.doctor", "arguments": {"repo_root": str(tmp_path)}},
            },
            repo_root=REPO_ROOT,
        )
        assert response is not None
        assert response["result"]["isError"] is False
        assert "ADS Doctor Report" in response["result"]["content"][0]["text"]

    def test_tools_call_runs_ads_resume(self, tmp_path):
        ads_init.init_repo(tmp_path, source_root=REPO_ROOT)
        task_path = write_file(tmp_path, ".ai/tasks/active/task.md", MINIMAL_TASK)
        response = ads_mcp_server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "ads.resume",
                    "arguments": {"task": str(task_path), "repo_root": str(tmp_path)},
                },
            },
            repo_root=REPO_ROOT,
        )
        assert response is not None
        assert response["result"]["isError"] is False
        assert "# ADS Resume" in response["result"]["content"][0]["text"]
