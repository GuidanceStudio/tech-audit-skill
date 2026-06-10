# D14 — Correctness & robustness 🐛

**Question**: "Does the code do the right thing when reality misbehaves — errors, retries, concurrency, boundary inputs? Or does it only work on the demo path?"

Always-deep, and the one dimension the `quick` cut ALWAYS runs on a
diff: functional bugs are the #1 thing a narrow scan exists to catch.
D3 asks whether the *tests* are adversarial; D14 asks whether the
*code* survives the adversary.

## Method

### Swallowed error paths

```sh
# Empty/blind exception handlers
grep -rnE 'catch\s*\([^)]*\)\s*\{\s*\}' --include='*.php' --include='*.ts' --include='*.js' .
grep -rnE '^\s*except[^:]*:\s*(pass|\.\.\.)\s*$' --include='*.py' -A0 .
grep -rn '@unlink\|@file_get_contents\|@mkdir' --include='*.php' .   # PHP @-suppression
grep -rn '|| true' --include='*.sh' .                                # shell: errors discarded
```

Each hit: is the suppression justified and commented? Silent swallow on
a write/network/auth path → 🔴. Uncommented suppression elsewhere → 🟡.

### Check-then-act races (TOCTOU)

```sh
# SELECT-then-INSERT instead of upsert / unique constraint
grep -rnB2 -A6 'firstOrCreate\|exists()\|->count() === 0\|SELECT COUNT' app/ src/ | head -40
# file check-then-use
grep -rnE 'if.*(file_exists|os\.path\.exists|fs\.existsSync)' -A3 . | grep -E 'open|write|unlink|remove' | head
```

Check-then-act on shared state without a transaction, lock, or unique
constraint backing it → 🟡; on money/quota/auth state → 🔴.

### Idempotency of retried operations

For every consumer of a retry-capable source (queue jobs, webhook
handlers, cron catch-ups): what happens when the same message arrives
twice? Look for idempotency keys, natural unique constraints, or
"already processed" guards.

```sh
grep -rln 'ShouldQueue\|@app.task\|process.on\|webhook' app/ src/ | head
```

Double-apply on a billing/credit/notification path → 🔴.

### Transaction boundaries

Multi-step writes (create parent + children, debit + credit, write +
audit-log) must be atomic. Look for sequences of saves without a
wrapping transaction; partial-write on a thrown exception is the bug.

```sh
grep -rn 'DB::transaction\|atomic()\|BEGIN' app/ src/ | wc -l   # compare against multi-write sites
```

Money/quota multi-writes without a transaction → 🔴; other paired
writes → 🟡.

### Resource leaks

```sh
# Python: opens without context manager
grep -rnE '^\s*\w+\s*=\s*open\(' --include='*.py' . | head
# unbounded in-memory growth: appends to module/class-level collections
grep -rnE '(self\.|this\.)\w+\.(append|push)\(' . | head -20
```

Handles/connections opened without `with`/`finally`/`defer` on
long-running processes → 🟡 (→ 🔴 if it's a server loop). Unbounded
caches/queues without eviction → 🟡.

### Boundary conditions

For each new/changed function in scope: empty input, single element,
max-size input, off-by-one at pagination/slicing edges, None/null
flowing where a value is assumed. Read the code with those five inputs
in mind — this is a reading method, not a grep.

### Input validation at trust boundaries

Request → handler → service: are types, ranges, and ownership checked
at the boundary (form request, pydantic model, zod schema), or do raw
values flow into queries and arithmetic? Unvalidated boundary input
reaching a query or money calculation → 🔴.

### Time and encoding pitfalls

```sh
grep -rn 'datetime.now()\|new Date()' --include='*.py' --include='*.ts' . | head   # naive vs aware / server-local tz
grep -rn 'strftime\|toLocaleString' . | head
```

Naive datetimes mixed with aware, or server-local timezone assumptions
in stored/compared timestamps → 🟡 (→ 🔴 when billing periods or token
expiry depend on it).

## PoC bar

- No silent error swallowing on write/network/auth paths.
- Retried operations are idempotent (key, constraint, or guard).
- Money/quota multi-writes are transactional.
- Boundary inputs (empty, max, null) handled on changed code paths.

## Production bar

- Idempotency keys on every externally-triggered mutation.
- Race-prone paths covered by concurrency tests (parallel duplicate
  requests).
- Resource lifecycles managed by construction (context managers,
  pooling) — not by review.
- All stored timestamps UTC; conversions only at the presentation edge.

## Cross-references

- D3 — tests-as-adversaries: every bug class found here deserves a
  pinning test there.
- D9 — data model integrity: constraints are the DB-side half of the
  idempotency/race story.
- `threat-models/ai-runtime.md` — model-output trust is the agentic
  special case of input validation.
