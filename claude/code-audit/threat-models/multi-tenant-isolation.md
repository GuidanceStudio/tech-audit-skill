# Threat model — multi-tenant isolation

The #1 reputation-ending bug class for B2B SaaS. Every check in D5 maps to one of these underlying patterns.

## Pattern 1 — request-supplied tenant ID

```python
@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: UUID):
    return await db.fetch("SELECT * FROM agents WHERE id = $1", agent_id)
    # Anyone with a valid session can read ANY agent if they guess the ID.
```

**Fix**: derive tenant from auth, scope the query:

```python
@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: UUID, user: User = Depends(current_user)):
    return await db.fetch(
        "SELECT * FROM agents WHERE id = $1 AND tenant_id = $2",
        agent_id, user.tenant_id,
    )
```

**Detect**: every endpoint that takes an ID in the URL → grep for the corresponding service / repo method → trace whether tenant_id is in the WHERE.

## Pattern 2 — async-pool connection reuse (silent)

```python
# Setting tenant on a connection at startup binds to THAT connection only.
# When the pool reuses it for another request, the setting persists OR resets
# depending on what's between requests.

await conn.execute("SET app.current_tenant = ?", tenant_id)
result = await conn.execute("SELECT * FROM conversations")
# If conn is reused by another request without re-setting tenant,
# the new request reads with the OLD tenant context.
```

**Fix**: `SET LOCAL` inside a transaction (auto-resets on commit/rollback):

```python
async with pool.acquire() as conn:
    async with conn.transaction():
        await conn.execute("SET LOCAL app.current_tenant = $1", tenant_id)
        result = await conn.execute("SELECT * FROM conversations")
    # tenant context cleared automatically
```

**Detect** — write a regression test that fails the OLD pattern:

```python
async def test_pool_tenant_isolation():
    # Open 10 connections concurrently, alternating tenant A and B.
    async def query_for(tenant):
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("SET LOCAL app.current_tenant = $1", tenant)
                rows = await conn.fetch("SELECT tenant_id FROM conversations")
                for r in rows:
                    assert r["tenant_id"] == tenant, f"LEAK: {r}"

    await asyncio.gather(*[
        query_for(TENANT_A) if i % 2 == 0 else query_for(TENANT_B)
        for i in range(20)
    ])
```

This test pins the bug — if anyone removes the `SET LOCAL`, the test catches it on the next run.

## Pattern 3 — global-scope bypass

```php
// Laravel — withoutGlobalScopes strips tenant scope
$results = Agent::withoutGlobalScopes()->where('name', 'doc-qa')->get();
// Returns agents from EVERY tenant.
```

**Fix**: don't bypass unless documented + tested. If bypass is required (admin tooling, reporting), gate by role + log it.

**Detect**:

```sh
grep -rnE 'withoutGlobalScopes?\(|::unscoped\(\)|->skip[Gg]lobalScope' .
```

Each match needs a comment + a test that the bypass doesn't leak to non-admin paths.

## Pattern 4 — raw query under ORM

```php
DB::raw("SELECT * FROM conversations WHERE user_id = $userId")
// Skips Eloquent's global scope. Even if $userId is properly bound,
// no tenant_id in the WHERE means cross-tenant leak.
```

**Fix**: include tenant_id in the raw WHERE, or convert to ORM.

**Detect**:

```sh
grep -rnE 'DB::(raw|statement|select)\(|->whereRaw\(' . --include="*.php"
```

## Pattern 5 — quota gate after billable work

```python
async def chat(message):
    response = await llm.complete(message)   # already billed
    if not await quota.has_capacity(user.tenant_id):
        raise QuotaExceeded()                # too late
    await save(response)
```

**Fix**: gate BEFORE the billable call. Use atomic decrement to avoid race:

```python
async def chat(message):
    if not await quota.reserve(user.tenant_id, est_cost):  # atomic + idempotent
        raise QuotaExceeded()
    try:
        response = await llm.complete(message)
        await quota.commit_actual(user.tenant_id, response.actual_cost)
    except Exception:
        await quota.release(user.tenant_id, est_cost)
        raise
    await save(response)
```

## Cross-tenant probe template

The audit you can run on every push:

```python
# tests/integration/test_cross_tenant_probe.py
TENANT_A = make_user("alice@a.test")
TENANT_B = make_user("bob@b.test")
TENANT_B_AGENT_ID = create_agent(TENANT_B)

@pytest.mark.parametrize("method,endpoint", [
    ("GET",    f"/api/agents/{TENANT_B_AGENT_ID}"),
    ("PUT",    f"/api/agents/{TENANT_B_AGENT_ID}"),
    ("DELETE", f"/api/agents/{TENANT_B_AGENT_ID}"),
    ("GET",    f"/api/agents/{TENANT_B_AGENT_ID}/messages"),
    # ... every tenant-scoped resource × every verb
])
def test_tenant_a_cannot_touch_tenant_b(method, endpoint):
    resp = TENANT_A.request(method, endpoint)
    assert resp.status_code in (403, 404), f"LEAK: {endpoint} → {resp.status_code}"
```

## DB-level fallback: RLS

PostgreSQL row-level security as the last line of defense. Even if the application layer is buggy, RLS catches the leak:

```sql
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON conversations
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

Test with `pgTAP` — see `tools/pgtap.md`.

## Cross-references

- `dimensions/D05-multi-tenant-isolation.md` — full method.
- `tools/pgtap.md` — DB-level test harness.
