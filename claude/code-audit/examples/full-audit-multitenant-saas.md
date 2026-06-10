# Example — full audit of a multi-tenant SaaS

Synthetic report. Stack: PHP/Laravel + Python/FastAPI + TS/Node + Postgres + Docker-compose. Multi-tenant (one VPS per tenant model). PoC heading to BETA. Reference for what the output of `cuts/full.md` looks like.

---

# Tech audit — 2026-06-15

**Auditor**: Claude code-audit skill under team direction
**Scope**: full 13-dim
**Repo HEAD at audit time**: `abc1234f`
**Previous audit**: `docs/internal/tech-audit-2026-03-15.md`

## Executive summary

- 🔴 **Top risk**: tenant context is not re-applied on asyncpg connection re-use in the FastAPI gateway. The fix is mechanical (5 lines) but the bug is currently shipping.
- 🟢 **Top strength**: D13 (setup replicability) is exemplary — fresh-clone → working stack in 4 minutes with only `.env` edits.
- 🟡 **Biggest gap**: D8 (CI) covers PHP only. Python + TypeScript paths have no automated checks; everything relies on developer discipline.

## Status overview

| Dim | Title | Status | 🔴 | 🟡 | 🟢 |
|---|---|---|---|---|---|
| D1 | Code essentiality | ⚠️ | 0 | 4 | 12 |
| D2 | Docs integrity | ✅ | 0 | 2 | 8 |
| D3 | Tests as adversaries | ⚠️ | 0 | 3 | 5 |
| D4 | Security posture | ⚠️ | 0 | 2 | 9 |
| D5 | Multi-tenant isolation | ❌ | 1 | 1 | 4 |
| D6 | Operational readiness | ⚠️ | 0 | 3 | 7 |
| D7 | Dependency hygiene | ✅ | 0 | 1 | 6 |
| D8 | Build / CI / dev-loop | ❌ | 1 | 2 | 3 |
| D9 | Data model integrity | ✅ | 0 | 1 | 5 |
| D10 | Performance & cost | ✅ | 0 | 0 | 4 |
| D11 | Legal / compliance | ⚠️ | 0 | 2 | 5 |
| D12 | Admin surface consistency | ⚠️ | 0 | 3 | 6 |
| D13 | Setup replicability | ✅ | 0 | 0 | 7 |
| **Total** | | | **2** | **24** | **81** |

## Trend vs 2026-03-15

| | This pass | Last pass | Delta |
|---|---|---|---|
| 🔴 | 2 | 4 | ▼ improved |
| 🟡 | 24 | 31 | ▼ improved |

Closed since last time:
- ✅ Two D4 🔴 (secret in git history, container running as root) — both shipped fixes.

New regressions:
- 🔴 D5 — async-pool tenant context. Introduced by the FastAPI gateway refactor (PR #189).
- 🔴 D8 — TS service has no CI; introduced when the Node bridge was extracted to its own repo.

## D1 — Code essentiality

**Status**: ⚠️ · 4 🟡 findings worth addressing within 2 weeks.

### Findings

- 🟡 `app/Services/AgentTemplateService.php:1-184` — 184-line service class, 12 public methods. Read-once-and-explain test fails — too many concerns. _Suggested fix_: extract `AgentTemplateCloning` into its own service; keep `AgentTemplateService` focused on CRUD.

- 🟡 `app/Services/AbstractGatewayClient.php:1-67` — single concrete implementation (`CeraseGatewayClient`); abstract class adds indirection without test seam. _Suggested fix_: inline the abstract class.

- 🟡 `agent-runtime/recipes/recipes.yaml` — clone density via jscpd flagged 4 recipes sharing the same 80-token shell template. _Suggested fix_: extract a template macro or move to a `recipes.d/_includes.yaml`.

- 🟡 `app/Concerns/` directory contains 2 traits, both used by ≤2 classes. _Suggested fix_: inline.

## D5 — Multi-tenant isolation

**Status**: ❌ · 1 🔴 (release-blocking).

### Findings

#### 🔴 `gateway/src/cerase_gateway/db_pool.py:42` — async-pool tenant context not re-applied on connection re-use.

- **What**: `tenant_id` is set on a connection at startup; subsequent requests reusing the same pooled connection inherit a stale tenant context.
- **Why it matters**: A request from tenant A can see rows belonging to tenant B if connection re-use happens to align that way. This is the canonical async-pool tenant-leak bug (see `threat-models/multi-tenant-isolation.md` pattern 2).
- **Suggested fix**: use `SET LOCAL` inside a transaction scope. ~5 lines.
- **Threat model**: `threat-models/multi-tenant-isolation.md` § Pattern 2.

- 🟡 `app/Models/AgentTemplate.php` — `withoutGlobalScopes()` in `getSharedTemplates()` lacks a justification comment. _Suggested fix_: add comment + a pgTAP assertion that this path can't read another tenant's templates.

## D8 — Build / CI / dev-loop

**Status**: ❌ · 1 🔴.

### Findings

#### 🔴 No CI for the TypeScript service.

- **What**: `cerase-acp` repo has no `.github/workflows/` running tests, lint, or type checks.
- **Why it matters**: TS changes ship to production without automated gates. The PHP + Python services have CI; the TS gap is asymmetric and surprising.
- **Suggested fix**: Add `templates/ci-github-actions.yml` § lint-typescript to the cerase-acp repo. ~2 h.

- 🟡 `cerase-core/.github/workflows/audit.yml` runs only PHP linters; Python ruff + mypy not invoked.
- 🟡 No Semgrep stage in any repo's CI.

## D13 — Setup replicability

**Status**: ✅ · 7 🟢 findings (nice-to-have polish).

Walkthrough: wiped workspace, fresh clone, `cp .env.example .env`, edited LLM API key + Discord bot token, ran `./cli.sh ghcr-login`, ran `./cli.sh stack-up`. 4 min 12 s to all-healthy. No manual `docker exec` / `chown` / `psql` steps required. Doctor exits 0.

This is the strongest dimension in the audit. Cluster-internal secrets all auto-bootstrap (the four `CERASE_*_SECRET` placeholders from a previous audit cycle have been removed from `.env.example` and replaced with the named-volume bootstrap pattern). 

## Triage — proposed follow-up milestones

| Finding | Suggested milestone | Devplan | Effort |
|---|---|---|---|
| 🔴 D5-1 | SEC-7: `SET LOCAL app.current_tenant` per request in async pool | poc.md | 30 min |
| 🔴 D8-1 | CI-3: GitHub Actions for cerase-acp (lint + tsc + test) | poc.md | 2 h |
| 🟡 D1-1 | OPT-50: extract `AgentTemplateCloning` from `AgentTemplateService` | v0.x.md | 4 h |
| 🟡 D8-2 | CI-4: add ruff + mypy + Semgrep to cerase-core CI | poc.md | 2 h |
| 🟡 D12-3 | UX-N: notification surface for failed Open Notebook syncs | poc.md | 2 h |

(... 14 more 🟡 entries listed in full report ...)

---

This example shows the shape and tone. Adapt to the actual repo's stack, severity profile, and devplan naming conventions.
