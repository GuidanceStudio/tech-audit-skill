# D2 — Docs integrity 📜

**Question**: "Does what the docs claim still match the code, the devplan, and each other? Is every doc the cheapest possible version of itself, or are there three places saying overlapping things that will drift?"

Always-deep. Three failure modes to catch separately: **accuracy** (claim ≠ code), **completeness** (a flow exists but isn't documented), **non-redundancy** (the same fact lives in 3 docs).

## Method

### Accuracy — architecture vs code

Pick 5 random claims from the project's `architecture.md` / `ARCHITECTURE.md` / `docs/architecture/`:

```sh
# Sample claim sources
grep -rnE "^- |^[0-9]+\." docs/architecture/*.md | shuf | head -5
```

For each: grep for the named symbol/file/table in the code. Drift counted:

- Doc claims a file exists, file doesn't → 🔴 (broken reference).
- Doc claims a behavior, code does something else → 🔴.
- Doc names a deprecated symbol → 🟡.
- Overall drift > 20% of sampled claims → ❌ for the dimension.

### Accuracy — devplan honesty

The devplan / TODO / roadmap file is the project's "what's shipped" register. Spot-check 5 ✅-flagged items per audit pass:

```sh
git log --all --grep="OPT-\|M[0-9]\|TASK-" --pretty=oneline | head -20
```

Open the commit referenced. Verify the feature is reachable end-to-end. Devplan ✅ that doesn't match git → 🔴 (one of the most common signs of audit-theater documentation).

### Completeness — operator paths reachable

For every "operator task" mentioned in `docs/operator/*` or README quickstart, find the corresponding CLI/Make/Task invocation. Tasks documented but not implemented → 🔴. CLI subcommands implemented but undocumented → 🟡.

```sh
# CLI subcommands (adapt to project's CLI entry point)
./cli.sh --help 2>&1 | grep -oE "^\s+[a-z][a-z-]+" | sort -u > /tmp/cli-cmds
grep -rEoh '\./cli\.sh [a-z-]+' docs/ | awk '{print $2}' | sort -u > /tmp/doc-cmds
diff /tmp/cli-cmds /tmp/doc-cmds
```

### Completeness — README fresh-clone test

The strongest accuracy test: walk the README quickstart top-to-bottom on a fresh Debian/Ubuntu VM (or a clean Docker container with the right base image).

- Any broken command (404 link, missing dep, wrong syntax) → 🔴.
- Any step the operator has to guess (e.g. "configure DNS" with no example) → 🟡.
- Quickstart takes >10 min for someone with no prior context → 🟡.

This overlaps with **D13 (Setup replicability)** — coordinate so neither dim duplicates the work.

### Non-redundancy sweep

Pick a topic likely repeated (e.g. "secret management", "stack-up", "deployment", "auth"). Grep across the doc tree:

```sh
TOPIC="secret management"
grep -rln "$TOPIC" README.md docs/ 2>/dev/null
```

If ≥3 docs hit, ONE must be the authoritative source; the others must **link to it**, not re-state. Free-standing duplicates of the same fact → 🟡 (drift risk).

Common redundancy hot spots:
- Install / setup instructions duplicated in README, `docs/install.md`, `docs/operator/setup.md`.
- Secret management explained in code comments, `.env.example`, `docs/security/`, and the devplan.
- Architecture diagrams in `architecture.md` AND `docs/`.

### Stale references

```sh
# Broken file/dir paths
grep -rnE '\][\s]*\(([^)]+\.(md|sh|py|php|ts))[\)]' README.md docs/ \
  | awk -F'[()]' '{print $2}' | sort -u \
  | while read f; do [ ! -e "$f" ] && echo "BROKEN: $f"; done

# Milestone references that have been superseded (project-specific)
grep -rn "OPT-46\|M5\.5" docs/    # adapt to project's milestone naming
```

### Doc redundancy in code comments

```sh
# Multi-line comments that repeat what the code says
grep -rnE '^\s*//' --include="*.{ts,js,php,go}" | wc -l
```

Excessive comment density (>1 comment line per 5 code lines) often indicates the comments are restating "what" rather than "why". Sample 20 random comments — kept if they explain non-obvious *why*; flagged if they paraphrase the next line.

## PoC bar

- README quickstart works on a clean Debian/Ubuntu VM.
- Every devplan ✅ matches git history.
- No "TODO" / "draft" in primary architecture docs.
- Every operator-facing concept has exactly one authoritative doc; others link.

## Production bar

- Doc CI: link checker, code-block extraction runs in a test container, redundancy linter.
- Versioned doc per release.
- ADR (decision-log) entries for every architectural change.
- Generated API docs for any HTTP surface.

## Cross-references

- D7 (Documentation accuracy) used to be a separate dim — folded here.
- D13 (Setup replicability) coordinates on the fresh-clone walkthrough.
- `playbooks/operations.md` describes the cadence for re-running this dimension.
