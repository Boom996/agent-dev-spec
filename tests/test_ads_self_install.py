#!/usr/bin/env python3
"""Tests for ADS self-install flow."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ads_self_install


def write_file(base: Path, rel: str, content: str) -> Path:
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def build_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "TargetProject"
    repo.mkdir(parents=True)
    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "ADS Test")
    write_file(
        repo,
        "docs/product/project-guide.md",
        "# Target Project\n\n> 一个用于验证 ADS 自接入流程的示例项目\n",
    )
    write_file(
        repo,
        "app/package.json",
        json.dumps(
            {
                "name": "target-project",
                "private": True,
                "scripts": {
                    "test": "vitest run",
                    "build": "vite build",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "init")
    return repo


class TestAdsSelfInstall:
    def test_perform_self_install_blocks_dirty_repo(self, tmp_path):
        target_root = build_git_repo(tmp_path)
        write_file(target_root, "README.md", "dirty change\n")

        try:
            ads_self_install.perform_self_install(
                target_root=target_root,
                ads_source_root=REPO_ROOT,
                start_dashboard=False,
                open_browser=False,
            )
        except RuntimeError as error:
            message = str(error)
        else:
            raise AssertionError("expected perform_self_install to fail on dirty repo")

        assert "先提交并优先上传" in message
        assert "README.md" in message

    def test_perform_self_install_creates_trial_branch_and_bootstraps_ads(self, tmp_path):
        target_root = build_git_repo(tmp_path)

        summary = ads_self_install.perform_self_install(
            target_root=target_root,
            ads_source_root=REPO_ROOT,
            start_dashboard=False,
            open_browser=False,
        )

        assert summary.branch_name.startswith("chore/ads-adoption-trial")
        assert summary.initial_branch == "main"
        assert run_git(target_root, "branch", "--show-current") == summary.branch_name
        assert (target_root / "README_AGENT.md").exists()
        assert (target_root / ".agent" / "identity.json").exists()
        assert (target_root / ".ai" / "START_HERE.md").exists()

    def test_perform_self_install_runs_validation_and_returns_dashboard_url(self, tmp_path):
        target_root = build_git_repo(tmp_path)

        summary = ads_self_install.perform_self_install(
            target_root=target_root,
            ads_source_root=REPO_ROOT,
            start_dashboard=False,
            open_browser=False,
            dashboard_port=8876,
        )

        assert summary.validate_ok is True
        assert summary.doctor_findings == []
        assert summary.dashboard_url == "http://127.0.0.1:8876"
        assert "README_AGENT.md" in summary.render_summary()
