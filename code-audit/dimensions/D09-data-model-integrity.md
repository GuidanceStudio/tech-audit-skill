# D9 — Data model integrity 🗄️

**Question**: "Are migrations safe (no DROP on shipped tables)? Is the audit log append-only? Are foreign keys declared? Is the schema documented?"

Scan dimension. The bar is "no production-data loss vector exists in code". A 🔴 here can mean unrecoverable data corruption.

## Method

### Destructive migration scan

```sh
grep -rnE "drop|DROP" $(find . -name "migrations" -type d) \
  | grep -vE "drop[A-Z]?[Cc]olumn|drop[Ii]ndex|drop[Ff]oreign"
```

`drop_column` on a column nobody reads → 🟡 (operator decides).
`Schema::drop('users')` on a table that exists in any released migration → 🔴.
`TRUNCATE` or `DELETE FROM` in a migration → 🔴 unless explicitly scoped to test fixtures.

### Migration runtime

A migration that takes >1s on a fresh DB is suspicious — likely doing a data backfill rather than schema-only work. Inspect each:

```sh
# Time migrations on a fresh DB
docker run --rm -v $(pwd):/repo -w /repo $YOUR_IMAGE \
  sh -c "php artisan migrate:fresh --pretend"
```

Slow migration that should be a one-off backfill → 🟡 (move to a separate `php artisan db:backfill` / Django data-migration command).

### Audit log invariants

If the project has an audit log / event log / activity log:

```sh
grep -rnE "(DELETE FROM|->delete\(\)|::truncate\(\)|->forceDelete\(\))" --include="*.php" --include="*.py" \
  | grep -iE "audit|event_log|activity"
```

Any DELETE / UPDATE path on the audit log → 🔴 unless gated by an explicit admin operation with audit-of-the-audit logged.

Foreign keys from the audit log → other tables with `ON DELETE CASCADE`:

```sh
grep -rnE "foreign.*audit|references.*audit.*on delete cascade" migrations/
```

Cascading deletes from operational tables into the audit log → 🔴 (deleting a user nukes their history).

### Foreign keys

Every relation in a tenant-scoped table should declare a FK with an appropriate `ON DELETE` policy:
- `CASCADE` — only when the child is fully owned by the parent.
- `RESTRICT` / `SET NULL` — for shared / soft-owned relations.
- `NO ACTION` — only with explicit reason.

Missing FK → 🟡. FK with `ON DELETE CASCADE` from tenant to a multi-tenant resource (shared template, etc.) → 🔴.

### Schema documentation

```sh
# Does the architecture doc reflect the latest migration?
last_migration=$(ls migrations/*.sql migrations/*.php 2>/dev/null | tail -1)
last_doc_update=$(git log -1 --format="%aI" docs/architecture/schema.md 2>/dev/null)
last_migration_date=$(git log -1 --format="%aI" "$last_migration" 2>/dev/null)
echo "migration: $last_migration_date  doc: $last_doc_update"
```

Doc older than the last migration → 🟡 (schema doc drift; D2 catches the general case).

### Backup / point-in-time recovery

This overlaps with D6 (operational readiness) but D9 owns the data-loss invariant:

- Is `pg_dump` / equivalent run on a schedule?
- Is WAL archiving on?
- What's the RPO (max acceptable data loss in minutes)?
- What's the RTO (max acceptable time to restore)?

Unmeasured / undocumented RPO/RTO at any non-trivial scale → 🟡.

## PoC bar

- No DROP TABLE on tables released in any past migration.
- Audit log accepts inserts only (or has gated DELETE with audit-of-audit).
- Foreign keys on every relation.
- Migrations complete in <1s on a fresh DB (or are flagged as backfill).

## Production bar

- Migrations gated by env (`prod` requires explicit opt-in for destructive ops).
- Audit log hash-chained or append-only at the storage layer.
- Schema versioned in a registry (DBT, Alembic, Atlas, ...).
- RPO / RTO documented + drilled.

## Cross-references

- D6 — operational backups + restore drills.
- `threat-models/data-loss.md` — broader data-loss patterns (untested backups, cascade chains).
