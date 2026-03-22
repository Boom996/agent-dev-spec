# Team Pattern — `frontend-backend-integration`

> 标准前端、后端、集成协作模式。适用于需要多角色接力、结构化 handoff、Integration 统一收口的小中型开发任务。

## Metadata

| 字段 | 值 |
|------|-----|
| **team_pattern_id** | `frontend-backend-integration` |
| **version** | `1` |
| **updated_at** | `2026-03-21T00:00:00Z` |
| **coordination_model** | `peer-parallel` |

## Description

适用于：

- 前端与后端并行开发
- 需要 Integration 统一复跑验证命令
- 需要显式 handoff 与 evidence 闭环

## Roles

- `Frontend`
- `Backend`
- `Integration`

## Entry Conditions

- 任务同时涉及 UI / API / shared schema 中至少两类改动
- 需要至少一次跨角色交接
- 完成标准中包含验证命令或集成复核步骤

## Shared Context Scope

**默认可读**：

- `README_AGENT.md`
- `.ai/tasks/**`
- `.ai/handoffs/**`
- `docs/**`
- 任务声明的 `related_paths`

**默认受限**：

- `secrets/**`
- 未在任务或 shared-change-request 中声明的敏感路径

## Handoff Rules

- Frontend 和 Backend 在移交 Integration 前都必须写 handoff
- handoff 必须附结构化 evidence
- 若改动共享 schema 或公共类型，必须附 shared-change-request

## Approval Flow

- Frontend / Backend 各自完成本角色交付
- `Integration` 负责最终复跑验证、检查证据、确认状态
- 需要共享改动批准时，由任务中的 `approval_owner` 或指定角色确认

## Integration Gate

最小要求：

- handoff 存在
- evidence 结构完整
- 标准验证命令已记录
- 共享改动已批准或明确标记为无

## State Model

- `planned`
- `active`
- `handoff`
- `integration`
- `done`
