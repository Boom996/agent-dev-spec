#!/usr/bin/env python3
"""Tests for ADS Phase 4 validations."""
from __future__ import annotations
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "tests"))
import validate_ads
from conftest import write_file


VALID_SPEC_CONTENT = """\
    ---
    spec_id: auth-capability
    version: 1.0.0
    status: active
    owned_by: architect
    related_changes:
      - change-20260322-001
    related_tasks:
      - TASK-20260322-001
    updated_at: 2026-03-22
    stale_after: 2026-09-22
    ---

    # Auth 能力（当前系统实际状态）

    ## 能力概述

    JWT 令牌认证能力，提供无状态身份验证。
"""


class TestSpecValidation:
    def test_valid_spec_has_no_errors(self, tmp_ads_repo):
        path = write_file(tmp_ads_repo, "spec.md", VALID_SPEC_CONTENT)
        errors = validate_ads.validate_spec(path)
        assert errors == []

    def test_missing_spec_id_returns_error(self, tmp_ads_repo):
        content = VALID_SPEC_CONTENT.replace("    spec_id: auth-capability\n", "")
        path = write_file(tmp_ads_repo, "spec.md", content)
        errors = validate_ads.validate_spec(path)
        assert any("spec_id" in e for e in errors)

    def test_missing_version_returns_error(self, tmp_ads_repo):
        content = VALID_SPEC_CONTENT.replace("    version: 1.0.0\n", "")
        path = write_file(tmp_ads_repo, "spec.md", content)
        errors = validate_ads.validate_spec(path)
        assert any("version" in e for e in errors)

    def test_missing_status_returns_error(self, tmp_ads_repo):
        content = VALID_SPEC_CONTENT.replace("    status: active\n", "")
        path = write_file(tmp_ads_repo, "spec.md", content)
        errors = validate_ads.validate_spec(path)
        assert any("status" in e for e in errors)

    def test_invalid_status_returns_error(self, tmp_ads_repo):
        content = VALID_SPEC_CONTENT.replace("    status: active", "    status: unknown")
        path = write_file(tmp_ads_repo, "spec.md", content)
        errors = validate_ads.validate_spec(path)
        assert any("status" in e for e in errors)

    def test_invalid_stale_after_format_returns_error(self, tmp_ads_repo):
        content = VALID_SPEC_CONTENT.replace("    stale_after: 2026-09-22", "    stale_after: P7D")
        path = write_file(tmp_ads_repo, "spec.md", content)
        errors = validate_ads.validate_spec(path)
        assert any("stale_after" in e for e in errors)

    def test_missing_owned_by_returns_error(self, tmp_ads_repo):
        content = VALID_SPEC_CONTENT.replace("    owned_by: architect\n", "")
        path = write_file(tmp_ads_repo, "spec.md", content)
        errors = validate_ads.validate_spec(path)
        assert any("owned_by" in e for e in errors)


class TestSpecIntegration:
    def test_valid_example_spec_has_no_errors(self):
        example_path = REPO_ROOT / "examples" / "case-spec.md"
        assert example_path.exists(), f"Example file not found: {example_path}"
        errors = validate_ads.validate_spec(example_path)
        assert errors == [], f"Unexpected errors: {errors}"
