# ADS Escalation — `<task_id>`

> 用于处理 **普通 handoff 无法闭环** 的阻塞：需要人类决策、跨团队上下文、跨仓库协调、安全/权限批准或运行时恢复动作。保存为 `.ai/escalations/<task_id>.md`。

## Metadata

| 字段 | 值 |
|------|-----|
| **escalation_id** | `ESC-YYYYMMDD-001` |
| **task_id** | `TASK-YYYYMMDD-001` |
| **source_handoff** | `.ai/handoffs/<task_id>.md` |
| **escalation_type** | `needs_human_decision` \| `needs_context` \| `cross_repo` \| `security` \| `runtime_failure` |
| **requested_by** | 角色 / 人 / Agent |
| **decision_owner** | 负责决策或解阻的人 / 角色 |
| **urgency** | `low` \| `medium` \| `high` |
| **status** | `pending` \| `resolved` \| `cancelled` |
| **trace_id** | `TRACE-...` |
| **updated_at** | ISO8601 |

## Current Block

**当前阻塞**：

（1～3 句话说明为什么现有任务或 handoff 无法继续）

**为什么普通 handoff 不够**：

- 缺什么决定 / 上下文 / 权限
- 为什么下一棒不能自行判断

## Decision Request

**需要谁做什么决定**：

- 决策 1
- 决策 2

**建议选项**：

- 选项 A：说明
- 选项 B：说明

**推荐路径**：

（一句话说明当前建议）

## Impact

**影响的任务 / 仓库 / 团队**：

- `TASK-...`
- `repo-or-system`

**如果不处理会怎样**：

- 风险 1
- 风险 2

## Evidence & Context

**相关证据**：

- `artifacts/...`
- `.ai/handoffs/<task_id>.md`

**补充上下文**：

- 事实 1
- 事实 2

## Resolution

**决策结果**：

（待填写）

**后续动作**：

- 谁回写 handoff / task
- 谁继续执行
