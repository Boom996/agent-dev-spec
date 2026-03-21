#!/usr/bin/env bash
# ADS 示例：占位脚本。可扩展为：扫描 skills/*/manifest.json，重写 tools/toolset.json。
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "[ADS] sync-tools stub: root=$ROOT"
echo "[ADS] TODO: aggregate manifests into tools/toolset.json"
echo "[ADS] TODO: emit Cursor / MCP config snippets if needed"
exit 0
