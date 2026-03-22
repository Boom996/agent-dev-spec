# Innovation Brief — `INV-20260322-001`

> 示例：任务执行过程中发现的缓存优化机会。

## Metadata

| 字段 | 值 |
|------|-----|
| **innovation_id** | `INV-20260322-001` |
| **title** | 用 Redis 替代内存缓存以支持水平扩展 |
| **submitted_by** | `developer-agent` |
| **submitted_at** | `2026-03-22T10:00:00+08:00` |
| **context_task** | `TASK-20260322-001` |
| **context_change** | `change-20260322-001` |
| **status** | `promoted` |
| **urgency** | `low` |
| **impact_estimate** | `medium` |
| **triage_by** | `architect` |
| **triage_deadline** | `2026-03-29` |
| **promoted_to** | `change-20260322-002` |

## 想法摘要

当前服务使用进程内内存缓存（`Map<string, T>`），在单实例部署时工作正常。
但在水平扩展（多副本部署）时，各实例缓存独立，导致缓存命中率下降并出现数据不一致。
建议迁移到 Redis 作为共享缓存层，根本解决水平扩展问题。

## 触发背景

在执行 TASK-20260322-001（实现 JWT 令牌支持）的负载测试阶段，发现在双副本压测时
`/api/refresh-token` 接口约 40% 的请求因缓存不命中而触发数据库查询，响应时间 P99 超标。

## 提交者的初步判断

迁移成本中等（需要新增 Redis 基础设施 + 修改 3-4 个 service 文件），
收益明确（水平扩展支持 + 缓存一致性）。不阻断当前任务，建议下个 sprint 作为独立
change proposal 评估。已标记 urgency: low，不影响 TASK-20260322-001 的交付。
