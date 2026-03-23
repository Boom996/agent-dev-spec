#!/usr/bin/env python3
"""Tests for check_stale_specs.py."""
from __future__ import annotations
import sys
import textwrap
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import check_stale_specs


def make_spec(tmp_path: Path, stale_after: str, spec_id: str = "test-cap") -> Path:
    content = f"""\
---
spec_id: {spec_id}
version: 1.0.0
status: active
owned_by: architect
updated_at: 2026-03-22
stale_after: {stale_after}
---

# Test capability
"""
    path = tmp_path / f"{spec_id}.md"
    path.write_text(content, encoding="utf-8")
    return path


class TestCheckStaleSpecs:
    def test_stale_spec_detected(self, tmp_path):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        path = make_spec(tmp_path, stale_after=yesterday)
        result = check_stale_specs.check_spec(path, date.today(), warn_days=30)
        assert result[1] == "STALE"

    def test_ok_spec_not_flagged(self, tmp_path):
        far_future = (date.today() + timedelta(days=180)).isoformat()
        path = make_spec(tmp_path, stale_after=far_future)
        result = check_stale_specs.check_spec(path, date.today(), warn_days=30)
        assert result[1] == "OK"

    def test_warn_within_warn_days(self, tmp_path):
        soon = (date.today() + timedelta(days=20)).isoformat()
        path = make_spec(tmp_path, stale_after=soon)
        result = check_stale_specs.check_spec(path, date.today(), warn_days=30)
        assert result[1] == "WARN"

    def test_missing_stale_after_returns_skip(self, tmp_path):
        content = """\
---
spec_id: no-stale
version: 1.0.0
status: active
owned_by: architect
updated_at: 2026-03-22
---

# No stale_after
"""
        path = tmp_path / "no-stale.md"
        path.write_text(content, encoding="utf-8")
        result = check_stale_specs.check_spec(path, date.today(), warn_days=30)
        assert result[1] == "SKIP"

    def test_scan_directory_returns_results(self, tmp_path):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        make_spec(tmp_path, stale_after=yesterday, spec_id="stale-cap")
        far_future = (date.today() + timedelta(days=180)).isoformat()
        make_spec(tmp_path, stale_after=far_future, spec_id="ok-cap")
        results = check_stale_specs.scan_directory(tmp_path, date.today(), warn_days=30)
        statuses = [r[1] for r in results]
        assert "STALE" in statuses
        assert "OK" in statuses
