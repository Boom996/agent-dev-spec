# 多客户端适配与企业 Agent Mesh

## 多客户端（项目内）

| 客户端类型 | 建议做法 |
|------------|----------|
| IDE 类（Cursor 等） | 项目规则中引用 `README_AGENT.md` 与 `tools/mcp/`；首读链写死 |
| Claude Code / 终端 Agent | 启动时 `cat README_AGENT.md`；任务从 `.ai/tasks` 读取 |
| Codex CLI / 其他无状态 CLI | 使用 [04-handoff-and-tasks.md](04-handoff-and-tasks.md) 的上下文包 + `handoff.md` |
| Web 类（GPTs / Projects） | 上传压缩后的 `docs` + specs；Actions 指向 OpenAPI 或 Proxy |

**`.agent/agent_map.yaml`** 存放：各工具的工作目录、环境文件、额外 include 路径，避免每人一套口头约定。

## 企业 Agent Mesh（扩展）

当多部门、多 Agent 软件需**互调能力**时：

- **不统一客户端**，而统一 **可调用接口**：MCP 或 HTTP+OpenAPI。
- **注册中心（Registry）**：登记 `tool_id`、描述、端点、权限级别。
- **配置同步**：小工具从 Registry 拉取 MCP 片段，注入各客户端配置。

ADS 在本仓库的 `tools/` + `skills/` 是 **Mesh 的项目级子集**；升级到组织级时，将 `toolset.json` 与 manifest 同步到中心 Registry 即可。

## 风险摘要

- 分布式 MCP 需要 **鉴权、审计、版本**（由平台组或最小 API Key 策略解决）。
- `toolset` 与实现漂移用 **CI 校验** 兜底。

上一篇：[04-handoff-and-tasks.md](04-handoff-and-tasks.md)
