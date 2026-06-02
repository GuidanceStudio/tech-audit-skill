# Docker — language-specific checks

Patterns for Dockerfiles + compose / k8s manifests.

## Non-root USER (D4)

Every image MUST declare a non-root USER:

```sh
for d in $(find . -name "Dockerfile*"); do
  user=$(grep -E '^\s*USER ' "$d" | tail -1 | awk '{print $2}')
  if [ -z "$user" ] || [ "$user" = "root" ] || [ "$user" = "0" ]; then
    echo "ROOT: $d"
  fi
done
```

Any image running as root in production → 🔴.

## Pinned base images (D8)

```sh
grep -rE '^FROM ' --include=Dockerfile* . | grep -vE 'FROM \w+(:[0-9]+\.[0-9]+|@sha256:)'
```

- `FROM python:latest` → 🟡 (`latest` is mutable; build breaks unpredictably).
- `FROM python:3.13-slim` → 🟢 (minor-pinned, acceptable for dev / fast iteration).
- `FROM python:3.13-slim@sha256:...` → ✅ (digest-pinned, fully reproducible).

## Build context size

`.dockerignore` should exclude `node_modules`, `.git`, `vendor`, `tests/`, `*.log` etc.:

```sh
ls -la .dockerignore 2>/dev/null && cat .dockerignore | head -20
```

No `.dockerignore` → 🟡 (slow + leaks build context).

## Healthcheck in Dockerfile or compose

```sh
grep -rE '^\s*HEALTHCHECK' --include=Dockerfile* .
```

Service without healthcheck → 🟡. Mission-critical service (DB, gateway, auth) without healthcheck → 🔴.

## Compose-level concerns

### Named volume perms

A named volume mounted into an image with non-root USER (uid 82, 1000, ...) starts root-owned by Docker. The container can't write — typical first-boot crash loop.

Solutions:
- `chown` the volume in a one-shot privileged container before service startup, OR
- Use a tmpfs / bind mount with operator-set perms, OR
- Use the image's entrypoint to chown (requires running as root + dropping priv — complicated).

See `threat-models/secret-management.md` for the named-volume bootstrap pattern.

### Bind mount perms drift

Bind-mounted host dirs see the operator's UID. Inside container as a different UID → EACCES. Pattern:
- Operator-owned host dir + container reads as root or matching uid: OK.
- Operator-owned host dir + container reads as different uid without `group_add`: ❌.
- Solution: chgrp the host dir to a known shared GID + `group_add: ["<gid>"]` in compose.

### Empty named volume perm reset

Docker re-applies the image's directory perms when mounting an EMPTY named volume. To make chown-based perms persist, also touch a marker file inside the volume — once non-empty, mounts respect the existing perms.

```sh
docker run --rm -v my-vol:/data alpine sh -c 'touch /data/.init && chown -R uid:gid /data'
```

See `threat-models/secret-management.md`.

### Secret env passthrough vs file mount

Anti-pattern: long PEM in `.env` → compose env passthrough → 8KB env var on every container. Multi-line PEM in shell env is fragile.

Better: a named volume mounted with the secret as a file. Compose ergonomics + Tier-0 / K8s evolution path (the volume becomes a K8s Secret with the same filesystem layout, zero code change).

### Compose project / volume label drift

When you `docker volume create` a named volume outside compose, then `docker compose up` warns "volume X already exists but was not created by Docker Compose". To silence + keep the volume managed:

```sh
docker volume create \
  --label "com.docker.compose.project=<PROJECT>" \
  --label "com.docker.compose.version=$(docker compose version --short)" \
  --label "com.docker.compose.volume=<SHORT_NAME>" \
  <FULL_NAME>
```

Required label set: `project`, `version`, `volume`. Missing any → the WARN fires.

## Tools to run

- **Hadolint** for Dockerfile lint.
- **Trivy** for image vuln + IaC + SBOM.

## Cross-references

- `threat-models/secret-management.md` — named-volume bootstrap, perm drift, label discipline.
- `tools/hadolint.md`, `tools/trivy.md`.
- `dimensions/D08-build-ci-devloop.md` — reproducibility.
- `dimensions/D04-security-posture.md` — non-root + image scanning.
