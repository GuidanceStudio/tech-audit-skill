---
name: code-audit
description: Methodical codebase audit across a 13-dimension tech-DD framework. Routes by intent — security pass, release check, deep per-dimension, full tech-DD, or explicit quick scan. Stack-aware (PHP/Laravel, Python/FastAPI, TS/Node, shell, Docker). Use for "audit", "tech DD", "security review", "ready to ship?" — NOT for routine PR diff review.
---

# Code audit — Router

Honest, actionable findings on a codebase: methodical questions across
13 dimensions, calibrated severity per finding, triageable output.

## When to invoke

- "audit my code/project/codebase", "tech audit", "tech DD"
- "security review", "security audit", "vuln scan"
- "is this ready to ship?", "release check", "pre-release"
- explicit `/code-audit`

Routine "review this PR/file" belongs to the builtin code-review
skill. The `quick` cut exists for explicit narrow scans only.

## Step 1 — pick the cut

If intent is clear, pick directly; ask only when genuinely ambiguous.

| Cut | When | Loads |
|---|---|---|
| **quick** | explicit narrow scan of a file/PR/diff | `cuts/quick.md` + languages |
| **security** | "security review", "OWASP" | `cuts/security.md` (D4+D5+threat-models) |
| **release** | "ready to ship?", release tag | `cuts/release.md` |
| **deep** | "deep audit on X", named dimensions | `cuts/deep.md` + those dimensions |
| **full** | "full audit", "tech DD" | `cuts/full.md` + every dimension |

No-args fallback: **quick** on a narrow open target, **full** on a
repo root.

## Step 2 — detect the stack

Markers are searched recursively (depth ≤3, dependency dirs pruned —
see `routing/detect-stack.md`; script: `scripts/_detect_stack.py`):
`composer.json` → `languages/php-laravel.md` · python manifests →
`languages/python-fastapi.md` · `package.json` →
`languages/typescript-node.md` · `*.sh` → `languages/shell.md` ·
Dockerfile/compose → `languages/docker.md`. Load all that match.

## Step 3 — execute, Step 4 — emit

Each `cuts/<mode>.md` is the orchestration; each `dimensions/D<N>-*.md`
is the method catalog; `threat-models/*.md` load on demand when a
method calls one out. Output templates per cut: quick →
`templates/quick-scan-output.md`, security →
`templates/security-pass-output.md`, release/deep →
`templates/triage-and-summary.md`, full →
`templates/full-audit-report.md`. Phrase findings per
`templates/finding-phrasing.md`. For deep + full, propose milestones
via `scripts/_findings_to_milestones.py`.

## Dimension registry (single source — other files cite IDs/tags, never re-list)

| # | Title | Tag | Topics |
|---|---|---|---|
| D1 | Code essentiality | always-deep | code quality, readability, dead code, over-abstraction |
| D2 | Docs integrity | always-deep | docs drift, arch docs, README accuracy |
| D3 | Tests as adversaries | always-deep | tests, coverage, regression, flake |
| D4 | Security posture | default-deep | security, vuln, OWASP |
| D5 | Multi-tenant isolation | default-deep | tenant, isolation, RLS, cross-tenant |
| D6 | Operational readiness | scan | ops, healthcheck, runbook, backup |
| D7 | Dependency hygiene | scan | deps, licenses, CVE |
| D8 | Build / CI / dev-loop | default-deep | CI, build, linter, pre-commit |
| D9 | Data model integrity | scan | schema, migrations, audit log |
| D10 | Performance & cost | release-only | perf, latency, cost |
| D11 | Legal / compliance | scan | GDPR, privacy, legal |
| D12 | Admin surface | scan | admin UI, Filament, empty states |
| D13 | Setup replicability | always-deep | setup, fresh clone, bootstrap |
| D14 | Correctness & robustness | always-deep | bugs, correctness, races, idempotency, error paths |

The 13-dimension framing in prose is historical; D14 was added in v0.2.

**always-deep** dims decay invisibly between audits — they run deep in
every cut that touches them. **default-deep** run deep when the
product has the matching surface. **scan** dims go deep only when a 🔴
surfaces. **release-only** runs when a tag is being cut.

## Severity and status

🔴 ship-blocker (fix before next pass) · 🟡 fix soon (<1 day,
defensible to defer) · 🟢 nice-to-have. Per dimension: ✅ no 🔴 and
≤2 🟡 · ⚠️ some 🟡 or a mitigated 🔴 · ❌ unmitigated 🔴.

## Execution discipline (applies to every cut)

- Send tool output to a file (`--format json -o ...`), then summarize
  counts + top findings — never dump raw scanner output into context.
- Sample grep/heatmap-first: deep-read only the top-N candidate files
  per method, never whole-repo reads.
- Keep intermediate notes terse (structured rows, not prose); prose
  belongs in the final report only.
- Cite `file:line`; paste code only when the hunk itself is the finding.

## Per-project extension

If the target repo has `.code-audit/extras/`, load every `*.md` in it
AFTER the default dimensions (schema: `extensions/README.md`).

Operational cadence, starter pack, and false-positive dismissal live in
`playbooks/operations.md` and `playbooks/false-positives.md` — load on
request.
