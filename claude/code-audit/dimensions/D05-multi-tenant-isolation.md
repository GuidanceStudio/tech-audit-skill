# D5 — Multi-tenant isolation ⚠️

**Question**: "Does `tenant_id` propagate through every query? Are quotas enforced before the work happens? Is billing accurate per tenant?"

Default-deep when the product is multi-tenant. Skip entirely for single-tenant products.

A single missed cross-tenant data leak is reputation-ending. This is the audit you do not skip.

## Method

### Service-method propagation trace

Pick 10 service methods that read/write tenant-owned data. For each, trace the call path from HTTP handler to DB query:

```
1. HTTP handler: where does `tenant_id` enter?
   - From the authenticated session (good) — `Auth::user()->tenant_id`
   - From a URL parameter (red flag — the user could pass another tenant's ID)
   - From a request body (red flag — same risk)
2. Service layer: how is `tenant_id` passed down?
   - Implicit (global scope, middleware-set) — auditable
   - Explicit argument — auditable
   - Pulled from session inside the service — coupling, but OK
   - Pulled from auth inside the model — surprise, fragile
3. DB query: does the WHERE include `tenant_id`?
   - Yes, every time → ✅
   - Through a global scope → ✅ but check the scope can't be bypassed (see below)
   - Sometimes → 🔴
```

For each method, verify the `tenant_id` originates from **authentication context**, never from request-supplied data without an explicit "is this user authorized for this tenant?" check.

### Global-scope bypass scan

Frameworks like Laravel offer `withoutGlobalScopes()` as an escape hatch. Search every use:

```sh
grep -rnE 'withoutGlobalScopes?\(|::unscoped\(\)|->skip[Gg]lobalScope' . \
  --include="*.php" --include="*.py"
```

Each use must have a comment explaining WHY the global scope is bypassed AND have a corresponding test that this path doesn't leak across tenants. Bypasses without justification → 🔴.

### Raw-query scan

Raw queries skip ORM global scopes:

```sh
grep -rnE 'DB::raw\(|DB::statement\(|->whereRaw\(|cursor\.execute\(' .
```

Each raw query must include `WHERE tenant_id = ?` (or equivalent). Missing → 🔴 on tenant-scoped tables.

### Cross-tenant probe suite

The audit you can run repeatedly. Authenticate as tenant A; try every endpoint with tenant B's IDs:

```python
# scripts/_cross_tenant_probe.py (sketch)
TENANT_A = ("alice@acme.example", "...")
TENANT_B_AGENT_ID = "01HAB-..."   # known to exist on tenant B

session = login(*TENANT_A)
for endpoint in [
    f"/api/agents/{TENANT_B_AGENT_ID}",          # GET
    f"/api/agents/{TENANT_B_AGENT_ID}",          # PUT
    f"/api/agents/{TENANT_B_AGENT_ID}",          # DELETE
    f"/api/agents/{TENANT_B_AGENT_ID}/messages", # nested
    # ...repeat for every tenant-scoped resource
]:
    resp = session.request(...)
    assert resp.status_code in (403, 404), f"LEAK: {endpoint} -> {resp.status_code}"
```

Run on every push as CI integration tests. Any leak → 🔴.

### Async-pool tenant context

The #1 silent tenant-leak pattern in async/pooled apps: a database connection reused across requests without re-applying the tenant context. Pure-unit tests miss this.

See `threat-models/multi-tenant-isolation.md` for the full pattern + test code.

Required check whenever the codebase touches:
- asyncpg pool
- psycopg connection pool
- Laravel's database manager with non-default connections
- ORM session reuse across goroutines / async tasks

### Quota / rate-limit gate

For products that meter usage per tenant:

- Where is the gate? (before or after the billed work?)
- Is the gate atomic? (or is there a race where two parallel calls both pass?)
- Is the gate bypassable? (admin path that skips it, "system" tenant, etc.)

Quota gate that runs AFTER the LLM call → 🔴 (revenue leak under burst).

### Billing reconciliation test

```python
# Ensure tenant A's spend doesn't land on tenant B's invoice
def test_billing_isolation():
    tenant_a, tenant_b = setup_two_tenants()
    burn_credits(tenant_a, amount=10)
    burn_credits(tenant_b, amount=5)
    assert get_invoice(tenant_a).total == 10
    assert get_invoice(tenant_b).total == 5
    assert get_invoice(tenant_a).line_items.tenant == tenant_a  # not B!
```

Missing → 🔴.

### DB-level invariants (Postgres RLS)

If the DB layer supports row-level security:

```sql
-- Enable + force RLS on tenant-scoped table
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON conversations
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

Then assert via pgTAP that the policy holds under role switches.

See `tools/pgtap.md` for the test harness.

## PoC bar

- Every Eloquent / ORM query on a tenant-scoped table goes through a global scope.
- Quota gate runs **before** every billed call.
- ≥1 cross-tenant isolation test in the suite (negative case: tenant A cannot read tenant B).
- Async-pool tenant context test if connection pooling is used.

## Production bar

- Row-level security at the DB level (Postgres RLS) or sharded DBs.
- Continuous tenant-isolation fuzzing (random tenant pairs, every endpoint).
- pgTAP RLS policy assertions in CI.
- Per-tenant resource limits at the cluster level (CPU, memory, connection cap).

## Cross-references

- `threat-models/multi-tenant-isolation.md` — async-pool pattern, cross-tenant probe template.
- `tools/pgtap.md` — DB-level test wiring.
- `languages/<stack>.md` — framework-specific bypass patterns (Laravel `withoutGlobalScopes`, Eloquent global-scope ergonomics, etc.).
