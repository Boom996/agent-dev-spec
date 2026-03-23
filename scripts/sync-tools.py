#!/usr/bin/env python3
"""Synchronize ADS tool registry entries from script tools and skill manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

CORE_SCRIPT_TOOLS = [
    {
        "tool_id": "ads.init",
        "title": "ADS Init",
        "description": "Scaffold the minimal ADS workspace into another repository.",
        "owner": "platform",
        "risk_level": "medium",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/ads_init.py",
    },
    {
        "tool_id": "ads.doctor",
        "title": "ADS Doctor",
        "description": "Check ADS bootstrap completeness, task/handoff alignment, and tool drift.",
        "owner": "platform",
        "risk_level": "low",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/ads_doctor.py",
    },
    {
        "tool_id": "ads.resume",
        "title": "ADS Resume",
        "description": "Build a resume-oriented context summary from task, handoff, change, and constitution artifacts.",
        "owner": "platform",
        "risk_level": "low",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/ads_resume.py",
    },
    {
        "tool_id": "ads.handoff_draft",
        "title": "ADS Handoff Draft",
        "description": "Generate a handoff draft from task metadata and the current git diff.",
        "owner": "platform",
        "risk_level": "medium",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/ads_handoff_draft.py",
    },
    {
        "tool_id": "ads.evidence_capture",
        "title": "ADS Evidence Capture",
        "description": "Execute a verification command and emit a standard ADS evidence table row.",
        "owner": "platform",
        "risk_level": "medium",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/ads_evidence_capture.py",
    },
    {
        "tool_id": "ads.validate",
        "title": "ADS Validate",
        "description": "Validate task, handoff, memory, request, QA, pattern, spec, and toolset artifacts.",
        "owner": "platform",
        "risk_level": "low",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/validate_ads.py",
    },
    {
        "tool_id": "ads.context_pack",
        "title": "ADS Context Pack",
        "description": "Generate a CLI context pack from a task and optional handoff.",
        "owner": "platform",
        "risk_level": "low",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/build_context_pack.py",
    },
    {
        "tool_id": "ads.knowledge_pack",
        "title": "ADS Knowledge Pack",
        "description": "Build a minimal knowledge pack from task, handoff, and memory objects.",
        "owner": "platform",
        "risk_level": "low",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/build_knowledge_pack.py",
    },
    {
        "tool_id": "ads.health_report",
        "title": "ADS Health Report",
        "description": "Generate a minimal collaboration health report for ADS workspaces.",
        "owner": "platform",
        "risk_level": "low",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/ads_health_report.py",
    },
    {
        "tool_id": "ads.check_stale_knowledge",
        "title": "ADS Check Stale Knowledge",
        "description": "Check whether ADS memory objects are stale relative to review windows and references.",
        "owner": "platform",
        "risk_level": "low",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/check_stale_knowledge.py",
    },
    {
        "tool_id": "ads.sync_tools",
        "title": "ADS Sync Tools",
        "description": "Synchronize toolset entries from ADS script tools and skill manifests.",
        "owner": "platform",
        "risk_level": "low",
        "version": "1.0.0",
        "source": "script",
        "entrypoint": "scripts/sync-tools.py",
    },
]

DEFAULT_MCP_SERVERS = [
    {
        "id": "ads-server",
        "config_path": "tools/mcp/ads-server.json.example",
    },
    {
        "id": "example-server",
        "config_path": "tools/mcp/example-server.json.example",
    },
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_skill_manifests(repo_root: Path) -> list[tuple[Path, dict]]:
    manifests: list[tuple[Path, dict]] = []
    for path in sorted(repo_root.glob("skills/**/manifest.json")):
        if path.is_file():
            manifests.append((path, read_json(path)))
    return manifests


def normalize_skill_entry(path: Path, manifest: dict, existing_entry: dict | None = None, repo_root: Path = REPO_ROOT) -> dict:
    tool_id = str(manifest.get("tool_id", "")).strip()
    name = str(manifest.get("name", "")).strip()
    version = str(manifest.get("version", "")).strip() or "1.0.0"
    description = str(manifest.get("description", "")).strip()
    rel_manifest = str(path.relative_to(repo_root))

    entry = {
        "tool_id": tool_id,
        "title": existing_entry.get("title") if existing_entry and existing_entry.get("title") else (name or tool_id),
        "description": description,
        "owner": existing_entry.get("owner") if existing_entry and existing_entry.get("owner") else "platform",
        "risk_level": existing_entry.get("risk_level") if existing_entry and existing_entry.get("risk_level") else "low",
        "version": version,
        "source": "skill",
        "manifest": rel_manifest,
    }
    tags = existing_entry.get("tags") if existing_entry else None
    if tags:
        entry["tags"] = tags
    return entry


def build_toolset(repo_root: Path, existing_toolset: dict | None = None) -> dict:
    existing_toolset = existing_toolset or {}
    existing_tools = {
        str(entry.get("tool_id", "")).strip(): entry
        for entry in existing_toolset.get("tools", [])
        if isinstance(entry, dict) and str(entry.get("tool_id", "")).strip()
    }

    tools: list[dict] = []
    for tool in CORE_SCRIPT_TOOLS:
        existing_entry = existing_tools.get(tool["tool_id"], {})
        merged = dict(tool)
        if existing_entry.get("tags"):
            merged["tags"] = existing_entry["tags"]
        tools.append(merged)

    for path, manifest in discover_skill_manifests(repo_root):
        tool_id = str(manifest.get("tool_id", "")).strip()
        if not tool_id:
            continue
        tools.append(normalize_skill_entry(path, manifest, existing_tools.get(tool_id, {}), repo_root=repo_root))

    tools.sort(key=lambda item: item["tool_id"])
    return {
        "$schema_comment": "ADS tool registry. Keep tool_id stable across clients and generate this file via scripts/sync-tools.py.",
        "version": "1.0",
        "registry": "project-local",
        "tools": tools,
        "mcp_servers": existing_toolset.get("mcp_servers", DEFAULT_MCP_SERVERS),
    }


def sync_toolset(repo_root: Path, output_path: Path | None = None) -> dict:
    if output_path is None:
        output_path = repo_root / "tools" / "toolset.json"
    existing = read_json(output_path) if output_path.exists() else {}
    toolset = build_toolset(repo_root, existing_toolset=existing)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(toolset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return toolset


def check_toolset(repo_root: Path, output_path: Path | None = None) -> bool:
    if output_path is None:
        output_path = repo_root / "tools" / "toolset.json"
    existing = read_json(output_path) if output_path.exists() else {}
    expected = build_toolset(repo_root, existing_toolset=existing)
    current_text = json.dumps(existing, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    expected_text = json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    return current_text == expected_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize ADS tool registry entries.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root to inspect")
    parser.add_argument("--output", help="Optional path for generated toolset.json")
    parser.add_argument("--check", action="store_true", help="Only check whether toolset.json is up to date")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_path = Path(args.output).resolve() if args.output else None

    if args.check:
        is_synced = check_toolset(repo_root, output_path=output_path)
        print("[sync-tools] up_to_date" if is_synced else "[sync-tools] drift_detected")
        return 0 if is_synced else 1

    toolset = sync_toolset(repo_root, output_path=output_path)
    print(f"[sync-tools] wrote {len(toolset['tools'])} tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
