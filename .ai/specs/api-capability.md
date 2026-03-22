---
spec_id: api-capability
version: 1.0.0
status: active
owned_by: architect
related_changes:
  - change-20260322-001
related_tasks:
  - TASK-20260322-002
updated_at: 2026-03-22
stale_after: 2026-09-22
---

# API 能力（当前系统实际状态）

## 能力概述

RESTful API 层，基于 Express.js，提供业务能力的 HTTP 接口。

## 接口 / 边界

- 基础路径：`/api/v1/`
- 认证：Bearer token（见 auth-capability）
- 响应格式：`{ data: T, error?: string }`

## 已知限制

- 暂无 GraphQL 支持
- Rate limiting 尚未实现

## 变更历史

| 变更 | 说明 |
|------|------|
| `change-20260322-001` | 增加 /auth/* 路由描述 |
