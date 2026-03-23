#!/usr/bin/env python3
"""Write an ADS handoff file using the core handoff draft builder."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_handoff_draft


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_task_id(task_path: Path) -> str:
    text = read_text(task_path)
    task_id = ads_handoff_draft.extract_table_value(text, "task_id")
    return task_id or task_path.stem


def write_handoff(
    task_path: Path,
    output_path: Path | None = None,
    repo_root: Path = REPO_ROOT,
    from_actor: str | None = None,
    handoff_status: str = "DONE",
    blocked_reason: str = "",
    evidence_items: list[str] | None = None,
    identity_path: Path | None = None,
) -> Path:
    task_id = extract_task_id(task_path)
    if output_path is None:
        output_path = repo_root / ".ai" / "handoffs" / f"{task_id}.md"
    draft = ads_handoff_draft.build_handoff_draft(
        task_path,
        repo_root=repo_root,
        from_actor=from_actor,
        handoff_status=handoff_status,
        blocked_reason=blocked_reason,
        evidence_items=evidence_items or [],
        identity_path=identity_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(draft, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write an ADS handoff file from a task and current repo state.")
    parser.add_argument("task_path", help="Path to the ADS task markdown file")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root used for git inspection")
    parser.add_argument("--output", help="Optional output path for the handoff markdown file")
    parser.add_argument("--from-actor", help="Override current actor, e.g. `Backend @ Codex`")
    parser.add_argument("--status", default="DONE", help="handoff_status value")
    parser.add_argument("--blocked-reason", default="", help="Reason when status is BLOCKED or NEEDS_CONTEXT")
    parser.add_argument("--evidence-item", action="append", default=[], help="Evidence item label, repeatable")
    parser.add_argument(
        "--identity",
        default=str(REPO_ROOT / ".agent" / "identity.json.example"),
        help="Path to identity.json or example identity file",
    )
    args = parser.parse_args()

    task_path = Path(args.task_path).resolve()
    repo_root = Path(args.repo_root).resolve()
    output_path = Path(args.output).resolve() if args.output else None
    identity_path = Path(args.identity).resolve() if args.identity else None

    written_path = write_handoff(
        task_path,
        output_path=output_path,
        repo_root=repo_root,
        from_actor=args.from_actor,
        handoff_status=args.status,
        blocked_reason=args.blocked_reason,
        evidence_items=args.evidence_item,
        identity_path=identity_path,
    )
    print(written_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
