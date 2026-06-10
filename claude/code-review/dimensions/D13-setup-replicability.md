# D13 — Setup replicability 🚀

**Question**: "Can a new operator go from `git clone` to a healthy running stack by editing **only `.env`** and running CLI / Make / Task subcommands? Or are there manual `docker compose`, `psql`, `chown`, etc. steps hidden in docs that the operator has to discover and execute?"

Always-deep. This is the operator-facing contract. The promise that justifies "set up a tenant in 10 minutes" or "self-hostable in one command" lives here.

A product whose fresh-clone bootstrap requires inventiveness fails this dimension regardless of how good the production deployment is.

## Method

### The fresh-clone walkthrough (the test that matters)

Wipe the dev directory. Fresh `git clone` of every required repo. Copy `.env.example` → `.env`. Fill ONLY the operator-visible external secrets (LLM API key, OAuth client IDs, bot tokens). Run the documented bootstrap sequence (`./cli.sh stack-up`, `make up`, `docker compose up -d`, whatever).

```sh
# Concrete test: outside the project, in a clean dir
WORKDIR=$(mktemp -d)
cd $WORKDIR
git clone $REPO_URL .
cp .env.example .env
# Fill .env (only what's required to be operator-visible)
$EDITOR .env
# Run the documented bootstrap
./BOOTSTRAP_COMMAND
# Verify health
./HEALTH_COMMAND
```

Every required step OUTSIDE that sequence → finding.

### Hidden-step grep

```sh
# Operator-side commands that should be in the CLI, not in raw docs
grep -rE 'docker compose|docker exec|docker run|chown|chmod|sudo|apt install|pip install|brew install' \
  README.md docs/ 2>/dev/null \
  | grep -vE 'docs/runbook/|docs/recovery/|docs/troubleshooting/' \
  | head -30
```

Each hit is either:
- Inside a CLI implementation file (OK — the operator never types it) → 🟢
- Inside a recovery-only runbook with a clear "only run if X" header → 🟢
- In the happy path of operator docs → 🟡 (or 🔴 if it's required for first boot)

### CLI completeness

Every operator task mentioned in `docs/operator/*` or README quickstart must map to a CLI subcommand.

```sh
# CLI subcommands available
./cli.sh --help 2>&1 | grep -oE "^\s+[a-z][a-z-]+" | sort -u > /tmp/cli-cmds

# Tasks documented as needing a raw command (anti-pattern)
grep -rE 'You need to [a-z]+ ' docs/operator/ README.md | head -10
```

Each documented task without a one-command CLI invocation → 🟡.

### `.env` boundary — operator-visible vs cluster-internal

Two classes of secret:

| Class | Examples | Where it lives |
|---|---|---|
| **External / operator-visible** | LLM API keys, OAuth client IDs, bot tokens, OAuth client secrets, SaaS API tokens | `.env` (operator fills) |
| **Cluster-internal** | JWT keypair, intra-cluster bearer tokens, admin shared secrets, encryption keys for at-rest data | Auto-bootstrapped (named volume, K8s Secret, Vault, ...) — NEVER operator-fillable |

For each cluster-internal secret with an operator-fillable placeholder in `.env.example` → 🔴.

The audit method: open `.env.example`, list every variable, and ask "can an operator meaningfully fill this?". If the answer is "no, this should be auto-generated and rotated by the system", the placeholder is a 🔴.

See `threat-models/secret-management.md` for the bootstrap + rotation patterns.

### Idempotent re-run

Running the bootstrap command twice back-to-back on the same host must be a no-op the second time.

```sh
./cli.sh stack-up
./cli.sh stack-up   # should NOT regenerate secrets, NOT restart healthy containers, NOT prompt for any input
```

Any preflight that:
- Writes new state on every invocation
- Rotates a secret unprompted
- Restarts an already-healthy container
- Asks the operator a question

…on the SECOND run → 🟡.

### Doctor / self-check command

The bootstrap should ship with a `./cli.sh doctor` (or equivalent: `make check`, `task verify`, ...) that emits a structured health report.

A healthy stack must produce a 0 exit code. Yellow warnings surviving a full fresh-clone bootstrap → 🟡 in the audit.

### Recovery vs. happy-path docs

Recovery runbooks (what to do when X breaks) live separately from setup docs. They MAY contain raw `docker compose restart`, `psql`, `chown` etc. — that's OK. They should NOT be in the operator's happy path.

```sh
ls -la docs/runbook/ docs/recovery/ 2>/dev/null
```

Recovery doc exists + happy path stays clean → ✅.

## PoC bar

- Fresh-clone → `cp .env.example .env` (edit external secrets only) → ONE bootstrap command → healthy stack.
- `./cli.sh doctor` (or equivalent) exits 0.
- Idempotent re-runs are no-ops.
- No cluster-internal secret has an operator-fillable placeholder in `.env.example`.
- Hidden raw-docker commands in operator docs: zero (recovery-only is fine).

## Production bar

- Fresh-install on a clean cloud VPS completes in ≤10 minutes.
- Every error condition surfaces a CLI-suggested next step, never a stack trace.
- CI exercises the full fresh-clone path on every push (a "smoke test that builds the world from scratch").
- The fresh-clone test runs against the published release tag (not just `main`) every quarter.

## Cross-references

- D2 — docs accuracy (the README fresh-clone walkthrough is also a D2 check).
- D8 — CI (the fresh-clone smoke is a CI stage).
- `threat-models/secret-management.md` — operator-visible vs cluster-internal split.
