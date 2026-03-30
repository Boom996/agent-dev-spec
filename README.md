# Agent Development Specification

ADS 是一套面向真实开发项目的 **Agent 工程协同规范与落地工具包**。它解决的不是“如何写一个提示词”，而是当多人类开发者、多个 Agent、多个客户端同时参与项目时，如何用一套 repo-native 的方式把 **任务、交接、证据、工具注册、共享记忆、最小治理** 固化到代码仓库里。

它适合这些团队：

- 已经在用 Codex、Claude Code、Cursor、OpenCode 或自研 Agent，但协作过程仍然主要依赖聊天历史
- 希望把 Agent 能力接入现有业务项目，而不是另建一套平台
- 希望跨客户端复用同一套工具注册、任务协议和 handoff 机制

<!-- ADS:START -->
## ADS Agent Quick Start

> 如果你是第一次读到这个仓库的人类开发者或 Agent，请把本区块当成唯一入口。

1. 先读当前根 `README.md`，理解 ADS 的目标、接入方式和安全边界。
2. 如果你要把 ADS 接到另一个项目，优先在目标项目根目录执行 `python3 /path/to/agent-dev-spec/scripts/ads_self_install.py`。
3. 接入前先提醒作者提交并优先上传当前本地修改，再创建新的 git 分支做接入。
4. 接入后先读目标项目根 `README.md` 中的 `ADS Agent Quick Start`，再读 `.ai/START_HERE.md`、`.agent/constitution.md`、`.agent/docs/guides/project-brief.md`。
5. 接入完成后优先回看 `.agent/docs/guides/ads-install-report.md`，确认这次接入的结果和下一步动作。
6. 开始真实开发前，先跑 `python3 scripts/ads_explain.py`、`python3 scripts/ads_doctor.py`、`python3 scripts/validate_ads.py`，必要时再开 `python3 scripts/ads_dashboard.py`。

### Entry Docs

- `README.md`
- `docs/guides/adoption-playbook.md`
- `docs/guides/client-adapters/codex-cli.md`
- `docs/00-overview.md`
<!-- ADS:END -->

## ADS 解决什么问题

典型失败模式包括：

- 会话一断，上下文就断，后续 Agent 只能从头猜
- 多个 Agent 同时改同一批文件，缺少边界，返工和冲突频发
- “完成”只是口头完成，没有 evidence、没有 QA、没有回溯依据
- 能力只藏在某个客户端配置里，换一个工具就失效

ADS 把这些问题收敛为一套简单但可执行的资产：

- 根 `README.md` 作为唯一仓库级自举入口
- `.ai/` 作为协作工作区
- `.agent/` 作为工程元数据与规范镜像
- `tools/toolset.json` + `skills/*/manifest.json` 作为统一工具注册层
- task / handoff / request / qa / memory / spec 作为标准协议面
- doctor / resume / handoff draft / evidence capture / MCP server 作为自动化执行面
- `duration_ms` / `cost_usd` / `retry_count` 作为可选 evidence telemetry 层

## 你能直接获得什么

- 一个可以植入任何项目的 ADS 骨架初始化器：[`scripts/ads_init.py`](scripts/ads_init.py)
- 一个面向存量项目的 ADS 自动接入器：`scripts/ads_adopt.py`，支持先生成试用判断报告，再自动写入并输出 apply 后下一步
- 一个面向“当前仓库自接入”的安全高层入口：`scripts/ads_self_install.py`，默认先检查本地修改、自动拉新分支，再完成 apply 和 dashboard 打开
- 一套接入与一致性检查能力：[`scripts/ads_doctor.py`](scripts/ads_doctor.py)、[`scripts/validate_ads.py`](scripts/validate_ads.py)
- 一个面向人和 Agent 的首读摘要器：`scripts/ads_explain.py`
- 一个本地网页状态面板：`scripts/ads_dashboard.py`，同时提供项目首页、今日控制台、上手引导与任务/风险/健康详情
- 一套让跨会话续做更稳定的辅助脚本：`ads_resume`、`ads_handoff_draft`、`ads_evidence_capture`
- 一套可渐进启用的 evidence observability 能力：成本、耗时、重试次数
- 一套正式的 blocked / needs-context 升级流程：`ads_escalation_draft` + `.ai/escalations/`
- 一套可移植的 skill 体系：task decomposition、handoff writing、blocked triage、spec sync、integration review、innovation capture
- 一套面向多客户端的接入思路：Claude Code / Codex CLI / Cursor / OpenCode

