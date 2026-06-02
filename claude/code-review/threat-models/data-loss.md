# Threat model — data loss

The audit pattern: assume something WILL be lost; check whether we can recover.

## Recovery objectives

- **RPO** (Recovery Point Objective) — how much data are we willing to lose? (e.g. "up to 15 minutes of writes")
- **RTO** (Recovery Time Objective) — how long can recovery take? (e.g. "under 4 hours")

Documented + tested → ✅.
Documented but never tested → 🟡 (it's a wish).
Undocumented → 🔴.

## Backup vs archive

- **Backup** — snapshot of live state, retained for short windows, used for point-in-time recovery.
- **Archive** — long-term cold storage, used for compliance or historical recovery.

Both have separate retention + encryption + access policies. Audit both.

## Restore drill — the test that matters

A backup that's never been restored is not a backup, it's a hope.

```sh
# Drill template
# 1. Pick a backup from N days ago (not the most recent).
# 2. Restore to an isolated environment.
# 3. Verify: schema present, sample data matches expectations.
# 4. Verify: an application can connect + read.
# 5. Document the time taken (this is your real RTO).
```

Drill cadence:
- Quarterly minimum for PoC / BETA.
- Monthly for production with paying customers.
- Weekly automated drill for enterprise / SOC2.

## Cascade-delete chains

ON DELETE CASCADE is convenient but dangerous when chains span domains:

```sql
-- Common anti-pattern
CREATE TABLE conversations (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    ...
);

-- Side effect: GDPR-delete of a user wipes ALL their conversations,
-- including ones the support team needs for an open ticket.
```

Audit method: trace ON DELETE CASCADE chains. Each chain → "is the full deletion intended?". If conversations should outlive the user (anonymized + retained), the cascade is wrong → 🔴.

## Audit log integrity

Audit log invariants:
- INSERT only.
- No DELETE / UPDATE paths.
- No cascade-delete from any table INTO the audit log.

```sh
# Search for audit-log mutation
grep -rnE '(DELETE FROM|->delete\(\)|::truncate\(\)|->forceDelete\(\))' --include="*.php" --include="*.py" --include="*.sql" \
  | grep -iE "audit|event_log|activity"
```

Any match → 🔴 unless explicitly gated by an admin operation with audit-of-the-audit.

## Multi-region replication consistency

If the product replicates across regions:
- What's the replication lag SLA?
- What happens during a failover — is there data loss?
- How is split-brain detected + resolved?

Undocumented multi-region story at any production scale → 🔴.

## Operator destructive operations

Anything in `cli.sh` / `Makefile` / `manage.py` that can destroy data should:

- Print what it's about to do.
- Require explicit confirmation (`--yes` or interactive `[y/N]`).
- Be logged.

Destructive operations with neither confirmation nor logging → 🔴 (will happen by accident).

## Encryption at rest

- Database disk encryption (cloud-provider-managed) → minimum.
- Application-level encryption of sensitive columns (Eloquent `encrypted` cast, Django `EncryptedField`) for PII.
- Backups encrypted with a separately-stored key.

Plaintext PII at rest in a B2B product → 🔴.

## Cross-references

- `dimensions/D06-operational-readiness.md` — backup test cadence.
- `dimensions/D09-data-model-integrity.md` — migration + cascade discipline.
- `dimensions/D11-legal-compliance.md` — GDPR delete vs audit retention tension.
