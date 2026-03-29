#!/usr/bin/env python3
"""Safely self-install ADS into the current project repository."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import ads_adopt
import ads_doctor
import ads_init


REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class GitState:
    repo_root: Path
    current_branch: str
    dirty_paths: list[str]
    has_upstream: bool
    ahead_count: int


@dataclass
class SelfInstallSummary:
    target_root: Path
    initial_branch: str
    branch_name: str
    report: ads_adopt.AdoptionReport
    init_result: ads_init.InitResult
    doctor_findings: list[ads_doctor.Finding]
    validate_ok: bool
    validate_output: str
    dashboard_url: str
    dashboard_started: bool

    def render_summary(self) -> str:
        lines = [
            "## ADS Self-Install Summary",
            "",
            f"- target_repo: `{self.target_root}`",
            f"- initial_branch: `{self.initial_branch}`",
            f"- ads_branch: `{self.branch_name}`",
            f"- validate_ok: `{self.validate_ok}`",
            f"- dashboard_url: `{self.dashboard_url}`",
            "",
            "## Entry Files",
            "- `README_AGENT.md`",
            "- `.agent/identity.json`",
            "- `.ai/START_HERE.md`",
            "- `.agent/docs/guides/project-brief.md`",
            "",
            "## Next Step",
            "- 从 `.ai/tasks/backlog/` 选择第一个真实任务，跑通 task -> evidence -> handoff。",
        ]
        return "\n".join(lines) + "\n"


def run_git(repo_root: Path, args: list[str], check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout.strip()


def detect_git_root(target_root: Path) -> Path:
    try:
        return Path(run_git(target_root, ["rev-parse", "--show-toplevel"])).resolve()
    except RuntimeError as error:
        raise RuntimeError(f"`{target_root}` 不是一个 git 仓库，无法执行 ADS 自接入。") from error


def inspect_git_state(repo_root: Path) -> GitState:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--branch"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    header = status[0] if status else "## HEAD"
    current_branch = run_git(repo_root, ["branch", "--show-current"]) or "HEAD"
    dirty_paths: list[str] = []
    for line in status[1:]:
        if not line.strip():
            continue
        candidate = line[3:].strip()
        if " -> " in candidate:
            candidate = candidate.split(" -> ", 1)[-1].strip()
        dirty_paths.append(candidate)

    has_upstream = "..." in header
    ahead_count = 0
    if "[" in header and "ahead " in header:
        tail = header.split("[", 1)[-1].rstrip("]")
        for part in tail.split(","):
            part = part.strip()
            if part.startswith("ahead "):
                try:
                    ahead_count = int(part.split("ahead ", 1)[1])
                except ValueError:
                    ahead_count = 0
                break

    return GitState(
        repo_root=repo_root,
        current_branch=current_branch,
        dirty_paths=dirty_paths,
        has_upstream=has_upstream,
        ahead_count=ahead_count,
    )


def ensure_clean_worktree(state: GitState) -> None:
    if not state.dirty_paths:
        return
    lines = [
        "检测到当前仓库存在未提交修改。请先提交并优先上传当前工作，再运行 ADS 自接入。",
        "未提交路径：",
    ]
    lines.extend(f"- {path}" for path in state.dirty_paths)
    raise RuntimeError("\n".join(lines))


def branch_exists(repo_root: Path, branch_name: str) -> bool:
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        cwd=repo_root,
        check=False,
    )
    return result.returncode == 0


def build_branch_name(repo_root: Path, prefix: str) -> str:
    base = f"{prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    candidate = base
    suffix = 2
    while branch_exists(repo_root, candidate):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def create_trial_branch(repo_root: Path, prefix: str) -> str:
    branch_name = build_branch_name(repo_root, prefix)
    run_git(repo_root, ["checkout", "-b", branch_name])
    return branch_name


def run_validate_script(target_root: Path) -> str:
    validate_path = target_root / "scripts" / "validate_ads.py"
    result = subprocess.run(
        [sys.executable, str(validate_path)],
        cwd=target_root,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise RuntimeError(f"validate_ads failed for `{target_root}`:\n{output}")
    return output


def launch_dashboard(target_root: Path, host: str, port: int, open_browser: bool) -> tuple[str, bool]:
    dashboard_path = target_root / "scripts" / "ads_dashboard.py"
    url = f"http://{host}:{port}"
    process = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            str(dashboard_path),
            "--repo-root",
            str(target_root),
            "--host",
            host,
            "--port",
            str(port),
        ],
        cwd=target_root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(0.3)
    running = process.poll() is None
    if running and open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    return url, running


def perform_self_install(
    target_root: Path,
    ads_source_root: Path = REPO_ROOT,
    project_name: str | None = None,
    branch_prefix: str = "chore/ads-adoption-trial",
    dashboard_host: str = "127.0.0.1",
    dashboard_port: int = 8765,
    start_dashboard_process: bool = True,
    start_dashboard: bool | None = None,
    open_browser: bool = True,
) -> SelfInstallSummary:
    if start_dashboard is not None:
        start_dashboard_process = start_dashboard
    source_root = ads_source_root.resolve()
    if source_root != REPO_ROOT:
        raise RuntimeError(f"`ads_source_root` 必须指向当前 ADS 仓库：`{REPO_ROOT}`")

    repo_root = detect_git_root(target_root.resolve())
    git_state = inspect_git_state(repo_root)
    ensure_clean_worktree(git_state)

    branch_name = create_trial_branch(repo_root, branch_prefix)
    report, init_result = ads_adopt.apply_adoption(repo_root, project_name=project_name)
    doctor_findings = ads_doctor.run_doctor(repo_root)
    if doctor_findings:
        raise RuntimeError(ads_doctor.render_report(repo_root, doctor_findings))

    validate_output = run_validate_script(repo_root)
    dashboard_url = f"http://{dashboard_host}:{dashboard_port}"
    dashboard_started = False
    if start_dashboard_process:
        dashboard_url, dashboard_started = launch_dashboard(repo_root, dashboard_host, dashboard_port, open_browser)

    return SelfInstallSummary(
        target_root=repo_root,
        initial_branch=git_state.current_branch,
        branch_name=branch_name,
        report=report,
        init_result=init_result,
        doctor_findings=doctor_findings,
        validate_ok=True,
        validate_output=validate_output,
        dashboard_url=dashboard_url,
        dashboard_started=dashboard_started,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-repo", default=".", help="target repository path; defaults to the current working tree")
    parser.add_argument("--project-name", help="optional project name override")
    parser.add_argument("--branch-prefix", default="chore/ads-adoption-trial", help="prefix for the temporary ADS adoption branch")
    parser.add_argument("--dashboard-host", default="127.0.0.1", help="host for the ADS dashboard")
    parser.add_argument("--dashboard-port", type=int, default=8765, help="port for the ADS dashboard")
    parser.add_argument("--no-open-dashboard", action="store_true", help="do not attempt to open the browser after starting the dashboard")
    parser.add_argument("--no-start-dashboard", action="store_true", help="do not start the dashboard server after installation")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        summary = perform_self_install(
            target_root=Path(args.target_repo),
            project_name=args.project_name,
            branch_prefix=args.branch_prefix,
            dashboard_host=args.dashboard_host,
            dashboard_port=args.dashboard_port,
            start_dashboard_process=not args.no_start_dashboard,
            open_browser=not args.no_open_dashboard,
        )
    except RuntimeError as error:
        print(f"[ads_self_install] {error}")
        return 2

    print("[ads_self_install] 建议先确认当前主分支的最新提交已经上传；ADS 已在新分支内完成接入。")
    print(ads_adopt.render_report_markdown(summary.report))
    ads_init.print_summary(summary.init_result, summary.target_root)
    print(ads_adopt.render_apply_summary(summary.report))
    print(summary.render_summary())
    if summary.dashboard_started:
        print(f"[ads_self_install] dashboard started at {summary.dashboard_url}")
    else:
        print(f"[ads_self_install] dashboard url: {summary.dashboard_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
