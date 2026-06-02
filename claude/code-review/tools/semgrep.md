# Semgrep

**What it catches**: cross-language SAST. Pattern-based rules covering OWASP top 10 + framework-specific anti-patterns. Fast (typically <2 min on a medium repo).

## Install

```sh
pip install semgrep
# OR
brew install semgrep
```

## Recommended rule packs

| Pack | What it covers |
|---|---|
| `p/owasp-top-ten` | universal OWASP A01–A10 |
| `p/secrets` | secret-shaped content in code (complement to Gitleaks) |
| `p/laravel` | PHP Laravel-specific (CSRF, mass-assignment, raw queries) |
| `p/fastapi` | FastAPI-specific (CORS, response_model, BackgroundTasks) |
| `p/django` | Django (raw, ORM bypass, template) |
| `p/typescript` | TS-specific (no-eval, no-unsafe-any) |
| `p/javascript` | JS-specific (xss, prototype pollution) |
| `p/python` | broad Python (Bandit-equivalent) |

## Usage

```sh
# Cross-language baseline
semgrep --config=p/owasp-top-ten --config=p/secrets --error .

# Stack-specific
semgrep --config=p/laravel --config=p/fastapi --error .

# Only NEW findings vs main branch
semgrep --config=auto --baseline-ref=origin/main --error .

# JSON output for programmatic triage
semgrep --config=p/owasp-top-ten --json . > findings.json
```

## CI snippet

```yaml
- name: Semgrep
  uses: semgrep/semgrep-action@v1
  with:
    config: >-
      p/owasp-top-ten
      p/secrets
      p/laravel
      p/fastapi
      p/typescript
```

## Tuning

- Start in warn-not-fail mode for one week to triage false positives.
- Flip to `--error` only after the false-positive baseline is clean.
- `.semgrepignore` for paths to exclude (test fixtures, vendored code).
- Inline suppression: `# nosemgrep: rule-id` with a reason comment.

## False positives

- Test fixtures (e.g. `password = "test123"` in `tests/`) — `.semgrepignore` the test directory or scope rules to non-test code.
- Generated code (Prisma client, GraphQL types) — exclude.
- Framework-specific patterns that look risky but are safe (e.g. Laravel's `DB::raw($safeConstant)`) — inline suppress with justification.

## Custom rules

When the audit surfaces a pattern that repeats but isn't in the public packs (project-specific gotcha), write a custom rule in `.semgrep/rules/`:

```yaml
rules:
  - id: cerase-no-without-global-scopes
    pattern: $X::withoutGlobalScopes(...)
    message: |
      withoutGlobalScopes strips tenant isolation. Add a justification
      comment + a paired test that this path doesn't leak.
    languages: [php]
    severity: WARNING
```

## Cross-references

- `dimensions/D04-security-posture.md`.
- `dimensions/D08-build-ci-devloop.md`.
- `languages/<stack>.md` — stack-specific rule pack selection.
