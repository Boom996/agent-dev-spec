# ADS Handoff — `TASK-20260321-001`

## Metadata

| 字段 | 值 |
|------|-----|
| **From** | Frontend @ Cursor |
| **To** | Integration |
| **task_id** | TASK-20260321-001 |
| **Priority** | High |
| **Timestamp** | 2026-03-21T14:30:00Z |
| **trace_id** | TRACE-20260321-001 |
| **updated_at** | 2026-03-21T14:30:00Z |
| **stale_after** | `P2D` |

## Context

**当前状态**：实现已完成；本地已跑 lint/build。请 Integration 复核并合并。

**相关路径**：

| 路径 | 内容说明 |
|------|----------|
| `frontend/src/components/ui/Button.vue` | 新增按钮组件，含 variant/disabled |
| `frontend/src/components/layout/AppLayout.vue` | 增加一处示例引用 |

**依赖**：无  
**约束**：未改动 `frontend/src/stores/**`

## Memory refs（可选）

- `examples/case-memory-button-contract.md` — Integration 复核时应沿用的共享事实

## Deliverable request

**需要什么**：合并到主分支前确认验收标准全部满足，并更新 `completed.md`。

**验收标准**（可勾选）：

- [x] Button 组件与变体
- [x] 无障碍与键盘
- [x] 布局示例
- [x] lint / build 通过

**参考资料**：`examples/case-task-button.md`

## Evidence expectation

**必须提供的证明**：lint + build 输出  
**已附证据**：

| evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
|---------------|-------------|-------------|--------|----------------|---------------|
| `lint` | Frontend @ Cursor | 2026-03-21T14:10:00Z | pass | `artifacts/lint.txt` | pending |
| `build` | Frontend @ Cursor | 2026-03-21T14:18:00Z | pass | `artifacts/build.txt` | pending |

**附加说明**：

- `npm run lint`：0 errors（节选见 PR 描述）
- `npm run build`：success（节选见 PR 描述）
- PR：`#42`（虚构）

## Approval

**approval_owner**：Integration  
**approval_status**：`pending`

## Handoff to next

**下一棒**：Integration  
**建议下一动作**：checkout 分支 `feat/button-001`，跑标准验证命令，PASS 后合并
