# Python / FastAPI — language-specific checks

Patterns to apply beyond the universal D1-D13 methods.

## Pydantic data exposure (D4)

- **`.dict()` echoes everything** — including fields the API shouldn't expose. Always use `response_model=` on FastAPI routes so the schema is enforced server-side.
- **`Field(exclude=True)`** — ensure it's actually used for non-API fields (`password_hash`, `tenant_id` when leaking sideways, internal flags).
- **`model_config = {"extra": "allow"}`** — permits extra fields. 🟡 unless explicitly justified.

## Async pool gotchas (D5)

The #1 silent tenant-leak pattern in FastAPI: a database connection from the pool reused across requests without the tenant context being re-applied. See `threat-models/multi-tenant-isolation.md`.

```python
# WRONG: tenant context set once at startup
await conn.execute("SET app.current_tenant = ...")  # only on this connection

# RIGHT: SET LOCAL per request, with `LOCAL` scope so it auto-resets on commit/rollback
async with pool.acquire() as conn:
    async with conn.transaction():
        await conn.execute("SET LOCAL app.current_tenant = $1", tenant_id)
        ...
```

Test pattern: `tests/test_rls_pool_reuse.py` — see threat-model file.

## BackgroundTasks tenant context propagation

```python
@app.post("/agents")
async def create_agent(...):
    bg.add_task(send_welcome_email, agent_id)
    # If send_welcome_email uses an async pool, it has NO tenant context unless explicitly passed.
```

BackgroundTasks running queries → propagate tenant_id explicitly. 🔴 if cross-tenant leak possible.

## CORS + credentials (D4)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ← anti-pattern
    allow_credentials=True,        # combined with above = CSRF universal
    ...
)
```

`allow_origins=["*"]` + `allow_credentials=True` → 🔴. Browsers should refuse this combo but historically don't always.

## Logging request bodies with PII (D4, D11)

```python
@app.middleware("http")
async def log_requests(request, call_next):
    body = await request.body()
    logger.info(f"Request: {body.decode()}")   # ← PII leak
```

Raw body logging when the product handles PII → 🔴. Route through the PII de-identification layer or whitelist field-level logging.

## Async exception propagation

```python
try:
    await some_call()
except Exception as e:
    logger.exception(e)   # ← swallow + continue is silent failure
```

See D12 — notification surface anti-pattern.

## Type safety (D1, D4)

- `from typing import Any` → grep for use; minimize.
- `# type: ignore` without an accompanying issue → 🟡.
- `mypy --strict` should pass on at least the service layer.

## Dependency injection ergonomics (D1)

FastAPI's `Depends()` is great until it becomes a 5-layer factory chain. If a single endpoint pulls 4+ `Depends` deep, it's a smell — likely the service layer is over-decomposed.

## ReDoS via user-supplied regex (D4)

```python
import re
# user-controlled pattern → catastrophic backtracking
re.match(user_input, target)
```

Compile + timeout, or use `regex` package, or constrain the input. 🟡.

## Tools to run

- **Ruff** with `--select S,B,E` (Bandit ruleset via ruff, 10-100× speed).
- **mypy --strict** on the service layer.
- **pip-audit** for dep CVE.

## Stack-specific anti-patterns (LLM-generated)

When 30-70% of code is AI-assisted, expect:
- `class XService` + `class XRepository` + `class XManager` for what could be 3 functions.
- `Pydantic` models duplicated across `schemas.py`, `models.py`, `dto.py`.
- Multiple `db.py` files at different layers (`infrastructure/db.py`, `app/db.py`, `core/db.py`).
- Generic `BaseService` / `BaseRepository` with no second concrete impl.

## Cross-references

- `threat-models/multi-tenant-isolation.md` — async pool tenant context.
- `threat-models/pii-data-flow.md` — Pydantic-aware PII handling.
- `tools/ruff.md`, `tools/mypy.md`.
