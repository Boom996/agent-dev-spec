#!/usr/bin/env python3
"""Tests for ADS evidence capture."""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_evidence_capture


class TestAdsEvidenceCapture:
    def test_capture_evidence_writes_artifact_and_pass_row(self, tmp_path):
        artifact_path = tmp_path / "artifacts" / "test.log"
        command = f"{sys.executable} -c \"print('ok')\""

        record = ads_evidence_capture.capture_evidence(
            item="test",
            command=command,
            repo_root=tmp_path,
            executed_by="Backend @ Codex",
            artifact_path=artifact_path,
        )

        row = ads_evidence_capture.render_markdown_row(record, repo_root=tmp_path)

        assert record["result"] == "pass"
        assert artifact_path.exists()
        assert "ok" in artifact_path.read_text(encoding="utf-8")
        assert "| `test` | Backend @ Codex |" in row
        assert "`artifacts/test.log`" in row

    def test_capture_evidence_returns_fail_for_failing_command(self, tmp_path):
        command = f"{sys.executable} -c \"import sys; sys.exit(3)\""

        record = ads_evidence_capture.capture_evidence(
            item="lint",
            command=command,
            repo_root=tmp_path,
        )

        assert record["result"] == "fail"
        assert record["returncode"] == 3
