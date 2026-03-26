#!/usr/bin/env python3
"""Minimal MCP stdio server for ADS tools."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parent.parent
JSON = dict[str, Any]


@dataclass
class ToolSpec:
    tool_id: str
    rel_script: str
    input_schema: JSON
    build_args: Callable[[JSON, Path], list[str]]
    description: str = ""


def read_json(path: Path) -> JSON:
    return json.loads(path.read_text(encoding="utf-8"))


def add_flag(args: list[str], flag: str, value: Any) -> None:
    if value is None or value == "":
        return
    args.extend([flag, str(value)])


def add_repeat(args: list[str], flag: str, values: list[Any] | None) -> None:
    if not values:
        return
    for value in values:
        if value is None or value == "":
            continue
        args.extend([flag, str(value)])


def build_init_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [str(arguments["target"])]
    if arguments.get("force"):
        args.append("--force")
    add_flag(args, "--project-name", arguments.get("project_name"))
    return args


def build_doctor_args(arguments: JSON, repo_root: Path) -> list[str]:
    args: list[str] = []
    add_flag(args, "--repo-root", arguments.get("repo_root") or str(repo_root))
    return args


def build_resume_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [str(arguments["task"])]
    add_flag(args, "--handoff", arguments.get("handoff"))
    add_flag(args, "--identity", arguments.get("identity"))
    add_flag(args, "--project-name", arguments.get("project_name"))
    add_flag(args, "--repo-root", arguments.get("repo_root") or str(repo_root))
    return args


def build_validate_args(arguments: JSON, repo_root: Path) -> list[str]:
    args: list[str] = []
    paths = arguments.get("paths") or []
    if paths:
        args.append("--paths")
        args.extend(str(path) for path in paths)
    return args


def build_handoff_draft_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [str(arguments["task"])]
    add_flag(args, "--repo-root", arguments.get("repo_root") or str(repo_root))
    add_flag(args, "--to", arguments.get("to"))
    add_flag(args, "--from-actor", arguments.get("from_actor"))
    add_flag(args, "--status", arguments.get("status"))
    add_flag(args, "--blocked-reason", arguments.get("blocked_reason"))
    add_repeat(args, "--evidence-item", arguments.get("evidence_items"))
    add_flag(args, "--identity", arguments.get("identity"))
    add_flag(args, "--output", arguments.get("output"))
    return args


def build_evidence_capture_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = ["--item", str(arguments["item"]), "--command", str(arguments["command"])]
    add_flag(args, "--repo-root", arguments.get("repo_root") or str(repo_root))
    add_flag(args, "--executed-by", arguments.get("executed_by"))
    add_flag(args, "--artifact", arguments.get("artifact"))
    add_flag(args, "--append-to", arguments.get("append_to"))
    add_flag(args, "--retry-count", arguments.get("retry_count"))
    add_flag(args, "--cost-usd", arguments.get("cost_usd"))
    return args


def build_task_decomposer_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [str(arguments["change_path"])]
    add_flag(args, "--output-dir", arguments.get("output_dir"))
    if arguments.get("force"):
        args.append("--force")
    return args


def build_handoff_writer_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [str(arguments["task_path"])]
    add_flag(args, "--repo-root", arguments.get("repo_root") or str(repo_root))
    add_flag(args, "--output", arguments.get("output"))
    add_flag(args, "--from-actor", arguments.get("from_actor"))
    add_flag(args, "--status", arguments.get("status"))
    add_flag(args, "--blocked-reason", arguments.get("blocked_reason"))
    add_repeat(args, "--evidence-item", arguments.get("evidence_items"))
    add_flag(args, "--identity", arguments.get("identity"))
    return args


def build_blocked_triager_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [str(arguments["task_path"])]
    add_flag(args, "--summary", arguments.get("summary"))
    add_repeat(args, "--target-path", arguments.get("target_paths"))
    add_flag(args, "--output", arguments.get("output"))
    add_flag(args, "--request-output", arguments.get("request_output"))
    return args


def build_spec_syncer_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [str(arguments["task_path"])]
    add_repeat(args, "--changed-path", arguments.get("changed_paths"))
    add_flag(args, "--output", arguments.get("output"))
    add_flag(args, "--spec-delta-output", arguments.get("spec_delta_output"))
    return args


def build_integration_reviewer_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [str(arguments["task_path"]), str(arguments["handoff_path"])]
    add_flag(args, "--qa-actor", arguments.get("qa_actor"))
    add_flag(args, "--output", arguments.get("output"))
    return args


def build_innovation_capture_args(arguments: JSON, repo_root: Path) -> list[str]:
    args = [
        str(arguments["task_path"]),
        "--title",
        str(arguments["title"]),
        "--summary",
        str(arguments["summary"]),
        "--trigger",
        str(arguments["trigger"]),
        "--judgement",
        str(arguments["judgement"]),
    ]
    add_flag(args, "--output", arguments.get("output"))
    return args


SCRIPT_TOOL_SPECS: dict[str, ToolSpec] = {
    "ads.init": ToolSpec(
        tool_id="ads.init",
        rel_script="scripts/ads_init.py",
        input_schema={
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "force": {"type": "boolean"},
                "project_name": {"type": "string"},
            },
            "required": ["target"],
        },
        build_args=build_init_args,
    ),
    "ads.doctor": ToolSpec(
        tool_id="ads.doctor",
        rel_script="scripts/ads_doctor.py",
        input_schema={
            "type": "object",
            "properties": {"repo_root": {"type": "string"}},
        },
        build_args=build_doctor_args,
    ),
    "ads.resume": ToolSpec(
        tool_id="ads.resume",
        rel_script="scripts/ads_resume.py",
        input_schema={
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "handoff": {"type": "string"},
                "identity": {"type": "string"},
                "project_name": {"type": "string"},
                "repo_root": {"type": "string"},
            },
            "required": ["task"],
        },
        build_args=build_resume_args,
    ),
    "ads.validate": ToolSpec(
        tool_id="ads.validate",
        rel_script="scripts/validate_ads.py",
        input_schema={
            "type": "object",
            "properties": {"paths": {"type": "array", "items": {"type": "string"}}},
        },
        build_args=build_validate_args,
    ),
    "ads.handoff_draft": ToolSpec(
        tool_id="ads.handoff_draft",
        rel_script="scripts/ads_handoff_draft.py",
        input_schema={
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "repo_root": {"type": "string"},
                "to": {"type": "string"},
                "from_actor": {"type": "string"},
                "status": {"type": "string"},
                "blocked_reason": {"type": "string"},
                "evidence_items": {"type": "array", "items": {"type": "string"}},
                "identity": {"type": "string"},
                "output": {"type": "string"},
            },
            "required": ["task"],
        },
        build_args=build_handoff_draft_args,
    ),
    "ads.evidence_capture": ToolSpec(
        tool_id="ads.evidence_capture",
        rel_script="scripts/ads_evidence_capture.py",
        input_schema={
            "type": "object",
            "properties": {
                "item": {"type": "string"},
                "command": {"type": "string"},
                "repo_root": {"type": "string"},
                "executed_by": {"type": "string"},
                "artifact": {"type": "string"},
                "append_to": {"type": "string"},
                "retry_count": {"type": "integer"},
                "cost_usd": {"type": "number"},
            },
            "required": ["item", "command"],
        },
        build_args=build_evidence_capture_args,
    ),
    "ads.task_decomposer": ToolSpec(
        tool_id="ads.task_decomposer",
        rel_script="skills/task-decomposer/run.py",
        input_schema={
            "type": "object",
            "properties": {
                "change_path": {"type": "string"},
                "output_dir": {"type": "string"},
                "force": {"type": "boolean"},
            },
            "required": ["change_path"],
        },
        build_args=build_task_decomposer_args,
    ),
    "ads.handoff_writer": ToolSpec(
        tool_id="ads.handoff_writer",
        rel_script="skills/handoff-writer/run.py",
        input_schema={
            "type": "object",
            "properties": {
                "task_path": {"type": "string"},
                "repo_root": {"type": "string"},
                "output": {"type": "string"},
                "from_actor": {"type": "string"},
                "status": {"type": "string"},
                "blocked_reason": {"type": "string"},
                "evidence_items": {"type": "array", "items": {"type": "string"}},
                "identity": {"type": "string"},
            },
            "required": ["task_path"],
        },
        build_args=build_handoff_writer_args,
    ),
    "ads.blocked_triager": ToolSpec(
        tool_id="ads.blocked_triager",
        rel_script="skills/blocked-triager/run.py",
        input_schema={
            "type": "object",
            "properties": {
                "task_path": {"type": "string"},
                "summary": {"type": "string"},
                "target_paths": {"type": "array", "items": {"type": "string"}},
                "output": {"type": "string"},
                "request_output": {"type": "string"},
            },
            "required": ["task_path"],
        },
        build_args=build_blocked_triager_args,
    ),
    "ads.spec_syncer": ToolSpec(
        tool_id="ads.spec_syncer",
        rel_script="skills/spec-syncer/run.py",
        input_schema={
            "type": "object",
            "properties": {
                "task_path": {"type": "string"},
                "changed_paths": {"type": "array", "items": {"type": "string"}},
                "output": {"type": "string"},
                "spec_delta_output": {"type": "string"},
            },
            "required": ["task_path"],
        },
        build_args=build_spec_syncer_args,
    ),
    "ads.integration_reviewer": ToolSpec(
        tool_id="ads.integration_reviewer",
        rel_script="skills/integration-reviewer/run.py",
        input_schema={
            "type": "object",
            "properties": {
                "task_path": {"type": "string"},
                "handoff_path": {"type": "string"},
                "qa_actor": {"type": "string"},
                "output": {"type": "string"},
            },
            "required": ["task_path", "handoff_path"],
        },
        build_args=build_integration_reviewer_args,
    ),
    "ads.innovation_capture": ToolSpec(
        tool_id="ads.innovation_capture",
        rel_script="skills/innovation-capture/run.py",
        input_schema={
            "type": "object",
            "properties": {
                "task_path": {"type": "string"},
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "trigger": {"type": "string"},
                "judgement": {"type": "string"},
                "output": {"type": "string"},
            },
            "required": ["task_path", "title", "summary", "trigger", "judgement"],
        },
        build_args=build_innovation_capture_args,
    ),
}


def load_tool_descriptions(repo_root: Path) -> dict[str, str]:
    toolset_path = repo_root / "tools" / "toolset.json"
    if not toolset_path.exists():
        return {}
    toolset = read_json(toolset_path)
    descriptions: dict[str, str] = {}
    for tool in toolset.get("tools", []):
        if not isinstance(tool, dict):
            continue
        tool_id = str(tool.get("tool_id", "")).strip()
        if tool_id:
            descriptions[tool_id] = str(tool.get("description", "")).strip()
    return descriptions


def get_tool_specs(repo_root: Path) -> dict[str, ToolSpec]:
    descriptions = load_tool_descriptions(repo_root)
    specs: dict[str, ToolSpec] = {}
    for tool_id, spec in SCRIPT_TOOL_SPECS.items():
        specs[tool_id] = ToolSpec(
            tool_id=spec.tool_id,
            rel_script=spec.rel_script,
            input_schema=spec.input_schema,
            build_args=spec.build_args,
            description=descriptions.get(tool_id, spec.description),
        )
    return specs


def run_tool(tool_id: str, arguments: JSON, repo_root: Path = REPO_ROOT) -> tuple[int, str]:
    specs = get_tool_specs(repo_root)
    if tool_id not in specs:
        return 1, f"unknown tool: {tool_id}"
    spec = specs[tool_id]
    command = [sys.executable, str(repo_root / spec.rel_script), *spec.build_args(arguments, repo_root)]
    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
    output = result.stdout
    if result.stderr:
        output = output + result.stderr
    return result.returncode, output.strip()


def handle_request(request: JSON, repo_root: Path = REPO_ROOT) -> JSON | None:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {}) or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "ads-mcp-server", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        tools = []
        for tool_id, spec in sorted(get_tool_specs(repo_root).items()):
            tools.append(
                {
                    "name": tool_id,
                    "description": spec.description,
                    "inputSchema": spec.input_schema,
                }
            )
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}
    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {}) or {}
        code, output = run_tool(str(tool_name), arguments, repo_root=repo_root)
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{"type": "text", "text": output}],
                "isError": code != 0,
            },
        }
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def read_message(stream) -> JSON | None:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        header = line.decode("utf-8").strip()
        if not header:
            break
        key, value = header.split(":", 1)
        headers[key.strip().lower()] = value.strip()
    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        return None
    body = stream.read(content_length)
    return json.loads(body.decode("utf-8"))


def write_message(stream, message: JSON) -> None:
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    stream.write(f"Content-Length: {len(payload)}\r\n\r\n".encode("utf-8"))
    stream.write(payload)
    stream.flush()


def serve(repo_root: Path = REPO_ROOT) -> int:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        request = read_message(stdin)
        if request is None:
            return 0
        response = handle_request(request, repo_root=repo_root)
        if response is not None:
            write_message(stdout, response)


def main() -> int:
    repo_root = REPO_ROOT
    if "--repo-root" in sys.argv:
        index = sys.argv.index("--repo-root")
        if index + 1 < len(sys.argv):
            repo_root = Path(sys.argv[index + 1]).resolve()
    return serve(repo_root=repo_root)


if __name__ == "__main__":
    raise SystemExit(main())
