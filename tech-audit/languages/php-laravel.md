# PHP / Laravel — language-specific checks

Beyond the universal D1-D13 methods, watch these patterns when reviewing a Laravel codebase.

## Auth / authz gotchas (D4)

- **`$fillable` drift** — model is mass-assigned via `Model::create($request->all())` but `$fillable` includes a field that shouldn't be user-settable (e.g. `role`, `is_admin`, `tenant_id`). 🔴.
- **`withoutGlobalScopes()`** — strips tenant scope. Every use needs a comment + test. See D5.
- **Route model binding without policy** — `Route::get('/agents/{agent}', ...)` fetches the model by ID without checking ownership. Combine with `authorize()` or a policy. 🟡 → 🔴 if tenant-scoped.
- **`Auth::user()` vs explicit user_id** — the latter is preferred in services to avoid coupling to the auth facade and to make the user context explicit.
- **`Hash::check` usage** — make sure passwords aren't compared with `===`.

## Eloquent gotchas (D5, D9)

- **Raw queries** — `DB::raw()`, `DB::statement()`, `->whereRaw()` skip global scopes. See D5.
- **`forceDelete` on audit log** — D9 invariant: audit log inserts only.
- **N+1 queries** — every `$collection->each(fn($x) => $x->relation)` without prior `->load()` is N+1. See D10.
- **Soft-delete + tenant scope** — `withTrashed()` AND `withoutGlobalScopes()` together is a leak vector.

## CSRF / state-changing routes (D4)

```sh
# Every state-changing route should be inside `web` middleware (CSRF on)
# or be in `api` with token auth.
grep -rnE "Route::(post|put|patch|delete)" routes/
```

POST/PUT/DELETE in `api.php` is fine (token-authenticated).
POST/PUT/DELETE in `web.php` without `auth` middleware OR without `csrf` middleware → 🔴.

## Filament admin gotchas (D12)

- **`->columns()` queries without tenant scope** — see D5.
- **`Notification::send()` swallowed in `try/catch` with `report()` only** — see D12.
- **Async work in `Pages\Edit` actions** — see D12.

## Migration safety (D9)

- `Schema::drop('users')` on released tables → 🔴.
- `DB::table('users')->update(...)` in a migration on a live table → 🟡 (move to a data migration).
- Long-running migrations (>1s) without batching → 🟡 (lock the table on prod deploy).

## Lock files (D7)

- `composer.lock` must be committed.
- `composer install` (production) vs `composer update` (dev) discipline matters; lock file vs platform-php-version mismatch breaks deploys.

## Tools to run

- **PHPStan + Larastan** at level 6 → 8 (`tools/phpstan-larastan.md`).
- **Psalm + psalm-laravel** with `TaintAnalysis` for deeper SAST.
- **Composer audit** for dep CVE.
- **`composer unused`** for dead dep detection (D1).

## Stack-specific anti-patterns (LLM-generated)

When 30-70% of code is AI-assisted, expect:
- Single-impl `Repository` / `Service` / `Manager` interfaces (LLM loves enterprise patterns). See D1.
- Action / Job classes that wrap a 5-line method body.
- DTO classes that duplicate Form Request data shape.

## Cross-references

- `threat-models/multi-tenant-isolation.md` — Laravel-specific bypass patterns.
- `threat-models/secret-management.md` — `.env` discipline.
- `tools/phpstan-larastan.md`.
