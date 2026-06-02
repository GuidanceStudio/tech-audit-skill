# Quick scan output template

Inline reply for `cuts/quick.md`. Goes back to the user in the chat — no file written.

```markdown
## Quick scan — <file or PR title>

**Scope**: <files reviewed> · **Dimensions**: <list> · **Stack**: <detected>

### Summary

<3 bullets, plain English, no jargon>
- <strongest signal>
- <second signal>
- <third signal — or ship verdict>

### Findings

| Severity | Location | Finding | Suggested fix |
|---|---|---|---|
| 🔴 | `path.ts:42` | <one-line> | <one-line> |
| 🟡 | `path.php:118-125` | <one-line> | <one-line> |
| 🟢 | `path.py:7` | <one-line> | <one-line> |

### Recommendation

**Ship** / **Hold** — <one sentence>.

(If hold: list the 🔴 that must clear first. If ship: note any 🟡 to follow up.)
```

## Examples

### Healthy PR

```markdown
## Quick scan — PR #143: "Add bulk archive endpoint"

**Scope**: 3 files · **Dimensions**: D1, D4, D5 · **Stack**: Python/FastAPI

### Summary

- Endpoint correctly enforces tenant scope via `Depends(current_user)`.
- One unused import in `routers/archive.py`.
- Adversarial inputs not yet tested (missing `tests/test_archive.py`).

### Findings

| Severity | Location | Finding | Suggested fix |
|---|---|---|---|
| 🟡 | `routers/archive.py` | No test file added; D3 regression-after-feature ratio drops. | Add `tests/test_archive.py` with happy + 403 cross-tenant + empty-list cases. |
| 🟢 | `routers/archive.py:3` | Unused `from datetime import timedelta`. | Remove. |

### Recommendation

**Ship** — add the tests in a follow-up PR (the change is small and the auth check is correct).
```

### PR with a 🔴

```markdown
## Quick scan — PR #168: "Add admin user impersonation"

**Scope**: 5 files · **Dimensions**: D1, D4, D5 · **Stack**: PHP/Laravel

### Summary

- The impersonation endpoint accepts a target user via URL param without verifying the requester is admin.
- Session ID does NOT rotate when impersonation begins.
- No audit log entry on impersonation start.

### Findings

| Severity | Location | Finding | Suggested fix |
|---|---|---|---|
| 🔴 | `routes/admin.php:42` | `Route::get('/admin/as/{user}', ...)` lacks `auth.admin` middleware. Any authenticated user can impersonate any other. | Wrap in `Route::middleware('auth.admin')->group(...)`. |
| 🔴 | `app/Http/Controllers/ImpersonateController.php:25` | `Auth::loginUsingId($user)` without `session()->regenerate()`. Pre-impersonation session ID continues; session-fixation vector. | Add `session()->regenerate()` immediately after `loginUsingId`. |
| 🟡 | `ImpersonateController.php:30` | No `AuditLog::record('impersonation_start', ...)` call. | Add an audit log entry on enter + exit. |

### Recommendation

**Hold** — the two 🔴 are auth-bypass + session-fixation. Both must clear before merge.
```

## Phrasing discipline

- One paragraph max per finding in the summary. The table carries detail.
- "Suggested fix" must be implementable in <30 min — not "consider refactoring the auth layer".
- If you can't articulate the "why it matters", the finding might be a style preference (🟢, not 🟡).
- Don't manufacture 🔴 to look thorough. If the PR is healthy, say so.

## Cross-references

- `cuts/quick.md`.
- `templates/finding-phrasing.md`.
