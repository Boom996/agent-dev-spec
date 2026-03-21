# 任务：<简短标题>

## 元数据

| 字段 | 值 |
|------|-----|
| **task_id** | `TASK-YYYYMMDD-001` |
| **owner_role** | Frontend / Backend / Architect / Integration / … |
| **owner** | （可选）人名或会话标识 |
| **priority** | Critical / High / Medium / Low |
| **deps** | `[]` 或依赖的 task_id 列表 |
| **handoff_to** | （可选）下一棒角色 |
| **team_pattern_id** | （可选）例如 `frontend-backend-integration` |
| **approval_owner** | （可选）批准人或批准角色 |
| **allowed_agents** | `[]` 或允许参与的 Agent / 客户端标识 |
| **trace_id** | `TRACE-YYYYMMDD-001` |
| **updated_at** | ISO8601 |

## 单写者范围

- **locked_paths**（本任务周期内仅主责可改）：
  - `path/to/fileOrDir` — 说明
- **forbidden_paths**（禁止改动）：
  - `path/to/sensitive` — 说明

## 共享改动升级（可选）

- 如需修改跨任务共享文件，请附上 `shared-change-request` 链接：
  - `templates/shared-change-request.md` 生成的文件路径
- 若无共享改动，写 `无`

## 背景与目标

（2～5 句话，说明用户/产品动机）

## 验收标准（可勾选）

- [ ] 标准 1（可验证）
- [ ] 标准 2
- [ ] 标准 3

## 相关路径

| 路径 | 说明 |
|------|------|
| `src/...` | … |

## Memory refs（可选）

- `path/to/memory-object.md` — 任务依赖的共享事实或决策
- 若无，写 `无`

## 证据期望（完成时必须附上）

例如：`npm run build` 成功输出节选、`npm test`、截图路径、PR 链接等。

## Freshness

- **stale_after**（可选）：`P2D` / `P7D` / 团队自定义
- **最后更新时间说明**：（一句话说明本次更新改了什么）

---

**状态**：`backlog` | `in-progress` | `blocked` | `review` | `done`
