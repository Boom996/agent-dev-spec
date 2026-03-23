---
name: handoff-writer
description: Generate a real ADS handoff file from task metadata and current repo state when an agent or developer needs to pause, transfer, or request review.
---

# Handoff Writer

Use this skill when the work is moving from one actor to another and you want a structured ADS handoff file instead of an ad hoc chat summary.

## What it does

- reads the current task
- inspects the git worktree
- builds a handoff draft using ADS metadata conventions
- writes the result to `.ai/handoffs/<task-id>.md` by default

## When to use it

- before ending a session
- before asking Integration or Reviewer to take over
- when converting an in-progress task into `pending_resume`, `DONE`, `DONE_WITH_CONCERNS`, or `BLOCKED`

## Command

```bash
python3 skills/handoff-writer/run.py .ai/tasks/active/<task-id>.md \
  --from-actor "AgentImplementer @ Codex"
```

Optional:

```bash
python3 skills/handoff-writer/run.py .ai/tasks/active/<task-id>.md \
  --status BLOCKED \
  --blocked-reason "Need API decision"
```

## Output

- default file: `.ai/handoffs/<task-id>.md`
- can be overridden with `--output`

## Review expectations

- fill in any missing evidence timestamps and final results
- rewrite `当前状态` if the auto-generated summary is too generic
- confirm `相关路径` reflects the actual diff you want the next actor to inspect
