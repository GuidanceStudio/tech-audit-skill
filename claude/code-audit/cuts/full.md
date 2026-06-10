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
   `threat-models/*.md` and `tools/*.md` as needed.

5. **Project extensions**: if `.code-audit/extras/` exists in the
   repo, load every `*.md` from it AFTER the default dimensions. Use
   them as additional dimensions (e.g. D14, D15) in the report.

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

## Time budget per dimension

| Dim | Treatment | Time |
|---|---|---|
| D1 | deep | 1 h |
| D2 | deep | 45 min |
| D3 | deep | 45 min |
| D4 | deep | 45 min |
| D5 | deep | 30 min (if multi-tenant) |
| D6 | scan | 15 min |
| D7 | scan | 15 min |
| D8 | deep | 30 min |
| D9 | scan | 15 min |
| D10 | release-only | skip / 30 min |
| D11 | scan | 15 min |
| D12 | scan | 20 min |
| D13 | deep | 30 min |
| assemble | — | 1 h |

Total ≈ 5-7 h depending on multi-tenant + release-tag.

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
