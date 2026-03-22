# ADS Handoff — `<task_id>`

> Agent Development Specification（ADS）交接信封。保存为 `.ai/handoffs/<task_id>.md`。

## Metadata

| 字段 | 值 |
|------|-----|
| **From** | （角色 / 工具，如 Frontend @ Cursor） |
| **To** | （下一棒，如 Integration） |
| **task_id** | |
| **Priority** | |
| **Timestamp** | ISO8601 |
| **trace_id** | |
| **updated_at** | ISO8601 |
| **stale_after** | `P2D` / `P7D` / 团队自定义 |
| **handoff_status** | `DONE` \| `DONE_WITH_CONCERNS` \| `NEEDS_CONTEXT` \| `BLOCKED` \| `pending_resume` |
| **blocked_reason** | （仅 NEEDS_CONTEXT / BLOCKED 时填写，说明阻断原因或缺失信息） |
| **spec_update_status** | `not_started` \| `in_progress` \| `updated` \| `not_applicable` |
| **team_pattern_id** | （可选）关联的团队协作模式 |

## Context

**当前状态**：（已完成 / 进行中 + 百分比；关键决策一句话）

**相关路径**：

| 路径 | 内容说明 |
|------|----------|
| | |

**依赖**：其他 task_id 或外部依赖是否已满足  
**约束**：技术、时间、合规等

## Memory refs（可选）

- `path/to/memory-object.md` — 下一棒继续工作前应阅读的共享事实
- 若无，写 `无`

## Deliverable request

**需要什么**：下一棒要产出的具体结果  

**验收标准**（可勾选）：

- [ ]
- [ ]

**参考资料**：spec、设计稿、Issue 链接

## Evidence expectation

> **两阶段 Evidence 说明**（Phase 1 可选，Phase 3 后对声明 team_pattern_id 的任务强制）：
> 在 Evidence expectation 的已附证据表格中，`evidence_item` 列可用以下 stage 前缀标注：
> - `spec_compliance:` — spec 合规性验证（第一阶段）
> - `code_quality:` — 代码质量验证（第二阶段）
> - `sub_task_aggregation:` — orchestrated 模式子任务产物汇总

**必须提供的证明**：（命令、日志路径、测试报告、截图）

**已附证据**：（本任务主责已填）

| evidence_item | executed_by | executed_at | result | artifact_paths | review_status |
|---------------|-------------|-------------|--------|----------------|---------------|
| `lint` | | | pass / fail | | pending / reviewed |
| `build` | | | pass / fail | | pending / reviewed |

**附加说明**：

- （例如）`npm run build` 输出节选
- （例如）PR / commit SHA

## Approval

**approval_owner**：角色名或人名  
**approval_status**：`pending` | `approved` | `changes_requested`

## Handoff to next

**下一棒**：角色名  
**建议下一动作**：一句话
