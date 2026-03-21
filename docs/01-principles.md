# ADS 原则与纪律

## 1. 单写者（Single Writer）

每个任务周期内，对**约定的一组路径**仅一名主责执行者（人或 Agent 会话）。

- **他人**：评审、评论、或另开子任务；不直接改主责路径，除非明确接管并更新任务元数据。
- **实操**：在任务中声明 `locked_paths` 或等价字段；或使用独立分支 / worktree，在任务描述中写清分支名。

## 2. 任务契约（Task Contract）

任务描述**不得**只有一句话功能名；至少包含：

- `id`：稳定标识（便于 handoff 文件名与引用）
- `owner_role` 或 `owner`：主责
- `deps`：依赖的其他任务 ID（可为空）
- `acceptance_criteria[]`：可勾选、可验证
- `related_paths[]`：相关文件或目录，附一句说明
- `handoff_to`：下一棒角色（若适用）
- `evidence_expectation`：完成时需要贴出的证明（命令、报告路径等）

模板见 `templates/task.md` 与 [04-handoff-and-tasks.md](04-handoff-and-tasks.md)。

## 3. 交接必须落盘

跨会话、跨工具（Cursor ↔ Claude Code ↔ Codex CLI）继续工作时：

- 必须存在 **`.ai/handoffs/<task-id>.md`**（路径可按项目调整，但须在 `README_AGENT` 中写明）。
- 内容遵循 **Handoff Envelope**，见 `templates/handoff.md`。

禁止仅依赖「上文聊天记录」作为唯一交接载体。

## 4. 证据与闸口（Integration）

标记任务完成前：

- 执行者在 handoff 或任务脚注中附上**证据**（与 `evidence_expectation` 一致）。
- **Integration**（或等价角色）负责：合并冲突处理、关键命令复跑、把摘要写入完成列表。

无证据的「完成」视为未完成。

## 5. 规格与事实分离（可选但推荐）

- **规格**：应该怎样实现（API、目录、约定）— 放在 `docs/` 或 `.ai/specs/`。
- **事实**：已确认的决策、用户偏好 — 可进长期记忆表或 `facts`（若宿主项目有记忆系统）。

Breaking change 必须反映到规格或迁移说明，不能只留在某次对话里。

上一篇：[00-overview.md](00-overview.md) · 下一篇：[02-uaw-mapping.md](02-uaw-mapping.md)