## 10 分钟接入路径

如果你是“在另一个项目里工作的 Agent”，拿到了 ADS 的 git 链接，请先阅读这份根 `README.md`，然后在**目标项目根目录**执行：

```bash
python3 /path/to/agent-dev-spec/scripts/ads_self_install.py
```

这个入口会默认：

- 检查当前项目 git 工作区
- 发现未提交修改时先停下并提醒作者优先提交/上传
- 自动创建新的 ADS 接入分支
- 对已有成熟项目默认采用 `lean` 接入档位，只注入高频协作控制面
- 完成 adopt -> apply -> doctor -> validate
- 接入成功后启动并打开 ADS dashboard

1. 如果是新项目或干净仓库，执行 `python3 scripts/ads_init.py /path/to/your-project`。
2. 如果是已有协作资产的存量项目，先执行 `python3 scripts/ads_adopt.py /path/to/your-project` 获取试用判断报告；如需保留接入报告，可追加 `--report-file` / `--json-file`；确认后再用 `--apply` 自动写入 ADS 骨架。
   完成后会自动生成项目级首读摘要：`.agent/docs/guides/project-brief.md`
   默认 `--adoption-profile auto` 会对成熟项目选择 `lean`，只保留 `README.md`、`project-brief`、`ads-install-report`、`legacy-workspace-mapping`、`.ai/START_HERE.md` 这类高频文件，把 ADS 低频参考手册留在 ADS 源仓库。
   如果你明确希望在宿主仓库保留完整 ADS 参考文档镜像，再改用 `--adoption-profile full`。
3. 让所有参与协作的人先阅读宿主仓库根部的 `README.md`，确认其中的 `ADS Agent Quick Start` 区块。
4. 修改宿主仓库的 `.agent/identity.json`、`.agent/constitution.md`、`.ai/START_HERE.md`。
5. 用一个真实任务跑通 task -> evidence -> handoff -> QA。
6. 在宿主仓库先执行 `python3 scripts/ads_explain.py`，确认项目使命、协作状态与首读顺序。
7. 如需本地可视化状态面板，执行 `python3 scripts/ads_dashboard.py`。
8. 再执行 `python3 scripts/ads_doctor.py` 和 `python3 scripts/validate_ads.py`。
9. 按需接入 [`docs/guides/client-adapters/README.md`](docs/guides/client-adapters/README.md) 中的客户端适配说明。

更细的落地路径见 [`docs/guides/adoption-playbook.md`](docs/guides/adoption-playbook.md)。

## Lean Adoption

针对已有产品文档、计划流程和 handoff 体系都比较成熟的项目，ADS 现在默认优先以“最小协作控制面”接入，而不是再向宿主仓库注入整套 ADS 手册。

- `auto`：默认模式。成熟仓库优先走 `lean`，greenfield / protocol-first 仓库走 `full`
- `lean`：只把高频日常协作入口放进宿主仓库，低频 ADS 参考文档仍留在 ADS 源仓库
- `full`：把完整 `.agent/docs/` ADS 参考文档镜像也复制到宿主仓库

这解决的是存量项目接入时最常见的两个问题：

- Agent 容易把整个 `.agent/docs/` 误当成“都得先读”的上下文，导致接入后日常实现链路变重
- 宿主项目原本已经成熟的产品文档和 handoff 材料，会被 ADS 自己的解释性文档稀释

## 这套仓库包含什么

```
agent-dev-spec/
├── README.md
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

- 根 `README.md` 中的 `ADS Agent Quick Start`
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
- 可视化层：`ads_dashboard` 本地网页面板（项目首页 + 今日控制台 + 上手引导 + 统一详情页）
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
