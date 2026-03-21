# Memory Object — `MEM-20260321-002`

## Metadata

| 字段 | 值 |
|------|-----|
| **memory_id** | `MEM-20260321-002` |
| **type** | `risk` |
| **title** | 高风险工具必须保留人工审批闸口 |
| **scope** | `project` |
| **owner** | HumanOwner |
| **status** | `active` |
| **freshness** | `durable` |
| **review_after** | `P30D` |
| **trace_id** | `TRACE-20260321-003` |
| **updated_at** | 2026-03-21T17:10:00Z |

## Links

**related_tasks**：

- `TASK-20260321-003`

**related_paths**：

- `tools/toolset.json.example`
- `docs/03-tools-and-mcp.md`

**source**：`task:TASK-20260321-003`

## Summary

对于 `risk_level=high` 的共享工具，ADS 要求至少保留一层人工审批或人工复核闸口。
这条规则优先通过 `human-agent-review`、`shared-change-request` 和文档说明来表达，而不是立即扩展为重型 registry 或复杂权限系统。

## Details

当前最小做法是：

- 在 toolset 或相关文档中写清人工审批期望
- 在 task / handoff / QA 中落下批准与复核证据
- 由 HumanOwner 或等价角色保留最终确认权
