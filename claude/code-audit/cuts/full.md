# Full audit cut

5-7 hours. The complete 13-dimension tech-DD report.

## When to invoke

- User says "full audit" / "tech DD" / "audit my whole codebase".
- Quarterly cadence per `playbooks/operations.md`.
- Pre-VC / pre-investment / pre-acquisition diligence.

## Inputs

- Repo root.
- (Optional) previous audit report path, for delta tracking.

## Procedure

1. **Read the previous audit** if one exists in
   `docs/internal/tech-audit-*.md`. Note which 🔴 / 🟡 from last
   time:
   - Closed (fix shipped) → trend up.
   - Still open → trend flat / down.
   - New regressions → trend down.

2. **Detect the stack** (per `SKILL.md` § Step 2). Load every
   matching `languages/<stack>.md`.

3. **Run every dimension**, treatment per the registry tags in
   `SKILL.md`: always-deep + default-deep → deep; scan → scan
   (promote to deep on a 🔴); release-only → skip unless this audit
   coincides with a release tag.

4. For each dimension, run all methods in `dimensions/D<N>-*.md`. Load
   `threat-models/*.md` and `tools/*.md` as needed. **Append each
   dimension's findings to `.code-audit/work/<date>/findings.tsv` as
   you close it, and run the 🔴 refutation pass** — both per the
   Findings pipeline in `SKILL.md`. Assemble the report from that file.

5. **Project extensions**: if `.code-audit/extras/` exists in the
   repo, load every `*.md` from it AFTER the default dimensions. Use
   them as additional dimensions (e.g. D15, D16) in the report.

6. **Run the over-engineering deep-dive** if D1 surfaces ≥5 findings:
   write a companion file `docs/internal/over-engineering-audit-<date>.md`
   detailing each dead class, single-impl interface, and orphan
   migration. The main report cross-references it.

7. **Emit per `templates/full-audit-report.md`**:
   - Header (auditor, scope, repo HEAD).
   - Executive summary (3 bullets — top risk, top strength, biggest
     gap).
   - Status overview table (13 dim × status).
   - Per-dim findings (all 🔴 + 🟡, sample of 🟢).
   - Triage section: proposed follow-up milestones with effort
     estimates.
   - Trend section if the previous audit was loaded.

## Execution: fan-out when subagents are available

A full audit can't fit one context window. Dimensions are nearly
independent, so parallelize:

**If the harness has subagents (Agent / Workflow tools) — preferred:**

1. **Shared pre-scan, computed ONCE by the orchestrator** and passed
   into every agent's prompt: stack detection
   (`scripts/_detect_stack.py`), the git-churn heatmap
   (`git log --since=... --name-only | sort | uniq -c | sort -rn`),
   and the file inventory. Dimension agents must NOT each re-discover
   the repo — that wastes tokens and scopes inconsistently.
2. **One agent per dimension** (skip release-only D10 unless tagging).
   Each loads ONLY its `dimensions/D<N>-*.md` + the matching
   `languages/*.md` + the threat-models its methods reference. Each
   returns findings as TSV rows (the `findings.tsv` schema) plus a
   coverage note: files deep-read, methods run vs sampled-out and why.
3. **Model tiering** (when the harness allows a per-agent model):
   scan-tier dims (D6, D7, D9, D11, D12) may run on a cheaper model;
   always-deep / default-deep dims and the 🔴 verifiers stay on the
   main model.
4. **Merge** all rows into `.code-audit/work/<date>/findings.tsv`,
   deduplicating cross-dimension overlaps (see dedup rule below).
5. **Refute** — one independent verifier agent per 🔴 (per the
   Findings pipeline refutation pass); drop/downgrade what's refuted.
6. **Assemble** the report from the merged, refuted file; aggregate the
   per-agent coverage notes into the report's scope section — state
   what was sampled out, never silently truncate.

**Sequential fallback (no subagents):** run dimensions in registry
order in this context, appending to `findings.tsv` at the close of
each (so a compaction mid-audit is recoverable), then refute and
assemble. Same outputs, one context.

**Dedup rule:** the same `file:line` surfaced by two dimensions stays
under the dimension whose method is most specific to it (e.g. a tenant
leak → D5, not D1); cross-reference it from the other.

**Scope, not clock.** Run each dimension's method catalog to
exhaustion; for sampling methods, deep-read the top-N churn-heatmap
files rather than the whole repo. Stop a dimension when its methods are
exhausted, not on a timer.

## Output

Two files (the second is optional):

1. `docs/internal/tech-audit-<YYYY-MM-DD>.md` — the main report.

2. `docs/internal/over-engineering-audit-<YYYY-MM-DD>.md` — only if
   D1 surfaces ≥5 findings worth detailed write-up.

If the repo doesn't have `docs/internal/`, default to writing
alongside the project's existing audit / quality dir, or output
inline if no such dir exists.

## Cross-references

- All 13 `dimensions/D<N>-*.md` files.
- `extensions/README.md` — how project-specific extras work.
- `templates/full-audit-report.md` — output template.
