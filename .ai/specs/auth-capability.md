---
spec_id: auth-capability
version: 1.0.0
status: active
owned_by: architect
related_changes:
  - change-20260322-001
related_tasks:
  - TASK-20260322-001
updated_at: 2026-03-22
stale_after: 2026-09-22
---

# Auth 能力（当前系统实际状态）

## 能力概述

基于 JWT 的无状态身份验证能力。令牌有效期 24 小时，支持刷新令牌（refresh token）机制。

## 接口 / 边界

- `POST /auth/login` — 用户名密码登录，返回 access_token + refresh_token
- `POST /auth/refresh` — 使用 refresh_token 换取新的 access_token
- `POST /auth/logout` — 撤销 refresh_token

## 已知限制

- 暂不支持 OAuth2 第三方登录（Phase 3+ 引入）
- refresh_token 存储在内存缓存中，水平扩展时需迁移到 Redis

## 变更历史

| 变更 | 说明 |
|------|------|
| `change-20260322-001` | 初始版本，实现 JWT 令牌支持 |
