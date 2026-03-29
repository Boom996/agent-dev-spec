# ADS Adoption Playbook

> 目标：让一个已有项目在最短时间内接入 **ADS（Agent Development Specification）**，并把多 Agent 协作从“聊天驱动”升级为“有契约、有交接、有证据、有治理”的工程流程。

## 适用场景

- 你的项目已经有代码仓库，但 AI 协作过程主要靠聊天记录、口头约定或零散脚本
- 你希望同一个项目同时支持 Codex、Claude Code、Cursor、OpenCode 等多个客户端
- 你希望把任务、handoff、evidence、tool registry 沉淀成仓库资产，而不是绑定到某个 IDE

## ADS 会给项目带来什么

- 一个统一的 **Agent 工作空间**：`.ai/`、`.agent/`、`tools/`、`skills/`
- 一套稳定的 **任务与交接协议**：task、handoff、request、qa、memory、spec
- 一组可直接运行的 **自动化脚本**：doctor、resume、handoff draft、evidence capture、tool sync、MCP server
- 一个可持续演进的 **团队协作控制面**：人类开发者、CLI Agent、IDE Agent 都按同一套约定工作

## 10 分钟落地路径

### 0. 如果你是当前项目里的 Agent，优先走自接入入口

如果你已经在目标项目仓库里工作，并且只是拿到了 ADS 仓库链接，推荐直接运行：

```bash
python3 /path/to/agent-dev-spec/scripts/ads_self_install.py
```

这个命令默认会：

- 把当前 git 仓库识别为接入目标
- 检查是否存在未提交修改
- 提醒作者优先提交/上传当前工作
- 自动创建新的 ADS 接入分支
- 完成 apply、doctor、validate
- 成功后启动并打开 ADS dashboard

这条路径比手动拼 `ads_adopt.py --apply` 更适合 Agent 自主执行。

### 1. 植入 ADS 骨架

在 ADS 仓库执行：

```bash
python3 scripts/ads_init.py /path/to/your-project
```

如果目标项目已经有自己的文档、handoff、Agent 入口或多层目录结构，先运行自动分析，拿到试用判断报告，再决定是否自动写入：

```bash
python3 scripts/ads_adopt.py /path/to/your-project
python3 scripts/ads_adopt.py /path/to/your-project --apply
```

如果你希望先把分析结果沉淀成文件，方便团队评审或让其他 Agent 读取：

```bash
python3 scripts/ads_adopt.py /path/to/your-project \
  --report-file /tmp/ads-adoption-report.md \
  --json-file /tmp/ads-adoption-report.json
```

完成后，宿主仓库会获得：

- `README.md` 中的 `ADS Agent Quick Start` 区块
- `.agent/identity.json`
- `.agent/docs/`
- `.agent/adoption-report.json`
- `.ai/START_HERE.md`
- `tools/toolset.json`
- `scripts/ads_doctor.py`、`scripts/ads_resume.py`、`scripts/ads_handoff_draft.py` 等基础脚本

`ads_adopt.py` 现在会优先告诉你：

- 这个项目是否适合先试 ADS
- 推荐采用什么接入方式
- 最小试用路径是什么
- apply 完成后先跑哪几个命令

如果你已经明确要在**当前仓库**里执行安全试接入，则优先改用 `ads_self_install.py`，因为它会默认处理分支与 dirty worktree 安全边界。

### 2. 补齐宿主项目信息

初始化后，优先修改这几个文件：

- `README.md`
  维护 `ADS Agent Quick Start` 区块，说明本项目是什么、当前阶段是什么、Agent 先读什么文档
- `.agent/identity.json`
  定义项目目标、约束、默认验证命令、关键角色
- `.agent/constitution.md`
  写清楚不能破坏的业务/架构规则
- `.ai/START_HERE.md`
  作为当前仓库多 Agent 协作入口

### 3. 建立第一条真实任务链路

推荐立即用一次真实迭代验证 ADS，而不是只复制模板：

1. 从 `templates/task.md` 生成一个真实任务
2. 在执行过程中记录 evidence；如果想衡量运行代价，同时补 telemetry（耗时 / 成本 / 重试）
3. 结束时生成 handoff
4. 由另一个人或 Agent 根据 handoff 接续
5. 用 QA 或 integration review 做 PASS/FAIL 闭环

对于存量项目，执行 `ads_adopt.py --apply` 后还会自动生成：

- `.agent/docs/guides/project-brief.md`

这个 brief 的目的不是替代 README，而是让第一次进入仓库的人或 Agent 能快速理解：

