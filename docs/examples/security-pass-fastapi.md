# Example — security pass on a FastAPI service

Synthetic. Stack: Python 3.13 + FastAPI + asyncpg + Postgres. Reference for `cuts/security.md` output.

---

# Security review — 2026-06-10

**Scope**: `gateway/` (FastAPI service)
**Reviewer**: Claude code-audit skill
**Stack detected**: Python / FastAPI / asyncpg / Postgres
**Tools run**: gitleaks, pip-audit, ruff (with S codes), mypy, semgrep (`p/owasp-top-ten`, `p/fastapi`), trivy (fs)

---

## Top risk (one line)

An async DB connection's tenant context persists across request boundaries — tenant A's request can read tenant B's data under specific pool re-use patterns.

---

## Findings — by severity

### 🔴 Ship-blockers

#### 🔴 Async-pool tenant context not re-applied on connection re-use

- **Where**: `gateway/src/cerase_gateway/db_pool.py:42`
- **What**: `await conn.execute("SET app.current_tenant = $1", tid)` is called once when the pool initializes a connection. Subsequent requests acquiring that same pooled connection inherit the previous request's tenant context.
- **Why it matters**: A request from tenant A can see rows belonging to tenant B whenever connection re-use happens to align tenant boundaries. An attacker timing requests can reproduce the leak deterministically.
- **Suggested fix**: use `SET LOCAL` inside a transaction. The `LOCAL` scope auto-resets on commit/rollback:

  ```python
  async with pool.acquire() as conn:
      async with conn.transaction():
          await conn.execute("SET LOCAL app.current_tenant = $1", tid)
          # query within this transaction is correctly scoped
  ```

- **Effort**: 30 min including the regression test (see `threat-models/multi-tenant-isolation.md` § Pattern 2 for the test template).
- **Threat model**: `threat-models/multi-tenant-isolation.md` § Pattern 2.

---

### 🟡 Fix soon

| Where | What | Why it matters | Fix | Effort |
|---|---|---|---|---|
| `gateway/src/cerase_gateway/server.py:48` | `CORSMiddleware` configured with `allow_origins=["*"]` AND `allow_credentials=True` | Browsers historically permit this combo despite spec; CSRF universal | Pin `allow_origins=[<actual prod origins>]` | 10 min |
| `gateway/src/cerase_gateway/server.py:142` | Background task fires `await db.execute(...)` without re-applying tenant context | Same root cause as the 🔴 above; affects async fire-and-forget paths | Pass `tenant_id` explicitly into the background task closure | 30 min |
| `gateway/src/cerase_gateway/logging.py:18` | Logger format includes `%(request_body)s`; PII could land in logs | Privacy regression risk; D11 applies | Switch to structured logger with field-level redaction (`structlog` processors) | 1 h |

---

### 🟢 Notes for the next cycle

- `gateway/src/cerase_gateway/auth.py:24` — JWT verification correctly pins `algorithms=["RS256"]`, audience, and issuer. ✅
- All Pydantic models use `response_model=` on routes. ✅
- `trivy fs .` flagged 0 HIGH/CRITICAL in deps.
- `gitleaks` clean over full history.

---

## Threat-model coverage

| Threat model | Status | Notes |
|---|---|---|
| Auth model | ✅ | JWT verification correct; session/JWT not mixed. |
| Multi-tenant isolation | ❌ | The async-pool finding is canonical. |
| Secret management | ✅ | Secrets read from `/var/cerase/secrets/` (named volume); no operator-fillable cluster-internal placeholders in `.env.example`. |
| PII data flow | ⚠️ | Logger PII risk noted; otherwise PII routes through the Presidio layer. |

---

## Tool output summary

| Tool | Findings | Top issue |
|---|---|---|
| gitleaks | 0 | — |
| pip-audit | 0 HIGH/CRITICAL, 2 MODERATE | `urllib3 2.0.7` — patched in 2.0.8; auto-bump pending |
| ruff (S) | 1 | `S307` `eval()` in a dev-only debug endpoint; acceptable if guarded by env flag |
| mypy --strict | 4 type errors | All in legacy `routes/legacy.py`; baseline'd, plan to address in v0.2 |
| semgrep p/owasp + p/fastapi | 3 | All covered by 🟡 findings above |
| trivy fs | 0 | — |

---

## Recommendation

**Block release** — the async-pool finding is a multi-tenant data-leak bug. Fixing it is 30 min (mechanical), with a regression test. The 🟡 items can ship in the next cycle.

Once the 🔴 clears, the service is in good security posture for BETA.
