# Deep cut — one or more dimensions

1-2 hours per dimension. The user names what they want examined.

## When to invoke

- User says "deep audit on X" / "review my tests" / "audit code essentiality" / "check tenant isolation".
- User wants a focused investigation, not a full report.

## Inputs

- Repo root.
- One or more dimension shortcodes (D1..D13) or names.

If the user names a topic but not a dim, map it via the **Topics**
column of the dimension registry in `SKILL.md`.

## Procedure

1. For each named dimension, load `dimensions/D<N>-*.md`.

2. Detect the stack (per `SKILL.md` § Step 2). Load matching
   `languages/<stack>.md`.

3. Run every method in the dimension file. Don't cherry-pick — the
   point of "deep" is to be thorough.

4. Load any cross-referenced `threat-models/*.md` when the method
   calls them out.

5. Run the relevant tools (per `tools/*.md`):
   - D1 → jscpd, dead-code detectors, language linters.
   - D4 → gitleaks, semgrep, trivy, audit commands.
   - D5 → pgTAP, cross-tenant probes.
   - etc.

6. **Emit per `templates/triage-and-summary.md`** (deep section):
   - Per-dim status + findings list with severity.
   - For each 🔴: dedicated paragraph (what, why, where, fix).
   - For each 🟡: one-line in a table.
   - Suggested milestones via `scripts/_findings_to_milestones.py` if
     >3 findings of any severity.

## What this cut does NOT do

- It does NOT auto-promote to other dimensions when one finds a
  related issue. Stay scoped to what the user asked for. (Mention
  the cross-link in the report, but don't widen the audit.)

## Cross-references

- `dimensions/D<N>-*.md` — the method catalogs.
- `threat-models/*.md` — loaded on demand.
- `templates/triage-and-summary.md` — output template.
