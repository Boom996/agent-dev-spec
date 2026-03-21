# Memory Object — `MEM-20260321-001`

## Metadata

| 字段 | 值 |
|------|-----|
| **memory_id** | `MEM-20260321-001` |
| **type** | `decision` |
| **title** | Button 组件最小契约 |
| **scope** | `project` |
| **owner** | Architect |
| **status** | `active` |
| **freshness** | `durable` |
| **review_after** | `P30D` |
| **trace_id** | `TRACE-20260321-001` |
| **updated_at** | 2026-03-21T08:10:00Z |

## Links

**related_tasks**：

- `TASK-20260321-001`

**related_paths**：

- `frontend/src/components/ui/Button.vue`
- `frontend/src/components/layout/AppLayout.vue`

**source**：`task:TASK-20260321-001`

## Summary

Button 组件第一版必须保持最小契约稳定：支持 `primary` / `secondary` 两种变体、支持 `disabled`、支持键盘触发，并在主布局中保留一个演示用例。

## Details

- 在后续任务显式批准前，不应新增额外视觉变体
- 样式应继续遵循主题类名，不引入内联魔法色值
- Integration 复核时应沿用本对象中的最小契约判断是否回归
