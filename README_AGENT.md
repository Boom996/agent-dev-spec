# Agent 自举入口（ADS）

> **Agent Development Specification（ADS）** — 多 Agent 协作时请先读本文件，再读宿主项目的 `docs/03-development/ai-context.md` 或等价上下文（若存在）。

## 本工程遵循的规范

- **规范名**：Agent 开发规范 / **Agent Development Specification（ADS）**
- **工作空间**：采用与 ADS 兼容的目录（参见本仓库 `docs/02-uaw-mapping.md`）。
- **工具**：优先通过 **MCP** 与 **`tools/toolset.json`** 声明可调用的能力；业务逻辑不锁死在某一客户端私有配置里。

## 首读顺序（建议固定）

1. **本文件**（`README_AGENT.md`）
2. 宿主项目 **AI 上下文**（例如 `docs/03-development/ai-context.md`）
3. 宿主项目 **协作入口**（例如 `.ai/START_HERE.md`）
4. **当前任务**对应的 `task.md` 或 backlog 条目（须含验收标准与相关路径）
5. **交接物**（若存在）：`.ai/handoffs/<task-id>.md`

## 你必须遵守的三条纪律

1. **单写者**：同一任务周期内，对约定路径仅一名主责开发者（人或 Agent）；他人只评审或开子任务。
2. **交接落盘**：跨会话/跨工具继续工作时，必须留下 **Handoff Envelope**（见 `templates/handoff.md`），禁止仅依赖聊天历史。
3. **证据闭环**：标记完成前，按任务中的 **Evidence expectation** 提供可验证输出（命令、测试结果、截图等）。

## 目录速查（复制本 ADS 模板后的典型布局）

| 路径 | 用途 |
|------|------|
| `.agent/identity.json` | 工程目标、约束、默认角色 |
| `.agent/agent_map.yaml` | 各客户端（Cursor / Claude Code / Codex 等）路径与片段映射 |
| `tools/mcp/` | MCP 连接配置 |
| `tools/toolset.json` | 统一工具 ID 清单 |
| `skills/<name>/manifest.json` | Schema-First 技能描述 |
| `.ai/tasks/` | 任务 backlog / in-progress |
| `.ai/handoffs/` | 结构化交接文档 |
| `.ai/requests/` | 共享改动升级请求 |
| `.ai/qa/` | QA / Integration 结论 |
| `.ai/patterns/` | 标准 team pattern |
| `.ai/memory/` | 共享事实层 |

## 不确定时

打开本仓库 **`docs/00-overview.md`**，按索引阅读细则。
