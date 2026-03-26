# ADS 文档索引

**Agent 开发规范（Agent Development Specification, ADS）** — 给人读的说明均在本目录。

| 序号 | 文档 | 说明 |
|------|------|------|
| 00 | [00-overview.md](00-overview.md) | 背景、目标、四层模型与信封 |
| 01 | [01-principles.md](01-principles.md) | 单写者、任务契约、证据与闸口 |
| 02 | [02-uaw-mapping.md](02-uaw-mapping.md) | UAW 目录映射与复制到业务仓库 |
| 03 | [03-tools-and-mcp.md](03-tools-and-mcp.md) | MCP、manifest、toolset、校验 |
| 04 | [04-handoff-and-tasks.md](04-handoff-and-tasks.md) | 任务字段、handoff 路径、CLI 上下文包 |
| 05 | [05-multi-client-and-mesh.md](05-multi-client-and-mesh.md) | 多客户端适配与企业 Agent Mesh 附录 |
| 06 | [06-evolution.md](06-evolution.md) | 从模板骨架到协作控制面、最小治理、共享记忆的演进 |
| 07 | [07-iteration-log.md](07-iteration-log.md) | 已执行增强、验证结果与后续迭代建议 |
| 08 | [08-harness-landscape-and-recovery.md](08-harness-landscape-and-recovery.md) | ADS 在 harness stack 中的位置，以及 recovery / escalation 协议定位 |

阅读顺序：**00 → 01 → 04 → 06**（其余按需要查阅）。

## 落地指南

- [guides/adoption-playbook.md](guides/adoption-playbook.md)：把 ADS 接入现有项目的 10 分钟落地路径、常见错误与检查清单
- [guides/client-adapters/README.md](guides/client-adapters/README.md)：按客户端查看 Claude Code、Codex CLI、Cursor、OpenCode 的适配说明

## 研究与对标

- [research/README.md](research/README.md)：ADS 外部生态研究目录与节奏
- [research/2026-03-agent-harness-landscape.md](research/2026-03-agent-harness-landscape.md)：首份 ADS harness 生态观察与 roadmap 回写结论
