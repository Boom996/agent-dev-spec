# tests/test_validate_ads_phase1.py
"""Tests for ADS Phase 1 new validations."""
from __future__ import annotations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).parent))
import validate_ads  # noqa: E402
from conftest import write_file


class TestConstitutionValidation:
    def test_missing_constitution_returns_error(self, tmp_ads_repo):
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert any("constitution.md" in e for e in errors)

    def test_empty_mission_returns_error(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".agent/constitution.md", """\
            # Project Constitution

            ## Mission

            ## Non-Negotiable Principles
            - No breaking changes

            ## Role Definitions
            - Developer: writes code

            ## Agent Governance
            - Humans approve
        """)
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert any("Mission" in e for e in errors)

    def test_valid_constitution_passes(self, tmp_ads_repo):
        write_file(tmp_ads_repo, ".agent/constitution.md", """\
            # Project Constitution

            ## Mission
            Build the best ADS-compatible project.

            ## Non-Negotiable Principles
            - No breaking API changes without migration guide

            ## Tech Stack Principles
            - Python 3.11+

            ## Role Definitions
            - PM: defines changes
            - Developer: implements tasks

            ## Agent Governance
            - Humans approve constitution changes

            ## Approval Hierarchy
            - Constitution: human only
        """)
        errors = validate_ads.validate_constitution(tmp_ads_repo)
        assert errors == []
