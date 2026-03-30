# Claude Code Adapter Guide

> 本文档是 ADS 协议的 Claude Code 专属适配指南。
> 协议规格请参考 `docs/00-overview.md`、`docs/01-principles.md` 与 `docs/03-tools-and-mcp.md`。

## 客户端能力概述

Claude Code 在 ADS 客户端中具备最强的自动化能力：
- CLAUDE.md 自动加载（零摩擦协议入口）
- Hooks 系统（SessionStart / PreToolUse / PostToolUse）
- Auto Memory（跨会话持久记忆）
- 子 Agent 并发派发
- Plan Mode（EnterPlanMode / ExitPlanMode）

## ADS 入口配置

在项目根目录创建 `CLAUDE.md`，引用 ADS 核心文件：

```markdown
# [项目名] — ADS 协作入口

## ADS 规范
@README.md

## ADS 宪法
@.agent/constitution.md

## 当前活跃任务
@.ai/tasks/active/[TASK-ID].md

## ADS 三条纪律
1. 单写者：修改文件前检查 locked_paths
2. 交接落盘：跨会话必须写 .ai/handoffs/<task-id>.md
3. 证据闭环：完成前附上命令输出
```

## 推荐 Hooks 配置

最小可用思路：

- `SessionStart`：提醒先读 `README.md`、`.agent/constitution.md`、`.ai/START_HERE.md`
- `PreToolUse`：在写文件前检查 task 中的 `locked_paths` / `forbidden_paths`
- `PostToolUse`：在任务结束前提醒补 handoff 与 evidence

如果团队需要更强的 Claude Code 工作流，可以在自己的私有研发仓库里维护更细的 hooks 模板，而不是把内部配置推演过程放进公开产品仓库。

## Auto Memory 与 ADS Memory 映射

| ADS 对象 | Claude Auto Memory 对应 |
|---------|----------------------|
| memory-object (decision) | MEMORY.md 的架构决策节 |
| memory-object (fact) | MEMORY.md 的项目事实节 |
| memory-object (risk) | MEMORY.md 的风险追踪节 |

## 已知限制

- CLAUDE.md 的 `@` 引用是 Claude Code 专属，其他客户端不支持
- Hooks 配置（`.claude/settings.json`）是 Claude Code 专属
- Auto Memory 目录（`.claude/projects/*/memory/`）不在 ADS repo 内，不能被其他客户端消费
