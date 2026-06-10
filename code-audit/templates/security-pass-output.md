# Security pass output template

For `cuts/security.md` output. Goes inline or to `docs/internal/security-review-<YYYY-MM-DD>.md` if the user wants a record.

```markdown
# Security review — <YYYY-MM-DD>

**Scope**: <repo name> · **Reviewer**: Claude code-audit skill
**Stack detected**: <list>
**Tools run**: <list — e.g. gitleaks, trivy, semgrep, phpstan-taint>

---

## Top risk (one line)

<the single most concerning finding, phrased so a non-technical reader gets the urgency>

---

## Findings — by severity

### 🔴 Ship-blockers

For each:

#### 🔴 <one-line title>

- **Where**: `path:line` (or component if cross-file)
- **What**: <plain-English description of the bug>
- **Why it matters**: <what bad thing happens; if a real attacker could exploit this in <5 min, say so>
- **Suggested fix**: <concrete change>
- **Effort**: <30 min / 1 day / 1 week>
- **Threat model**: <link to `threat-models/<file>.md` if applicable>

(Each 🔴 gets its own block — they deserve attention.)

### 🟡 Fix soon

| Where | What | Why it matters | Fix | Effort |
|---|---|---|---|---|
| `path:line` | <one-line> | <one-line> | <one-line> | <effort> |

(Tabular — operator triages in 5 min.)

### 🟢 Notes for the next cycle

- Bullet list, terse. Trivia, style, "could be tighter".

---

## Threat-model coverage

| Threat model | Status | Notes |
|---|---|---|
| Auth model | ✅/⚠️/❌ | <one-line> |
| Multi-tenant isolation | ✅/⚠️/❌ | <one-line> |
| Secret management | ✅/⚠️/❌ | <one-line> |
| PII data flow | ✅/⚠️/❌ | <one-line> |

(Only if the threat model applies to the product.)

---

## Tool output summary

| Tool | Findings | Top issue |
|---|---|---|
| gitleaks | 0 / N | <or "—"> |
| trivy fs | 2 HIGH, 5 MODERATE | CVE-2024-XXXX in xyz |
| semgrep | 3 | <top> |
| stack-SAST | 0 | — |

---

## Recommendation

**Block release** / **Fix this week** / **Acceptable risk** — <one-paragraph reasoning>.

If "Acceptable risk", explicitly list which 🟡 you're accepting and why.
```

## Tone calibration

- Plain English in the "Why it matters" sections. The CEO or sales lead might read this; don't lose them on jargon.
- For 🔴 with a clear exploit, say so plainly. ("An unauthenticated user can read any tenant's data by changing the URL." — not "Authorization may not be properly enforced.")
- Don't conflate severity. A linter warning isn't a security finding.

## Cross-references

- `cuts/security.md`.
- `templates/finding-phrasing.md`.
- `threat-models/*.md` — cross-referenced inline.
