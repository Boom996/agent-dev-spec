---
name: task-decomposer
description: Generate ADS task drafts from a change proposal when a large change needs to be split into role-oriented tasks with clear path ownership.
---

# Task Decomposer

Use this skill when a change proposal is approved or being refined and the next step is to turn it into executable ADS tasks instead of keeping the work as one vague blob.

## What it does

- reads a change proposal
- groups impact paths by likely owner role
- emits one ADS task draft per role
- pre-fills `parent_change_id`, `trace_id`, `approval_owner`, related paths, and baseline acceptance criteria

## When to use it

- a single change touches frontend + backend + spec + integration paths
- you want to enforce single-writer boundaries early
- you want a fast starting point before humans refine the final task wording

## Command

```bash
python3 skills/task-decomposer/run.py .ai/changes/<change-id>/proposal.md
```

Optional:

```bash
python3 skills/task-decomposer/run.py .ai/changes/<change-id>/proposal.md \
  --output-dir .ai/tasks/generated/<change-id> \
  --force
```

## Output

- one markdown file per inferred owner role
- default destination: `.ai/tasks/generated/<change-id>/`

## Review expectations

- verify the inferred owner roles make sense
- tighten acceptance criteria before execution starts
- confirm generated `locked_paths` do not overlap in a risky way
