# D15 — UX & interaction design 🧭

**Question**: "Can a user actually complete their tasks — every flow has
an entrance, a success path, an error recovery, and the in-between
states are handled? Or does the happy path work and everything else
dead-ends?"

Default-deep when a UI surface is detected (frontend markers — see
`routing/detect-stack.md`). Two passes: a **base** source-level pass
that needs no running app, and an **advanced** rendered pass that drives
a real browser. D12 covers admin-surface coherence; this covers
product-wide UX; the rendered pixel review is delegated to the
`ui-review` skill (don't reimplement capture here).

## Base pass — source-level (always)

Reads the code; no browser required.

### Flow completeness

Every user-facing action must have a destination and every failure a
recovery. Trace the primary flows (auth, the core task, checkout/submit)
through the code.

```sh
# Buttons / links / actions — do they all resolve to a route or handler?
grep -rnE '<(button|a |Link|router-push|navigate)' --include='*.{tsx,jsx,vue,svelte,blade.php}' . | head -40
# Submit handlers without an error branch
grep -rnB2 -A8 'onSubmit\|handleSubmit\|@submit' --include='*.{tsx,jsx,vue}' . | grep -L 'catch\|error' | head
```

A CTA with no destination, or a submit/mutation with no error branch →
🟡 (🔴 on auth / payment / data-loss flows).

### Interaction-state coverage

For every async view/component, four states must be reachable in code:
**loading, empty, error, success**. Missing branches are the states
teams forget.

```sh
grep -rlnE 'useQuery|useSWR|useFetch|createResource|await fetch|axios' \
  --include='*.{tsx,jsx,vue,svelte}' . | head
```

For each: are loading/empty/error all handled, not just success?
Missing error or empty branch on a primary view → 🟡.

### Form UX

- Field-level validation feedback (not just a generic banner).
- Disabled / in-flight submit state (prevents double-submit).
- Destructive/irreversible actions gated by a confirm step.

```sh
grep -rnE 'type="submit"|<form' --include='*.{tsx,jsx,vue,blade.php}' . | head
grep -rniE 'delete|remove|destroy|reset' --include='*.{tsx,jsx,vue}' . | grep -i 'onClick\|@click' | head
```

Destructive action with no confirm, or a form with no in-flight guard →
🟡.

### Information architecture & navigation

Is there a coherent nav structure (the user always knows where they are
and how to get back)? Look for active-route indication, breadcrumbs on
deep pages, a consistent back/close affordance on modals. Dead-end
modals (no close) → 🟡.

### Accessibility in the markup

```sh
# images without alt, icon-only buttons without a label, missing form labels
grep -rnE '<img(?![^>]*alt=)' --include='*.{tsx,jsx,vue,blade.php,html}' . | head
grep -rnE '<button[^>]*>(\s*<(svg|i|Icon))' --include='*.{tsx,jsx,vue}' . | head
grep -rnE '<input(?![^>]*(aria-label|id=))' --include='*.{tsx,jsx,vue,blade.php}' . | head
```

Icon-only controls without an accessible label, images without `alt`,
inputs without an associated label → 🟡 (these are the source-detectable
WCAG misses; focus order / live-region behavior needs the advanced pass
or axe).

### i18n readiness

```sh
# user-facing literals hardcoded instead of going through a translation fn
grep -rnE '>[A-Z][a-z]+ [a-z]' --include='*.{tsx,jsx,vue,blade.php}' . | grep -vE 't\(|i18n|trans\(|__\(' | head -20
```

In a project that HAS an i18n layer, user-facing strings bypassing it →
🟡; mixed-language UI in one surface → 🟡 (see `ui-review` for the
rendered check).

### Perceived performance

Skeletons/optimistic updates on slow views; no layout shift on load.
Source signal: a `loading` branch that renders a skeleton vs a bare
spinner vs nothing.

## Advanced pass — rendered (opt-in, needs a runnable app)

The base pass proves the code has the branches; only a render proves the
user can actually move through them. When the app is runnable and
Node + Playwright are available:

- **Hand off to the `ui-review` skill** (or run its
  `scripts/capture.mjs`) to screenshot the real surfaces, then apply its
  Usability (Nielsen), State-coverage, and Responsive dimensions. That
  skill owns rendered capture + the pixel-level rubric — invoke it
  rather than duplicating it.
- Fold the rendered findings back into this audit's `findings.tsv`
  tagged `D15`, cross-referencing the `ui-review` report.

Without a runnable app or Playwright, stay source-level and record the
rendered pass as **deferred** in the report (don't silently skip it).

## PoC bar

- Every primary flow: entrance + success + error-recovery present in code.
- Loading/empty/error/success branches on primary async views.
- Destructive actions confirmed; forms guard against double-submit.
- No source-detectable a11y misses (alt, labels) on core screens.

## Production bar

- Advanced rendered pass run on every release (via `ui-review`), no open
  severity-3+ usability/state findings.
- axe-core / pa11y in CI for the un-seeable a11y (focus, keyboard, ARIA).
- i18n: zero hardcoded user-facing strings; one language per surface.

## Cross-references

- D12 — admin-surface coherence (operator surface; coordinate so a
  finding lands in one dimension, not both).
- D16 — UI & design-system craft (visual layer; shares the advanced
  rendered hand-off — see D16's note).
- `ui-review` skill — owns the rendered pixel/UX review; this dimension
  delegates the advanced pass to it.
