# Renovate / Dependabot — auto dep updates

**What they catch**: stale dependencies, especially those with newly-disclosed CVEs.

Renovate and Dependabot do the same thing. Pick one. Renovate is more configurable; Dependabot is more zero-config and integrated tightly with GitHub.

## Dependabot (simplest)

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "composer"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5

  - package-ecosystem: "npm"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5

  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5

  - package-ecosystem: "docker"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "monthly" }
```

5 PRs/week per ecosystem is the sweet spot for a small team — they pile up faster than you can review otherwise.

## Renovate (more control)

```json
// renovate.json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:base"],
  "schedule": ["before 4am on Monday"],
  "prConcurrentLimit": 5,
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true
    },
    {
      "matchPackagePatterns": ["^@types/"],
      "automerge": true
    }
  ],
  "vulnerabilityAlerts": {
    "labels": ["security"]
  }
}
```

Automerge for minor/patch saves review time on the 80% boring bumps. Major bumps stay manual.

## Triage discipline

When dep update PRs arrive:

1. CI passes? → merge.
2. CI fails? → triage:
   - Test regression: open follow-up, hold PR.
   - Breaking API change: open follow-up, hold PR.
   - Lockfile-only conflict: rebase + merge.
3. Major version with breaking notes? → schedule for next sprint.

## Cross-references

- `dimensions/D07-dependency-hygiene.md`.
- `dimensions/D04-security-posture.md`.
