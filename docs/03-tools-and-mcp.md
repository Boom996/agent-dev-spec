# 工具层：MCP、manifest 与 toolset

## 目标

- 同一能力在 **Cursor / Claude Code / Codex CLI / 自研运行时** 中以**同一 `tool_id`** 被理解。
- 描述与参数以 **Schema** 为准，避免口头约定漂移。

## MCP（推荐）

- 将可复用能力封装为 **MCP Server**（本地或内网）。
- 连接信息放在 **`tools/mcp/`**（按 server 分文件或子目录），不在各客户端重复手写多份矛盾配置。
- 客户端仅「指向」该目录或生成后的片段。

## Schema-First：Skill manifest

每个技能目录建议包含 **`manifest.json`**（或等价 YAML），字段至少包括：

- `name` / `tool_id`：稳定 ID，与 `toolset.json` 一致
- `description`：供模型与用户理解
- `parameters`：JSON Schema 或 OpenAPI 风格的参数描述
- `entry`：入口命令、脚本路径或服务端点说明

示例见 `skills/_example-skill/manifest.json`。

## toolset.json

**`tools/toolset.json`** 聚合：

- 本仓库注册的 MCP tools（或引用 manifest）
- 版本、责任人、风险等级、标签（可选）

供脚本生成各客户端配置片段，或供人类查阅「全仓可调用的工具 ID」。

最小治理字段建议优先保持精简：

- `owner`
- `risk_level`
- `version`

对于 `risk_level=high` 的工具，建议额外配套：

- `human-agent-review` 这类人工审批 pattern
- `shared-change-request` 批准记录
- 在 handoff / QA 中留下复核证据

先不要一开始就把 `toolset` 推向完整 registry；项目级模板阶段以“可读、可校验、可追责”为主。

## 校验与防漂移

建议在 CI 或 pre-commit 中：

- manifest 引用的文件存在
- `toolset.json` 中的 ID 与 manifest 一致
- MCP 配置 JSON/YAML 可解析

## 无 MCP 时的降级

使用 **`tools/openapi/`** 保存契约，由轻量 **HTTP Proxy** 暴露给仅支持 Actions/HTTP 的客户端；仍在 `toolset.json` 中登记同一 `tool_id`。

上一篇：[02-uaw-mapping.md](02-uaw-mapping.md) · 下一篇：[04-handoff-and-tasks.md](04-handoff-and-tasks.md)
