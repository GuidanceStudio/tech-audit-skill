# D8 — Build / CI / dev-loop ⚠️

**Question**: "Is there a CI? Pre-commit hooks? Do tests run on every push? Are images built reproducibly? Is the dev loop fast enough that engineers actually use it?"

Default-deep. The CI is where automated audit gates live — if there's no CI, the rest of this framework is a hope, not a guarantee.

## Method

### CI presence

```sh
ls -la .github/workflows/ .gitlab-ci.yml .circleci/ azure-pipelines.yml 2>/dev/null
```

No CI at all → 🔴.

One CI pipeline running unit tests on every push → ✅ for PoC bar.

### CI matrix coverage

For each CI workflow, what does it actually run?

```yaml
# Minimum recommended stages for a multi-stack repo:
- lint (per language)
- type-check (per language)
- unit tests
- secret scan (Gitleaks)
- container scan (Trivy)
- SAST (Semgrep)
- build
- (release only) push tagged image
```

Missing stage → 🟡. Missing secret scan or container scan → 🔴.

### Pre-commit hooks

```sh
cat .pre-commit-config.yaml 2>/dev/null
ls -la .husky/ .git/hooks/pre-commit 2>/dev/null
```

Hooks present + enforced (config in repo, not just docs) → ✅.

Hooks documented but not enforced (in README only) → 🟡 (each engineer's responsibility, no guarantee).

### Reproducible builds

Docker base images:

```sh
grep -rE '^FROM ' --include=Dockerfile* . | grep -vE 'FROM \w+(:[a-f0-9]{64}|@sha256:)'
```

`FROM python:latest` → 🟡. `FROM python:3.13-slim` → 🟢 (mutable but stable enough). `FROM python:3.13-slim@sha256:...` → ✅ (full pinning).

Two consecutive builds of the same commit → same image hash? Spot-check:

```sh
docker build -t test:1 . && docker build -t test:2 .
docker inspect --format='{{.Id}}' test:1 test:2
```

If different (and the inputs were identical) → 🟡 (some layer is non-deterministic, e.g. `apt-get` without `--no-install-recommends`).

### Single dev-loop entry point

```sh
ls -la Makefile justfile Taskfile.yml cli.sh ./bin/run 2>/dev/null
```

Multiple entry points (Makefile + a separate `cli.sh` + a third `scripts/dev.sh`) without docs explaining when to use which → 🟡. The team will diverge on which one to call.

Common operations should be one-keystroke (or one short command):

| Operation | Acceptable |
|---|---|
| Run tests | `make test` / `./cli.sh test` |
| Start dev stack | `make up` / `./cli.sh stack-up` |
| Lint | `make lint` |
| Format | `make format` |
| Generate docs | `make docs` |

Each common operation that requires a 4+ word incantation in docs → 🟡 (friction the team will route around).

### Tool wiring matrix

The deployable open-source stack for a multi-stack shop. See
`tools/_matrix.md` for the lookup table + setup time per tool.

Each tool's individual page covers: what it catches, install command,
sample CI config, common false positives, how to tune.

## PoC bar

- One CI pipeline running unit tests on every push.
- Secret scan in CI.
- Container scan in CI for any image deployed.
- Single dev-loop entry point (`Makefile` / `Taskfile` / `cli.sh`).

## Production bar

- Multi-stage CI: lint → type-check → unit → integration → live → security scan → build → push.
- Pre-commit hooks enforced (commit fails if hooks aren't installed).
- Reproducible builds with digest-pinned bases.
- Tag-based release with auto-generated changelog.
- Build cache shared across CI runs (BuildKit cache, sccache, ...).

## Cross-references

- `tools/_matrix.md` — the canonical tool list (Gitleaks, Trivy, Semgrep, PHPStan, Ruff, mypy, Biome, Hadolint, jscpd, pgTAP).
- `tools/<tool>.md` — per-tool setup.
- `playbooks/operations.md` § Starter pack — 5-week / 30-min-per-week onboarding.
- D7 — dep CVE scanning (the auto-update pipeline runs under D8 infrastructure).
