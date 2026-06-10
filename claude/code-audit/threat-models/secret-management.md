# Threat model — secret management

Two distinct classes of secret that demand different lifecycles. Conflating them is the source of most "fresh-clone bootstrap broke" incidents.

## Two classes

| Class | Examples | Lifecycle | Who knows |
|---|---|---|---|
| **External** (operator-visible) | LLM API key, OAuth client ID, bot tokens | Set in `.env` (or operator's secret store); rotated by the operator. | The operator. |
| **Cluster-internal** | JWT keypair, intra-cluster bearer tokens, admin shared secrets, encryption-at-rest keys for managed data | Auto-bootstrapped by the system at first boot; auto-rotated on schedule. Never operator-fillable. | Nobody (the system manages them). |

The audit rule: every cluster-internal secret with an operator-fillable placeholder in `.env.example` → 🔴.

The reason: operators inevitably leave such placeholders empty → the system crash-loops on missing credentials → operator has no way to recover except deep debugging.

## Storage patterns (cheapest → most robust)

### Pattern A — env vars + manual rotation

- Simple, but: multi-line values (PEM) are fragile in shell env files; rotation requires operator action; no audit trail.
- **OK for**: external secrets only.
- **Anti-pattern for**: cluster-internal.

### Pattern B — named volume + filesystem files

- A shared Docker named volume mounted r/w on the writer (the service that generates the secret) and r-only on consumers.
- Pros: clean separation (operator never sees), atomic file writes, file-watcher hot-reload possible.
- Cons: container perm gymnastics (gid sharing, world-readable vs group-readable trade-offs).
- **Used by**: small-to-medium docker-compose deployments.

### Pattern C — Docker secrets / Kubernetes Secrets

- Native platform-level secret store mounted as files.
- Pros: standard, audit-able, rotatable via API.
- Cons: requires the orchestrator (Swarm / K8s).
- **Used by**: production K8s deployments.

### Pattern D — HashiCorp Vault / AWS Secrets Manager / GCP Secret Manager

- External secret manager with API-level access + rotation policies.
- Pros: full audit, fine-grained ACL, key rotation hooks.
- Cons: another piece of infrastructure, requires bootstrap of the bootstrap (how do consumers authenticate to Vault?).
- **Used by**: enterprise / regulated workloads.

## Pattern B implementation gotchas (most common shop)

### Empty-volume perm reset

Docker re-applies image directory perms when mounting an EMPTY named volume. To make `chown` persist, touch a marker file so the volume isn't empty:

```sh
docker run --rm -v my-secrets:/data alpine sh -c \
  'touch /data/.init && chown -R 82:82 /data'
```

After this, subsequent mounts respect the existing ownership.

### Compose project / volume labels

When a volume is pre-created outside compose, compose warns "volume already exists but was not created by Docker Compose" and skips it during `down --volumes`. To silence + keep managed:

```sh
docker volume create \
  --label "com.docker.compose.project=PROJECT" \
  --label "com.docker.compose.version=$(docker compose version --short)" \
  --label "com.docker.compose.volume=SHORT_NAME" \
  PROJECT_SHORT_NAME
```

Required labels: `project`, `version`, `volume`. Missing any → WARN fires.

### Cross-container read access via group

If the writer is uid X and the consumer is uid Y, the consumer needs gid X as a supplementary group (or the file mode must be 0644 — usually too permissive for secrets):

```yaml
# compose
cerase-gateway:
  group_add:
    - "82"   # writer's gid; gives this container read access to writer-owned files
```

Files at 0640 owned by uid X gid X → world has no access, gid-X has read access. Containers in `group_add: ["X"]` can read.

### Atomic write

Write to a temp file in the same directory, then rename. Avoids consumers reading half-written files:

```python
tmp = path + ".tmp." + os.getpid()
open(tmp, "w").write(content)
os.chmod(tmp, 0o640)
os.rename(tmp, path)
```

## Rotation patterns

### Rotation pattern 1 — restart-on-rotation (PoC bar)

- Writer regenerates the secret.
- Writer signals consumers to restart (Docker socket, supervisord, ...).
- Consumers boot, re-read the secret from the volume.

Simple, lossy (brief downtime), works for small clusters.

### Rotation pattern 2 — file-watch hot-reload (production bar)

- Writer regenerates the secret atomically.
- Consumers watch the file with `inotify` / `fsnotify` and re-read on change.
- Zero downtime; needs careful handling of in-flight requests using the old secret.

## Drift detection

After image rebuild, the in-image keypair / generated state may differ from what's in the volume. Detection method:

```sh
# Hash the public key as control-plane sees it
docker exec writer sh -c 'sha256sum /var/secrets/public.pem'
# Hash the public key as gateway sees it
docker exec consumer sh -c 'sha256sum /var/secrets/public.pem'
# Must match. If not, the volume has drifted from the image-bundled state.
```

If you store keys inside the image at build time AND inside a volume, you have two sources of truth — guaranteed drift. Pick one. The volume wins for everything-not-baked.

## Audit checks (D4, D13)

1. Every cluster-internal secret has NO placeholder in `.env.example` → ✅.
2. The bootstrap command is idempotent — re-running it doesn't rotate live secrets unprompted.
3. Doctor check verifies: secret file exists, non-empty, owner / mode correct, keypair coherent (private derives public).
4. Atomic-write pattern used everywhere (no half-written file reads).

## Cross-references

- `dimensions/D04-security-posture.md`.
- `dimensions/D13-setup-replicability.md` — the operator boundary.
- `languages/docker.md` — compose perm patterns.
