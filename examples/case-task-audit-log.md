# 任务：补后端审计日志契约

## 元数据

| 字段 | 值 |
|------|-----|
| **task_id** | `TASK-20260321-002` |
| **owner_role** | Backend |
| **owner** | session-claude-backend-01 |
| **priority** | High |
| **deps** | `["TASK-20260321-001"]` |
| **handoff_to** | Integration |
| **team_pattern_id** | `frontend-backend-integration` |
| **approval_owner** | Architect |
| **allowed_agents** | `[claude-code, codex-cli]` |
| **trace_id** | `TRACE-20260321-002` |
| **updated_at** | 2026-03-21T10:30:00Z |

## 单写者范围

- **locked_paths**（本任务周期内仅主责可改）：
  - `backend/src/audit/approval_log.ts` — 新增审计日志契约
  - `backend/src/api/approval.ts` — 接口返回审计字段
- **forbidden_paths**（禁止改动）：
  - `frontend/src/**` — 本任务不改前端渲染层

## 共享改动升级（可选）

- 如需修改跨任务共享文件，请附上 `shared-change-request` 链接：
  - `examples/case-shared-change-request.md`
- 若无共享改动，写 `无`

## 背景与目标

为了让 Integration 和后续审计链路都能追踪“审批事件是谁触发、何时记录”，本任务补齐后端最小审计日志契约，并在接口层透出必要字段。

## 验收标准（可勾选）

- [ ] 存在最小审计事件契约，包含 `actor_type`、`actor_id`、`timestamp`
- [ ] `approval.ts` 返回审计字段摘要
- [ ] 共享契约改动已通过 shared-change-request 批准
- [ ] `npm run test` 通过
- [ ] `npm run build` 通过

## 相关路径

| 路径 | 说明 |
|------|------|
| `backend/src/audit/` | 审计日志契约目录 |
| `backend/src/api/` | 审批 API 目录 |
| `shared/contracts/` | 共享契约目录（如需升级） |

## Memory refs（可选）

- `examples/case-memory-button-contract.md` — 前后端都应沿用的最小契约风格

## 证据期望（完成时必须附上）

- `npm run test` 与 `npm run build` 成功输出节选
- shared-change-request 批准结果

## Freshness

- **stale_after**（可选）：`P2D`
- **最后更新时间说明**：补后端审计日志任务与共享改动引用

---

**状态**：`review`
