# Shared Change Request — `SCR-20260321-002`

## Metadata

| 字段 | 值 |
|------|-----|
| **request_id** | `SCR-20260321-002` |
| **task_id** | `TASK-20260321-001` |
| **requested_by** | Frontend @ Cursor |
| **approval_owner** | Architect |
| **trace_id** | `TRACE-20260321-001` |
| **updated_at** | 2026-03-21T10:15:00Z |

## Requested change

**目标文件 / 目录**：

- `shared/theme/tokens.ts` — 希望顺手重命名按钮色板 token

**为什么不能留在当前 locked_paths 内解决**：

按钮样式想统一为新命名，但 token 文件是跨组件共享资产，不属于当前前端任务的 locked_paths。

**拟议改动**：

- 将 `buttonPrimary` 重命名为 `brandButtonPrimary`
- 同步修改现有消费方

## Impact

**可能影响的任务**：

- `TASK-20260321-001`
- 后续所有使用旧 token 的 UI 任务

**风险说明**：

- 会引入额外的迁移范围
- 与本轮“只交付最小 Button 能力”的目标不一致

## Decision

**结论**：`rejected`

**批准备注**：

本轮不扩展设计 token 命名范围，先保持既有主题稳定，后续单开 token 治理任务。

**后续动作**：

- Frontend 保持使用现有主题类名完成 Button
- 若仍需 token 重构，单独创建新 task 和 shared-change-request
