# Agent Development Specification

ADS 是一套面向真实开发项目的 **Agent 工程协同规范与落地工具包**。它解决的不是“如何写一个提示词”，而是当多人类开发者、多个 Agent、多个客户端同时参与项目时，如何用一套 repo-native 的方式把 **任务、交接、证据、工具注册、共享记忆、最小治理** 固化到代码仓库里。

它适合这些团队：

- 已经在用 Codex、Claude Code、Cursor、OpenCode 或自研 Agent，但协作过程仍然主要依赖聊天历史
- 希望把 Agent 能力接入现有业务项目，而不是另建一套平台
- 希望跨客户端复用同一套工具注册、任务协议和 handoff 机制

## ADS 解决什么问题

典型失败模式包括：

- 会话一断，上下文就断，后续 Agent 只能从头猜
- 多个 Agent 同时改同一批文件，缺少边界，返工和冲突频发
- “完成”只是口头完成，没有 evidence、没有 QA、没有回溯依据
- 能力只藏在某个客户端配置里，换一个工具就失效

ADS 把这些问题收敛为一套简单但可执行的资产：

- `README_AGENT.md` 作为仓库级自举入口
- `.ai/` 作为协作工作区
- `.agent/` 作为工程元数据与规范镜像
- `tools/toolset.json` + `skills/*/manifest.json` 作为统一工具注册层
- task / handoff / request / qa / memory / spec 作为标准协议面
- doctor / resume / handoff draft / evidence capture / MCP server 作为自动化执行面
- `duration_ms` / `cost_usd` / `retry_count` 作为可选 evidence telemetry 层

## 你能直接获得什么

- 一个可以植入任何项目的 ADS 骨架初始化器：[`scripts/ads_init.py`](scripts/ads_init.py)
- 一个面向存量项目的 ADS 自动接入器：`scripts/ads_adopt.py`，支持分析、自动写入、导出 markdown/json 接入报告
- 一套接入与一致性检查能力：[`scripts/ads_doctor.py`](scripts/ads_doctor.py)、[`scripts/validate_ads.py`](scripts/validate_ads.py)
- 一个面向人和 Agent 的首读摘要器：`scripts/ads_explain.py`
- 一个本地网页状态面板：`scripts/ads_dashboard.py`
- 一套让跨会话续做更稳定的辅助脚本：`ads_resume`、`ads_handoff_draft`、`ads_evidence_capture`
- 一套可渐进启用的 evidence observability 能力：成本、耗时、重试次数
- 一套正式的 blocked / needs-context 升级流程：`ads_escalation_draft` + `.ai/escalations/`
- 一套可移植的 skill 体系：task decomposition、handoff writing、blocked triage、spec sync、integration review、innovation capture
- 一套面向多客户端的接入思路：Claude Code / Codex CLI / Cursor / OpenCode

## 10 分钟接入路径

1. 如果是新项目或干净仓库，执行 `python3 scripts/ads_init.py /path/to/your-project`。
2. 如果是已有协作资产的存量项目，先执行 `python3 scripts/ads_adopt.py /path/to/your-project` 分析；如需保留接入报告，可追加 `--report-file` / `--json-file`；确认后再用 `--apply` 自动写入 ADS 骨架。
   完成后会自动生成项目级首读摘要：`.agent/docs/guides/project-brief.md`
3. 让所有参与协作的人先阅读宿主仓库根部的 [`README_AGENT.md`](README_AGENT.md)。
4. 修改宿主仓库的 `.agent/identity.json`、`.agent/constitution.md`、`.ai/START_HERE.md`。
5. 用一个真实任务跑通 task -> evidence -> handoff -> QA。
6. 在宿主仓库先执行 `python3 scripts/ads_explain.py`，确认项目使命、协作状态与首读顺序。
7. 如需本地可视化状态面板，执行 `python3 scripts/ads_dashboard.py`。
8. 再执行 `python3 scripts/ads_doctor.py` 和 `python3 scripts/validate_ads.py`。
9. 按需接入 [`docs/guides/client-adapters/README.md`](docs/guides/client-adapters/README.md) 中的客户端适配说明。

更细的落地路径见 [`docs/guides/adoption-playbook.md`](docs/guides/adoption-playbook.md)。

## 这套仓库包含什么

```
agent-dev-spec/
├── README.md
├── README_AGENT.md
├── docs/
├── templates/
├── .agent/
├── .ai/
├── tools/
├── skills/
├── scripts/
└── examples/
```

关键部分：

- [`docs/`](docs/)：协议说明、演进背景、客户端适配文档
- [`templates/`](templates/)：task、handoff、request、QA、memory 模板
- [`scripts/`](scripts/)：初始化、校验、续做、handoff 草稿、证据捕获、MCP 服务
- [`skills/`](skills/)：可复用的 operational skills
- [`examples/`](examples/)：完整案例链路

## 推荐阅读顺序

- [`docs/00-overview.md`](docs/00-overview.md)
- [`docs/01-principles.md`](docs/01-principles.md)
- [`docs/04-handoff-and-tasks.md`](docs/04-handoff-and-tasks.md)
- [`docs/08-harness-landscape-and-recovery.md`](docs/08-harness-landscape-and-recovery.md)
- [`docs/guides/adoption-playbook.md`](docs/guides/adoption-playbook.md)
- [`docs/guides/client-adapters/README.md`](docs/guides/client-adapters/README.md)
- [`examples/README.md`](examples/README.md)

## 产品化能力现状

当前 ADS 已完成并稳定提供：

- 协议层：task / handoff / request / qa / memory / spec / toolset 校验
- 自动化层：doctor、resume、handoff draft、escalation draft、evidence capture、tool sync、MCP server
- 入门层：`ads_explain` 首读摘要
- 可视化层：`ads_dashboard` 本地网页面板（概览页 + 统一详情页）
- 观测层：evidence 主表 + telemetry 子表（cost / latency / retry）
- Skill 层：task-decomposer、handoff-writer、blocked-triager、spec-syncer、integration-reviewer、innovation-capture
- 适配层：Claude Code、Codex CLI、Cursor、OpenCode
- 示例层：端到端案例、上下文包、知识包、共享改动、QA 结论
- 研究层：外部 harness landscape 研究与 roadmap 回写

## 从这里开始

- 接入现有项目：[`docs/guides/adoption-playbook.md`](docs/guides/adoption-playbook.md)
- 查看所有文档：[`docs/README.md`](docs/README.md)
- 查看客户端适配：[`docs/guides/client-adapters/README.md`](docs/guides/client-adapters/README.md)
- 查看端到端案例：[`examples/README.md`](examples/README.md)

## 许可与商业授权

本仓库采用的是“公开源码、禁止商业使用”的发布方式，方便开发者学习、研究、评估和非商业实践；它**不是** OSI 定义下的开放源代码许可证项目。

- 代码默认适用 [`LICENSE`](LICENSE) 中声明的 `PolyForm Noncommercial 1.0.0`
- 商业使用、商业集成、商业分发、商业培训或基于本仓库提供收费服务，需要单独取得书面商业授权
- 商业授权联系：`17764546751@163.com`
- 具体说明见 [`COMMERCIAL_LICENSE.md`](COMMERCIAL_LICENSE.md)
