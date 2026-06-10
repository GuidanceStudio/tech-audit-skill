# Full audit report template

Use this template for `cuts/full.md` output. Write to
`docs/internal/tech-audit-<YYYY-MM-DD>.md` in the audited repo
(or output inline if the repo has no `docs/internal/`).

```markdown
# Tech audit — <YYYY-MM-DD>

**Auditor**: <name or "Claude code-audit skill under <user>'s direction">
**Scope**: full (all dimensions)
**Repo HEAD at audit time**: <git rev-parse HEAD>
**Findings source**: `.code-audit/work/<YYYY-MM-DD>/findings.tsv` — all 🔴 survived the refutation pass
**Previous audit**: <link to docs/internal/tech-audit-<previous-date>.md if any>

---

## Executive summary

- 🔴 **Top risk**: <one line>
- 🟢 **Top strength**: <one line>
- 🟡 **Biggest gap**: <one line>

(Three lines. No more. The reviewer reads only this if they have
3 minutes.)

---

## Status overview

| Dim | Title | Status | 🔴 | 🟡 | 🟢 |
|---|---|---|---|---|---|
| D1 | Code essentiality | ✅/⚠️/❌ | n | n | n |
| D2 | Docs integrity | ... | ... | ... | ... |
| D3 | Tests as adversaries | ... | ... | ... | ... |
| D4 | Security posture | ... | ... | ... | ... |
| D5 | Multi-tenant isolation | ... | ... | ... | ... |
| D6 | Operational readiness | ... | ... | ... | ... |
| D7 | Dependency hygiene | ... | ... | ... | ... |
| D8 | Build / CI / dev-loop | ... | ... | ... | ... |
| D9 | Data model integrity | ... | ... | ... | ... |
| D10 | Performance & cost | ... | ... | ... | ... |
| D11 | Legal / compliance | ... | ... | ... | ... |
| D12 | Admin surface consistency | ... | ... | ... | ... |
| D13 | Setup replicability | ... | ... | ... | ... |
| **Total** | | | **N** | **N** | **N** |

(Project-specific extras from `.code-audit/extras/` listed below if present.)

---

## Trend vs previous audit

(Only if a previous audit was loaded.)

| | This pass | Last pass | Delta |
|---|---|---|---|
| 🔴 | N | N | ▲▼ |
| 🟡 | N | N | ▲▼ |
| Avg dim status | ✅/⚠️ | ✅/⚠️ | improved / regressed |

Closed since last time:
- ✅ <finding>

Still open:
- <finding> (now N audits old)

New regressions:
- 🔴/🟡 <finding>

---

## D1 — Code essentiality

**Status**: <emoji> · <one-line summary>

### Findings

- 🔴 `<path:line>` — <one-line title>.
  _Why it matters_: <impact>.
  _Suggested fix_: <concrete fix in 1-2 lines>.

- 🟡 `<path:line>` — <one-line title>.
  _Why it matters_: <impact>.
  _Suggested fix_: <concrete fix>.

(repeat for every 🔴 / 🟡. Sample 2-3 🟢 for context; the rest go in
an appendix if the operator wants them.)

---

## D2 — Docs integrity

[same structure: status + findings]

---

[... D3 through D13 ...]

---

## Triage — proposed follow-up milestones

| Finding | Suggested milestone | Devplan file (if known) | Effort |
|---|---|---|---|
| 🔴 D4-3 — secret in `.env` git history | OPS-12: rotate + history-rewrite | poc.md | 4 h |
| 🔴 D5-1 — async-pool tenant context missing | SEC-7: SET LOCAL on every connection acquire | poc.md | 1 day |
| 🟡 D8-1 — no CI on Python services | CI-3: GH Actions for ruff + mypy + pytest | poc.md | 2 h |
| 🟡 D2-4 — README quickstart fails on clean VM | DOCS-9: fresh-clone test in CI | poc.md | 4 h |

---

## Appendix — 🟢 findings (optional)

(Long tail of 🟢 findings, browsable but not headlining the report.)
```

## Phrasing reminders

- Cite the exact location (file:line).
- Quote 2-4 lines of code if helpful (no more — the reader has the repo).
- "_Why it matters_" in plain language — what bad thing happens if we don't fix it.
- "_Suggested fix_" in 1-2 lines — concrete code change or process step.
- Don't pile on. If 50 occurrences of the same pattern exist, file ONE finding "pattern X appears 50× — see appendix" with the list as an appendix.

See `templates/finding-phrasing.md` for tone calibration.

## Cross-references

- `cuts/full.md` — what runs to produce this report.
- `templates/finding-phrasing.md`.
- `templates/triage-and-summary.md` — used standalone for `deep` and `release` cuts.
