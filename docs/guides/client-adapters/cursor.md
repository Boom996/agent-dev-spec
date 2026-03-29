# Cursor Adapter Guide

> 本文档是 ADS 协议的 Cursor 专属适配指南。
> 协议规格请参考 [`docs/00-overview.md`](../../00-overview.md) 与 [`docs/03-tools-and-mcp.md`](../../03-tools-and-mcp.md)。

## 客户端能力概述

Cursor 适合把 ADS 用作：

- 仓库内协作协议入口
- MCP 工具消费端
- 代码编辑与局部实现客户端

它不应成为 ADS 的唯一实现层。协议文件、CLI 工具和 MCP bridge 仍应保持 repo-native。

## 推荐入口

1. `README.md`
2. `.agent/constitution.md`
3. `.ai/START_HERE.md`
4. 当前 task 与 handoff

## MCP 接入建议

将 Cursor 的 MCP 配置指向 ADS server：

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

接入后，优先暴露这些 tool_id：

- `ads.doctor`
- `ads.resume`
- `ads.handoff_draft`
- `ads.integration_reviewer`

## 推荐工作流

- 用 MCP 调 `ads.resume` 恢复上下文
- 代码改动完成后调 `ads.handoff_draft` 生成交接草稿
- 进入集成环节时调 `ads.integration_reviewer` 生成 QA 结果

## 已知限制

- Cursor 规则文件和 UI 交互属于客户端专属层，不能替代 `.ai/` 协议文件
- 若 MCP 配置损坏，ADS 仍应能通过本地脚本继续工作