- 这个项目为什么接入 ADS
- 当前应该先读什么
- 下一步该执行什么命令

此外，`--apply` 结束时还会额外输出一段试用结果摘要，直接告诉你：

- 当前已经具备哪些 ADS 入口
- 先跑哪 3 个命令
- 如何判断这次试用接入已经成功

如果想先看参考样例，直接阅读 [`examples/README.md`](../../examples/README.md)。

### 4. 接入工具注册与客户端

推荐顺序：

1. 维护 `tools/toolset.json`
2. 为项目 skill 增加 `skills/<name>/manifest.json`
3. 运行 `python3 scripts/sync-tools.py`
4. 参考 [`client-adapters/README.md`](client-adapters/README.md) 为 Claude Code / Codex / Cursor / OpenCode 做入口映射

### 5. 接入最小 CI

将仓库中的 [`.github/workflows/ads-checks.yml.example`](../../.github/workflows/ads-checks.yml.example) 复制为宿主项目工作流，并按实际依赖调整：

- `ads_doctor.py`：检查 ADS 接入完整性和漂移
- `validate_ads.py`：检查 task / handoff / memory / request / qa / toolset
- 宿主项目自己的 lint / test / build

### 6. 做一次自检

在宿主仓库运行：

```bash
python3 scripts/ads_explain.py
python3 scripts/ads_doctor.py
python3 scripts/validate_ads.py
```

如果需要把验证代价一起落盘，可以顺手执行：

```bash
python3 scripts/ads_evidence_capture.py \
  --item test \
  --command "python3 -m pytest -q" \
  --retry-count 1 \
  --cost-usd 0.012500
```

其中：

- `ads_explain.py` 用来确认“这个仓库为什么使用 ADS、先看什么、下一步做什么”
- `ads_dashboard.py` 用来本地打开项目状态面板，快速查看项目首页、今日控制台、上手引导、当前重点、风险和健康情况
- `ads_doctor.py` 用来确认结构是否齐全
- `validate_ads.py` 用来确认协议文件是否合法

如果这三步都通过，说明 ADS 基本接入完成，可以开始把真实工作流迁移到这套协议上。

如果你希望团队成员或新加入的人更直观地理解项目现状，推荐再启动：

```bash
python3 scripts/ads_dashboard.py
```

默认会在本地启动网页服务，提供：

- 项目首页
- 今日控制台
- 新成员 / 续做成员上手引导
- 统一详情页（任务 / 风险 / 健康）

## 推荐接入节奏

### Day 1

- 完成骨架初始化
- 让所有参与协作的人先读根 `README.md` 的 `ADS Agent Quick Start`
- 用一个真实小任务跑通 task -> handoff -> QA

### Week 1

- 将项目内已有高频协作任务抽成 skill
- 建立 `tools/toolset.json` 与 manifest 的同步机制
- 让至少两个客户端接入同一套 ADS 工作区

### Week 2+

- 为关键流程补充 CI
- 把常见 blocked 情况、integration review、spec sync 固化为标准 skill
- 逐步沉淀 `.ai/memory/`、`.ai/specs/`、`.ai/patterns/`

## 接入时最常见的错误

- 只复制模板，不用真实任务验证
- 仍然依赖聊天历史，而不写 handoff
- 让多个 Agent 同时直接改同一组文件，没有单写者边界
- 把工具能力只写在某个客户端私有配置里，没有回写 `toolset.json`
- 只有“做完了”的描述，没有 evidence 和 QA 结论

## 落地检查清单

- [ ] 宿主仓库 `README.md` 已包含 `ADS Agent Quick Start`
- [ ] `README.md` 的 ADS 区块明确首读顺序
- [ ] `.agent/identity.json` 已填写真实 verify commands
- [ ] `.ai/START_HERE.md` 已根据宿主项目改写
- [ ] `tools/toolset.json` 已纳入项目自有工具
- [ ] 至少有 1 条真实 task 与 handoff
- [ ] `python3 scripts/ads_doctor.py` 通过
- [ ] `python3 scripts/validate_ads.py` 通过
- [ ] 已为主要客户端补齐 adapter 配置
- [ ] 已决定哪些流程进入 CI

## 继续阅读

- [`../00-overview.md`](../00-overview.md)
- [`../04-handoff-and-tasks.md`](../04-handoff-and-tasks.md)
- [`client-adapters/README.md`](client-adapters/README.md)
- [`../../examples/README.md`](../../examples/README.md)
