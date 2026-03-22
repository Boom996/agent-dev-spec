# [项目/公司名] Constitution

> ADS Layer 6 — 最高层治理文档。变更频率极低，每次变更需记录原因和审批人。
> 保存为 `.agent/constitution.md`。

## Mission

（一句话：这个项目/公司是干什么的，存在的意义是什么）

## Non-Negotiable Principles

- （技术层面不可妥协的原则，如"无破坏性 API 变更"）
- （产品层面，如"用户数据不出域"）
- （协作层面，如"所有 task 必须有 evidence 才能标记完成"）

## Tech Stack Principles

- 主语言/框架：
- 禁止引入的依赖类型：
- 测试要求：

## Role Definitions

- **PM**：负责 change proposal 的提出和优先级排序
- **Architect**：负责 design.md 和 Spec Library 维护
- **Developer**：负责 task 执行和 handoff 产出
- **Reviewer**：负责 spec compliance + code quality 两阶段验证
- （可扩展：QA、Integration、HumanOwner 等）

## Agent Governance

- 哪些 Agent 角色的操作需要人类审批：
- 哪些路径任何 Agent 都不能修改（全局 forbidden_paths）：
- Agent 的最大自治范围说明：

## Approval Hierarchy

- Constitution 变更：需要最高级别人类审批，记录审批人和变更原因
- Spec（`.ai/specs/`）变更：需要 Architect 角色审批
- Change Proposal design.md：需要 `human_checkpoint: design_approved` 才能进入执行
- Task 执行：按各 task 的 `allowed_agents` 字段约束

## Budget Policy（可选）

- 默认 token 预算策略：
- 超出预算的处理方式：
