# Agent 自举入口（ADS）

> **Agent Development Specification（ADS）** — 多 Agent 协作时请先读本文件，再读宿主项目的 `docs/03-development/ai-context.md` 或等价上下文（若存在）。

## 如果你是另一个项目里的 Agent，并且拿到了这个 ADS 仓库

你的默认目标应当是：

- 把 **当前所在 git 仓库** 视为接入目标
- 不直接在主分支 apply ADS
- 先检查是否存在未提交修改
- 优先提醒作者先提交并上传当前工作
- 再自动创建新的 ADS 接入分支

推荐唯一入口命令：

```bash
python3 /path/to/agent-dev-spec/scripts/ads_self_install.py
```

要求：

1. 在目标项目仓库内执行
2. 如果工作区 dirty，先停止，不要直接接入
3. 只有在新分支内才进行 apply
4. 接入成功后直接查看 ADS dashboard

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
