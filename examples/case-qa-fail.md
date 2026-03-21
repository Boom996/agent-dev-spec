# QA 结论：FAIL — `TASK-20260321-002`

## 任务

| 字段 | 值 |
|------|-----|
| **task_id** | TASK-20260321-002 |
| **描述** | 后端审计契约首轮交付后，Integration 发现字段命名与前端消费预期不一致 |
| **Developer** | Backend @ Claude Code |
| **QA** | Integration |
| **Attempt** | 第 1 次 |
| **Timestamp** | 2026-03-21T13:30:00Z |

## 结论：FAIL

## 问题列表

### Issue 1 — 严重级别：High

| 项 | 内容 |
|----|------|
| **描述** | 共享契约导出的时间字段命名为 `created_at`，与已批准请求中的 `timestamp` 不一致 |
| **期望** | 保持 `SCR-20260321-001` 中约定的最小字段：`actor_type`、`actor_id`、`timestamp` |
| **实际** | 实现中输出为 `actor_type`、`actor_id`、`created_at` |
| **证据** | 本地类型检查通过，但前端 mock 消费时报字段缺失；参见 `examples/case-shared-change-request.md` 中批准结论 |
| **修复指令** | 将共享契约字段统一回 `timestamp`，更新 handoff 中的 evidence，并重新提交 Integration 复核 |
| **涉及路径** | `shared/contracts/approval_event.ts` |

## 下一动作

→ Developer：按修复指令修改后更新 `.ai/handoffs/TASK-20260321-002.md` 并重新提交评审
