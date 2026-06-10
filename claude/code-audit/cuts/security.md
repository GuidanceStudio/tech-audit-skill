# Security pass cut

~30 minutes. OWASP-flavoured + multi-tenant + secrets. No depth on UX,
no depth on docs.

## When to invoke

- User says "security review" / "security audit" / "vuln scan" / "OWASP review".
- A new auth surface or external integration just landed.
- Pre-release security check before tagging.

## Inputs

- Repo root (or a specific service if the user narrows).
- (Optional) the threat the user is most worried about — surfaces it
  first in the report.

## Procedure

1. **Detect the stack** (per `SKILL.md` § Step 2). Load matching
   `languages/<stack>.md`.

2. **Run dimensions in order**:
   - **D4 — Security posture** (always).
   - **D5 — Multi-tenant isolation** (only if the product is
     multi-tenant — skip otherwise).
   - **D7 — Dependency hygiene** (CVE focus — pull just the security
     subset).
   - Targeted bits of **D9 — Data model integrity** (audit log
     append-only, destructive migrations).

3. **Load threat-models on demand** based on what D4 + D5 surface:
   - Auth-related findings → `threat-models/auth-model.md`.
   - PII handling → `threat-models/pii-data-flow.md`.
   - Secret bootstrap → `threat-models/secret-management.md`.
   - Async / pooled DB → `threat-models/multi-tenant-isolation.md`.
   - LLM / agent / MCP / tool-gateway surface → `threat-models/ai-runtime.md`
     (default-load when detect-stack flags an agentic product).

4. **Run automated tools** (read `tools/<tool>.md` for usage; emit the
   commands the user should run if you can't run them yourself):
   - `gitleaks detect --no-banner` (always).
   - `trivy fs .` (always — covers IaC + SBOM + deps + image).
   - `semgrep --config=p/owasp-top-ten --config=p/secrets` + stack pack.
   - Stack-specific SAST (`phpstan` + `psalm-taint`, `mypy --strict`,
     `tsc --noEmit --strict`, ...).

5. **Emit per `templates/security-pass-output.md`**:
   - Executive summary (top risk in one line).
   - Findings table grouped by severity.
   - Threat-model annotations (e.g. "this is the async-pool tenant
     leak pattern, see threat-models/multi-tenant-isolation.md").
   - Suggested next steps (which findings to fix this week, which to
     accept as risk, which need a longer milestone).

## What this cut does NOT do

- It does NOT do compliance / GDPR posture (that's D11, in `full`).
- It does NOT do performance / cost (D10, release-only deep).
- It does NOT block a release on 🟡 alone. Release-block recommendation
  only for 🔴.

## Tooling order

Run tools cheap-first per `tools/_matrix.md` § Wiring order. If a fast
tool surfaces 🔴, surface that finding immediately — don't make the
operator wait for the slow tools.

## Cross-references

- `dimensions/D04-security-posture.md`
- `dimensions/D05-multi-tenant-isolation.md`
- `threat-models/*` — loaded on demand.
- `tools/*` — per-tool commands.
- `templates/security-pass-output.md` — output template.
