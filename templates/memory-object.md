# Memory Object — `<memory_id>`

> 共享事实层最小对象。建议保存为 `.ai/memory/<memory_id>.md`。

## Metadata

| 字段 | 值 |
|------|-----|
| **memory_id** | `MEM-YYYYMMDD-001` |
| **type** | `decision` / `fact` / `risk` / `handoff-summary` / `integration-note` |
| **title** | 一句话标题 |
| **scope** | `task` / `team` / `project` |
| **owner** | 角色 / 人 / Agent |
| **status** | `active` / `archived` |
| **freshness** | `durable` / `operational` |
| **review_after** | `P7D` / `P30D` / 团队自定义 |
| **trace_id** | `TRACE-YYYYMMDD-001` |
| **updated_at** | ISO8601 |

## Links

**related_tasks**：

- `TASK-...`

**related_paths**：

- `path/to/file`

**source**：`task:TASK-...` / `handoff:TASK-...` / `manual`

## Summary

（2～4 句话说明这个 memory object 保存了什么共享事实）

## Details

（需要时补充细节）
