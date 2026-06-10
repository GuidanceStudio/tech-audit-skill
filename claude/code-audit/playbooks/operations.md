# Operations playbook

How the audit hygiene runs day-to-day. Four sections — read whichever applies.

---

## 1. Cadence

Calibrated for a 1–3 engineer shop at PoC → BETA with paying customers. SOC2 / ISO27001 readiness programs are a trap at this scale (months of paperwork for zero customer value pre-first-enterprise-deal); calibrate up only when a real prospect requires it.

| Tier | What runs | When | Effort |
|---|---|---|---|
| **Per push** (automated, blocking CI) | lint, type-check, secret scan, dep CVE, container scan, unit + tenancy tests | Every PR + push to main | 0 min/engineer (CI runs it) |
| **Per release tag** (human) | `cuts/release.md` — scan all dims + deep on diff since previous tag | Before tagging `v0.x.y` | ~30 min |
| **Quarterly** (half-day) | `cuts/full.md` + restore-from-backup drill + dep major-version sweep + sub-processor list refresh | Every 3 months | 5-7 h |
| **Triggered** (out-of-cycle) | Targeted dims | New channel/integration; new tenant tier; post-incident; secret-store change | Variable |

**Always-deep** dimensions (D1, D2, D3, D13) run at every release-tag pass. They decay invisibly between audits.

**Default-deep** dimensions (D4, D5, D8) run at every release-tag pass for products with multi-tenant or external-integration surface.

**Scan-only** dimensions (D6, D7, D9, D11, D12) run quarterly OR when an incident promotes them.

**Release-only deep** (D10) runs only when a release tag is being cut.

---

## 2. Starter pack — 30 min/week, 5 weeks

Onboarding plan when bootstrapping audit hygiene from scratch. Each step is ~30 min of focused work. After week 5 the ongoing cost is ~10 min/week.

| Week | Step | Outcome |
|---|---|---|
| 1 | **Gitleaks** as pre-commit hook + GH Action across all repos | Secrets become impossible to commit; existing history triaged. |
| 2 | **Trivy** + **Renovate/Dependabot** in CI, blocking on HIGH/CRITICAL | Container CVE alerts + auto-PR for dep bumps. Closes the "Log4Shell at 2am no playbook" gap. |
| 3 | **Semgrep** CI with `p/owasp-top-ten` + stack packs, in warn-not-fail mode for one week, then flip to block | Cross-language SAST as a passive safety net. |
| 4 | Write 5 cross-tenant probe tests as a Pest / pytest dataset (per `threat-models/multi-tenant-isolation.md`) | The multi-tenant promise becomes a CI gate. |
| 5 | **pgTAP** RLS assertions for the 3 most sensitive tables | DB-level isolation invariants checkable in CI. |

Optional follow-ups (when audit findings expose the need):
- **PHPStan / Larastan level 6** when D1 surfaces PHP type-laxness.
- **Ruff + mypy strict** when D1 surfaces the same on the Python side.
- **jscpd clone detection** when D1 flags duplicate code clusters.
- **pgTAP coverage extension** beyond the 3 sensitive tables.

Ongoing weekly maintenance (~10 min):
- Review the week's Renovate / Dependabot PRs.
- Triage one Semgrep finding.
- Quarterly: run one restore-from-backup drill.

---

## 3. Anti-patterns — DON'T

For a 1-3 engineer shop pre-first-enterprise-deal, these audit practices look reasonable in process docs but produce zero customer value at this stage. Calibrate up only when the org needs it.

1. **Full SOC2 readiness program.** 3-6 months of paperwork before any customer asks. Start when a real €50k+ ARR enterprise prospect requests it.

2. **PR review with 2+ approvers.** At 1-3 engineers, the founder's "push-to-main with strong CI" preference matches the established 37signals / Basecamp playbook. PR ceremony starts paying for itself around 5-8 engineers.

3. **100% line-coverage targets.** Encourages assertion-free tests. Target *branch coverage* on tenant-isolation and billing paths only.

4. **Quarterly external pen-test at PoC stage.** €5-15k per round for findings CI would catch. Wait for product-market fit + first paying enterprise.

5. **Security committee with formal meetings.** Two engineers don't need governance — they need a 1-pager incident runbook in `docs/security/`.

6. **Custom ADR system or formal CHANGELOG ceremony.** The devplan + git log already function as the decision log. Adding a parallel system doubles maintenance for zero new info.

7. **Snyk / SonarCloud paid tier.** Trivy + Semgrep + native `composer / npm / pip audit` cover ~90% for €0.

8. **STRIDE / formal threat-model documents per feature.** Nobody reads them. Replace with a 5-line "what changed in trust boundaries?" note at release-tag time.

9. **License-compliance scanners (FOSSA, Black Duck).** Useful at enterprise sale; premature now. `composer licenses` + `pip-licenses` ad-hoc is enough.

---

## 4. What bites if skipped

These look optional until they don't. Do them even when nothing's asking.

- **Quarterly backup-restore drill.** Backups never restored aren't backups, they're hope.
- **Cross-tenant regression suite.** The day a multi-tenant bug ships to a paying customer, the privacy promise dies.
- **Key rotation runbook.** Leaked OpenRouter / Stripe / OAuth token at 2am with no playbook = panic.
- **Dep CVE alerting wired to chat.** Log4Shell-class events need <24h response, not "we'll check Monday".
- **"What does this AI-written module do?" review.** With 30-70% LLM-assisted code, file-level dead-weight accretes silently. Quarterly D1 deep pass catches it before it becomes refactor-blocking.

## Cross-references

- `tools/_matrix.md` — the canonical tool list.
- `templates/ci-github-actions.yml` — starter CI workflow.
- `templates/ci-pre-commit.yaml` — starter pre-commit hooks.
- `dimensions/D01-code-essentiality.md` (LLM-assisted-code addendum).
