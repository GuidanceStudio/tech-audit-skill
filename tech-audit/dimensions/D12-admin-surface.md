# D12 — Admin surface consistency 🎛️

**Question**: "Does the admin / operator surface stay coherent with the underlying DB state? Empty-states rendered, failures surfaced, labels consistent across pages, async work routed through queues?"

Scan dimension. Surface-level, but the symptoms operators see when this dim is neglected look like "the product is broken" — even when the core is fine.

## Method

### Empty-state coverage

For every dashboard / list / widget that queries data, run it against an empty DB and confirm a specific empty-state copy renders (not a blank div or "0 results" with no context).

```sh
# Grep for early-return-on-empty patterns
grep -rnE 'if .*->isEmpty\(\)\) (return|continue)|if not .*: return' app/ src/ \
  | head -30
```

Each match is a candidate "missing empty-state copy". For UI components, render with empty fixtures + screenshot.

Production-facing widget with no empty-state copy → 🟡.

### Notification surfaces for failures

Every observer + every background task + every page action that hits external services must SURFACE failures, not swallow them.

```sh
# Laravel: report() and rethrow() are OK; report() and continue is silent failure
grep -rnE 'catch.*report\(.*\)\s*;\s*\}' --include="*.php" | head

# Python: bare except: + log + continue is the same anti-pattern
grep -rnE '^(\s+)except.*:\s*\n\1\s+(logger\.|logging\.|print\()' --include="*.py" | head
```

Each match: did we surface the failure to the user via UI / Slack / email? Or did we swallow + continue → operator finds out from a customer support ticket?

Silent failure on a user-facing operation → 🔴.
Silent failure on a background sync that has retry → 🟡 with the suggested fix being a circuit-breaker + admin notification when retries exhaust.

### Async vs sync routing

Any HTTP route / page action that does >5s of work in the request thread is a 504 candidate.

```sh
# Suspect patterns
grep -rnE 'foreach.*uploadFile|foreach.*->call\(.*[Aa]pi|while.*page.*<' app/ src/ \
  | head
```

Each match: should this be a queued job + UI polling, instead?

Long-running sync work on a user-facing route → 🔴 (will time out under load).

### Label consistency across pages

When a label changes (e.g. "Templates" → "Recipes"), does it propagate across the whole admin surface?

```sh
# Pick a recently-renamed term from git log
git log --since="3 months ago" --pretty=format:"%s" \
  | grep -iE "rename|relabel|terminology" \
  | head

# Then grep for the old term
grep -rn "OLD_TERM" --include="*.blade.php" --include="*.tsx" --include="*.vue" \
  --include="*.html"
```

Old-term survivors on list pages / nav badges / dashboards while edit forms use new term → 🟡.

### Loading + error state coverage

For every async UI component, three states must render:

1. Loading (spinner, skeleton, ...)
2. Success (the actual data)
3. Error (a message, a retry button, ...)

```sh
# React / Vue rough sniff
grep -rnE 'useQuery|useSWR|useFetch' --include="*.{tsx,jsx,vue}" \
  | head -10
```

For each: does the component handle the three states? Components without explicit error rendering → 🟡.

### Form validation feedback

Forms must show field-level validation feedback, not just a generic "Something went wrong":

```sh
# Look for the "generic error" anti-pattern
grep -rnE "Something went wrong|unknown error|Errore generico" .
```

Each match → 🟡 unless the surrounding code routes to field-level messages too.

### Permission feedback

When a user clicks a button they aren't permitted to use, what happens?

- Best: button is hidden / disabled with a tooltip explaining why.
- OK: click triggers a clear "you need role X to do this" message.
- Worst: silent failure or generic 403 page with no context.

Find permission gates without UI feedback → 🟡.

### API ↔ admin-UI parity

Every state-changing action the admin UI exposes should have an
equivalent programmatic endpoint (a headless operator / CI / another
service can't click buttons). Diff the admin mutations against the API
surface:

```sh
# Admin-surface actions (Filament resources/pages, or admin routes)
grep -rnE 'public function (create|edit|delete|update|store|destroy)' app/Filament/ \
  2>/dev/null | head -40
grep -rnE "Route::(post|put|patch|delete).*'/admin" routes/ 2>/dev/null | head

# Public/programmatic API surface
grep -rnE "Route::(post|put|patch|delete)" routes/api*.php 2>/dev/null | head -40
```

For each admin-doable mutation with no API equivalent → 🟡 (the fix is
to add the `/api/v1` route, not to remove the UI). Read-only admin
views are exempt. Generalize beyond Filament: any admin-only route
whose verb mutates state, compared against the public API routes.

## PoC bar

- Every widget querying data has an empty-state branch tested in pest / playwright.
- Every observer surfaces failures via a `Notification::danger()` (test pin exists).
- No request-thread work >5s on user-facing routes.

## Production bar

- BETA partner completes "fresh-install → first agent → first conversation" with zero operator inventiveness beyond what's documented.
- Every screen carries telemetry for empty-state hit-rate (signal of misunderstood UX, not of empty data).
- Async work routed through a queue with retries + dead-letter + admin visibility.

## Cross-references

- D2 — operator docs (the CLI walkthrough overlaps with this; coordinate so neither duplicates).
- D6 — operational readiness (runbook for failure scenarios).
- This dimension audits admin-surface **source** (empty-states, parity,
  failure routing). Rendered UI/UX depth — visual design, WCAG
  accessibility, responsive behavior on real screenshots — is the
  `uxui-audit` skill's job, not this one. Point the user there for a
  rendered-interface review.
