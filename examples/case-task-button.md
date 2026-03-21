# 任务：新增 Button 组件并挂到主布局

## 元数据

| 字段 | 值 |
|------|-----|
| **task_id** | `TASK-20260321-001` |
| **owner_role** | Frontend |
| **owner** | session-cursor-fe-01 |
| **priority** | High |
| **deps** | `[]` |
| **handoff_to** | Integration |
| **team_pattern_id** | `frontend-backend-integration` |
| **approval_owner** | Integration |
| **allowed_agents** | `[cursor-agent, codex-cli]` |
| **trace_id** | `TRACE-20260321-001` |
| **updated_at** | 2026-03-21T09:00:00Z |

## 单写者范围

- **locked_paths**：
  - `frontend/src/components/ui/Button.vue` — 新建组件
  - `frontend/src/components/layout/AppLayout.vue` — 插入示例引用（若文件不存在则仅创建 Button）
- **forbidden_paths**：
  - `frontend/src/stores/**` — 本任务不改状态管理

## 共享改动升级（可选）

- 若需改动共享类型或主题 token，需新建 shared-change-request
- 当前任务：无

## 背景与目标

设计系统需要首个可复用按钮；本任务交付可访问、可聚焦的默认变体，并在主布局中展示一处用法以便联调样式。

## 验收标准（可勾选）

- [ ] 存在 `Button.vue`，暴露 `variant`（至少 `primary` / `secondary`）与 `disabled`
- [ ] 使用 Tailwind，无内联魔法色值（使用主题类名）
- [ ] 键盘可聚焦，Enter/Space 可触发 click
- [ ] `AppLayout.vue`（或等价布局）中有一处 `<Button>` 示例
- [ ] `npm run lint` 无新增错误
- [ ] `npm run build` 通过

## 相关路径

| 路径 | 说明 |
|------|------|
| `frontend/src/components/ui/` | 目标组件目录 |
| `docs/03-development/coding-standards.md` | 样式与组件约定 |

## Memory refs（可选）

- `examples/case-memory-button-contract.md` — 记录按钮组件的共享事实和约束

## 证据期望（完成时必须附上）

- `npm run lint` 与 `npm run build` 终端输出节选（成功）
- 如有视觉验收：附一张本地截图路径说明

## Freshness

- **stale_after**（可选）：`P2D`
- **最后更新时间说明**：补充 trace、批准人和 Agent 参与范围

---

**状态**：`in-progress`
