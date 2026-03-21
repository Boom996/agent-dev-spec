# Team Pattern — `human-agent-review`

> 标准人机协同评审模式。适用于 Agent 先产出实现或方案，再由人类负责人做显式审查、批准和收口的中高风险任务。

## Metadata

| 字段 | 值 |
|------|-----|
| **team_pattern_id** | `human-agent-review` |
| **version** | `1` |
| **updated_at** | `2026-03-21T00:00:00Z` |

## Description

适用于：

- 涉及共享契约、架构决策或高风险配置改动
- 需要人类负责人显式批准后才能进入集成
- Agent 可以先完成草案、实现或证据准备

## Roles

- `HumanOwner`
- `AgentImplementer`
- `Reviewer`
- `Integration`

## Entry Conditions

- 任务包含高风险路径、共享文件或高影响决策
- 完成标准要求显式 review / approval 记录
- 需要把“谁批准、为什么批准”落到仓库文件中

## Shared Context Scope

**默认可读**：

- `README_AGENT.md`
- `.ai/tasks/**`
- `.ai/handoffs/**`
- `.ai/requests/**`
- `.ai/memory/**`
- 任务声明的 `related_paths`

**默认受限**：

- `secrets/**`
- 未在 task、handoff、shared-change-request 中声明的高风险路径

## Handoff Rules

- Agent 在请求人工评审前必须写 handoff
- 若涉及共享改动，必须附 shared-change-request
- 人工评审结论应回写到 handoff、QA 或请求文件中

## Approval Flow

- `AgentImplementer` 先完成实现、证据和风险说明
- `Reviewer` 或 `HumanOwner` 做显式审批或驳回
- `Integration` 仅在批准记录存在后执行最终复跑与收口

## Integration Gate

最小要求：

- handoff 存在
- 审批记录存在
- 验证命令已复跑或明确说明未复跑原因
- 若有 shared-change-request，其状态不是 `pending`

## State Model

- `planned`
- `active`
- `review`
- `approved`
- `integration`
- `done`
