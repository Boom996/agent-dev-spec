#!/usr/bin/env python3
"""Analyze and bootstrap ADS into an existing project."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import ads_init


REPO_ROOT = Path(__file__).resolve().parent.parent
EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".venv",
    "venv",
    "__pycache__",
}


@dataclass
class CodeRoot:
    path: str
    score: int
    markers: list[str]
    verify_commands: dict[str, str]
    has_nested_git: bool = False


@dataclass
class AdoptionReport:
    workspace_root: str
    project_name: str
    vision_one_liner: str
    primary_code_root: str
    additional_code_roots: list[str] = field(default_factory=list)
    verify_commands: dict[str, str] = field(default_factory=dict)
    existing_systems: list[str] = field(default_factory=list)
    context_docs: list[str] = field(default_factory=list)
    legacy_handoffs: list[str] = field(default_factory=list)
    nested_git_roots: list[str] = field(default_factory=list)
    code_roots: list[CodeRoot] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    docs_entry: dict[str, str] = field(default_factory=dict)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def iter_files(root: Path, names: set[str], max_depth: int = 5) -> list[Path]:
    found: list[Path] = []
    for path in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.is_dir():
            continue
        rel = path.relative_to(root)
        if len(rel.parts) > max_depth:
            continue
        if path.name in names:
            found.append(path)
    return sorted(found)


def relative_to(root: Path, path: Path) -> str:
    rel = path.relative_to(root)
    return "." if str(rel) == "." else rel.as_posix()


def detect_nested_git_roots(target_root: Path) -> list[Path]:
    nested: list[Path] = []
    for git_dir in target_root.rglob(".git"):
        if any(part in EXCLUDED_DIRS - {".git"} for part in git_dir.parts):
            continue
        if git_dir.parent == target_root:
            continue
        nested.append(git_dir.parent)
    return sorted(nested)


def load_json(path: Path) -> dict:
    return json.loads(read_text(path))


def infer_node_package_manager(code_root: Path) -> str:
    package_data = load_json(code_root / "package.json")
    package_manager = str(package_data.get("packageManager", "")).lower()
    if "pnpm" in package_manager or (code_root / "pnpm-lock.yaml").exists() or (code_root / "pnpm-workspace.yaml").exists():
        return "pnpm"
    if "npm" in package_manager or (code_root / "package-lock.json").exists():
        return "npm"
    if "yarn" in package_manager or (code_root / "yarn.lock").exists():
        return "yarn"
    if "bun" in package_manager or (code_root / "bun.lockb").exists():
        return "bun"
    return "npm"


def build_node_script_command(package_manager: str, workspace_root: Path, code_root: Path, script_name: str) -> str:
    rel = relative_to(workspace_root, code_root)
    if package_manager == "pnpm":
        if rel == ".":
            return f"pnpm {script_name}"
        return f"pnpm --dir {rel} {script_name}"
    if package_manager == "npm":
        if rel == ".":
            return f"npm run {script_name}"
        return f"npm --prefix {rel} run {script_name}"
    if package_manager == "yarn":
        if rel == ".":
            return f"yarn {script_name}"
        return f"yarn --cwd {rel} {script_name}"
    if rel == ".":
        return f"bun run {script_name}"
    return f"cd {rel} && bun run {script_name}"


def infer_verify_commands_for_dir(code_root: Path, workspace_root: Path) -> dict[str, str]:
    if (code_root / "package.json").exists():
        package_data = load_json(code_root / "package.json")
        scripts = package_data.get("scripts", {})
        if isinstance(scripts, dict):
            package_manager = infer_node_package_manager(code_root)
            verify_commands: dict[str, str] = {}
            for name in ("lint", "test", "build", "typecheck"):
                if name in scripts:
                    verify_commands[name] = build_node_script_command(package_manager, workspace_root, code_root, name)
            if verify_commands:
                return verify_commands
    if (code_root / "pyproject.toml").exists() or (code_root / "requirements.txt").exists():
        rel = relative_to(workspace_root, code_root)
        if rel == ".":
            return {"test": "python3 -m pytest -q"}
        return {"test": f"cd {rel} && python3 -m pytest -q"}
    if (code_root / "Cargo.toml").exists():
        rel = relative_to(workspace_root, code_root)
        if rel == ".":
            return {"test": "cargo test", "build": "cargo build"}
        return {"test": f"cd {rel} && cargo test", "build": f"cd {rel} && cargo build"}
    if (code_root / "go.mod").exists():
        rel = relative_to(workspace_root, code_root)
        if rel == ".":
            return {"test": "go test ./...", "build": "go build ./..."}
        return {"test": f"cd {rel} && go test ./...", "build": f"cd {rel} && go build ./..."}
    return {"test": "TODO: add your standard verify command"}


def score_code_root(code_root: Path, target_root: Path, nested_git_roots: set[Path]) -> CodeRoot:
    score = 0
    markers: list[str] = []
    if (code_root / "package.json").exists():
        score += 30
        markers.append("package.json")
        package_data = load_json(code_root / "package.json")
        scripts = package_data.get("scripts", {})
        if isinstance(scripts, dict):
            for name in ("lint", "test", "build", "typecheck"):
                if name in scripts:
                    score += 5
                    markers.append(f"script:{name}")
        if "packageManager" in package_data:
            score += 5
            markers.append(f"packageManager:{package_data['packageManager']}")
    for marker_file, label, delta in (
        ("pnpm-workspace.yaml", "pnpm-workspace", 30),
        ("turbo.json", "turbo", 20),
        ("pyproject.toml", "pyproject", 25),
        ("Cargo.toml", "cargo", 25),
        ("go.mod", "go", 25),
    ):
        if (code_root / marker_file).exists():
            score += delta
            markers.append(label)
    for marker_dir, delta in (("apps", 15), ("packages", 15), ("src", 10), ("app", 10)):
        if (code_root / marker_dir).exists():
            score += delta
            markers.append(f"dir:{marker_dir}")
    if code_root in nested_git_roots:
        score += 10
        markers.append("nested-git")
    verify_commands = infer_verify_commands_for_dir(code_root, target_root)
    return CodeRoot(
        path=relative_to(target_root, code_root),
        score=score,
        markers=markers,
        verify_commands=verify_commands,
        has_nested_git=code_root in nested_git_roots,
    )


def detect_code_roots(target_root: Path, nested_git_roots: list[Path]) -> list[CodeRoot]:
    candidates: set[Path] = set()
    for marker in ("package.json", "pyproject.toml", "Cargo.toml", "go.mod"):
        for path in iter_files(target_root, {marker}, max_depth=5):
            candidates.add(path.parent)
    scored = [score_code_root(path, target_root, set(nested_git_roots)) for path in candidates]
    return sorted(scored, key=lambda item: (-item.score, item.path))


def detect_existing_systems(target_root: Path) -> list[str]:
    systems: list[str] = []
    checks = [
        (".golutra", "golutra_workspace"),
        (".superpowers", "superpowers_workspace"),
        ("docs/superpowers", "superpowers_docs"),
        ("README_AGENT.md", "ads_readme_agent"),
        ("tools/toolset.json", "ads_toolset"),
        (".agent/identity.json", "ads_identity"),
        (".ai/START_HERE.md", "ads_start_here"),
    ]
    for rel, name in checks:
        if (target_root / rel).exists():
            systems.append(name)
    for path in iter_files(target_root, {"AGENTS.md", "CLAUDE.md"}, max_depth=5):
        systems.append(relative_to(target_root, path))
    return systems


def collect_context_docs(target_root: Path) -> list[Path]:
    docs = [path for path in target_root.rglob("*.md") if path.is_file()]
    filtered: list[Path] = []
    for path in docs:
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        rel = relative_to(target_root, path)
        lowered = rel.lower()
        if any(token in lowered for token in ("spec", "guide", "plan", "product", "handoff")):
            filtered.append(path)
    def score(path: Path) -> tuple[int, str]:
        rel = relative_to(target_root, path).lower()
        priority = 0
        if "project-guide" in rel:
            priority -= 50
        if "product" in rel:
            priority -= 40
        if "master" in rel:
            priority -= 30
        if "specs/" in rel:
            priority -= 20
        if "handoff" in rel:
            priority -= 10
        return (priority, rel)
    return sorted(filtered, key=score)


def collect_handoff_docs(target_root: Path) -> list[Path]:
    return [
        path
        for path in collect_context_docs(target_root)
        if "handoff" in relative_to(target_root, path).lower()
    ]


def infer_vision_one_liner(target_root: Path, context_docs: list[Path]) -> str:
    quoted_candidates: list[str] = []
    fallback_candidates: list[str] = []
    for path in context_docs:
        text = read_text(path)
        lines = [line.strip() for line in text.splitlines()]
        for line in lines:
            if not line or line.startswith("#") or line.startswith("**") or line.startswith("---"):
                continue
            if line.startswith(">"):
                candidate = line[1:].strip().strip("`")
                if candidate:
                    quoted_candidates.append(candidate)
                    continue
            if line.endswith(":") or line.endswith("："):
                continue
            if len(line) <= 120:
                fallback_candidates.append(line.strip("`"))
    if quoted_candidates:
        return quoted_candidates[0]
    if fallback_candidates:
        return fallback_candidates[0]
    return "用一句话描述产品或本仓库目标"


def build_report(target_root: Path, project_name: str | None = None) -> AdoptionReport:
    nested_git_roots = detect_nested_git_roots(target_root)
    code_roots = detect_code_roots(target_root, nested_git_roots)
    primary = code_roots[0] if code_roots else CodeRoot(".", 0, [], {"test": "TODO: add your standard verify command"})
    context_docs = collect_context_docs(target_root)
    legacy_handoffs = collect_handoff_docs(target_root)
    vision = infer_vision_one_liner(target_root, context_docs)

    risks: list[str] = []
    if nested_git_roots:
        risks.append("Detected nested git repositories. Define whether ADS governs the outer workspace, the inner code repo, or both before changing repository boundaries.")
    if any(system == "golutra_workspace" for system in detect_existing_systems(target_root)):
        risks.append("Existing Golutra workflow assets are present. ADS should map and preserve them instead of overwriting them.")
    if any("docs/superpowers" in doc for doc in [relative_to(target_root, path) for path in context_docs]):
        risks.append("Legacy spec and handoff documents already exist under docs/superpowers. They should be treated as migration inputs, not discarded.")

    recommended_actions = [
        "Adopt ADS at the workspace root and keep the current product docs as primary context until they are normalized into `.ai/specs/`.",
        f"Treat `{primary.path}` as the primary code root for verification and implementation work.",
        "Generate ADS identity, constitution, start-here, and migration guide files before normalizing existing handoff/task assets.",
    ]

    primary_context = relative_to(target_root, context_docs[0]) if context_docs else ".agent/docs/guides/project-adoption-report.md"
    return AdoptionReport(
        workspace_root=str(target_root),
        project_name=project_name or target_root.name,
        vision_one_liner=vision,
        primary_code_root=primary.path,
        additional_code_roots=[item.path for item in code_roots[1:4]],
        verify_commands=primary.verify_commands,
        existing_systems=detect_existing_systems(target_root),
        context_docs=[relative_to(target_root, path) for path in context_docs[:8]],
        legacy_handoffs=[relative_to(target_root, path) for path in legacy_handoffs[:5]],
        nested_git_roots=[relative_to(target_root, path) for path in nested_git_roots],
        code_roots=code_roots[:5],
        risks=risks,
        recommended_actions=recommended_actions,
        docs_entry={
            "readme_agent": "README_AGENT.md",
            "ai_context": primary_context,
            "start_here": ".ai/START_HERE.md",
        },
    )


def render_report_markdown(report: AdoptionReport) -> str:
    lines = [
        "# ADS Adoption Report",
        "",
        f"- workspace_root: `{report.workspace_root}`",
        f"- project_name: `{report.project_name}`",
        f"- vision_one_liner: {report.vision_one_liner}",
        f"- primary_code_root: `{report.primary_code_root}`",
        "",
        "## Verify Commands",
    ]
    for name, command in report.verify_commands.items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(["", "## Existing Systems"])
    lines.extend(f"- `{item}`" for item in (report.existing_systems or ["none detected"]))
    lines.extend(["", "## Context Docs"])
    lines.extend(f"- `{item}`" for item in (report.context_docs or ["none detected"]))
    lines.extend(["", "## Nested Git Roots"])
    lines.extend(f"- `{item}`" for item in (report.nested_git_roots or ["none detected"]))
    lines.extend(["", "## Recommended Actions"])
    lines.extend(f"- {item}" for item in report.recommended_actions)
    if report.risks:
        lines.extend(["", "## Risks"])
        lines.extend(f"- {item}" for item in report.risks)
    return "\n".join(lines) + "\n"


def render_readme_agent(report: AdoptionReport) -> str:
    context_doc = report.docs_entry.get("ai_context", ".agent/docs/guides/project-adoption-report.md")
    lines = [
        "# Agent 自举入口（ADS）",
        "",
        f"> 本项目已接入 **ADS（Agent Development Specification）**。当前产品目标：{report.vision_one_liner}",
        "",
        "## 本项目工作区约定",
        "",
        f"- **ADS 根目录**：`{Path(report.workspace_root).name}/`",
        f"- **主代码根**：`{report.primary_code_root}`",
        "- **统一协作区**：`.ai/`、`.agent/`、`tools/`、`skills/`",
        "- **旧协作资产**：保留原有 docs / handoff / orchestration 资料，优先映射，不直接删除",
        "",
        "## 首读顺序",
        "",
        "1. **本文件**（`README_AGENT.md`）",
        f"2. **项目主上下文**（`{context_doc}`）",
        "3. **迁移映射说明**（`.agent/docs/guides/legacy-workspace-mapping.md`）",
        "4. **ADS 当前协作入口**（`.ai/START_HERE.md`）",
    ]
    if report.legacy_handoffs:
        lines.append(f"5. **历史交接文档**（`{report.legacy_handoffs[0]}`）")
    lines.extend(
        [
            "",
            "## 你必须遵守的纪律",
            "",
            "1. 先按 ADS 入口阅读，不要直接只看聊天历史。",
            f"2. 实现工作默认在 **`{report.primary_code_root}`** 下展开，除非 task 明确允许其他路径。",
            "3. 旧文档仍有效，但新增协作信息应优先沉淀到 ADS 结构化工件中。",
            "",
            "## 标准验证命令",
            "",
        ]
    )
    for name, command in report.verify_commands.items():
        lines.append(f"- `{name}`: `{command}`")
    lines.extend(
        [
            "",
            "## 不确定时",
            "",
            "- 先看 `.agent/docs/guides/project-adoption-report.md`",
            "- 再看 `.agent/docs/00-overview.md` 与 `.agent/docs/guides/adoption-playbook.md`",
        ]
    )
    return "\n".join(lines) + "\n"


def render_start_here(report: AdoptionReport) -> str:
    lines = [
        "# 多 Agent 协作入口",
        "",
        f"> 当前阶段目标：在不打断既有开发的前提下，把 `{report.project_name}` 的协作流转统一到 ADS。",
        "",
        "## 当前重点",
        "",
        f"- 产品目标：{report.vision_one_liner}",
        f"- 主代码根：`{report.primary_code_root}`",
        "- 优先保留并映射 legacy docs / legacy handoff，再逐步规范化到 ADS 资产",
        "",
        "## 角色建议",
        "",
        "| 角色 | 职责 |",
        "|------|------|",
        "| Architect | 维护 spec、结构迁移、边界决策 |",
        "| Frontend | UI、页面、交互实现 |",
        "| Backend | API、数据、Agent runtime、MCP 对接 |",
        "| Integration | 验证命令、QA、handoff、发布闭环 |",
        "",
        "## 任务入口",
        "",
        "- backlog：`.ai/tasks/backlog/`",
        "- in-progress：`.ai/tasks/in-progress/`",
        "- handoff：`.ai/handoffs/`",
        "",
        "## 迁移上下文",
        "",
        f"- 项目接入报告：`.agent/docs/guides/project-adoption-report.md`",
        f"- 旧工作区映射：`.agent/docs/guides/legacy-workspace-mapping.md`",
        f"- 当前主上下文：`{report.docs_entry.get('ai_context', '.agent/docs/guides/project-adoption-report.md')}`",
        "",
        "## 纪律提醒",
        "",
        "1. 所有新协作都优先落到 ADS 工件，而不是只写在聊天里。",
        "2. 不要擅自删除旧系统资料，先迁移、再归档。",
        "3. 每个实现 task 完成前都要留下 evidence 和 handoff。",
    ]
    return "\n".join(lines) + "\n"


def render_constitution(report: AdoptionReport) -> str:
    verify_summary = ", ".join(f"`{command}`" for command in report.verify_commands.values())
    lines = [
        f"# {report.project_name} Constitution",
        "",
        "> 该文档由 ADS adoption automation 生成，后续应由项目 owner / architect 继续收敛。",
        "",
        "## Mission",
        "",
        report.vision_one_liner,
        "",
        "## Non-Negotiable Principles",
        "",
        f"- 主开发代码默认位于 `{report.primary_code_root}`，跨目录修改必须在 task 中明确声明。",
        "- 旧协作资产和现有规划文档先映射、再迁移，不允许未经确认直接删除或改写真源。",
        "- 所有任务完成必须附带 evidence；跨会话续做必须留下 handoff。",
        "",
        "## Tech Stack Principles",
        "",
        "- 主语言/框架：按宿主项目当前主代码根自动识别并延续",
        "- 禁止引入的依赖类型：未经架构决策的新基础设施或新运行时",
        f"- 测试要求：至少运行宿主项目标准验证命令（{verify_summary}）中的相关项",
        "",
        "## Role Definitions",
        "",
        "- **Architect**：负责 ADS 接入策略、spec 和协作边界维护",
        "- **Frontend / Backend**：负责主代码根内的实现工作",
        "- **Integration**：负责验证命令、QA 结论、handoff 闭环",
        "- **HumanOwner**：负责高风险结构改动与治理文档审批",
        "",
        "## Agent Governance",
        "",
        "- 哪些 Agent 角色的操作需要人类审批：删除 legacy docs、变更仓库结构、处理 nested git",
        "- 哪些路径任何 Agent 都不能修改（全局 forbidden_paths）：密钥、凭证、未确认的生成物目录",
        "- Agent 的最大自治范围说明：默认可在 task 允许路径内实现、测试、补文档，但不能自行重组仓库边界",
        "",
        "## Approval Hierarchy",
        "",
        "- Constitution 变更：HumanOwner / Architect 审批",
        "- Spec 体系迁移：Architect 审批",
        "- 共享协作目录改造：HumanOwner 审批",
        "- 日常 task 执行：按 task 的 `allowed_agents` 和锁路径约束",
    ]
    return "\n".join(lines) + "\n"


def render_project_adoption_report(report: AdoptionReport) -> str:
    lines = [
        "# Project Adoption Report",
        "",
        f"- project_name: `{report.project_name}`",
        f"- workspace_root: `{report.workspace_root}`",
        f"- primary_code_root: `{report.primary_code_root}`",
        f"- vision_one_liner: {report.vision_one_liner}",
        "",
        "## Detected Code Roots",
    ]
    for item in report.code_roots:
        lines.append(f"- `{item.path}` score={item.score} markers={', '.join(item.markers) or 'none'}")
    lines.extend(["", "## Existing Systems"])
    lines.extend(f"- `{item}`" for item in (report.existing_systems or ["none detected"]))
    lines.extend(["", "## Context Sources"])
    lines.extend(f"- `{item}`" for item in (report.context_docs or ["none detected"]))
    if report.legacy_handoffs:
        lines.extend(["", "## Legacy Handoff Sources"])
        lines.extend(f"- `{item}`" for item in report.legacy_handoffs)
    if report.nested_git_roots:
        lines.extend(["", "## Nested Git Roots"])
        lines.extend(f"- `{item}`" for item in report.nested_git_roots)
    lines.extend(["", "## Recommended Verify Commands"])
    for name, command in report.verify_commands.items():
        lines.append(f"- `{name}`: `{command}`")
    if report.risks:
        lines.extend(["", "## Risks"])
        lines.extend(f"- {item}" for item in report.risks)
    lines.extend(["", "## Recommended Actions"])
    lines.extend(f"- {item}" for item in report.recommended_actions)
    return "\n".join(lines) + "\n"


def render_legacy_mapping(report: AdoptionReport) -> str:
    lines = [
        "# Legacy Workspace Mapping",
        "",
        "| Legacy Path | ADS Target | Mapping Rule |",
        "|-------------|------------|--------------|",
    ]
    mappings = [
        ("docs/superpowers/specs/", ".ai/specs/ or .agent/docs/guides/", "Treat existing superpowers specs as current source context until normalized."),
        ("docs/superpowers/plans/HANDOFF.md", ".ai/handoffs/<task-id>.md", "Use the legacy handoff as migration input when creating normalized ADS handoff files."),
        (".golutra/", ".ai/ and .agent/", "Preserve orchestration metadata and migrate only stable workflow rules into ADS."),
        (report.primary_code_root, report.primary_code_root, "Keep implementation work in the existing code root; ADS adds collaboration structure around it."),
    ]
    for legacy, target, rule in mappings:
        lines.append(f"| `{legacy}` | `{target}` | {rule} |")
    return "\n".join(lines) + "\n"


def render_adoption_task(report: AdoptionReport) -> str:
    task_id = "TASK-00000000-001"
    lines = [
        "# 任务：完成 legacy workspace 到 ADS 的标准化接入",
        "",
        "## 元数据",
        "",
        "| 字段 | 值 |",
        "|------|-----|",
        f"| **task_id** | `{task_id}` |",
        "| **owner_role** | Architect |",
        "| **priority** | High |",
        "| **deps** | `[]` |",
        "| **handoff_to** | Integration |",
        "| **team_pattern_id** | |",
        "| **approval_owner** | HumanOwner |",
        "| **allowed_agents** | `[]` |",
        "| **parent_change_id** | |",
        "| **coordination_model** | `direct` |",
        "| **autonomy_level** | `semi-autonomous` |",
        "| **trace_id** | `TRACE-00000000-001` |",
        "| **updated_at** | 2026-01-01T00:00:00Z |",
        "",
        "## 单写者范围",
        "",
        "- **locked_paths**（本任务周期内仅主责可改）：",
        "  - `.agent/` — ADS 治理和项目映射",
        "  - `.ai/` — ADS 协作工件",
        "  - `README_AGENT.md` — 仓库级 Agent 入口",
        "- **forbidden_paths**（禁止改动）：",
        f"  - `{report.primary_code_root}` — 先完成协作层接入，再修改业务实现",
        "",
        "## 共享改动升级（可选）",
        "",
        "无",
        "",
        "## 背景与目标",
        "",
        f"将已有项目 `{report.project_name}` 的 legacy workspace 纳入 ADS 协作层，同时保留原有上下文与开发节奏。",
        "",
        "## 验收标准（可勾选）",
        "",
        "- [ ] README_AGENT、identity、constitution、START_HERE 已按项目语义定制",
        "- [ ] 旧工作区映射文档已建立",
        "- [ ] 宿主项目标准验证命令已写入 identity",
        "",
        "## 相关路径",
        "",
        "| 路径 | 说明 |",
        "|------|------|",
        "| `README_AGENT.md` | 仓库级 Agent 入口 |",
        "| `.agent/docs/guides/project-adoption-report.md` | 当前宿主项目接入报告 |",
        "| `.agent/docs/guides/legacy-workspace-mapping.md` | 旧工作区到 ADS 的映射说明 |",
        "",
        "## Memory refs（可选）",
        "",
        "无",
        "",
        "## 证据期望（完成时必须附上）",
        "",
        "`python3 scripts/ads_doctor.py`",
        "",
        "## Freshness",
        "",
        "- **stale_after**（可选）：`P7D`",
        "- **最后更新时间说明**：自动生成的 ADS adoption backlog task",
        "",
        "---",
        "",
        "**状态**：`backlog`",
    ]
    return "\n".join(lines) + "\n"


def apply_adoption(target_root: Path, force: bool = False, project_name: str | None = None) -> tuple[AdoptionReport, ads_init.InitResult]:
    report = build_report(target_root, project_name=project_name)
    existing_before = {
        target_root / "README_AGENT.md",
        target_root / ".agent" / "identity.json",
        target_root / ".agent" / "constitution.md",
        target_root / ".ai" / "START_HERE.md",
        target_root / ".agent" / "docs" / "guides" / "project-adoption-report.md",
        target_root / ".agent" / "docs" / "guides" / "legacy-workspace-mapping.md",
        target_root / ".ai" / "tasks" / "backlog" / "TASK-00000000-001-ads-adoption.md",
    }
    existed_map = {path: path.exists() for path in existing_before}
    result = ads_init.init_repo(target_root, source_root=REPO_ROOT, force=force, project_name=report.project_name)

    identity = json.loads(ads_init.build_identity(REPO_ROOT, target_root, report.project_name))
    identity["vision_one_liner"] = report.vision_one_liner
    identity["standard_verify_commands"] = report.verify_commands
    identity["docs_entry"] = report.docs_entry
    identity["constraints"] = [
        f"主代码根：{report.primary_code_root}",
        "legacy docs 先映射再迁移",
        "完成任务必须有 evidence 和 handoff",
    ]

    def write_generated(path: Path, content: str) -> None:
        should_force = force or not existed_map.get(path, False)
        ads_init.maybe_write(path, content, should_force, result)

    write_generated(target_root / "README_AGENT.md", render_readme_agent(report))
    write_generated(target_root / ".agent" / "identity.json", json.dumps(identity, ensure_ascii=False, indent=2) + "\n")
    write_generated(target_root / ".agent" / "constitution.md", render_constitution(report))
    write_generated(target_root / ".ai" / "START_HERE.md", render_start_here(report))
    write_generated(
        target_root / ".agent" / "docs" / "guides" / "project-adoption-report.md",
        render_project_adoption_report(report),
    )
    write_generated(
        target_root / ".agent" / "docs" / "guides" / "legacy-workspace-mapping.md",
        render_legacy_mapping(report),
    )
    write_generated(
        target_root / ".ai" / "tasks" / "backlog" / "TASK-00000000-001-ads-adoption.md",
        render_adoption_task(report),
    )
    return report, result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="target repository root to analyze or adopt")
    parser.add_argument("--apply", action="store_true", help="bootstrap ADS into the target repository")
    parser.add_argument("--force", action="store_true", help="overwrite existing ADS files when applying")
    parser.add_argument("--project-name", help="override the detected project name, useful when adopting into a sandbox copy")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown", help="report output format")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_root = args.target.resolve()
    if args.apply:
        report, result = apply_adoption(target_root, force=args.force, project_name=args.project_name)
        print(render_report_markdown(report))
        ads_init.print_summary(result, target_root)
        return 0

    report = build_report(target_root, project_name=args.project_name)
    if args.format == "json":
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(render_report_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
