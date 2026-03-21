# ADS Knowledge Pack — TASK-20260321-003

- task_id: TASK-20260321-003
- owner_role: AgentImplementer
- trace_id: TRACE-20260321-003

## Acceptance Snapshot
- `shared_release_gate` 条目明确包含人工审批说明
- 工具文档说明高风险工具建议搭配 `human-agent-review`
- shared-change-request 已由 `HumanOwner` 明确批准
- `python3 scripts/validate_ads.py` 通过
- `python3 scripts/ads_health_report.py` 可输出 request / qa 视角

## Related Paths
- tools/toolset.json.example
- docs/03-tools-and-mcp.md
- .ai/patterns/human-agent-review.md

## Handoff Status
高风险工具的人工审批说明已补齐，HumanOwner 已批准共享改动，等待 Integration 复核并记录最终 QA 结论。

## Memory Objects
- MEM-20260321-002 (risk) — 高风险工具必须保留人工审批闸口
  owner: HumanOwner, scope: project, updated_at: 2026-03-21T17:10:00Z, review_after: P30D
  summary: 对于 `risk_level=high` 的共享工具，ADS 要求至少保留一层人工审批或人工复核闸口。 这条规则优先通过 `human-agent-review`、`shared-change-request` 和文档说明来表达，而不是立即扩展为重型 registry 或复杂权限系统。
  related_paths: tools/toolset.json.example, docs/03-tools-and-mcp.md

## Source Files
- examples/case-task-human-review-release-gate.md
- examples/case-handoff-human-review-release-gate.md
- examples/case-memory-release-gate-risk.md
