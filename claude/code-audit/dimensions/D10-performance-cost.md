# D10 — Performance & cost baseline 📊

**Question**: "Is the latency baseline measured? Is the cost-per-user model concrete? Is capacity sizing justified?"

Release-tag-only deep. Between releases, scan-only — re-measuring p95 every audit pass is busywork unless something changed.

## Method

### Latency baseline existence

Find any benchmarks doc / file:

```sh
find . -iname "*benchmark*" -o -iname "*latency*" -o -iname "*perf*" \
  | head -10
```

Has numbers (p50 / p95 for representative requests) → 🟢.
Has numbers >12 months old without a re-measurement note → 🟡.
No numbers at all → 🟡 (PoC bar) / 🔴 (production bar).

### Cost model concreteness

For products with variable upstream costs (LLM calls, third-party APIs metered by usage):

- Is there a cost-per-user / cost-per-tenant model?
- Are the inputs real (LLM SpendLogs queries, billing exports) or guesstimates?
- Does the model account for tier mix (cheap / mid / expensive request types)?

Guesstimate-only cost model at scale → 🟡 (you'll be surprised by your own bill).

### Capacity sizing justification

For each tenant / customer / deployment tier:

- What VPS / instance size is recommended?
- What's the basis (load test, hunch, hand-wave)?
- What's the headroom (typical load vs sized capacity)?

Tier sizing "because that's what we tested with one customer" → 🟡.

### Load tests

```sh
find . -iname "*load*test*" -o -iname "*stress*" -o -iname "*k6*" -o -iname "*locust*"
```

Load test in the repo, runnable from CI → ✅.
Mention of load testing in docs but no runnable script → 🟡.
Zero → 🟡 for B2B-multi-tenant, 🟢 for early PoC.

### Slow-query / N+1 detection

Most performance footguns are N+1 queries surfacing only under load:

```sh
# Laravel
grep -rn "->load(" app/ | wc -l   # eager-loading usage
# vs lazy loads:
grep -rn "->[a-z]*->" app/ | wc -l  # rough proxy

# Django
grep -rn "select_related\|prefetch_related" --include="*.py"
```

If the framework offers eager-loading directives, but the codebase rarely uses them → 🟡 (likely N+1 latent).

## PoC bar

- Cost-per-user model exists with at least 3 data points (real, not estimated).
- Latency measured once for representative request types.
- Capacity sizing justified by tier mix (not "we'll figure it out at scale").

## Production bar

- SLO / SLI with explicit latency budget.
- Cost dashboards per tenant / per feature.
- Capacity model validated by load test at 2× expected peak.
- Continuous benchmark in CI, failing on regression > 20%.

## Cross-references

- D11 (Legal / compliance) — data residency cost implications.
- `playbooks/operations.md` — cadence (deep only on release tag).
