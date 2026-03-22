# Agent Identity — `<agent_id>`

> Per-agent 身份文件。保存为 `.agent/agents/<agent-id>.md`。
> 来自 Clawith soul.md 设计，适配 ADS 协议层。

## Metadata

| 字段 | 值 |
|------|-----|
| **agent_id** | `agent-frontend-001` |
| **role** | （取值来自 constitution.md Role Definitions，如 Frontend / Backend / Architect） |
| **owner** | （人名或 Agent 标识） |
| **active_since** | ISO8601 |
| **updated_at** | ISO8601 |

## Capability Boundary

**可做**：

- （一条一条列出该 Agent 负责的能力范围）

**不可做**：

- （明确边界，避免越权）

## Allowed Agents / Clients

- `claude-code` / `cursor` / `codex-cli` / ... — 该角色允许使用的 AI 客户端

## Cross-Session Memory Summary

（跨会话的关键事实摘要，如：偏好的技术栈、历史决策、已知 gotcha）

- 无（新 Agent，尚无跨会话记忆）

## Notes

（其他补充，如临时约束、当前状态）
