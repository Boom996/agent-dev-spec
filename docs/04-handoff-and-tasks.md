# 任务、交接与 CLI 上下文包

## 任务文件放哪里

推荐：

- `.ai/tasks/backlog.md` / `in-progress.md` / `completed.md`  
  或每条任务独立：`.ai/tasks/active/<task-id>.md`

**关键**：任务文件必须包含 [01-principles.md](01-principles.md) 中的契约字段。

建议补充最小 freshness / trace 字段：

- `trace_id`
- `updated_at`
- `approval_owner`
- `allowed_agents`
- `team_pattern_id`（若任务遵循标准 team pattern）

## 交接文件放哪里

推荐：

```
.ai/handoffs/<task-id>.md
```

- **谁写**：主责执行者在切换工具或移交下一棒之前写。
- **谁读**：下一棒会话的第一条上下文来源之一（与 `README_AGENT` 首读链配合）。

与其配套的常见落盘路径还包括：

- `.ai/requests/<request-id>.md`：共享改动升级请求
- `.ai/qa/<task-id>-pass.md` / `.ai/qa/<task-id>-fail.md`：QA 或 Integration 结论

## Handoff Envelope

正文结构见 **`templates/handoff.md`**。务必包含：

- 相关路径列表（每条附一句话说明）
- 可勾选验收标准
- 明确 Evidence expectation
- 结构化 evidence 表格
- `trace_id`、`updated_at`、`stale_after`

## CLI 一键上下文包（Codex 等）

无状态 CLI **无法**依赖长会话。建议从任务生成 **≤120 行** 的「上下文包」，包含：

1. 任务 ID + 主责 + `locked_paths`
2. `acceptance_criteria` 全文
3. `related_paths` 与禁止修改路径
4. 标准验证命令（来自 `.agent/identity.json` 或项目文档）
5. 上一版 handoff 的链接或摘要

可将该包保存为 `.ai/handoffs/<task-id>-context.txt` 或由脚本生成，供粘贴进 CLI。

本仓库提供示例脚本：

- `scripts/build_context_pack.py <task.md> --handoff <handoff.md> --output .ai/handoffs/<task-id>-context.txt`
- `scripts/ads_health_report.py` 扫描缺 handoff、缺 evidence、长期未更新任务

说明：

- `build_context_pack.py` 默认从 `.agent/identity.json`（或示例 identity）读取标准验证命令
- 若提供 `--handoff`，上下文包会额外带上 handoff 状态与 `Memory refs`

## Memory refs（最小原型）

当任务或 handoff 依赖跨会话共享事实时，可在文档中增加：

- `## Memory refs（可选）`

推荐引用：

- `.ai/memory/*.md`
- 或示例阶段的 `examples/case-memory-*.md`

本仓库提供最小知识组装脚本：

- `scripts/build_knowledge_pack.py <task.md> --handoff <handoff.md>`
- 可对照 `examples/case-knowledge-pack.md` 查看示例输出

当前约定是：

- `memory-object`：共享事实层
- `knowledge-pack`：从 task、handoff、memory 组装出的只读消费产物

建议给 memory object 增加最小 freshness 字段：

- `freshness`
- `review_after`
- `updated_at`

本仓库提供最小 freshness 检查脚本：

- `scripts/check_stale_knowledge.py`

## Team Pattern

当任务符合标准多人协作模式时，可在 task 元数据中声明：

- `team_pattern_id`

本仓库当前内置首个 pattern：

- `.ai/patterns/frontend-backend-integration.md`

也可用于高风险评审场景：

- `.ai/patterns/human-agent-review.md`

建议让 validator 检查 task 中声明的 pattern 是否存在，并据此逐步增强 handoff / evidence 约束。

## 共享文件升级路径

当任务需要修改共享 schema、公共类型、配置文件等超出当前 `locked_paths` 的内容时：

- 不建议直接越过单写者原则
- 建议使用 `templates/shared-change-request.md` 生成共享改动请求
- 在 task 与 handoff 中引用该请求文件路径

这样可以把“必须跨任务改动”的理由和批准链显式落盘。

## 与编排工具（如 Golutra）的关系

编排工具负责**状态与指派**；ADS 负责**文件契约**。建议：

- 看板上的任务卡片链接到 `.ai/tasks/...` 或 `task-id`
- 完成条件包含：**handoff 文件存在 + 证据已填**

上一篇：[03-tools-and-mcp.md](03-tools-and-mcp.md) · 下一篇：[05-multi-client-and-mesh.md](05-multi-client-and-mesh.md)
