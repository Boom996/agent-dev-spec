# Codex CLI Adapter Guide

> 本文档是 ADS 协议的 Codex CLI 专属适配指南。
> 协议规格请参考 [`docs/00-overview.md`](../../00-overview.md) 与 [`docs/03-tools-and-mcp.md`](../../03-tools-and-mcp.md)。

## 客户端能力概述

Codex CLI 在 ADS 体系里最适合承担三类动作：

- 消费根 `README.md`、task、handoff 等 repo-native 文档
- 运行 ADS CLI 工具，生成 resume / handoff / evidence 等结构化工件
- 在同一工作树内完成实现、验证、提交与交接

它的特点是：

- 以仓库工作树为中心，适合 repo-native protocol
- 没有 Claude Code 那种专属 `@` 引用机制，因此更依赖明确的文件入口
- 很适合把 ADS 工具做成 shell / python 脚本，直接被调用

## 推荐入口顺序

进入一个 ADS 项目后，优先读取：

1. `README.md`
2. `.agent/constitution.md`
3. `.ai/START_HERE.md`
4. `.ai/tasks/active/<task-id>.md`
5. `.ai/handoffs/<task-id>.md`

如果当前是恢复上下文而不是新开任务，优先先跑：

```bash
python3 scripts/ads_resume.py .ai/tasks/active/<task-id>.md
```

如果你是第一次进入该仓库，先跑：

```bash
python3 scripts/ads_explain.py
```

如果你想直接在本地网页里查看项目首页和控制台，再跑：

```bash
python3 scripts/ads_dashboard.py
```

这个页面现在除了项目首页与概览，还会给出今日控制台、首读文档、推荐命令，以及没有 active task 时的下一步提示。

如果你当前已经在目标项目仓库中，而只是拿到了 ADS 仓库链接，推荐优先运行：

```bash
python3 /path/to/agent-dev-spec/scripts/ads_self_install.py
```

它会默认：

- 把当前 git 仓库当成接入目标
- dirty worktree 时先停下
- 自动创建新的 ADS 接入分支
- 对已有成熟项目默认走 `lean` 接入档位
- 接入成功后打开 ADS dashboard

## 推荐命令工作流

### 1. 接入新仓库

```bash
python3 scripts/ads_init.py /path/to/target-repo
cd /path/to/target-repo
python3 scripts/ads_doctor.py
```

如果是存量项目，推荐先跑：

```bash
python3 scripts/ads_adopt.py /path/to/target-repo
```

先看试用判断报告，再决定是否执行：

```bash
python3 scripts/ads_adopt.py /path/to/target-repo --apply
```

默认 `--adoption-profile auto` 会优先让成熟项目走 `lean`，只把高频协作入口注入宿主仓库；如果你明确需要把 ADS 完整参考手册镜像也复制进去，再指定 `--adoption-profile full`。

### 2. 恢复任务上下文

```bash
python3 scripts/ads_resume.py .ai/tasks/active/<task-id>.md
```

### 3. 生成 handoff 草稿

```bash
python3 scripts/ads_handoff_draft.py .ai/tasks/active/<task-id>.md \
  --from-actor "AgentImplementer @ Codex" \
  --output .ai/handoffs/<task-id>.md
```

### 4. 记录验证证据

```bash
python3 scripts/ads_evidence_capture.py \
  --item test \
  --command "python3 -m pytest -q" \
  --retry-count 1 \
  --cost-usd 0.012500
```

脚本会输出：

- 一条主 evidence row
- 一条 telemetry row（`duration_ms / cost_usd / retry_count`）

### 5. 检查 registry 是否漂移

```bash
python3 scripts/sync-tools.py --check
python3 scripts/sync-tools.py
```

### 6. 通过 MCP 统一调用 ADS 工具

如果当前 Codex 环境支持 MCP，可直接指向：

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

## 字段映射建议

| ADS 对象 | Codex CLI 中的体现 |
|---------|--------------------|
| `locked_paths` / `forbidden_paths` | 作为当前会话的显式编辑边界 |
| `handoff_status` | 判断当前是继续实现、等待恢复还是已阻塞 |
| `Evidence expectation` | 转换为要执行的验证命令与 artifact |
| `tool_id` | 在 `tools/toolset.json` 中统一登记，便于未来 MCP / adapter 共享 |

## 推荐实践

- 让根 `README.md` 成为固定首读入口，不依赖聊天历史
- 用 `ads_resume.py` 代替人工总结上下文，减少会话切换损耗
- 用 `ads_handoff_draft.py` 先生成草稿，再由执行者补充真实状态和证据
- 将 `python3 scripts/sync-tools.py --check` 纳入 CI，避免 `toolset.json` 漂移

## 已知限制

- Codex CLI 本身不是 MCP 注册中心，仍需 `toolset.json` 作为统一 registry
- 没有客户端原生 task 面板，仍需依赖 `.ai/` 目录中的任务与交接文件
- 即使已接入 ADS MCP server，repo-native 文件仍是唯一事实源，不应把状态藏进客户端私有配置
