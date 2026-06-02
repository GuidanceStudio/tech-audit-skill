# D6 — Operational readiness 🏥

**Question**: "Healthcheck on every service? Logs structured? Backup *actually* tested? Runbook complete?"

Scan dimension. Promote to deep when an incident exposes a gap.

## Method

### Healthcheck coverage

For docker-compose stacks:

```sh
docker compose config --format json \
  | jq '[.services|to_entries[]|select(.value.healthcheck|not)|.key]'
```

The naive `grep -c "healthcheck:" docker-compose.yml` under-counts when YAML anchors (`<<: *anchor`) inherit healthchecks — `compose config --format json` expands anchors first.

Services without healthcheck → 🟡. Mission-critical service without healthcheck (the one the stack depends on) → 🔴.

### Log structure

Sample 3 services. Are their logs JSON / structured, or `print` / `echo`?

```sh
docker logs $SERVICE 2>&1 | head -5 | python3 -c "
import sys, json
for line in sys.stdin:
    try: json.loads(line); print('JSON: ok')
    except: print('NOT JSON: ' + line.strip()[:80])
"
```

Plain-text logs at any service touching production data → 🟡 (operators can't grep structured fields).

### Correlation IDs

Search for `request_id` / `trace_id` / `correlation_id` propagation:

```sh
grep -rnE "request[-_]?id|trace[-_]?id|correlation[-_]?id" --include="*.py" --include="*.php" --include="*.ts" | head -20
```

Missing across the stack → 🟡 (debugging multi-service incidents is unnecessarily hard).

### Runbook coverage

Open `docs/operator/` or `docs/runbook/`. Does it cover the 5 most likely incidents for this product?

Standard list:
1. Database down / unreachable.
2. Upstream API (LLM, payment, ...) returns 5xx.
3. Upstream API rate-limits / quotas us out.
4. Disk full on the host.
5. Container OOM / killed.

Each uncovered → 🟡. Zero runbook → 🔴.

### Backup actually restored

When was the last time the project's `restore.sh` (or equivalent) ran against a real backup?

```sh
# If the project tracks restore drills
git log --all --grep="restore drill\|backup restore" --pretty=oneline | head -3
```

"We have backups" without a restore drill in living memory → 🟡 (backups untested are wishes).

### Resource limits

```sh
grep -E 'mem_limit|cpus:' docker-compose.yml | wc -l
```

Production stack without resource limits → 🟡 (one runaway service can OOM the host).

### Scheduled tasks visibility

```sh
# Laravel scheduler
grep -rn "schedule->" app/Console/Kernel.php config/

# Systemd timers / cron
ls -la /etc/systemd/system/*.timer /etc/cron.* 2>/dev/null
```

Scheduled jobs without `LastRunAt` / monitoring visibility → 🟡.

## PoC bar

- Healthcheck on every service.
- Backup → restore exercised at least once in dry-run.
- Runbook covers the 3 most common incidents.

## Production bar

- All logs JSON with trace-id.
- Prometheus / OTel metrics on every service.
- SLO/SLI defined per surface.
- Restore exercised weekly via automated drill.

## Cross-references

- `threat-models/data-loss.md` — backup + restore patterns.
- `playbooks/operations.md` — cadence for re-running this dimension.
