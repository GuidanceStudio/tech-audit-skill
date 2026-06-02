# D7 — Dependency hygiene 📦

**Question**: "Lock files committed? GPL in a commercial product? Frameworks current? Any unmaintained dep?"

Scan dimension. Heavy automation does most of the work — see `tools/auto-dep-updates.md`.

## Method

### Lock files committed

| Stack | Expected lock file |
|---|---|
| PHP / Composer | `composer.lock` |
| Node | `package-lock.json` or `yarn.lock` or `pnpm-lock.yaml` |
| Python | `uv.lock` or `poetry.lock` or `requirements.txt` (pinned) |
| Rust | `Cargo.lock` |
| Go | `go.sum` |

Missing lock file in a deployable artifact → 🔴 (builds are non-reproducible).

### License inventory

```sh
composer licenses                                # PHP
npm ls --json | jq '.dependencies | .. .license? // empty' | sort -u
pip-licenses                                     # Python
```

Flag licenses:
- **AGPL / SSPL** in a commercial closed-source product → 🔴.
- **GPL v2/v3** in a commercial closed-source product → 🔴 (with copyleft viral concern; LGPL is usually OK with dynamic linking).
- **Custom / non-OSI** → 🟡 (manual review needed).
- **Unknown / unparsed** → 🟡 (might be license string in a non-standard place).

### Out-of-date frameworks

```sh
composer outdated --direct      # PHP, top-level only
npm outdated --json | jq        # Node
pip list --outdated             # Python
```

Severity:
- Framework (Laravel, Django, Next.js, Rails) > 1 major behind → 🟡.
- Any dep > 12 months without an update **and** not at v1.0+ → 🟡 (likely abandonware).
- Any dep with known CVE no upgrade available → escalated to D4.

### Auto-update wiring

The project should have Renovate or Dependabot (or equivalent) enabled. If not → 🟡 (the team will accrue stale deps).

See `tools/auto-dep-updates.md` for setup.

### Unused deps

```sh
composer-unused                                 # PHP
depcheck                                         # Node
pip-check-reqs   # or: vulture on requirements   # Python
```

Each unused dep → 🟢 (clean up next sweep). Many unused → 🟡 (signal of past refactor not finished).

### Transitive risk concentration

A dep tree where 80% of nodes are pulled by 2-3 packages is fragile. Single-maintainer deps in critical paths are risky.

```sh
# Node: count maintainers per direct dep
npm view <pkg> maintainers
```

Single-maintainer dep on the critical path of a B2B product → 🟡 (document the mitigation: vendoring plan, fork-readiness).

## PoC bar

- All lock files committed.
- No GPL / AGPL / SSPL in a commercial closed-source product.
- Major frameworks <1 release behind.
- No dep >2 years untouched in production.

## Production bar

- Renovate / Dependabot enabled, blocking PRs with HIGH/CRITICAL CVEs.
- SBOM generated per release (`syft`, `cyclonedx`).
- License review per new dep (PR template prompt).
- Single-maintainer transitive deps documented + monitored.

## Cross-references

- `tools/auto-dep-updates.md` — wiring Renovate / Dependabot.
- D4 — security CVE scanning (overlap by design).
