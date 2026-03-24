# MCP 配置目录（ADS）

将各 MCP Server 的连接配置放在此目录，例如：

- `my-server.json` — 本地或远程 MCP 的 command/url/args
- 敏感信息使用环境变量占位，勿提交密钥

业务仓库复制 ADS 模板后：

1. 将 `*.example` 改名为实际配置（并加入 `.gitignore` 若含秘密）。
2. 在 `tools/toolset.json` 的 `mcp_servers` 中引用对应文件路径。

当前模板提供两个示例：

- `ads-server.json.example` — ADS MCP stdio server 示例配置，默认指向 `scripts/ads_mcp_server.py`
- `example-server.json.example` — 通用 MCP server 示例
