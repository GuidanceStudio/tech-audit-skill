# Tool wiring matrix

Open-source-first stack for a multi-stack shop (PHP + Python + TS + shell + Docker). All free. ~1 engineer-day to wire end-to-end. ~10 min/week ongoing.

## The canonical set

| Tool | Layer | Catches | Setup | Per-file detail |
|---|---|---|---|---|
| **Gitleaks** | secrets in git history | committed `.env`, API keys, tokens | 5 min | `gitleaks.md` |
| **Trivy** | container CVE + IaC + SBOM + filesystem | vuln base images, exposed Dockerfile patterns, dep CVEs in lockfiles | 15 min | `trivy.md` |
| **Semgrep** | cross-language SAST | OWASP top 10, framework-specific anti-patterns | 15 min | `semgrep.md` |
| **PHPStan + Larastan** | PHP types + Laravel rules | missing auth checks, `withoutGlobalScopes` strips, `$fillable` drift | 20 min + baseline | `phpstan-larastan.md` |
| **Ruff** | Python lint + Bandit ruleset | insecure subprocess, eval, weak crypto, type hints | 10 min | `ruff.md` |
| **mypy** | Python types | implicit Any, contract violations | 30 min + ignore list | `mypy.md` |
| **Biome** | TS lint + format | `no-floating-promises`, `no-explicit-any` | 10 min | `biome.md` |
| **Hadolint** | Dockerfile lint | latest-tag, root user, missing healthcheck | 10 min | `hadolint.md` |
| **jscpd** | cross-language clone detection | LLM-pasted dead code clusters (D1) | 10 min | `jscpd.md` |
| **pgTAP** | DB-level RLS policy assertions | tenant leak via misconfigured policy | 2-3h once | `pgtap.md` |
| **Renovate / Dependabot** | auto-bumping deps | stale CVE-fixable versions | 5 min | `auto-dep-updates.md` |
| **shellcheck** | shell scripts | SC2086, secrets in argv | (already canonical) | see `languages/shell.md` |

## What to skip at this scale

- **Snyk / SonarCloud paid tiers** — Trivy + Semgrep + native `composer / npm / pip audit` cover ~90% for €0.
- **WAF, IDS/IPS, dedicated SIEM** — defer until first enterprise contract requires.
- **Sigstore / cosign image signing** — defer.
- **Formal SBOM signing / attestation pipelines** — Trivy generates SBOM; that's enough at this scale.
- **TruffleHog as a separate stage** — gitleaks covers 90%. TruffleHog (verified-only) is the deeper variant if false positives become a problem.

## Wiring order — fast-feedback first

When running tools (in CI or interactively), order by speed so the operator sees something within seconds:

1. **Gitleaks** (seconds).
2. **composer audit / npm audit / pip-audit** (seconds).
3. **Linters** (Ruff, Biome, PHPStan — seconds to a minute each).
4. **Type checks** (mypy, tsc — minute or two).
5. **Trivy fs scan** (~minute on first run, cached after).
6. **Semgrep with the right rule packs** (a few minutes).
7. **Stack-specific deep SAST** (Psalm with TaintAnalysis — several minutes).

If a fast tool surfaces 🔴, escalate immediately. Don't wait for the slow tools.

## CI wiring snippets

See `templates/ci-github-actions.yml` and `templates/ci-pre-commit.yaml` for ready-to-copy snippets.

## Cross-references

- Each tool: dedicated `tools/<tool>.md` with installation, sample config, false-positive triage.
- `playbooks/operations.md` § Starter pack — 5-week / 30-min-per-week onboarding sequence.
