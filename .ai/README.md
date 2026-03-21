# `.ai/` 协作区（ADS 模板）

复制到业务仓库后使用。建议内容：

| 路径 | 用途 |
|------|------|
| `START_HERE.md` | 人类与 Agent 的协作入口（可从 `START_HERE.md.example` 改名） |
| `tasks/` | backlog / in-progress / completed 或 `active/<task-id>.md` |
| `handoffs/` | `Handoff Envelope` 文件：`<task-id>.md` |
| `patterns/` | 标准 team pattern，例如前后端加 Integration 协作模式 |
| `requests/` | 共享改动升级请求，如 `shared-change-request` |
| `qa/` | QA / Integration 结论文档，如 pass / fail 报告 |
| `memory/` | 共享事实层，例如 decision / fact / risk 等 memory object |
| `specs/` | 功能切片规格（可选） |
| `templates/` | 从仓库根 `templates/` 同步任务/交接/QA 模板，或符号链接 |

模板文件本体在 **`../templates/`**；此处可放项目定制覆盖版。

建议配套脚本：

- `scripts/build_context_pack.py`
- `scripts/build_knowledge_pack.py`
- `scripts/check_stale_knowledge.py`
- `scripts/ads_health_report.py`
