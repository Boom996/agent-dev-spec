# ADS Demo Project Constitution

> ADS Layer 6 示例文件（examples/case-constitution.md）。

## Mission

构建最完整的 ADS 演示项目，展示六层架构的完整协作流程。

## Non-Negotiable Principles

- 所有 task 必须有 evidence 才能标记 DONE
- 不允许在没有 handoff 的情况下跨会话继续工作
- 破坏性 API 变更必须创建 Change Proposal

## Tech Stack Principles

- 主语言：Python 3.11+
- 测试框架：pytest
- 文档格式：Markdown + YAML frontmatter

## Role Definitions

- **PM**：负责 change proposal 的提出和优先级排序
- **Architect**：负责 design.md 和 Spec Library 维护
- **Developer**：负责 task 执行和 handoff 产出
- **Reviewer**：负责 spec compliance + code quality 两阶段验证

## Agent Governance

- Constitution 变更：需要 HumanOwner 审批并记录原因
- 任何 Agent 不得修改 `.agent/` 目录下文件（仅 HumanOwner 可改）
- Developer Agent 最大自治范围：单个 task 的 locked_paths 内

## Approval Hierarchy

- Constitution 变更：HumanOwner 唯一审批人
- Spec 变更：Architect 角色审批
- Change Proposal design.md：human_checkpoint design_approved
- Task 执行：按各 task 的 allowed_agents 字段约束
