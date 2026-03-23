#!/usr/bin/env python3
"""Scan ADS spec files for stale or soon-expiring freshness dates."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_frontmatter_value(text: str, key: str) -> str | None:
    pattern = rf"^{re.escape(key)}:\s*(.+)$"
    match = re.search(pattern, text[:2000], flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def check_spec(path: Path, today: date, warn_days: int) -> tuple[str | None, str]:
    """Return (message, status) where status is STALE / WARN / OK / SKIP."""
    text = read_text(path)
    stale_after_str = extract_frontmatter_value(text, "stale_after")
    if not stale_after_str:
        return None, "SKIP"
    try:
        stale_date = date.fromisoformat(stale_after_str)
    except ValueError:
        return f"invalid stale_after format: {stale_after_str!r}", "SKIP"
    if today > stale_date:
        delta = (today - stale_date).days
        return f"overdue by {delta} day(s)", "STALE"
    if stale_date - today <= timedelta(days=warn_days):
        delta = (stale_date - today).days
        return f"expires in {delta} day(s)", "WARN"
    return None, "OK"


def scan_directory(directory: Path, today: date, warn_days: int) -> list[tuple[Path, str, str | None]]:
    results = []
    for path in sorted(directory.rglob("*.md")):
        msg, status = check_spec(path, today, warn_days)
        results.append((path, status, msg))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ADS spec files for stale freshness dates.")
    parser.add_argument("--warn-days", type=int, default=30,
                        help="Warn N days before stale_after (default: 30)")
    parser.add_argument("paths", nargs="*",
                        help="Files or directories to scan (default: .ai/specs/)")
    args = parser.parse_args()

    scan_paths = [Path(p) for p in args.paths] if args.paths else [REPO_ROOT / ".ai" / "specs"]
    today = date.today()
    has_stale = False

    for scan_path in scan_paths:
        if scan_path.is_dir():
            results = scan_directory(scan_path, today, args.warn_days)
        elif scan_path.is_file():
            msg, status = check_spec(scan_path, today, args.warn_days)
            results = [(scan_path, status, msg)]
        else:
            print(f"[SKIP] {scan_path} (not found)")
            continue

        for path, status, msg in results:
            try:
                rel = path.relative_to(REPO_ROOT)
            except ValueError:
                rel = path
            if status == "STALE":
                has_stale = True
                print(f"[STALE]  {rel}  ({msg})")
            elif status == "WARN":
                print(f"[WARN]   {rel}  ({msg})")
            elif status == "OK":
                print(f"[OK]     {rel}")
            # SKIP: don't print

    return 1 if has_stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
