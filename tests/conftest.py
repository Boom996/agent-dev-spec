# tests/conftest.py
"""Shared test fixtures for ADS Phase 1 validation tests."""
from __future__ import annotations
import textwrap
from pathlib import Path
import pytest


@pytest.fixture
def tmp_ads_repo(tmp_path: Path) -> Path:
    """Create a minimal ADS repo structure in a temp directory."""
    (tmp_path / ".agent").mkdir()
    (tmp_path / ".ai" / "tasks" / "active").mkdir(parents=True)
    (tmp_path / ".ai" / "handoffs").mkdir(parents=True)
    return tmp_path


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path
