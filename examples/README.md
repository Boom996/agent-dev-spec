# ADS 完整模版案例（演练）

本目录提供**一次虚构但完整**的小迭代，演示 **Agent 开发规范（ADS）** 从任务到交接、共享改动、记忆对象、QA、CLI / knowledge pack 的用法。可与 `docs/00-overview.md` 与 `docs/06-evolution.md` 对照阅读。

## 场景

**目标**：为示例前端项目新增 `Button` 组件，并补一条后端审计日志契约（虚构路径）。

**参与**：Frontend（Cursor）、Backend（Claude Code）、Architect（审查）、Integration（合并与跑 build）。

## 文件列表

| 文件 | 说明 |
|------|------|
| [case-identity.json](case-identity.json) | 填好的 `identity.json` 示例 |
| [case-task-button.md](case-task-button.md) | 前端任务契约 |
| [case-task-audit-log.md](case-task-audit-log.md) | 后端任务契约 |
| [case-shared-change-request.md](case-shared-change-request.md) | 共享文件升级请求 |
| [case-shared-change-request-rejected.md](case-shared-change-request-rejected.md) | 被拒绝的共享改动请求示例 |
| [case-memory-button-contract.md](case-memory-button-contract.md) | 最小共享记忆对象 |
| [case-handoff-button.md](case-handoff-button.md) | Frontend → Integration 交接信封 |
| [case-handoff-audit-log.md](case-handoff-audit-log.md) | Backend → Integration 交接信封 |
| [case-qa-pass.md](case-qa-pass.md) | QA / Integration 通过结论 |
| [case-qa-fail.md](case-qa-fail.md) | QA / Integration 驳回结论 |
| [case-cli-context.txt](case-cli-context.txt) | 供 Codex CLI 粘贴的上下文包 |
| [case-knowledge-pack.md](case-knowledge-pack.md) | 由 task / handoff / memory 派生出的知识消费包 |

## 建议阅读顺序

1. `case-task-button.md` 与 `case-task-audit-log.md` — 多角色任务如何写全契约字段  
2. `case-shared-change-request.md` 与 `case-shared-change-request-rejected.md` — 共享改动如何升级，以及何时应该拒绝扩 scope  
3. `case-memory-button-contract.md` — 共享记忆如何作为 task / handoff 的事实层  
4. `case-handoff-button.md` 与 `case-handoff-audit-log.md` — 交接如何防丢上下文  
5. `case-cli-context.txt` — 无状态 CLI 如何吃同一套信息  
6. `case-knowledge-pack.md` — 同一批输入如何派生为只读知识消费包  
7. `case-qa-pass.md` 与 `case-qa-fail.md` — 证据如何挂钩验收标准，以及失败时如何回写修复指令  

将上述流程映射到你自己的目录名与命令即可落地。
