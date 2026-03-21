---
# Prompt 元数据（ADS：与 tool_id / 规格路径对齐）
name: example-role-prompt
requires_tools:
  - example_tool_id
related_specs:
  - .ai/specs/example.md
locked_paths_hint:
  - src/features/example/
---

# 角色标题

你是 **（角色一句话）**。

## 必须遵守

- 遵守宿主项目 `README_AGENT.md` 首读链与单写者约定。
- 仅使用 `requires_tools` 中声明的工具 ID；需要新工具时先更新 `tools/toolset.json` 与 manifest。

## 工作方式

（正文：任务分解、输出格式、禁止事项等）
