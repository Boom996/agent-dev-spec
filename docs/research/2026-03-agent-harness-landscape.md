# ADS Agent Harness Landscape — 2026-03

## 研究目的

基于 `Awesome Agent Harness` 等外部资料，建立 ADS 对 Agent Harness 生态的结构化认识，并明确哪些方向值得吸收进入 ADS 主线。

## 外部生态的共同分层

| 层 | 核心职责 | 代表能力 |
|----|----------|----------|
| Human Oversight | 批准、兜底、治理 | proposal approval、review、release sign-off |
| Planning & Requirements | idea -> spec -> task | spec generation、task DAG、change proposal |
| Orchestration & Scheduling | 并行执行与隔离 | worktree isolation、parallel agents、CI feedback |
| Coding Agents | 实际编码与修复 | Codex、Claude Code、OpenCode、Gemini CLI |
| Infrastructure / Protocols | 工具连接、配置、标准 | MCP、AGENTS.md、agents.md、CI/CD |

## 对 ADS 的判断

### ADS 当前已经强的地方

- repo-native planning / governance
- task、handoff、memory、request、qa 的结构化协议
- MCP / tool registry / client adapter 连接层
- brownfield adoption（`ads_adopt.py`）

### ADS 还不够强的地方

- failure recovery / escalation 协议不够正式
- multi-repo 协作还没有正式语义
- 生态研究机制此前没有产品化
- 对外“我处在 stack 哪一层”的表达还不够清晰

## 本轮吸收结论

### 已决定纳入 ADS 主线

1. **Stack Positioning**
   - 明确 ADS 不是 coding agent，也不是完整 orchestrator
   - 它是 repo-native control plane

2. **Research Layer**
   - 建立 `docs/research/`
   - 研究输出要回写 roadmap，而不是停留在观察

3. **Escalation / Recovery**
   - 把 BLOCKED / NEEDS_CONTEXT 的正式升级路径协议化
   - 用结构化工件承接人机交接，而不是只留在聊天里

### 暂列下一阶段

1. multi-repo workspace 协议
2. agent cost observability
3. orchestrator 对接适配层

## 对 ADS roadmap 的影响

### P0

- escalation template + draft script + doctor / resume / validate 联动
- stack positioning 文档
- research 目录与月度报告格式

### P1

- multi-repo adoption report
- cross-repo handoff / escalation 语义
- cost / runtime evidence 字段

### P2

- orchestrator adapter guides
- research automation scaffolding
