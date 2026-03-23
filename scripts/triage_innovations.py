#!/usr/bin/env python3
"""Scan ADS Innovation Briefs for overdue triage decisions."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

TERMINAL_STATUSES = {"promoted", "deferred", "rejected"}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_frontmatter_value(text: str, key: str) -> str | None:
    pattern = rf"^{re.escape(key)}:\s*(.+)$"
    match = re.search(pattern, text[:2000], flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def check_innovation(path: Path, today: date, warn_days: int) -> tuple[str | None, str]:
    """Return (message, status) where status is OVERDUE / SOON / OK."""
    text = read_text(path)
    status = extract_frontmatter_value(text, "status") or ""
    # Terminal statuses need no action
    if status in TERMINAL_STATUSES:
        return None, "OK"
    # Non-proposed (evaluating) also not overdue
    deadline_str = extract_frontmatter_value(text, "triage_deadline")
    if not deadline_str:
        return None, "OK"
    try:
        deadline = date.fromisoformat(deadline_str)
    except ValueError:
        return None, "OK"
    triage_by = extract_frontmatter_value(text, "triage_by") or "unknown"
    if today > deadline:
        delta = (today - deadline).days
        return f"overdue by {delta} day(s), triage_by={triage_by}", "OVERDUE"
    if deadline - today <= timedelta(days=warn_days):
        delta = (deadline - today).days
        return f"in {delta} day(s), triage_by={triage_by}", "SOON"
    return None, "OK"


def scan_directory(directory: Path, today: date, warn_days: int) -> list[tuple[Path, str, str | None]]:
    results = []
    for path in sorted(directory.rglob("*.md")):
        msg, status = check_innovation(path, today, warn_days)
        results.append((path, status, msg))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Triage ADS Innovation Briefs.")
    parser.add_argument("--warn-days", type=int, default=7,
                        help="Warn N days before triage_deadline (default: 7)")
    parser.add_argument("paths", nargs="*",
                        help="Files or directories to scan (default: .ai/innovations/)")
    args = parser.parse_args()

    scan_paths = [Path(p) for p in args.paths] if args.paths else [REPO_ROOT / ".ai" / "innovations"]
    today = date.today()
    has_overdue = False

    for scan_path in scan_paths:
        if not scan_path.exists():
            continue
        if scan_path.is_dir():
            results = scan_directory(scan_path, today, args.warn_days)
        else:
            msg, status = check_innovation(scan_path, today, args.warn_days)
            results = [(scan_path, status, msg)]

        for path, status, msg in results:
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            if status == "OVERDUE":
                has_overdue = True
                print(f"[OVERDUE] {rel}  ({msg})")
            elif status == "SOON":
                print(f"[SOON]    {rel}  ({msg})")
            else:
                print(f"[OK]      {rel}")

    return 1 if has_overdue else 0


if __name__ == "__main__":
    raise SystemExit(main())
