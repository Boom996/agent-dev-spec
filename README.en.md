# Agent Development Specification

[中文](README.md) | [English](README.en.md)

ADS is a **repo-native collaboration specification and tooling kit for real software projects with agents**. It is not about writing a better one-off prompt. It is about making multi-human, multi-agent, multi-client development recoverable, auditable, and reusable inside the repository itself.

Public entry points are intentionally focused on product-facing docs:

- `README.en.md` / `README.md`
- [`docs/README.md`](docs/README.md)
- [`docs/guides/adoption-playbook.md`](docs/guides/adoption-playbook.md)
- [`docs/guides/client-adapters/README.md`](docs/guides/client-adapters/README.md)

ADS is useful if your team:

- already uses Codex, Claude Code, Cursor, OpenCode, or custom agents, but collaboration still depends too much on chat history
- wants to adopt agent workflows inside an existing project rather than building a separate platform
- wants one shared task, handoff, tool registration, and recovery layer across clients

<!-- ADS:START -->
## ADS Agent Quick Start

> If you are opening this repository for the first time, treat this block as the only required starting point.

1. Read the root `README` first to understand ADS, adoption flow, and safety rules.
2. If you want to install ADS into another project, run `python3 /path/to/agent-dev-spec/scripts/ads_self_install.py` from the target project root.
3. Before adoption, ask the author to commit and preferably push current local work, then create a new git branch for the ADS trial.
4. After adoption, read the target repository's `ADS Agent Quick Start`, then `.ai/START_HERE.md`, `.agent/constitution.md`, and `.agent/docs/guides/project-brief.md`.
5. Review `.agent/docs/guides/ads-install-report.md` to confirm what ADS generated and what to do next.
6. Before real work starts, run `python3 scripts/ads_explain.py`, `python3 scripts/ads_doctor.py`, `python3 scripts/validate_ads.py`, and optionally `python3 scripts/ads_dashboard.py`.

### Entry Docs

- `README.en.md`
- `docs/guides/adoption-playbook.md`
- `docs/guides/client-adapters/codex-cli.md`
- `docs/00-overview.md`
<!-- ADS:END -->

## What ADS Solves

Common failure modes in agent development:

- the session ends and context disappears with it
- multiple agents edit overlapping files without clear boundaries
- “done” is only stated in chat, with no evidence, QA, or recovery trail
- capabilities live inside one client config and do not transfer to another

ADS turns that into a small but executable repo contract:

- root `README` as the single repository bootstrap entry
- `.ai/` as the collaboration workspace
- `.agent/` as project metadata and governance mirror
- `tools/toolset.json` plus `skills/*/manifest.json` as a shared tool registry
- task / handoff / request / qa / memory / spec as the protocol layer
- doctor / resume / handoff draft / evidence capture / MCP server as the automation layer
- optional evidence telemetry through `duration_ms`, `cost_usd`, and `retry_count`

## What You Get

- `scripts/ads_init.py`: bootstrap ADS into any repository
- `scripts/ads_adopt.py`: analyze an existing project, then adopt ADS with a project-aware report
- `scripts/ads_self_install.py`: a safer high-level self-install path that checks git state, creates a branch, applies ADS, validates, and opens the dashboard
- `scripts/ads_doctor.py` and `scripts/validate_ads.py`: structural and protocol validation
- `scripts/ads_explain.py`: a first-run brief for humans and agents
- `scripts/ads_dashboard.py`: a local web dashboard for project overview, current focus, risks, and health
- `ads_resume`, `ads_handoff_draft`, and `ads_evidence_capture`: continuity helpers
- blocked / needs-context escalation flow through `ads_escalation_draft` and `.ai/escalations/`
- reusable skill structure for decomposition, handoff writing, triage, review, and innovation capture

## 10-Minute Adoption Path

If you are an agent working in another repository and you only received the ADS git link, start from this README and then run from the target project root:

```bash
python3 /path/to/agent-dev-spec/scripts/ads_self_install.py
```

By default this flow:

- inspects the current git workspace
- stops when local changes are uncommitted and tells the author to commit and push first
- creates a dedicated ADS adoption branch
- uses `lean` adoption by default for mature projects, keeping only the high-frequency collaboration layer in the host repo
- runs adopt -> apply -> doctor -> validate
- starts and opens the ADS dashboard after a successful install

