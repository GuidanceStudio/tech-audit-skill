# Release cadence cut

~30 minutes. Per-release-tag gate: scan over every dimension, deep on
what changed since the last tag.

## When to invoke

- User says "ready to ship?" / "release check" / "pre-release audit".
- About to tag `v0.x.y`.
- Just landed a multi-day feature and wants a sanity check.

## Inputs

- Repo at HEAD on `main` (or release branch).
- The previous release tag (auto-detected via `git describe --tags --abbrev=0`).
- (Optional) the planned release tag name (for the report header).

## Procedure

0. **Load the accepted-findings baseline** (`.code-audit/accepted.tsv`,
   per `SKILL.md` § Repeat-audit memory) and filter suppressed findings
   out of the ship-block decision; report `suppressed: N`. Past their
   `revisit-by` date, accepted findings resurface.

1. **Compute the diff since the last tag**:

   ```sh
   PREV=$(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~50)
   git diff --stat "$PREV"..HEAD
   git log "$PREV"..HEAD --oneline
   ```

2. **Identify the trust-boundary changes** — the subset of the diff
   that touches:
   - Auth / authz / session
   - Multi-tenant scope / tenant_id propagation
   - Migrations / schema
   - Secret bootstrap / Dockerfile / docker-compose
   - External API integrations (LLM, payments, ...)

3. **Run cuts inline**:
   - On the trust-boundary changes: apply `cuts/security.md` (D4 + D5
     deep).
   - On all changed files: apply `cuts/quick.md` (D1 essentiality +
     D2 doc drift since last tag).
   - On the whole repo: a scan-only pass over D6, D7, D8, D9, D11,
     D12, D13 — promote any to deep if a 🔴 surfaces.

4. **Always-deep dimensions** (the always-deep tag in the `SKILL.md`
   registry: D1, D2, D3, D13, D14) get a 5-min focused scan even if not
   touched by the diff. They decay between tags.

5. **Release-only deep on D10** (performance & cost baseline): pull
   benchmark numbers and compare to the previous tag's recorded
   baseline. Regression > 20% → 🔴.

6. **Persist + verify** per the Findings pipeline in `SKILL.md`:
   accumulate findings in `.code-audit/work/<date>/findings.tsv`; run
   the 🔴 refutation pass before the ship-block list — a false 🔴
   wrongly holds a release.

7. **Emit per `templates/triage-and-summary.md`** (release section):
   - Header: previous tag, planned tag, diff stats.
   - Trust-boundary changes section (the focused security pass).
   - Status overview table for all dimensions.
   - Ship-block list (🔴 only).
   - Things to fix this week (🟡 likely worth before next tag).
   - Things accepted as risk (🟡 deferred, with reason).
   - Top 3 risks in plain English (for the changelog / release notes).

## What this cut does NOT do

- It does NOT do a full audit (5-7 h). That's `full`.
- It does NOT replace the security pass — it RUNS the security pass
  on the diff subset.

## Heuristics

- **No 🔴 + ≤3 🟡 → ship**. The release is in healthy band.
- **No 🔴 + many 🟡 → ship if reasoned**. The team chose accumulation
  consciously and is tracking; document the next tag's quality
  milestones.
- **Any 🔴 → hold the release**. Even if customer demand is loud.

## Cross-references

- `cuts/security.md` — invoked inline on trust-boundary changes.
- `cuts/quick.md` — invoked inline on each changed file.
- `templates/triage-and-summary.md` — output template (release section).
