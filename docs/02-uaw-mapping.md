# UAW 目录映射（ADS 落地）

**UAW** = 统一 Agent 工作空间思想：**声明式配置 + 标准化接口**。ADS 不强制固定目录名，但推荐下表；复制到业务仓库时保持**相对关系**即可。

## 推荐映射表

| UAW 概念 | ADS 推荐路径 | 说明 |
|----------|--------------|------|
| 工程身份 | `.agent/identity.json` | 目标、约束、默认角色、标准验证命令 |
| 客户端映射 | `.agent/agent_map.yaml` | Cursor / Claude Code / Codex 等到路径、env、首读文件的映射 |
| 原子能力 | `skills/<name>/` | 脚本或可执行逻辑 + `manifest.json` |
| MCP 配置 | `tools/mcp/` | 各 MCP Server 的连接配置 |
| OpenAPI（可选） | `tools/openapi/` | HTTP 契约，供不支持 MCP 的客户端 |
| 工具清单 | `tools/toolset.json` | 统一 `tool_id` 列表与描述 |
| 人类文档 | 宿主 `docs/` | 架构、功能、开发指南 |
| Agent 规格 | `.ai/specs/`（可选） | 面向实现的切片规格 |
| 任务 | `.ai/tasks/` | backlog / in-progress / completed |
| 交接 | `.ai/handoffs/` | `<task-id>.md` |
| 模板 | `.ai/templates/` | 从本仓库 `templates/` 同步或软链 |

## 复制到业务仓库的最小集

**P0（协作纪律）**

- 根目录 `README_AGENT.md`
- `.ai/tasks/` + `.ai/handoffs/`
- `templates/task.md` / `handoff.md`（可放在 `.ai/templates/`）

**P1（多客户端一致）**

- `.agent/identity.json`
- `.agent/agent_map.yaml`

**P2（工具标准化）**

- `tools/toolset.json`
- `tools/mcp/`
- `skills/*/manifest.json`

## 原则

**业务逻辑**放在 `skills/`、应用源码目录或服务代码中；**不要**把唯一实现锁在某个 IDE 插件私有存储里。

上一篇：[01-principles.md](01-principles.md) · 下一篇：[03-tools-and-mcp.md](03-tools-and-mcp.md)
