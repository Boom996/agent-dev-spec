# 任务：为 shared_release_gate 增补人工审批说明

## 元数据

| 字段 | 值 |
|------|-----|
| **task_id** | `TASK-20260321-003` |
| **owner_role** | AgentImplementer |
| **owner** | session-codex-risk-01 |
| **priority** | High |
| **deps** | `[]` |
| **handoff_to** | Reviewer |
| **team_pattern_id** | `human-agent-review` |
| **approval_owner** | HumanOwner |
| **allowed_agents** | `[codex-cli, reviewer-human]` |
| **trace_id** | `TRACE-20260321-003` |
| **updated_at** | 2026-03-21T17:00:00Z |

## 单写者范围

- **locked_paths**（本任务周期内仅主责可改）：
  - `tools/toolset.json.example` — 为高风险工具条目补充人工审批说明
  - `docs/03-tools-and-mcp.md` — 说明高风险工具应搭配人工评审模式
- **forbidden_paths**（禁止改动）：
  - `scripts/**` — 本任务只改协议与示例，不改运行脚本

## 共享改动升级（可选）

- 如需修改跨任务共享文件，请附上 `shared-change-request` 链接：
  - `examples/case-shared-change-request-human-review.md`
- 若无共享改动，写 `无`

## 背景与目标

`shared_release_gate` 属于高风险共享工具，占位示例虽然已经标记了 `risk_level=high`，但还没有把“必须经 HumanOwner 审批后才能进入集成”写成清晰约束。
本任务把这条规则同时写入 toolset 示例和工具文档，形成可被人和 Agent 同时理解的最小治理说明。

## 验收标准（可勾选）

- [ ] `shared_release_gate` 条目明确包含人工审批说明
- [ ] 工具文档说明高风险工具建议搭配 `human-agent-review`
- [ ] shared-change-request 已由 `HumanOwner` 明确批准
- [ ] `python3 scripts/validate_ads.py` 通过
- [ ] `python3 scripts/ads_health_report.py` 可输出 request / qa 视角

## 相关路径

| 路径 | 说明 |
|------|------|
| `tools/toolset.json.example` | 工具注册示例 |
| `docs/03-tools-and-mcp.md` | 工具治理说明 |
| `.ai/patterns/human-agent-review.md` | 协作模式定义 |

## Memory refs（可选）

- `examples/case-memory-release-gate-risk.md` — 记录高风险工具的共享治理原则

## 证据期望（完成时必须附上）

- `python3 scripts/validate_ads.py` 输出
- `python3 scripts/ads_health_report.py` 输出
- HumanOwner 的批准结论

## Freshness

- **stale_after**（可选）：`P3D`
- **最后更新时间说明**：补 high-risk tool 的人工审批说明与评审链路

---

**状态**：`review`
