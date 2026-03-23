#!/usr/bin/env python3
"""Run a verification command and emit a standard ADS evidence table row."""

from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def slugify(value: str) -> str:
    result = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    result = "-".join(part for part in result.split("-") if part)
    return result or "evidence"


def capture_evidence(
    item: str,
    command: str,
    repo_root: Path = REPO_ROOT,
    executed_by: str = "AgentImplementer @ CLI",
    artifact_path: Path | None = None,
    review_status: str = "pending",
) -> dict[str, object]:
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if artifact_path is None:
        artifact_path = repo_root / "artifacts" / f"{slugify(item)}.log"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(command, cwd=repo_root, shell=True, capture_output=True, text=True, check=False)
    combined_output = result.stdout + result.stderr
    artifact_path.write_text(combined_output, encoding="utf-8")

    return {
        "item": item,
        "executed_by": executed_by,
        "executed_at": timestamp,
        "result": "pass" if result.returncode == 0 else "fail",
        "artifact_path": artifact_path,
        "review_status": review_status,
        "returncode": result.returncode,
        "output": combined_output,
    }


def render_markdown_row(record: dict[str, object], repo_root: Path = REPO_ROOT) -> str:
    artifact_path = record["artifact_path"]
    artifact_display = str(artifact_path)
    if isinstance(artifact_path, Path):
        artifact_display = str(artifact_path.relative_to(repo_root))
    return (
        f"| `{record['item']}` | {record['executed_by']} | {record['executed_at']} | "
        f"{record['result']} | `{artifact_display}` | {record['review_status']} |"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture ADS evidence by executing a verification command.")
    parser.add_argument("--item", required=True, help="Evidence item label")
    parser.add_argument("--command", required=True, help="Shell command to execute")
    parser.add_argument("--repo-root", default=str(REPO_ROOT), help="Repository root used as working directory")
    parser.add_argument("--executed-by", default="AgentImplementer @ CLI", help="Actor shown in evidence row")
    parser.add_argument("--artifact", help="Optional artifact file path")
    parser.add_argument("--append-to", help="Optional markdown file to append the generated row to")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    artifact_path = Path(args.artifact).resolve() if args.artifact else None
    record = capture_evidence(
        item=args.item,
        command=args.command,
        repo_root=repo_root,
        executed_by=args.executed_by,
        artifact_path=artifact_path,
    )
    row = render_markdown_row(record, repo_root=repo_root)
    print(row)

    if args.append_to:
        append_path = Path(args.append_to).resolve()
        append_path.parent.mkdir(parents=True, exist_ok=True)
        with append_path.open("a", encoding="utf-8") as handle:
            handle.write(row + "\n")

    return int(record["returncode"])


if __name__ == "__main__":
    raise SystemExit(main())