1. For a new or clean repository, run `python3 scripts/ads_init.py /path/to/your-project`.
2. For an existing project, run `python3 scripts/ads_adopt.py /path/to/your-project` first, then use `--apply` once the trial report looks correct.
3. Ask all collaborators to read the target repo's root `README` and its `ADS Agent Quick Start` block.
4. Update `.agent/identity.json`, `.agent/constitution.md`, and `.ai/START_HERE.md` for the host project.
5. Validate the workflow with one real task through task -> evidence -> handoff -> QA.
6. Run `python3 scripts/ads_explain.py` in the host repo.
7. Open the local dashboard with `python3 scripts/ads_dashboard.py` if needed.
8. Run `python3 scripts/ads_doctor.py` and `python3 scripts/validate_ads.py`.

For mature repositories, `--adoption-profile auto` now prefers `lean`:

- `auto`: choose `lean` for mature brownfield projects and `full` for protocol-first or greenfield repos
- `lean`: keep only daily-use ADS documents in the host repo
- `full`: also copy the full local ADS reference mirror into the host repo

## Lean Adoption

For projects that already have product specs, planning flows, and handoff materials, ADS should behave like a **minimal collaboration control plane**, not like a second documentation system.

That is why lean adoption exists:

- reduce unnecessary `.agent/docs/` mirror generation in mature projects
- keep host-project docs as the primary source of context
- separate high-frequency operational docs from low-frequency ADS reference docs
- reduce onboarding length, cognitive load, and context/token waste for day-to-day implementation work

## Repository Layout

```text
agent-dev-spec/
├── README.md
├── README.en.md
├── docs/
├── templates/
├── .agent/
├── .ai/
├── tools/
├── skills/
├── scripts/
└── examples/
```

Key parts:

- [`docs/`](docs/) for protocol and adoption docs
- [`templates/`](templates/) for task, handoff, request, QA, and memory templates
- [`scripts/`](scripts/) for bootstrap, validation, continuity, evidence, and MCP automation
- [`skills/`](skills/) for reusable operational skills
- [`examples/`](examples/) for end-to-end examples

## Recommended Reading

- `ADS Agent Quick Start` in the root README
- [`docs/00-overview.md`](docs/00-overview.md)
- [`docs/01-principles.md`](docs/01-principles.md)
- [`docs/04-handoff-and-tasks.md`](docs/04-handoff-and-tasks.md)
- [`docs/08-harness-landscape-and-recovery.md`](docs/08-harness-landscape-and-recovery.md)
- [`docs/guides/adoption-playbook.md`](docs/guides/adoption-playbook.md)
- [`docs/guides/client-adapters/README.md`](docs/guides/client-adapters/README.md)
- [`examples/README.md`](examples/README.md)

## Current Product Maturity

ADS currently provides:

- protocol validation for task / handoff / request / qa / memory / spec / toolset
- automation tooling for doctor, resume, handoff draft, escalation draft, evidence capture, tool sync, and MCP server
- first-run briefing through `ads_explain`
- local visualization through `ads_dashboard`
- evidence observability with cost / latency / retry telemetry
- reusable skills for decomposition, handoff writing, triage, review, and innovation capture
- client adapters for Claude Code, Codex CLI, Cursor, and OpenCode
- examples, context packs, knowledge packs, and recovery-oriented patterns

## Start Here

- Adopt ADS into an existing project: [`docs/guides/adoption-playbook.md`](docs/guides/adoption-playbook.md)
- Browse documentation: [`docs/README.md`](docs/README.md)
- Review client adapters: [`docs/guides/client-adapters/README.md`](docs/guides/client-adapters/README.md)
- Explore examples: [`examples/README.md`](examples/README.md)

## License and Commercial Use

This repository is published as source-available and non-commercial. It is available for learning, evaluation, research, and non-commercial practice, but it is **not** an OSI open-source licensed project.

- Code is released under [`LICENSE`](LICENSE): `PolyForm Noncommercial 1.0.0`
- Commercial use, commercial integration, commercial distribution, paid training, or paid services based on this repository require a separate written commercial license
- Commercial licensing contact: `17764546751@163.com`
- See [`COMMERCIAL_LICENSE.md`](COMMERCIAL_LICENSE.md) for details
