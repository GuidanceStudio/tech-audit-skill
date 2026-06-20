---
name: tech-audit
description: Methodical codebase audit across a multi-dimension tech-DD framework. Routes by intent — security pass, release check, deep per-dimension, full tech-DD, or explicit quick scan. Stack-aware (PHP/Laravel, Python/FastAPI, TS/Node, shell, Docker). Use for "audit", "tech DD", "security review", "ready to ship?" — NOT for routine PR diff review.
---

# Code audit — Router

Honest, actionable codebase findings across a multi-dimension framework. Assistant-neutral.

## When to invoke

- "audit my code/project/codebase", "tech audit", "tech DD"
- "security review", "security audit", "vuln scan"
- "is this ready to ship?", "release check", "pre-release"
- an explicit invocation of this skill (a `/tech-audit` slash command,
  an `@tech-audit` mention, or however your assistant invokes skills)

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

Markers are searched recursively. See `routing/detect-stack.md`.
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

| # | Title | Tag |
|---|---|---|
| D1 | Code essentiality | always-deep |
| D2 | Docs integrity | always-deep |
| D3 | Tests as adversaries | always-deep |
| D4 | Security posture | default-deep |
| D5 | Multi-tenant isolation | default-deep |
| D6 | Operational readiness | scan |
| D7 | Dependency hygiene | scan |
| D8 | Build / CI / dev-loop | default-deep |
| D9 | Data model integrity | scan |
| D10 | Performance & cost | release-only |
| D11 | Legal / compliance | scan |
| D12 | Admin surface | scan |
| D13 | Setup replicability | always-deep |
| D14 | Correctness & robustness | always-deep |
| D15 | UX & interaction | ui-deep |
| D16 | UI & design-system craft | ui-deep |

**always-deep** dims decay invisibly between audits — they run deep in
every cut that touches them. **default-deep** run deep when the
product has the matching surface. **ui-deep** run deep when a UI
surface is detected (frontend markers per `routing/detect-stack.md`);
each has a base source-level pass and an advanced rendered pass that
delegates to the `uxui-audit` skill. **scan** dims go deep only when a
🔴 surfaces. **release-only** runs when a tag is being cut.

## Severity and status

Severity uses the unified 0–4 scale shared with the `uxui-audit` skill
(they are one family):

| # | Emoji | Label | Bar |
|---|---|---|---|
| 4 | 🔴 | Catastrophic / ship-blocker | fix before next release |
| 3 | 🟡 | Major / fix soon | fix within 1 day, defensible to defer |
| 2 | 🟢 | Minor / nice-to-have | low priority |
| 1 | 🟢 | Cosmetic | fix only if time allows |
| 0 | — | Not a problem | — |
| — | — | **Health** | ✅ no 4 and ≤2 of 3 · ⚠️ some 3 or a mitigated 4 · ❌ unmitigated 4.

Dimension method bodies use 🔴/🟡/🟢 shorthand (4/3/0-2); the numeric scale is the source of truth.

## Findings pipeline (deep / full / release)

Long audits outlive a single context window. Persist as you go, verify before emit.

- **Incremental TSV.** Write to `.tech-audit/work/<YYYY-MM-DD>/findings.tsv`: schema `severity⇥dim⇥location⇥title⇥fix⇥effort⇥confidence` (6 or 7 columns). Append at the close of each dimension — survives compaction, resumable. Assemble the final report from this file, not memory. `quick`/`security` stay inline.
- **Resume.** If today's `findings.tsv` exists, read it, skip dimensions already represented, continue.
- **Refute every 🔴.** Re-read the actual code path and prove it wrong: is auth handled upstream? is the path dead? is validation done elsewhere? Refuted → drop/downgrade. Can't verify without runtime → mark `confidence: needs-verification`. Mandatory for 🔴 — single biggest false-positive reducer.
- **Milestone prefix.** Match the target devplan's ID scheme: `scripts/_findings_to_milestones.py --prefix M --start <next>`. Don't default to `AUDIT`.

### Repeat-audit memory

- **Accepted-findings baseline** — `.tech-audit/accepted.tsv`: one row per dismissed finding, key = `dim␟location␟title-slug`, plus severity, reason, date, optional `revisit-by`. Every cut filters against it; past `revisit-by` entries resurface. Dismissal flow: `playbooks/false-positives.md`.
- **Mechanical deltas** — diff current `findings.tsv` against most recent prior: new / fixed / still-open per severity. Trend section from that diff, not from re-reading old prose.

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

If the target repo has `.tech-audit/extras/`, load every `*.md` in it
AFTER the default dimensions (schema: `extensions/README.md`).

Operational cadence, starter pack, and false-positive dismissal live in
`playbooks/operations.md` and `playbooks/false-positives.md` — load on
request.
