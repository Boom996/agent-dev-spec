---
name: integration-reviewer
description: Turn task and handoff artifacts into a concrete QA PASS or FAIL result with explicit spec-compliance and code-quality findings.
---

# Integration Reviewer

Use this skill when a task is ready for integration or reviewer takeover and you want a structured QA result instead of an ad hoc “looks good”.

## What it does

- validates the handoff structure using ADS rules
- checks whether required `spec_compliance` evidence exists
- checks whether evidence rows show pass/fail/pending signals
- emits a QA PASS or QA FAIL markdown file

## When to use it

- before merging a task marked `review`
- after a developer or agent hands work to Integration
- when you need a repeatable gate for `spec compliance + code quality`

## Command

```bash
python3 skills/integration-reviewer/run.py \
  .ai/tasks/active/<task-id>.md \
  .ai/handoffs/<task-id>.md
```

Optional:

```bash
python3 skills/integration-reviewer/run.py \
  .ai/tasks/active/<task-id>.md \
  .ai/handoffs/<task-id>.md \
  --qa-actor "Integration @ Codex"
```

## Output

- default path: `.ai/qa/<task-id>-pass.md` or `.ai/qa/<task-id>-fail.md`
- can be overridden with `--output`

## Review expectations

- inspect the generated issues before sending a FAIL result back to the developer
- add command excerpts or screenshots if your team expects richer evidence
- keep the QA result linked from the latest handoff when the decision matters for audit
