# Spec — `<spec_id>`

> Layer 5 Spec Library 文档。描述系统**当前是什么**，不是**应该是什么**。
> 保存为 `.ai/specs/<spec-id>.md`。每次功能上线后必须更新。

---
spec_id: capability-name
version: 1.0.0
status: active          # active / deprecated / draft
owned_by: architect     # 角色，不绑定具体 Agent
related_changes:
  - change-YYYYMMDD-001
related_tasks:
  - TASK-YYYYMMDD-001
updated_at: YYYY-MM-DD
stale_after: YYYY-MM-DD  # 绝对日期，通常 6 个月后
---

## 能力概述

（1-2 段，描述该能力当前的实现状态）

## 接口 / 边界

（当前暴露的接口、路径、协议约定）

## 已知限制

（已知的技术债务、边界情况、非目标）

## 变更历史

| 变更 | 说明 |
|------|------|
| `change-YYYYMMDD-001` | 初始版本 |
