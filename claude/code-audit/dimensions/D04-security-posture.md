# D4 — Security posture ⚠️

**Question**: "Are there secrets in git? Is the auth model sound? Are the deps free of known CVEs? Do containers run as root? Is privacy enforced where it should be?"

Default-deep. Maps to OWASP ASVS L1 + OWASP Top 10 + cloud-native baseline.

## Method

### Secrets in git history

```sh
# Whole-history scan
gitleaks detect --no-banner --report-format=json --report-path=/tmp/leaks.json
jq '.[] | {file: .File, line: .StartLine, rule: .RuleID}' /tmp/leaks.json

# Verified-only (lower false-positives, slower)
trufflehog git file://. --json --only-verified
```

Any verified leak → 🔴 (rotate the credential immediately, then `git filter-repo` history if the secret is value-only).

See `tools/gitleaks.md` for setup.

### Auth model audit (stack-specific deep-dive)

Load `languages/<stack>.md` for the framework-level checks. Universal checks:

- **State-changing routes without CSRF/origin protection**: grep for routes accepting `POST/PUT/DELETE` and verify the framework's CSRF middleware is on.
- **Auth-bypass via "trusted" header**: any code reading `X-Forwarded-User`, `X-Real-IP`, `X-Tenant-Id` without verifying the gateway authoritatively set it → 🔴.
- **Session fixation**: session ID must rotate on login. Look for `session.regenerate()` or equivalent.
- **Hardcoded credentials in code**: `password === "admin"`, dev-only checks that survived to prod, etc.
- **JWT verification**: see `threat-models/auth-model.md` for full pattern (alg=none, kid confusion, signature stripped).

### Dependency CVEs

```sh
composer audit                 # PHP
npm audit --json               # Node
pip-audit                      # Python
cargo audit                    # Rust
```

Severity grades:
- HIGH / CRITICAL with no upgrade path available → 🟡 (document the mitigation).
- HIGH / CRITICAL with available upgrade → 🔴.
- MODERATE → 🟢 (track, fix in next dep sweep).

See `tools/auto-dep-updates.md` for ongoing alerting.

### Container security

```sh
# Non-root USER in every Dockerfile
for d in $(find . -name "Dockerfile*"); do
  user=$(grep -E '^\s*USER ' "$d" | tail -1 | awk '{print $2}')
  [ -z "$user" ] || [ "$user" = "root" ] && echo "ROOT: $d"
done

# Container vuln scan
trivy image $YOUR_IMAGE
trivy fs .   # also scans IaC + SBOM
```

Any image running as root in production → 🔴.

See `tools/trivy.md`, `tools/hadolint.md`.

### SAST cross-language

```sh
semgrep --config=p/owasp-top-ten --config=p/secrets --json . > /tmp/semgrep.json
jq '.results | length' /tmp/semgrep.json
```

Tune per stack:
- PHP: add `p/laravel`
- Python: add `p/fastapi` or `p/python`
- Node/TS: add `p/typescript` and `p/javascript`

See `tools/semgrep.md` for tuning + false-positive triage.

### Privacy guardrail (when PII is the product)

If the product processes PII, verify every external egress (LLM call, third-party API) routes through the PII de-identification layer:

```sh
# Find external HTTP calls
grep -rnE 'http\.post|requests\.post|HttpClient\(|fetch\(|->post\(' \
  --include="*.py" --include="*.php" --include="*.ts" \
  | grep -vE 'localhost|cerase-|127\.0\.0\.1|internal\.'
```

Each external call NOT going through the PII layer → 🔴 if it carries user input.

See `threat-models/pii-data-flow.md` for the full audit pattern.

### Tenant-scoped secret leak prevention

If the product is multi-tenant with per-tenant credentials (per-tenant API keys, OAuth tokens, etc.):

- Are credentials stored encrypted at rest with a tenant-scoped key?
- Can a code path read tenant A's credential while serving tenant B's request? See D5.
- Are credentials redacted from logs?

```sh
grep -rnE 'logger\..*\$.*token|console\.log.*token|fmt\.Print.*token' .
```

### Backup encryption

If backups exist, they must be encrypted at rest with a key NOT stored alongside the data. Common failure: `.tar.gz` of database in the same S3 bucket as a `key.txt`.

- Are backups encrypted? (`gpg`, `age`, `restic`, ...)
- Is the encryption key rotated?
- Where is the key stored?

Unencrypted backup with PII inside → 🔴.

## PoC bar

- No secret in git history (verified).
- No SQLi in the admin panel.
- All containers run as non-root.
- Dependencies <12 months behind major versions.
- Privacy guardrail on every external LLM call.
- Backups encrypted at rest.

## Production bar

- SAST + DAST in CI, blocking on HIGH/CRITICAL.
- Secret rotation policy documented + tested.
- Threat model documented (`docs/security/threat-model.md`).
- Pen-test report from a recognized firm (only after PMF + first enterprise prospect).
- Bug-bounty program (only at enterprise scale).

## Cross-references

- `threat-models/auth-model.md` — JWT verification deep-dive.
- `threat-models/secret-management.md` — bootstrap + rotation patterns.
- `threat-models/pii-data-flow.md` — PII corpus + masking pipeline.
- `tools/{gitleaks,trivy,semgrep,hadolint}.md`.
- `languages/<stack>.md` — framework-level auth gotchas.
