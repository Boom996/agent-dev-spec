# OpenCode Adapter Guide

> 本文档是 ADS 协议的 OpenCode / AGENTS 风格客户端适配指南。
> 协议规格请参考 [`docs/00-overview.md`](../../00-overview.md) 与 [`docs/03-tools-and-mcp.md`](../../03-tools-and-mcp.md)。

## 客户端能力概述

OpenCode 一类客户端通常具备：

- `AGENTS.md` 作为规则入口
- 本地命令执行能力
- 可选的 MCP 配置支持

这类客户端非常适合消费 ADS 的 repo-native 结构，但依然应把核心状态留在 `.ai/`、`.agent/`、`tools/` 下。

## 推荐入口

在项目根的 `AGENTS.md` 中显式引用：

- `README_AGENT.md`
- `.agent/constitution.md`
- `.ai/START_HERE.md`

## 推荐工作流

如果客户端偏命令式而不是 UI 驱动，直接运行：

```bash
python3 scripts/ads_resume.py .ai/tasks/active/<task-id>.md
python3 skills/handoff-writer/run.py .ai/tasks/active/<task-id>.md
python3 skills/integration-reviewer/run.py .ai/tasks/active/<task-id>.md .ai/handoffs/<task-id>.md
```

如果客户端支持 MCP，则推荐直接接入：

```json
{
  "mcpServers": {
    "ads-server": {
      "command": "python3",
      "args": [
        "scripts/ads_mcp_server.py",
        "--repo-root",
        "."
      ]
    }
  }
}
```

## 已知限制

- 不同 OpenCode 风格客户端对 `AGENTS.md` 的自动加载行为不完全一致
- 因此仍需要保留 CLI 作为稳定降级路径
