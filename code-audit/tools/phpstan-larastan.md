# PHPStan + Larastan

**What it catches**: PHP type errors + Laravel-specific anti-patterns (missing `Auth::user()` checks, `$fillable` drift, `withoutGlobalScopes` misuse, Eloquent return-type narrowing).

## Install

```sh
composer require --dev phpstan/phpstan larastan/larastan
```

## Config

```neon
# phpstan.neon
includes:
    - vendor/larastan/larastan/extension.neon

parameters:
    level: 6                        # start here, ramp to 8
    paths:
        - app/
        - tests/
    excludePaths:
        - app/Console/Kernel.php    # baseline-excluded
```

## Usage

```sh
vendor/bin/phpstan analyse --memory-limit=512M

# Generate / refresh baseline (legacy findings to ignore)
vendor/bin/phpstan analyse --generate-baseline

# Strict mode for new code: only report findings not in baseline
vendor/bin/phpstan analyse --error-format=github
```

## CI snippet

```yaml
- name: PHPStan
  run: vendor/bin/phpstan analyse --error-format=github
```

## Levels

| Level | Catches |
|---|---|
| 0 | Basic — undefined vars, classes |
| 4 | Method existence, callable typehints |
| 6 | Missing return / param types — the practical baseline |
| 7 | Null safety |
| 8 | Strict mixed handling |

Start at 6 + baseline. Ramp one level every release tag, regenerating baseline.

## Deeper variant

For taint analysis (data flow from sources to sinks — SQLi, XSS):

```sh
composer require --dev vimeo/psalm psalm/plugin-laravel
vendor/bin/psalm --taint-analysis
```

Heavy CI run; valuable on the auth + DB-query paths. Run on release tags, not every push.

## Cross-references

- `languages/php-laravel.md`.
- `dimensions/D04-security-posture.md`.
