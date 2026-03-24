---
name: innovation-capture
description: Convert in-flight implementation ideas into a structured Innovation Brief without blocking the current task.
---

# Innovation Capture

Use this skill when a useful idea appears during implementation or review, but the idea should not interrupt the current task or get lost in chat history.

## What it does

- reads the current task context
- derives `context_task` and `context_change`
- creates a compliant `Innovation Brief`
- writes the result to `.ai/innovations/`

## When to use it

- you find an architectural improvement during delivery work
- you discover a performance, governance, or workflow improvement that should be evaluated later
- you want to preserve an idea without turning it into an immediate change proposal

## Command

```bash
python3 skills/innovation-capture/run.py \
  .ai/tasks/active/<task-id>.md \
  --title "Use Redis for shared cache coordination" \
  --summary "Current cache is process-local..." \
  --trigger "Observed cache misses during multi-replica load test." \
  --judgement "Medium implementation cost, clear scalability value."
```

## Output

- default destination: `.ai/innovations/INV-YYYYMMDD-XXX.md`
- status defaults to `proposed`
- urgency defaults to `medium`

## Review expectations

- keep the brief lightweight; do not over-design it into a change proposal
- if urgency is high, reference the innovation in the handoff and let triage decide whether to re-plan
- move promoted ideas into a formal change proposal instead of expanding the innovation brief forever
