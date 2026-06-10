# Quick scan cut

5-10 minutes. Single file, single PR diff, or a narrow slice ("review the auth changes").

## When to invoke

- User says "review this file" / "review this PR" / "review my changes".
- User pastes a diff or links to a PR.
- Default fallback when invoked on a narrow target.

## Inputs

- A file path, a PR URL, or a diff (via `git diff` or pasted).
- (Optional) the user's stated concern: "is this safe?", "is this readable?", etc.

## Procedure

1. **Detect the change surface** — what code is in scope?
   - File path → just that file + its direct imports.
   - PR URL → fetch via `gh pr view --json files`.
   - Diff → parse with `git diff --stat` for the file list.

2. **Detect the stack** of the changed files (per `SKILL.md` § Step 2).
   Load matching `languages/<stack>.md`.

3. **Pick a subset of dimensions** to apply, scaled to the change:
   - Touched auth code → D4 + relevant threat-models.
   - Touched query layer → D5 (multi-tenant) + D9 (data integrity).
   - Touched migrations → D9.
   - Touched bootstrap / Dockerfile / docker-compose → D13 + D6.
   - Touched UI / Filament / admin pages → D12.
   - Touched an LLM/agent/tool-gateway surface → D4 + `threat-models/ai-runtime.md`.
   - **Always: D14 (correctness on the diff) + D1 (essentiality on the diff).**
     Correctness is the primary reason a quick scan exists — run it on
     every diff, not just when something looks risky.

4. **Run methods only on the diff**, not the full codebase. The diff is the unit of review.

5. **Emit per `templates/quick-scan-output.md`**:
   - 3-bullet executive summary.
   - Findings table (severity, location, finding, suggested fix).
   - One-line "ship / hold" recommendation.

## What this cut does NOT do

- It does NOT scan the whole repo. That's `full` or `deep`.
- It does NOT generate milestone proposals. Findings are inline only.
- It does NOT run heavy tooling (Trivy, Semgrep across the repo). Tool runs are diff-scoped:
  - `gitleaks protect --staged` (or against the diff)
  - `semgrep --config=auto --baseline-ref=<base>` (only new findings)
  - Linter on the diff only.

## Anti-patterns to flag

The model has a known tendency to be either too soft ("looks good!" with three nits) or too harsh (laundry list of style preferences). Calibrate:

- **No 🔴 → no 🔴**. Don't manufacture severity to look thorough.
- **Style preferences are 🟢**, not 🟡.
- **Cite the line / hunk** for every finding. "There's a security issue somewhere in this PR" is useless.
- **Suggest a concrete fix**, not "consider refactoring".

## Cross-references

- `templates/quick-scan-output.md` — output template.
- `templates/finding-phrasing.md` — tone calibration.
- `languages/*.md` — stack-specific gotchas.
