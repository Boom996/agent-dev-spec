---
name: spec-syncer
description: Detect which spec documents are impacted by a task or change and generate a spec-delta draft before handoff completion.
---

# Spec Syncer

Use this skill when implementation has started and you need to decide whether the current task should update existing specs, create new specs, or mark the work as not affecting the spec library.

## What it does

- reads task metadata, related paths, and `parent_change_id`
- scans `.ai/specs/` for linked or likely impacted spec files
- suggests `spec_update_status`
- can write `.ai/changes/<change-id>/spec-delta.md`

## When to use it

- before setting handoff to `DONE` or `DONE_WITH_CONCERNS`
- when a task is linked to a change proposal and you need to keep spec history aligned
- when code changed but the team is unsure whether a spec update is required

## Command

```bash
python3 skills/spec-syncer/run.py .ai/tasks/active/<task-id>.md
```

Optional:

```bash
python3 skills/spec-syncer/run.py .ai/tasks/active/<task-id>.md \
  --changed-path backend/src/auth/jwt.py \
  --spec-delta-output .ai/changes/<change-id>/spec-delta.md
```

## Review expectations

- confirm the inferred spec files are the right documents
- adjust `新增 / 修改 / 废弃` before merge if the heuristic picked the wrong change type
- keep `spec-delta.md` in sync with the final code review outcome
