---
spec_id: caching-capability
version: 0.1.0
status: draft
owned_by: architect
related_changes: []
related_tasks: []
updated_at: 2026-03-22
stale_after: 2026-06-22
---

# Caching 能力（当前系统实际状态）

## 能力概述

当前使用进程内 Map 实现内存缓存，仅支持单实例部署。

## 接口 / 边界

- 内部 API，不对外暴露
- `cache.get(key)` / `cache.set(key, value, ttl)`

## 已知限制

- 不支持水平扩展（多实例间缓存不共享）
- 进程重启后缓存清空
- 计划迁移到 Redis（见 INV-20260322-001）

## 变更历史

| 变更 | 说明 |
|------|------|
| — | 初始草稿，待 Redis 迁移后正式发布 |
