# Shell — language-specific checks

Shell is where many "single-keystroke operator UX" promises live. Patterns to apply.

## Word splitting (D1, D4)

```sh
# Run shellcheck on all .sh files
shellcheck $(find . -name '*.sh' -not -path './node_modules/*')
```

Most common offenders:
- **SC2086 — quote `$var`** to prevent word splitting. Especially around `rm`, `mv`, `cp`. Unquoted `$file` containing a space is a data-loss footgun.
- **SC2046 — quote `$(cmd)`** for the same reason.
- **SC2154 — undefined variable** — typos in env var names silently expand to empty.

Each unquoted expansion in a destructive path → 🔴.

## Secrets in argv (D4)

```sh
# Anti-pattern: secret in argv (visible to ps)
curl -H "Authorization: Bearer $TOKEN" ...

# That's actually OK — TOKEN doesn't show in ps. But:
mysql --password=$PASSWORD ...   # ← password in argv, visible in ps -ef
```

Use `--password-stdin` patterns. Or env var. Never argv for secrets.

## `set -euo pipefail`

Top of every non-trivial script. Absence → 🟡:

```sh
#!/usr/bin/env bash
set -euo pipefail
```

`-e` exits on error. `-u` errors on undefined var. `-o pipefail` propagates pipe errors. Together they prevent silent partial failure.

## `rm -rf` with unset variable

```sh
# THIS WILL DELETE YOUR FILESYSTEM ROOT if BUILD_DIR is unset
rm -rf "$BUILD_DIR/*"
```

With `set -u` this errors. Without, it expands to `rm -rf /*`. 🔴 if found.

## Operator UX (D13)

- Scripts that are part of the operator's happy path must be idempotent.
- Scripts that need root should `sudo` themselves up explicitly, not rely on the user running with sudo.
- Long-running scripts should emit progress, not silence.

## Tools to run

- **shellcheck** (already canonical) — run in CI.
- **shfmt** for formatting consistency.

## Cross-references

- `dimensions/D13-setup-replicability.md` — operator UX promise.
- `threat-models/secret-management.md` — secret handling in scripts.
