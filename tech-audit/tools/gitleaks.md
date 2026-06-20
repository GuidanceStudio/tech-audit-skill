# Gitleaks

**What it catches**: committed secrets (API keys, tokens, `.env` content) anywhere in the git history.

## Install

```sh
# macOS / Linux
brew install gitleaks
# OR
go install github.com/gitleaks/gitleaks/v8@latest
```

## Usage

```sh
# Scan the entire git history
gitleaks detect --no-banner --report-format=json --report-path=leaks.json

# Pre-commit hook (block before push)
gitleaks protect --staged --no-banner
```

## CI snippet (GitHub Actions)

```yaml
- name: Gitleaks
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Pre-commit hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
```

## Tuning

- **Inline allow** for false positives: comment `gitleaks:allow` on the offending line.
- **`.gitleaksignore`** for committed-but-known-public credentials.
- **Custom rules** in `.gitleaks.toml` for project-specific token shapes.

## False positives

- Example credentials in docs (`sk_test_xxxxx`) — add to `.gitleaksignore`.
- Tokens in fixtures (`tests/fixtures/sample_jwt.txt`) — allow with comment.
- Long random-looking strings (image digests, UUIDs) — usually auto-filtered by entropy heuristics.

## Deeper variant

For verified-only scanning (lower false-positive rate, slower): **TruffleHog** with `--only-verified`. Add as a separate CI stage if false-positive triage becomes painful, not as a replacement.

## Cross-references

- `threat-models/secret-management.md`.
- `dimensions/D04-security-posture.md`.
