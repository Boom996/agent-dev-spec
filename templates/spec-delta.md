# Spec Delta — `<change_id>`

> 记录本次变更影响的 Spec 文档，确保 spec 与实现同步。保存为 `.ai/changes/<change-id>/spec-delta.md`。

## 本次变更影响的 Spec 文档

| Spec 文件 | 变更类型 | 变更摘要 |
|----------|---------|---------|
| `.ai/specs/...` | 新增 / 修改 / 废弃 | （一句话） |

## 更新责任

Developer 角色在将 `handoff_status` 设置为 `DONE` 或 `DONE_WITH_CONCERNS` 之前，
必须完成上述 spec 文档的更新，并在 handoff evidence_items 的 `spec_compliance`
阶段的 notes 中注明"spec-delta.md 引用的 spec 文档已更新"。

## 若无 Spec 影响

写 `无` — 明确声明本次变更不影响任何 Spec 文档。
