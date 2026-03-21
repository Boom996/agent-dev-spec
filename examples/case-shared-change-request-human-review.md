# Shared Change Request — `SCR-20260321-003`

## Metadata

| 字段 | 值 |
|------|-----|
| **request_id** | `SCR-20260321-003` |
| **task_id** | `TASK-20260321-003` |
| **requested_by** | AgentImplementer @ Codex |
| **approval_owner** | HumanOwner |
| **trace_id** | `TRACE-20260321-003` |
| **updated_at** | 2026-03-21T17:20:00Z |

## Requested change

**目标文件 / 目录**：

- `tools/toolset.json.example` — 为高风险工具写入人工审批说明
- `docs/03-tools-and-mcp.md` — 补充 high-risk tool 的治理建议

**为什么不能留在当前 locked_paths 内解决**：

本次改动会影响项目对高风险工具的通用治理口径，不只是单一任务的局部实现，需要显式获得 HumanOwner 批准后才能作为共享协议落盘。

**拟议改动**：

- 在 `shared_release_gate` 描述中写明“变更前需 HumanOwner review”
- 在工具文档中增加 `human-agent-review` 的配套建议

## Impact

**可能影响的任务**：

- `TASK-20260321-003`
- 后续所有引用 `shared_release_gate` 的集成与发布任务

**风险说明**：

- 若审批规则表述过重，会让 ADS 偏向重治理
- 若表述过轻，高风险工具仍可能被 Agent 直接调用而绕过人工审核

## Decision

**结论**：`approved`

**批准备注**：

只增加最小审批说明，不引入新的工具 schema 字段，继续保持 ADS 轻量。

**后续动作**：

- AgentImplementer 更新 toolset 示例和工具文档
- Reviewer 复核文案是否清晰，再交由 Integration 做最终收口
