---
name: blocked-triager
description: Decide whether a task can continue, needs more context, is externally blocked, or should be upgraded to a shared-change-request.
---

# Blocked Triager

Use this skill when execution slows down because the next step is unclear, blocked by another actor, or appears to require touching files outside the task's single-writer scope.

## What it does

- reads the task's `locked_paths` and `forbidden_paths`
- inspects the reported blocker summary and candidate target paths
- classifies the situation as:
  - `CONTINUE`
  - `NEEDS_CONTEXT`
  - `BLOCKED`
  - `ESCALATE_SHARED_CHANGE_REQUEST`
- can draft a `shared-change-request` file when escalation is required

## When to use it

- the implementation needs to modify shared files outside current `locked_paths`
- the actor is waiting on approval, external dependency, credentials, or another task
- the actor lacks design/spec context and needs a structured handoff or clarification

## Command

```bash
python3 skills/blocked-triager/run.py .ai/tasks/active/<task-id>.md \
  --summary "Need to change a shared contract outside locked paths" \
  --target-path shared/contracts/approval_event.ts
```

Optional request drafting:

```bash
python3 skills/blocked-triager/run.py .ai/tasks/active/<task-id>.md \
  --summary "Need to modify shared contract" \
  --target-path shared/contracts/approval_event.ts \
  --request-output .ai/requests/SCR-20260324-001.md
```

## Review expectations

- confirm the target paths really fall outside the task scope before sending a request
- tighten the generated `shared-change-request` draft before asking for approval
- use the triage result to decide whether the handoff status should become `NEEDS_CONTEXT` or `BLOCKED`
