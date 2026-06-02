---
name: code-review
description: Generalist codebase audit + code review. Routes by intent (quick PR diff, security-only, pre-release, deep per-dimension, or full tech-DD) across a 13-dimension framework that pays special attention to code essentiality, docs integrity, tests-as-adversaries, and setup replicability. Stack-aware via auto-detection (PHP/Laravel, Python/FastAPI, TypeScript/Node, shell, Docker). Lean by design — loads only the files relevant to the chosen cut.
---

# Code review — Router

This skill produces honest, actionable findings on a codebase. It is
**not** a generic "tell me if this code is good"; it asks specific,
methodical questions across 13 dimensions, picks severity per finding,
and emits triageable output.

It absorbs the best of `anthropics/knowledge-work-plugins/engineering/skills/code-review` (Apache-2.0), `anthropics/claude-code-security-review` (MIT), `VoltAgent/awesome-claude-code-subagents`, `awesome-skills/code-review-skill`, OWASP ASVS L1, and a generalized 13-dimension tech-DD framework forged on a multi-stack production codebase.

## When to invoke

Trigger keywords (any of):
- "review this code/PR/codebase/file"
- "audit my code/project", "tech audit", "tech DD"
- "security review", "security audit", "vuln scan"
- "is this ready to ship?", "release check", "pre-release"
- explicit `/code-review` slash command

## Step 1 — pick the cut

Five cuts, picked by user intent. If the prompt makes intent clear,
pick directly. **Only ask** (via `AskUserQuestion`) when genuinely
ambiguous.

| Cut | When | What loads | Effort |
|---|---|---|---|
| **quick** | "review this file/PR" | `cuts/quick.md` + matching `languages/*.md` | 5-10 min |
| **security** | "security review", "OWASP" | `cuts/security.md` + D4 + D5 + `threat-models/{auth,multi-tenant,secret-mgmt,pii}.md` + matching languages | 30 min |
| **release** | "ready to ship?", "release check" | `cuts/release.md` + scan over all dim, deep on diff since last tag | 30 min |
| **deep** | "deep audit on D5" / "review tests" | `cuts/deep.md` + the listed dimensions | 1–2 h per dim |
| **full** | "full audit", "tech DD" | `cuts/full.md` + every dimension (D1/D2/D3/D13 deep, ⚠️ deep, rest scan) | 5–7 h |

Default fallback when invoked alone with no args: **quick** if a
single file or PR is open, **full** if invoked on a repo root with
no narrower target.

## Step 2 — detect the stack

Auto-detect from repo markers (single shell pass, < 1s):

| Marker | Loads | |
|---|---|---|
| `composer.json` | `languages/php-laravel.md` |
| `pyproject.toml` / `requirements.txt` | `languages/python-fastapi.md` |
| `package.json` | `languages/typescript-node.md` |
| `*.sh` files | `languages/shell.md` |
| `Dockerfile` / `docker-compose.yml` | `languages/docker.md` |

Multiple markers → load multiple files (polyglot repos are normal).
Implementation: `scripts/_detect_stack.py` if precise output needed
in subsequent steps.

## Step 3 — execute per cut + dimension

Each `cuts/<mode>.md` is the **orchestration**: which dimensions in
which order, what to skip, when to call helper scripts. Each
`dimensions/D<N>-*.md` is the **method catalog**: question, concrete
shell snippets, PoC bar, production bar.

Threat-models (`threat-models/*.md`) are cross-cutting patterns
referenced from multiple dimensions — load on demand when a
dimension's method calls one out.

## Step 4 — emit output

Pick the template matching the cut:

| Cut | Template |
|---|---|
| quick | `templates/quick-scan-output.md` |
| security | `templates/security-pass-output.md` |
| release | `templates/triage-and-summary.md` (release section) |
| deep | `templates/triage-and-summary.md` |
| full | `templates/full-audit-report.md` |

Findings get severity 🔴/🟡/🟢 + dimension status ✅/⚠️/❌ per
the schemes below. Phrase per `templates/finding-phrasing.md` —
never alarmist, never patronizing, always with a concrete fix.

For deep + full: also propose **milestones** via
`scripts/_findings_to_milestones.py` so the user can drop them into
their project's devplan / issue tracker.

## The 13 dimensions

Loaded on demand from `dimensions/D<N>-*.md`.

| # | Title | Tag |
|---|---|---|
| D1 | Code essentiality | always-deep |
| D2 | Docs integrity | always-deep |
| D3 | Tests as adversaries | always-deep |
| D4 | Security posture | ⚠️ default-deep |
| D5 | Multi-tenant isolation | ⚠️ default-deep |
| D6 | Operational readiness | scan |
| D7 | Dependency hygiene | scan |
| D8 | Build / CI / dev-loop | ⚠️ default-deep |
| D9 | Data model integrity | scan |
| D10 | Performance & cost baseline | release-only deep |
| D11 | Legal / compliance | scan |
| D12 | Admin surface consistency | scan |
| D13 | Setup replicability | always-deep |

D1, D2, D3, D13 are "always-deep" because they decay invisibly
between audits — nobody notices code rot, doc drift, test
homogeneity, or replicability regression until someone tries to
clone fresh.

## Severity scheme

| Mark | Meaning | Example |
|---|---|---|
| 🔴 | **Ship-blocker.** Fix before next audit pass. | Plain-text secret in git history; cross-tenant data leak; SQLi in admin panel. |
| 🟡 | **Fix soon.** Defensible to leave, real auditor will note. <1 day to fix. | Healthcheck missing; dep 6mo behind; doc claim doesn't match code. |
| 🟢 | **Nice-to-have.** Acceptable, document, move on. | TODO in dev tooling; non-pinned base image tag in dev compose. |

## Status per dimension

| Mark | Meaning |
|---|---|
| ✅ | No 🔴 and ≤2 🟡 |
| ⚠️ | Some 🟡 or one 🔴 with mitigation |
| ❌ | One or more 🔴, no mitigation |

## Per-project extension

If the repo has a `.code-review/extras/` directory, load every
`*.md` file from it AFTER the default dimensions. Use this to add
project-specific dimensions, threat models, or language gotchas
without forking the skill.

Schema in `extensions/README.md` (loaded once if the directory is
present).

## What this skill does NOT do

- It doesn't replace your test runner. It tells you what to test.
- It doesn't auto-fix. It produces findings + suggested milestones.
- It doesn't run paid SaaS (Snyk, FOSSA). It points at OSS
  equivalents (Trivy, Semgrep) and explains why.
- It doesn't drive SOC2 / ISO27001 programs. For shops chasing
  formal compliance, layer a compliance skill on top — this one
  covers the ASVS-L1 baseline that gets you to a real conversation.

## Cadence + onboarding

Operational guidance lives in `playbooks/operations.md` (cadence,
30-min/week starter pack, anti-patterns) and
`playbooks/false-positives.md` (how to dismiss findings).

These are reference docs — load when the user asks "where do we
start?" or "how often should we audit?".

## Output discipline

This skill itself follows the rules it audits: small modular
files, no redundancy (each fact lives in one place + is
cross-referenced), no dead content, every file earns its place.
Updating the skill should be a 5-minute edit, not a hunt across
six near-duplicates.

Sources, licenses, and provenance live in `README.md`.
