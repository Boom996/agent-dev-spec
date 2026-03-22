# Change Proposal — `change-20260322-001`

> 示例变更提案：展示 ADS Layer 4 Change Proposal 对象的完整用法。

## Metadata

| 字段 | 值 |
|------|-----|
| **change_id** | `change-20260322-001` |
| **title** | 为用户认证功能实现 JWT 令牌支持 |
| **status** | `approved` |
| **proposed_by** | `architect` |
| **approval_owner** | `tech-lead` |
| **trace_id** | `TRACE-20260322-001` |
| **updated_at** | `2026-03-22T10:00:00+08:00` |

## What & Why

本次变更为用户认证系统增加 JWT（JSON Web Token）令牌支持，替换现有的 session-based 认证方案。
主要驱动因素是微服务架构下无状态认证的需求，以及前后端分离后跨域认证的复杂性。
JWT 支持后，移动端和第三方集成也可以使用统一的认证机制。

## Scope

**影响层级**：Layer 1-2（Task / Handoff）、Layer 4（Change Proposal）、Layer 5（Spec Library）

**影响路径**：

- `backend/src/auth/` — JWT 生成与校验逻辑
- `frontend/src/hooks/useAuth.ts` — 客户端认证 hook
- `.ai/specs/auth-capability.md` — 认证能力 spec（新增）

## Impact

**关联任务**：

- `TASK-20260322-001` — 实现 JWT 生成逻辑（Backend）
- `TASK-20260322-002` — 实现前端认证 hook（Frontend）

**风险说明**：

- 现有 session 数据在切换后失效，需要平滑迁移方案
- JWT secret 轮换机制需在 Phase 2 完善

**回滚方案**：

切换 feature flag `USE_JWT=false`，回退至 session 认证，无数据迁移成本。
