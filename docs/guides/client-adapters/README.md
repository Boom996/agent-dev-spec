# ADS Client Adapter Guides

> **重要架构边界**：本目录下的文档是各客户端的 **Adapter Guide**（适配指南），
> 不是 ADS 协议规格的一部分。
>
> - **ADS 协议**（`docs/` 下的规范文档）：client-agnostic，任何工具均适用
> - **Adapter Guide**（本目录）：客户端专属实现建议，不影响协议定义
>
> 增加新客户端支持时，在本目录新建 `<client-name>.md`，不要修改 ADS 协议文档。

## 可用适配指南

| 客户端 | 指南 | 说明 |
|--------|------|------|
| Claude Code | [claude-code.md](claude-code.md) | CLAUDE.md 模板、hooks 配置、Auto Memory 映射 |
| Codex CLI | [codex-cli.md](codex-cli.md) | `ads_resume` / `ads_handoff_draft` / `ads_evidence_capture` 工作流 |
| Cursor | [cursor.md](cursor.md) | MCP 驱动的 ADS tool workflow |
| OpenCode | [opencode.md](opencode.md) | `AGENTS.md` + CLI / MCP 结合方式 |

## 适配指南编写规范

每个适配指南应包含：

1. **客户端能力概述**：该客户端有哪些 ADS 相关能力
2. **入口配置**：如何让客户端自动读取 ADS 协议文件
3. **字段映射**：ADS 字段如何在该客户端中体现
4. **推荐配置**：该客户端的最佳实践配置示例
5. **已知限制**：该客户端无法支持的 ADS 能力
