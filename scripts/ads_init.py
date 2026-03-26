#!/usr/bin/env python3
"""Scaffold a minimal, runnable ADS workspace into another repository."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

COPY_MAP = {
    "README_AGENT.md": "README_AGENT.md",
    ".ai/README.md": ".ai/README.md",
    ".ai/templates/README.md": ".ai/templates/README.md",
    ".ai/patterns/frontend-backend-integration.md": ".ai/patterns/frontend-backend-integration.md",
    ".ai/patterns/human-agent-review.md": ".ai/patterns/human-agent-review.md",
    ".github/workflows/ads-checks.yml.example": ".github/workflows/ads-checks.yml.example",
    ".agent/constitution.md": ".agent/constitution.md",
    ".agent/agent_map.yaml.example": ".agent/agent_map.yaml",
    "tools/mcp/README.md": "tools/mcp/README.md",
    "tools/mcp/ads-server.json.example": "tools/mcp/ads-server.json.example",
    "tools/mcp/example-server.json.example": "tools/mcp/example-server.json.example",
    "scripts/validate_ads.py": "scripts/validate_ads.py",
    "scripts/build_context_pack.py": "scripts/build_context_pack.py",
    "scripts/build_knowledge_pack.py": "scripts/build_knowledge_pack.py",
    "scripts/check_stale_knowledge.py": "scripts/check_stale_knowledge.py",
    "scripts/ads_dashboard.py": "scripts/ads_dashboard.py",
    "scripts/ads_health_report.py": "scripts/ads_health_report.py",
    "scripts/ads_doctor.py": "scripts/ads_doctor.py",
    "scripts/ads_explain.py": "scripts/ads_explain.py",
    "scripts/ads_resume.py": "scripts/ads_resume.py",
    "scripts/ads_handoff_draft.py": "scripts/ads_handoff_draft.py",
    "scripts/ads_evidence_capture.py": "scripts/ads_evidence_capture.py",
    "scripts/ads_escalation_draft.py": "scripts/ads_escalation_draft.py",
    "scripts/ads_mcp_server.py": "scripts/ads_mcp_server.py",
    "scripts/sync-tools.py": "scripts/sync-tools.py",
}

DOC_FILES = [
    "README.md",
    "00-overview.md",
    "01-principles.md",
    "02-uaw-mapping.md",
    "03-tools-and-mcp.md",
    "04-handoff-and-tasks.md",
    "05-multi-client-and-mesh.md",
    "06-evolution.md",
    "07-iteration-log.md",
    "08-harness-landscape-and-recovery.md",
    "guides/adoption-playbook.md",
    "guides/client-adapters/README.md",
    "guides/client-adapters/claude-code.md",
    "guides/client-adapters/codex-cli.md",
    "guides/client-adapters/cursor.md",
    "guides/client-adapters/opencode.md",
    "research/README.md",
    "research/2026-03-agent-harness-landscape.md",
]

GENERATED_DIRS = [
    ".ai/tasks",
    ".ai/handoffs",
    ".ai/escalations",
    ".ai/requests",
    ".ai/qa",
    ".ai/memory",
    ".ai/innovations",
    ".ai/specs",
    "skills",
]


@dataclass
class InitResult:
    created: list[Path] = field(default_factory=list)
    overwritten: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def infer_verify_commands(target_root: Path) -> dict[str, str]:
    if (target_root / "package.json").exists():
        return {
            "lint": "npm run lint",
            "test": "npm run test",
            "build": "npm run build",
        }
    if (target_root / "pyproject.toml").exists() or (target_root / "requirements.txt").exists():
        return {
            "test": "python3 -m pytest -q",
        }
    return {
        "test": "TODO: add your standard verify command",
    }


def build_identity(source_root: Path, target_root: Path, project_name: str | None) -> str:
    template_path = source_root / ".agent" / "identity.json.example"
    data = json.loads(read_text(template_path))
    data["project_name"] = project_name or target_root.name
    data["standard_verify_commands"] = infer_verify_commands(target_root)
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def build_toolset() -> str:
    data = {
        "$schema_comment": "ADS tool registry skeleton. Register project skills and MCP tools here.",
        "version": "1.0",
        "registry": "project-local",
        "tools": [
            {
                "tool_id": "ads.dashboard",
                "title": "ADS Dashboard",
                "description": "Serve a lightweight local web dashboard for project overview, current focus, risks, and health status.",
                "owner": "platform",
                "risk_level": "low",
                "version": "1.0.0",
                "source": "script",
                "entrypoint": "scripts/ads_dashboard.py",
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
                "tool_id": "ads.explain",
                "title": "ADS Explain",
                "description": "Generate a plain-language first-run brief so humans and agents can quickly understand the project mission, collaboration status, and next steps.",
                "owner": "platform",
                "risk_level": "low",
                "version": "1.0.0",
                "source": "script",
                "entrypoint": "scripts/ads_explain.py",
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
                "tool_id": "ads.escalation_draft",
                "title": "ADS Escalation Draft",
                "description": "Generate a structured escalation draft when a blocked or context-missing handoff cannot be resolved by the next actor alone.",
                "owner": "platform",
                "risk_level": "medium",
                "version": "1.0.0",
                "source": "script",
                "entrypoint": "scripts/ads_escalation_draft.py",
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
                "tool_id": "ads.sync_tools",
                "title": "ADS Sync Tools",
                "description": "Synchronize toolset entries from ADS script tools and skill manifests.",
                "owner": "platform",
                "risk_level": "low",
                "version": "1.0.0",
                "source": "script",
                "entrypoint": "scripts/sync-tools.py",
            }
        ],
        "mcp_servers": [
            {
                "id": "ads-server",
                "config_path": "tools/mcp/ads-server.json.example",
            }
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def render_start_here(source_root: Path) -> str:
    text = read_text(source_root / ".ai" / "START_HERE.md.example")
    text = text.replace("# 多 Agent 协作入口（示例）", "# 多 Agent 协作入口")
    text = text.replace("> 将本文件复制为 `.ai/START_HERE.md` 并按项目修改。  \n", "")
    return text


def render_readme_agent(source_root: Path) -> str:
    text = read_text(source_root / "README_AGENT.md")
    text = text.replace(
        "采用与 ADS 兼容的目录（参见本仓库 `docs/02-uaw-mapping.md`）。",
        "采用与 ADS 兼容的目录（参见 `.agent/docs/02-uaw-mapping.md`）。",
    )
    text = text.replace(
        "打开本仓库 **`docs/00-overview.md`**，按索引阅读细则。",
        "优先打开 **`.agent/docs/guides/adoption-playbook.md`** 完成接入，再按 **`.agent/docs/00-overview.md`** 的索引阅读细则。",
    )
    return text


def maybe_write(path: Path, content: str, force: bool, result: InitResult) -> None:
    if path.exists() and not force:
        result.skipped.append(path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        result.overwritten.append(path)
    else:
        result.created.append(path)
    path.write_text(content, encoding="utf-8")


def ensure_dir(path: Path, result: InitResult) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        result.created.append(path)


def init_repo(target_root: Path, source_root: Path = REPO_ROOT, force: bool = False, project_name: str | None = None) -> InitResult:
    result = InitResult()
    target_root.mkdir(parents=True, exist_ok=True)

    for directory in GENERATED_DIRS:
        ensure_dir(target_root / directory, result)

    maybe_write(target_root / ".agent" / "identity.json", build_identity(source_root, target_root, project_name), force, result)
    maybe_write(target_root / ".ai" / "START_HERE.md", render_start_here(source_root), force, result)
    maybe_write(target_root / "README_AGENT.md", render_readme_agent(source_root), force, result)
    maybe_write(target_root / "tools" / "toolset.json", build_toolset(), force, result)

    for source_rel, target_rel in COPY_MAP.items():
        source_path = source_root / source_rel
        target_path = target_root / target_rel
        maybe_write(target_path, read_text(source_path), force, result)

    for template_path in sorted((source_root / "templates").glob("*.md")):
        target_path = target_root / "templates" / template_path.name
        maybe_write(target_path, read_text(template_path), force, result)

    for doc_rel in DOC_FILES:
        source_path = source_root / "docs" / doc_rel
        target_path = target_root / ".agent" / "docs" / doc_rel
        maybe_write(target_path, read_text(source_path), force, result)

    return result


def print_summary(result: InitResult, target_root: Path) -> None:
    print(f"[ads_init] target={target_root}")
    print(f"[ads_init] created={len(result.created)} overwritten={len(result.overwritten)} skipped={len(result.skipped)}")
    if result.created:
        print("[ads_init] created_paths:")
        for path in result.created:
            print(f"- {path}")
    if result.overwritten:
        print("[ads_init] overwritten_paths:")
        for path in result.overwritten:
            print(f"- {path}")
    if result.skipped:
        print("[ads_init] skipped_paths:")
        for path in result.skipped:
            print(f"- {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold ADS into another repository.")
    parser.add_argument("target", help="Target repository root to scaffold")
    parser.add_argument("--force", action="store_true", help="Overwrite existing ADS files")
    parser.add_argument("--project-name", help="Project name written into .agent/identity.json")
    args = parser.parse_args()

    target_root = Path(args.target).resolve()
    result = init_repo(target_root, force=args.force, project_name=args.project_name)
    print_summary(result, target_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
