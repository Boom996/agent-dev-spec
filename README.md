# Agent 开发规范（ADS）

| 项目 | 内容 |
|------|------|
| **中文名** | Agent 开发规范 |
| **英文名** | **Agent Development Specification** |
| **缩写** | **ADS** |

本目录是一套**与具体业务仓库解耦**的通用模板：约定多 Agent / 多客户端（IDE、CLI、团队编排工具）协作时的**目录、契约、交接、证据、最小治理与共享记忆**，可与 [UAW](docs/02-uaw-mapping.md) 式工作空间及 **MCP** 工具链对齐。

## 快速开始

1. 运行 `python3 scripts/ads_init.py /path/to/your-project`，将最小可运行 ADS 骨架植入目标仓库。
2. 让参与者**首先阅读**根目录 [`README_AGENT.md`](README_AGENT.md)。
3. 按 [`docs/`](docs/) 索引阅读原则与落地步骤。
4. 从 [`templates/`](templates/) 与 [`.ai/templates/`](.ai/templates/) 复制范例到业务仓库并改名使用。
5. 参考 [`examples/`](examples/) 中的**完整案例**（任务 → 共享改动 → 交接 → 记忆对象 → CLI / knowledge pack）走一遍流程。

初始化完成后，建议在目标仓库执行 `python3 scripts/ads_doctor.py` 做一次接入自检。

## 目录结构

```
agent-dev-spec/
├── README.md                 # 本文件
├── README_AGENT.md           # 自举入口（复制到业务仓库根）
├── docs/                     # 给人看的规范说明
├── templates/                # 任务、交接、QA 等片段模板
├── .agent/                   # 工程元数据示例（identity / 客户端映射）
├── tools/                    # toolset / MCP 配置约定与示例
├── skills/                   # Skill + manifest 示例
├── .ai/                      # 协作区示例（任务、handoffs、patterns、requests、qa、memory）
├── scripts/                  # 校验、上下文包、健康报告、知识 freshness 脚本
└── examples/                 # 端到端模版案例（虚构小迭代）
```

## 文档索引

见 [`docs/README.md`](docs/README.md)。

## 当前已实现的最小能力

- 任务 / 交接模板增强：`trace_id`、`updated_at`、结构化 evidence、共享改动升级
- `ads_init.py`：将 ADS 最小工作区快速植入其他项目
- `validate_ads.py`：校验 task / handoff / memory / request / qa / pattern / toolset
- `ads_doctor.py`：检查接入仓库的自举完整性、task/handoff 对齐、toolset/manifest 漂移
- `ads_resume.py`：从 task / handoff / change proposal / constitution 生成续做上下文摘要
- `ads_handoff_draft.py`：从 task 元数据 + git diff 生成 handoff 草稿
- `ads_evidence_capture.py`：执行验证命令并输出标准 evidence 表格行
- `sync-tools.py`：同步 `skills/*/manifest.json` 与 `tools/toolset.json`，统一工具注册
- `build_context_pack.py`：生成 CLI 上下文包
- `ads_health_report.py`：输出最小协作健康摘要
- `build_knowledge_pack.py`：从 task / handoff / memory 生成知识消费包
- `skills/task-decomposer/`：将 change proposal 拆成 role-oriented ADS task 草稿
- `skills/handoff-writer/`：把 task + 当前 worktree 收敛成可落盘的 handoff 文件
- `skills/blocked-triager/`：判断任务是 `NEEDS_CONTEXT`、`BLOCKED` 还是应升级为 `shared-change-request`
- `skills/spec-syncer/`：推断受影响 spec，输出 `spec_update_status` 建议并可生成 `spec-delta`
- `skills/integration-reviewer/`：基于 task + handoff 产出 QA PASS/FAIL 结论，覆盖 spec compliance 与 code quality 闸口
- `skills/innovation-capture/`：把执行中出现的想法快速沉淀为标准 `Innovation Brief`
- `skills/blocked-triager/`：判断任务是 `NEEDS_CONTEXT`、`BLOCKED` 还是应升级为 `shared-change-request`
- `skills/spec-syncer/`：推断受影响 spec，输出 `spec_update_status` 建议并可生成 `spec-delta`
- `check_stale_knowledge.py`：检查 memory freshness
- `.ai/patterns/`：内置 team patterns
- `.ai/memory/`：最小共享事实层

## 许可

模板文本可按需修改后用于商业项目；默认建议与宿主项目许可证保持一致。
