# ADS Knowledge Pack — TASK-20260321-001

- task_id: TASK-20260321-001
- owner_role: Frontend
- trace_id: TRACE-20260321-001

## Acceptance Snapshot
- 存在 `Button.vue`，暴露 `variant`（至少 `primary` / `secondary`）与 `disabled`
- 使用 Tailwind，无内联魔法色值（使用主题类名）
- 键盘可聚焦，Enter/Space 可触发 click
- `AppLayout.vue`（或等价布局）中有一处 `<Button>` 示例
- `npm run lint` 无新增错误
- `npm run build` 通过

## Related Paths
- frontend/src/components/ui/
- docs/03-development/coding-standards.md

## Handoff Status
实现已完成；本地已跑 lint/build。请 Integration 复核并合并。

## Memory Objects
- MEM-20260321-001 (decision) — Button 组件最小契约
  owner: Architect, scope: project, updated_at: 2026-03-21T08:10:00Z, review_after: P30D
  summary: Button 组件第一版必须保持最小契约稳定：支持 `primary` / `secondary` 两种变体、支持 `disabled`、支持键盘触发，并在主布局中保留一个演示用例。
  related_paths: frontend/src/components/ui/Button.vue, frontend/src/components/layout/AppLayout.vue

## Source Files
- examples/case-task-button.md
- examples/case-handoff-button.md
- examples/case-memory-button-contract.md
