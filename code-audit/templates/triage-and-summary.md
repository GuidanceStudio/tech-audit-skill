# Triage and summary template

Used by `cuts/deep.md` and `cuts/release.md`. Two sections — pick the one that matches your cut.

---

## Deep cut — per-dimension report

For `cuts/deep.md` (one or more dimensions, on-demand).

```markdown
# Deep audit — <dimensions> — <YYYY-MM-DD>

**Repo**: <name> · **Stack**: <detected> · **HEAD**: <git sha>
**Findings source**: `.code-audit/work/<YYYY-MM-DD>/findings.tsv` ·
all 🔴 survived the refutation pass

## D<N> — <title>

**Status**: <emoji> · **Findings**: 🔴 N · 🟡 N · 🟢 N

### Top finding

<one paragraph in plain language>

### All 🔴 / 🟡 findings

For each:

- **Severity** + `path:line` + one-line title
- 1-3 line description
- Suggested fix

(... repeat per dimension ...)

## Triage — proposed milestones

| Finding | Suggested milestone | Devplan target | Effort |
|---|---|---|---|
| 🔴 D5-1 | <name> | <file> | <hours/days> |
| 🟡 D1-3 | <name> | <file> | <hours> |
```

---

## Release cut — pre-tag check

For `cuts/release.md` (cadence pass before tagging a release).

```markdown
# Release check — <planned tag> — <YYYY-MM-DD>

**Previous tag**: <prev> · **Diff stats**: <files changed, ± lines>
**Repo**: <name> · **HEAD**: <git sha>

## Verdict

**Ship / Hold** — <one sentence>.

## Top 3 risks (for release notes)

- <plain-English line for the changelog>
- <plain-English line>
- <plain-English line>

## Status overview (since last tag)

| Dim | Status | Notes |
|---|---|---|
| D1 | ✅/⚠️/❌ | <one line — did the diff add or fix code-essentiality findings> |
| ... | ... | ... |
| D13 | ✅/⚠️/❌ | <fresh-clone test still passes?> |

## Trust-boundary changes

(The subset of the diff that touched auth, tenant scope, migrations, secrets, external integrations.)

| File | Change | Risk |
|---|---|---|
| `path` | <summary> | <one-line risk> |

(If empty: "No trust-boundary changes since previous tag.")

## Ship-blockers (🔴)

- <one per line, with `path:line` + one-line fix>

## Fix this week (🟡)

- <one per line>

## Accepted risk this cycle (🟡 deferred)

- <one per line, with the reason for deferring>

## Performance delta (if D10 ran)

| Metric | Previous tag | This tag | Δ |
|---|---|---|---|
| p95 latency | 250ms | 260ms | +4% (within budget) |
| Cost per 1K requests | €0.012 | €0.013 | +8% (within budget) |
```

## Triage milestone phrasing

When suggesting milestones, follow the project's existing naming convention. Common patterns:

- `OPT-<N>` (Cerase-style optimisation milestones)
- `M<N>` (numbered milestones)
- `<prefix>-<short-name>` (e.g. `SEC-rotate-jwt`, `OPS-restore-drill`)
- Issue tracker ID format if the project uses one (`AUDIT-12`, `BUG-3091`)

Don't invent a milestone naming scheme. Match what's in the project's devplan or issue tracker.

## Effort estimates

Anchor estimates in concrete units:

- **30 min** — config change, single-file fix, dep bump
- **2 h** — small refactor with tests
- **1 day** — feature-sized: code + tests + docs
- **1 week** — cross-cutting: multiple files, migration, rollout plan

Don't say "depends" — give a range if you're unsure ("2-4 h").

## Cross-references

- `cuts/deep.md`, `cuts/release.md`.
- `templates/finding-phrasing.md`.
