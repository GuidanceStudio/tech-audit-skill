# D16 — UI & design-system craft 🎨

**Question**: "Is the interface built from a consistent design system —
tokens, scale, components — or from one-off hex values and magic
pixels? Does it hit the bar of a modern Western scale-up, or does it
read as unfinished?"

Default-deep when a UI surface is detected (`ui-deep` tag — see
`routing/detect-stack.md`). Base source-level pass + advanced rendered
pass. D15 owns *interaction/UX*; this owns the *visual/system* layer.

## The reference bar — "Western scale-up"

Findings are calibrated against the craft level of a well-funded Western
B2B/SaaS scale-up — **Linear, Stripe, Vercel, Notion class**:

- **Systematic spacing** — a single spacing scale (4/8px rhythm), not
  arbitrary margins. Consistent gutters and vertical rhythm.
- **Restrained palette** — a neutral grey ramp + ONE brand accent;
  semantic colors (success/warning/danger) used only semantically. Not
  a rainbow.
- **Typographic hierarchy** — a small, deliberate type scale (≈4–6
  sizes), one or two families, readable body (~16px), clear h1→body
  contrast.
- **Generous whitespace** — content breathes; density tuned to the
  audience (dense for B2B power tools, airier for marketing), never
  cramped-by-accident.
- **Purposeful motion** — transitions that aid orientation (150–250ms,
  ease-out), not decorative bounce. Respects `prefers-reduced-motion`.
- **Crisp, consistent components** — same control = same look
  everywhere; one corner-radius scale; consistent borders/shadows;
  coherent iconography (one set, one weight).

A finding names the gap to that bar concretely ("12 distinct hardcoded
greys where a 5-step neutral ramp would do"), never "make it look more
premium".

## Base pass — source-level (always)

### Design-token discipline

```sh
# Hardcoded colors and magic pixel values instead of tokens/scale
grep -rnoE '#[0-9a-fA-F]{3,8}\b' --include='*.{css,scss,tsx,jsx,vue,svelte}' . | sort | uniq -c | sort -rn | head -20
grep -rnoE '[^0-9-][0-9]{1,3}px' --include='*.{css,scss,tsx,jsx,vue}' . | wc -l
# Is there a token source of truth?
ls tailwind.config.* theme.* tokens.* 2>/dev/null; grep -rln 'var(--' --include='*.css' . | head
```

Many distinct raw hex values / px literals and no token source → 🟡
(🔴 when there's a design system but components bypass it). A handful of
greys that should be a neutral ramp → name the ramp.

### Component reuse vs one-off styling

```sh
# Same visual element re-implemented instead of a shared component
grep -rnE 'className="[^"]*(btn|button|card|badge)' --include='*.{tsx,jsx,vue}' . | wc -l
# inline style attributes (one-off styling smell)
grep -rnE 'style=\{?\{|style="' --include='*.{tsx,jsx,vue,blade.php}' . | wc -l
```

Repeated bespoke styling of what should be one component, or pervasive
inline styles → 🟡 (consolidate into a variant of a shared component).

### Scale consistency

- **Type scale**: count distinct `font-size` declarations — a sprawl
  (>8) signals no scale → 🟡.
- **Radius / shadow / border**: count distinct values; >3–4 each → 🟡.

```sh
grep -rhoE 'font-size:\s*[0-9.]+(px|rem|em)' --include='*.{css,scss}' . | sort -u | head -20
grep -rhoE 'border-radius:\s*[0-9.]+(px|rem)' --include='*.{css,scss}' . | sort -u
```

### Responsive in code

Breakpoints defined consistently (a shared set, not ad-hoc media
queries everywhere); fluid layout, not fixed desktop widths.

```sh
grep -rhoE '@media[^{]+' --include='*.{css,scss}' . | sort | uniq -c | sort -rn | head
grep -rnE 'width:\s*[0-9]{3,}px' --include='*.{css,scss}' . | head   # fixed wide widths
```

Ad-hoc breakpoints / fixed desktop widths → 🟡.

### Theming & dark mode

If a theme/dark-mode is offered, are colors token-driven (so both
themes stay consistent) or hardcoded per component? Hardcoded colors
that break one theme → 🟡.

### Motion discipline

```sh
grep -rnE 'transition|animation|@keyframes' --include='*.{css,scss,tsx,jsx,vue}' . | head
grep -rln 'prefers-reduced-motion' --include='*.{css,scss}' . | head
```

Decorative/long animations, or no `prefers-reduced-motion` guard → 🟡
(accessibility + polish).

## Advanced pass — rendered (opt-in, needs a runnable app)

Source proves the *system*; only a render proves the *result*. When the
app is runnable with Node + Playwright, use the **shared rendered
hand-off** (see D15): invoke the `uxui-audit` skill (or its
`scripts/capture.mjs`) once, and apply its **Visual design** and
**Responsive** dimensions to the screenshots — that skill owns capture
and the pixel rubric. Fold findings back tagged `D16`. Both skills
share the unified 0–4 severity scale; findings fold directly, no
mapping needed. Run the capture ONCE and split findings between D15
(usability/state) and D16 (visual/responsive); don't screenshot twice.

Without a runnable app or Playwright, stay source-level and record the
rendered pass as **deferred**.

## PoC bar

- A token source of truth exists (colors, spacing, type) and components
  use it rather than raw values.
- One type scale, one radius/shadow scale, a shared breakpoint set.
- Motion is short, purposeful, and reduced-motion-safe.

## Production bar

- Design tokens enforced (lint rule against raw hex/px in components).
- Advanced rendered pass clean of severity-3+ visual/responsive
  findings on every release (via `uxui-audit`).
- A documented component library; new UI composes it rather than
  restyling.

## Cross-references

- D15 — UX & interaction (shares the advanced rendered hand-off; run
  `uxui-audit` capture once, split findings D15/D16).
- D12 — admin-surface coherence (label/state consistency overlaps;
  keep a finding in one dimension).
- `uxui-audit` skill — owns rendered capture + the visual-design rubric.
