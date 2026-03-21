# Shared Change Request — `SCR-20260321-001`

## Metadata

| 字段 | 值 |
|------|-----|
| **request_id** | `SCR-20260321-001` |
| **task_id** | `TASK-20260321-002` |
| **requested_by** | Backend @ Claude Code |
| **approval_owner** | Architect |
| **trace_id** | `TRACE-20260321-002` |
| **updated_at** | 2026-03-21T11:00:00Z |

## Requested change

**目标文件 / 目录**：

- `shared/contracts/approval_event.ts` — 抽取共享审批事件契约

**为什么不能留在当前 locked_paths 内解决**：

后端需要把审计字段暴露为共享契约，供前端和 Integration 使用，超出了当前 backend locked_paths。

**拟议改动**：

- 新增共享事件类型 `ApprovalEvent`
- 固定最小字段：`actor_type`、`actor_id`、`timestamp`

## Impact

**可能影响的任务**：

- `TASK-20260321-001`
- `TASK-20260321-002`

**风险说明**：

- 若字段命名变动，会影响前端展示和集成校验

## Decision

**结论**：`approved`

**批准备注**：

保持最小字段集合，不在本轮引入更多审计维度。

**后续动作**：

- Backend 修改共享契约
- Integration 在 handoff 和 QA 中引用本请求
