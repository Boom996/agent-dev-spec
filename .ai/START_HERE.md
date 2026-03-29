# 多 Agent 协作入口

> 当前阶段目标：把 ADS 打磨成外部项目拿到仓库链接后就能安全接入、快速理解并直接开始协同的产品级范本。

## 当前重点

- 产品目标：让外部 Agent 只读根 `README.md` 就知道如何安全接入 ADS
- 主代码根：`.`
- 优先把接入体验、文档入口、脚本一致性和本地 dashboard 打磨完整

## 角色

| 角色 | 职责 |
|------|------|
| Architect | 维护 ADS 协议边界、接入策略与产品路线 |
| Backend | 维护 CLI 脚本、协议校验、doctor、adopt、自接入流程 |
| Frontend | 维护本地 dashboard、项目首页、控制台与引导体验 |
| Integration | 维护测试、验证命令、文档一致性与发布闭环 |

## 任务入口

- 待办：`.ai/tasks/backlog/`
- 进行中：`.ai/tasks/active/`
- 交接：`.ai/handoffs/`

## 纪律提醒

1. 先读根 `README.md` 中的 `ADS Agent Quick Start`
2. 接入别的项目前，先提醒作者提交并优先上传本地修改，再新建分支
3. 完成任务前补齐 evidence、handoff 与必要的文档更新

## 规格目录

- `.ai/specs/`
- `docs/`
