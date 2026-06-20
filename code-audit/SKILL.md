---
name: code-audit
description: Methodical codebase audit across a multi-dimension tech-DD framework. Routes by intent — security pass, release check, deep per-dimension, full tech-DD, or explicit quick scan. Stack-aware (PHP/Laravel, Python/FastAPI, TS/Node, shell, Docker). Use for "audit", "tech DD", "security review", "ready to ship?" — NOT for routine PR diff review.
---

# Code audit — Router

Honest, actionable findings on a codebase: methodical questions across
a multi-dimension framework (see the registry below), calibrated
severity per finding, triageable output. Assistant-neutral — works
wherever this skill folder is loaded.

## When to invoke

- "audit my code/project/codebase", "tech audit", "tech DD"
- "security review", "security audit", "vuln scan"
- "is this ready to ship?", "release check", "pre-release"
- an explicit invocation of this skill (a `/code-audit` slash command,
  an `@code-audit` mention, or however your assistant invokes skills)

Routine "review this PR/file" is better served by a lightweight diff-
review tool if your assistant ships one. The `quick` cut here exists
for explicit narrow scans.

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
| D15 | UX & interaction | ui-deep | ux, flows, states, forms, navigation, a11y, i18n |
| D16 | UI & design-system craft | ui-deep | ui, design system, tokens, typography, spacing, visual |

The "13-dimension" framing in older prose is historical; D14 was added
in v0.2, D15–D16 in v0.3.

**always-deep** dims decay invisibly between audits — they run deep in
every cut that touches them. **default-deep** run deep when the
product has the matching surface. **ui-deep** run deep when a UI
surface is detected (frontend markers per `routing/detect-stack.md`);
each has a base source-level pass and an advanced rendered pass that
delegates to the `uxui-audit` skill. **scan** dims go deep only when a
🔴 surfaces. **release-only** runs when a tag is being cut.

## Severity and status

🔴 ship-blocker (fix before next pass) · 🟡 fix soon (<1 day,
defensible to defer) · 🟢 nice-to-have. Per dimension: ✅ no 🔴 and
≤2 🟡 · ⚠️ some 🟡 or a mitigated 🔴 · ❌ unmitigated 🔴.

## Findings pipeline (deep / full / release)

Long audits outlive a single context window. Persist as you go and
verify before you emit.

- **Incremental findings file.** Write findings to
  `.code-audit/work/<YYYY-MM-DD>/findings.tsv` — one TSV row per
  finding, the schema `scripts/_findings_to_milestones.py` consumes:
  `severity⇥dim⇥location⇥title⇥fix⇥effort⇥confidence` (the 7th column
  is M6; the script also accepts 6-column rows). Append **at the close
  of each dimension**, not at the end — the audit survives compaction
  and is resumable. Assemble the final report from this file, not from
  memory. `quick` and `security` are short enough to stay inline.
- **Resume.** On re-invocation, if today's `findings.tsv` exists, read
  it, skip dimensions already represented, and continue.
- **Refutation pass for every 🔴.** Before a 🔴 reaches the report,
  re-read the actual code path and actively try to prove it wrong: is
  the auth check applied by a parent middleware/scope? is the path
  dead? is the "missing" validation done upstream? Refuted → drop it,
  or downgrade with the reason recorded. Can't verify without runtime
  or unavailable code → keep it but mark `confidence:
  needs-verification`. This is the single biggest false-positive
  reducer; it is not optional for 🔴.
- **Milestone convention.** When emitting milestone stubs, match the
  target devplan's existing ID scheme — pass the matching `--prefix`
  to `scripts/_findings_to_milestones.py` (e.g. `--prefix M --start
  <next>`), don't default to `AUDIT` blindly.

### Repeat-audit memory

So a re-audit doesn't re-litigate what was already decided, and the
trend is mechanical rather than eyeballed:

- **Accepted-findings baseline** — `.code-audit/accepted.tsv` in the
  target repo: one row per dismissed/accepted finding, key =
  `dim␟location␟title-slug`, plus severity, reason, date, optional
  `revisit-by`. Every cut filters its fresh findings against it before
  reporting, and shows a `suppressed: N accepted findings` line.
  Entries past their `revisit-by` date resurface automatically. The
  dismissal flow that writes here lives in
  `playbooks/false-positives.md`.
- **Mechanical deltas** — `full` and `release` cuts diff the current
  `findings.tsv` against the most recent prior
  `.code-audit/work/<date>/findings.tsv`: new / fixed / still-open per
  severity. The report's trend section is generated from that diff,
  not from re-reading the previous prose report.

## Execution discipline (applies to every cut)

- Send tool output to a file (`--format json -o ...`), then summarize
  counts + top findings — never dump raw scanner output into context.
- Sample grep/heatmap-first: deep-read only the top-N candidate files
  per method, never whole-repo reads.
- Keep intermediate notes terse (structured rows, not prose); prose
  belongs in the final report only.
- Cite `file:line`; paste code only when the hunk itself is the finding.

## Workspace / multi-repo mode

If the target directory holds multiple git checkouts (a sibling-repo
workspace, e.g. a microservice or appliance monorepo of separate
repos), enumerate them, confirm the scope with the user, run stack
detection **per repo**, and produce per-repo findings plus one merged
executive summary. A finding's `location` carries the repo prefix so
the merged `findings.tsv` stays unambiguous.

## Per-project extension

If the target repo has `.code-audit/extras/`, load every `*.md` in it
AFTER the default dimensions (schema: `extensions/README.md`).

Operational cadence, starter pack, and false-positive dismissal live in
`playbooks/operations.md` and `playbooks/false-positives.md` — load on
request.
