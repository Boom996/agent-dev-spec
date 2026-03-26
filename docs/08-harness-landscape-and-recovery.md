# ADS 在 Agent Harness Stack 中的位置

## 为什么补这篇文档

外部的 Agent Harness 生态已经明显分层：规划与需求、任务编排、执行代理、运行时、协议与治理。  
ADS 以前更像“大家知道它有很多组件”，但对外表达上还不够清楚：

- 它不是单纯的 coding agent
- 它不是完整 orchestrator
- 它也不是重 runtime

ADS 的核心价值，是把 **规划、任务、handoff、证据、治理、工具注册、客户端适配** 固化到 repo 内，成为多 Agent 协作的控制面。

## Agent Harness Stack 视角

| 层 | 主要问题 | 典型代表 | ADS 角色 |
|----|----------|----------|----------|
| Human Oversight | 谁批准、谁兜底、谁回写治理结论 | PR 审核、人工批准流 | ADS 强项 |
| Planning & Requirements | Idea -> spec -> task | Chorus、OpenSpec、Spec Kit | ADS 强项 |
| Orchestration & Scheduling | 并行执行、隔离、排程 | Symphony、Vibe Kanban、Emdash | ADS 可对接，不主打替代 |
| Coding Agents | 写代码、跑命令、修 bug | Codex、Claude Code、OpenCode | ADS 兼容层 |
| Infrastructure / Protocols | MCP、agents.md、worktrees、CI | MCP、AGENTS.md、GitAgent | ADS 强项 |

## ADS 最适合做什么

### 1. 把仓库变成系统真源

- 任务、handoff、memory、spec、request、qa 都有结构化文件
- 工具声明进 `tools/toolset.json`
- 规则沉淀进 `README_AGENT.md`、`.agent/constitution.md`

### 2. 让不同客户端共享一套协作语义

- Claude Code、Codex、Cursor、OpenCode 读同一套协议
- skill / tool / MCP 统一注册
- 迁移时优先迁结构，不迁某个客户端的私有提示词

### 3. 把“阻塞”和“恢复”变成标准流程

普通 handoff 适合顺滑继续执行；  
但当任务进入 `BLOCKED` 或 `NEEDS_CONTEXT` 时，仅靠 handoff 不够。

这时 ADS 应进入 **Escalation / Recovery** 流程：

- 生成 escalation 工件
- 明确谁做决定、缺什么上下文、影响哪些任务
- 要求结论回写到 task / handoff / escalation

## 为什么 Escalation 是这轮优先级最高的新增

外部 harness landscape 明确暴露了几个生态空白：

- failure recovery
- human-agent handoff protocols
- multi-repo orchestration

ADS 最先能补上的就是前两项，因为它已经有：

- task contract
- handoff envelope
- evidence expectation
- doctor / resume / adopt 这些结构化脚本

所以这轮新增：

- `templates/escalation-handoff.md`
- `scripts/ads_escalation_draft.py`
- `.ai/escalations/` 目录约定
- `validate_ads.py` / `ads_doctor.py` / `ads_resume.py` 对 escalation 的联动支持

## 使用建议

### 什么时候只用 handoff

- 下一棒只是继续干活
- 不需要新的审批或跨边界决策
- 缺的只是普通执行上下文

### 什么时候必须升级为 escalation

- 需要人类做明确决策
- 需要跨仓库 / 跨团队协调
- 涉及安全、权限、生产策略
- 任务已经 BLOCKED，但聊天之外没有正式回写路径

## 对 ADS 后续演进的含义

这一视角会把 ADS 后续迭代从“多加几个脚本”拉回到更清楚的方向：

1. 持续加强 repo-native planning / governance / recovery
2. 对接 orchestrator，而不是重复造 orchestrator
3. 为 multi-repo / cost observability 预留正式协议面
