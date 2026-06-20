# Full audit cut

The complete multi-dimension tech-DD report.

## When to invoke

- User says "full audit" / "tech DD" / "audit my whole codebase".
- Quarterly cadence per `playbooks/operations.md`.
- Pre-VC / pre-investment / pre-acquisition diligence.

## Inputs

- Repo root.
- (Optional) previous audit report path, for delta tracking.

## Procedure

1. **Compute the trend mechanically** (per `SKILL.md` § Repeat-audit
   memory): diff this run's `findings.tsv` against the most recent
   prior `.tech-audit/work/<date>/findings.tsv` — fixed (gone),
   still-open (present in both), new (this run only), per severity.
   The trend section is generated from that diff, not from re-reading
   the previous prose report. Load the accepted-findings baseline
   (`.tech-audit/accepted.tsv`) and filter suppressed findings out
   before reporting.

2. **Detect the stack** (per `SKILL.md` § Step 2). Load every
   matching `languages/<stack>.md`.

3. **Run every dimension** (treatment per registry tags in `SKILL.md` § Dimension registry).

4. For each dimension, run all methods in `dimensions/D<N>-*.md`. Load
   `threat-models/*.md` and `tools/*.md` as needed. **Append each
   dimension's findings to `.tech-audit/work/<date>/findings.tsv` as
   you close it, and run the 🔴 refutation pass** — both per the
   Findings pipeline in `SKILL.md`. Assemble the report from that file.

5. **Project extensions**: if `.tech-audit/extras/` exists in the
   repo, load every `*.md` from it AFTER the default dimensions. Use
   them as additional dimensions (e.g. D17+) in the report.

6. **Run the over-engineering deep-dive** if D1 surfaces ≥5 findings:
   write a companion file `docs/internal/over-engineering-audit-<date>.md`
   detailing each dead class, single-impl interface, and orphan
   migration. Rank the companion report by the D1 essentiality taxonomy
   in `dimensions/D01-code-essentiality.md`, biggest safe deletion
   first. The main report cross-references it.

7. **Emit per `templates/full-audit-report.md`**:
   - Header (auditor, scope, repo HEAD).
   - Executive summary (3 bullets — top risk, top strength, biggest
     gap).
   - Status overview table (every dimension × status).
   - Per-dim findings (all 🔴 + 🟡, sample of 🟢).
   - Triage section: proposed follow-up milestones with effort
     estimates.
   - Trend section if the previous audit was loaded.

## Execution: fan-out when subagents are available

Parallelize by dimension. Pre-compute repo inventory once (stack detection + git-churn heatmap + file inventory). One agent per dimension (skip release-only D10 unless tagging). Merge TSV rows, dedup cross-dimension overlaps (most-specific dimension wins), verify 🔴s independently per `SKILL.md` § Findings pipeline, assemble report. Sequential fallback: run dimensions in registry order, appending to `findings.tsv` after each. Scope, not clock — run each dimension's method catalog to exhaustion, sampling top-N churn-heatmap files.

## Output

Two files (the second is optional):

1. `docs/internal/tech-audit-<YYYY-MM-DD>.md` — the main report.

2. `docs/internal/over-engineering-audit-<YYYY-MM-DD>.md` — only if
   D1 surfaces ≥5 findings worth detailed write-up.

If the repo doesn't have `docs/internal/`, default to writing
alongside the project's existing audit / quality dir, or output
inline if no such dir exists.

## Cross-references

- All `dimensions/D<N>-*.md` method catalogs.
- `extensions/README.md` — how project-specific extras work.
- `templates/full-audit-report.md` — output template.
