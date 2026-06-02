# pgTAP

**What it catches**: DB-level invariants — row-level security (RLS) policies actually working, schema constraints holding, foreign-key cascades behaving. The last line of defense when application-layer multi-tenant scope might be buggy.

## Install

```sh
# As a PostgreSQL extension on the DB host
sudo apt-get install postgresql-XX-pgtap  # Debian/Ubuntu, XX = major version

# Then in the DB
CREATE EXTENSION pgtap;
```

## Usage

```sql
-- tests/db/test_rls.sql
BEGIN;
SELECT plan(3);

-- Set tenant A's context
SET app.current_tenant TO 'tenant-a-uuid';
SELECT results_eq(
  'SELECT COUNT(*) FROM conversations WHERE tenant_id = ''tenant-a-uuid''',
  ARRAY[(SELECT COUNT(*) FROM conversations WHERE tenant_id = ''tenant-a-uuid'')::bigint],
  'tenant A sees own conversations'
);

-- Switch to tenant B's context
SET app.current_tenant TO 'tenant-b-uuid';
SELECT is_empty(
  'SELECT * FROM conversations WHERE tenant_id = ''tenant-a-uuid''',
  'tenant B sees NO of tenant A''s conversations (RLS blocks)'
);

-- Negative: try to disable RLS as a non-superuser
SELECT throws_ok(
  'ALTER TABLE conversations DISABLE ROW LEVEL SECURITY',
  '42501',
  NULL,
  'non-superuser cannot disable RLS'
);

SELECT * FROM finish();
ROLLBACK;
```

Run with `psql`:

```sh
psql -X -f tests/db/test_rls.sql -d my_db
```

Or wire into pytest:

```python
def test_rls_policies():
    out = subprocess.run(
        ["psql", "-X", "-f", "tests/db/test_rls.sql", "-d", DB_NAME],
        capture_output=True, text=True,
    )
    assert "ok" in out.stdout and "not ok" not in out.stdout
```

## CI snippet

```yaml
- name: pgTAP RLS checks
  run: |
    psql -X -f tests/db/test_rls.sql -d $POSTGRES_DB
```

## RLS policy template

```sql
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_select ON conversations
  FOR SELECT
  USING (tenant_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY tenant_isolation_modify ON conversations
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);
```

Then test each policy with pgTAP — separate assertions for SELECT, INSERT, UPDATE, DELETE.

## Cross-references

- `threat-models/multi-tenant-isolation.md`.
- `dimensions/D05-multi-tenant-isolation.md`.
