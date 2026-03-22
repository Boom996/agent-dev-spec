# ADS 演进路线

## 为什么要有这一篇

ADS 最初是一个偏文档和模板的规范仓库。随着本仓库逐步补齐校验器、上下文包、team pattern、memory object、health report 之后，已经不再只是“模板集合”，而是开始形成一个轻量的协作控制面。

本篇用于回答三个问题：

- ADS 当前已经具备了什么
- ADS 还没有做什么
- 后续应如何继续演进而不失控

## 当前定位

当前更准确的定位是：

`repo-native collaboration control plane for human + agent mixed software teams`

也就是说，ADS 当前强调的是：

- 任务契约
- 交接信封
- 结构化证据
- 无状态 CLI 上下文包
- 最小 team pattern
- 最小治理字段
- 最小共享记忆与知识消费包

而不是：

- 重型 agent runtime
- 组织级图谱平台
- IDE 插件平台

## 已落地能力

### 1. 协作内核

- [task.md](/Users/woodjelly/MyAIproject/agent-dev-spec/templates/task.md)
- [handoff.md](/Users/woodjelly/MyAIproject/agent-dev-spec/templates/handoff.md)
- [shared-change-request.md](/Users/woodjelly/MyAIproject/agent-dev-spec/templates/shared-change-request.md)

解决的问题：

- 谁负责什么
- 哪些路径可改
- 共享改动如何升级
- 完成凭什么算数

### 2. 生成与校验

- [validate_ads.py](/Users/woodjelly/MyAIproject/agent-dev-spec/scripts/validate_ads.py)
- [build_context_pack.py](/Users/woodjelly/MyAIproject/agent-dev-spec/scripts/build_context_pack.py)
- [ads_health_report.py](/Users/woodjelly/MyAIproject/agent-dev-spec/scripts/ads_health_report.py)

解决的问题：

- 模板漂移
- context pack 手工整理
- shared-change-request / QA / pattern 纳入机器校验
- 缺 handoff / 缺 evidence / 待批准 / 高风险工具可见性

### 3. Team Pattern

- [frontend-backend-integration.md](/Users/woodjelly/MyAIproject/agent-dev-spec/.ai/patterns/frontend-backend-integration.md)
- [human-agent-review.md](/Users/woodjelly/MyAIproject/agent-dev-spec/.ai/patterns/human-agent-review.md)

解决的问题：

- 多角色协作模式标准化
- task 与 team pattern 的显式关联
- 人机评审与高风险审批有固定协作骨架

### 4. 共享记忆与知识消费

- [memory-object.md](/Users/woodjelly/MyAIproject/agent-dev-spec/templates/memory-object.md)
- [build_knowledge_pack.py](/Users/woodjelly/MyAIproject/agent-dev-spec/scripts/build_knowledge_pack.py)
- [check_stale_knowledge.py](/Users/woodjelly/MyAIproject/agent-dev-spec/scripts/check_stale_knowledge.py)

解决的问题：

- 共享事实落盘
- 只读 knowledge pack 生成
- memory freshness 检查

## 明确没有做的事

为了保持 ADS 轻量，当前明确没有做：

- graph database
- 多租户 registry
- IDE 插件协议
- 大而全 dashboard
- 自动采集 `context_read` / `actual_touched_paths`
- 复杂的 runtime orchestration

## 推荐的继续演进方式

### 1. 先做“更稳”

优先级最高的是：

- 继续压简字段
- 提高校验覆盖率
- 增加更多真实案例
- 让脚本对边界情况更稳

### 2. 再做“更好用”

包括：

- 增加更多 team pattern
- 增加更贴近 Integration 的报告
- 让 knowledge pack 支持多种输出模式
- 让 health report 支持按 team pattern 聚合阻塞信号

### 3. 最后才做“更强”

包括：

- knowledge dashboard
- project-level index
- 跨 repo 知识入口

## 一个简单判断标准

如果某项新能力会让 ADS 更像平台，而不会让团队“第一周就更省事”，那它就不该优先做。
