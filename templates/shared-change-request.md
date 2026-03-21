# Shared Change Request — `<request_id>`

> 用于处理跨任务共享文件改动，避免直接绕过单写者原则。保存为 `.ai/requests/<request_id>.md` 或团队约定路径。

## Metadata

| 字段 | 值 |
|------|-----|
| **request_id** | `SCR-YYYYMMDD-001` |
| **task_id** | |
| **requested_by** | 角色 / 人 / Agent |
| **approval_owner** | |
| **trace_id** | |
| **updated_at** | ISO8601 |

## Requested change

**目标文件 / 目录**：

- `path/to/shared/file` — 说明

**为什么不能留在当前 locked_paths 内解决**：

（1～3 句话）

**拟议改动**：

- 变更 1
- 变更 2

## Impact

**可能影响的任务**：

- `TASK-...`

**风险说明**：

- 风险 1
- 风险 2

## Decision

**结论**：`pending` | `approved` | `rejected`

**批准备注**：

（一句话）

**后续动作**：

- 谁来改
- 改完回写到哪个 task / handoff
