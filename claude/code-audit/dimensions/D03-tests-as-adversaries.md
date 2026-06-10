# D3 — Tests as adversaries 🧪

**Question**: "Do the tests actively try to break the system, or do they just confirm the happy path? Does every bug we fix get a test that pins it shut? Does at least one test exercise the full user-visible flow?"

Always-deep. The previous framing — "critical-path coverage" — was too gentle. A real audit asks **adversary mindset**: edge cases, malformed input, concurrent access, partial failure.

## Method

### Tier inventory

Count tests per tier. A pure-unit-only suite at any non-trivial scale is a smell.

```sh
find . -path ./node_modules -prune -o -name "*Test.php" -print | wc -l
find tests/ -name "*.bats" 2>/dev/null | wc -l
find . -path ./node_modules -prune -o -name "test_*.py" -print | wc -l
find . -name "*.test.ts" -o -name "*.spec.ts" | wc -l
```

Compare:
- **Unit** (in-process, no DB / no network).
- **Integration** (in-process with real DB / real Redis / real cache).
- **Live** (against the actual running stack — Docker compose up, hit endpoints).
- **E2E** (full user-visible flow: front-door request → all backends → response).
- **Benchmark** (perf regression).

Test:service-file ratio < 20% → 🟡.

### Critical-path coverage matrix

For each critical path in the codebase, assert ≥1 happy + ≥1 negative + ≥1 edge-case test.

Standard critical paths to look for:

| Path | Where it lives | What to test |
|---|---|---|
| Authentication | `*Auth*`, `login`, `session` | Happy login, bad password, expired session, MFA fallback |
| Authorization | `*Policy*`, middleware | Right role grants, wrong role 403s, missing role 401s |
| Billing / payment | `Charge`, `Subscription`, `Stripe*` | Successful charge, declined card, idempotency |
| Privacy / PII | `Pii*`, `Presidio*`, `Mask*` | PII detected, masked, rehydrated |
| Multi-tenant scope | `tenant_id`, `team_id`, global scope | Cross-tenant read denied, write denied |
| Audit log | `AuditSink`, `event_log` | Insert succeeds, DELETE forbidden, UPDATE forbidden |
| JWT / token issuance | `*Jwt*`, `*Issuer*` | Valid token verifies, expired rejects, wrong-aud rejects |
| MCP / RPC dispatch | gateway, dispatch layer | Allowed call OK, denied call refused, timeout handled |

Each cell missing → 🟡. Auth or billing happy-path missing → 🔴.

### E2E user-flow coverage

At least one test that exercises a realistic full-stack scenario WITHOUT mocking the backends. For an LLM-driven product: "user message → all middleware → LLM call → tool invocation → response chunks → reply rendered". For a B2B SaaS: "signup → activation → first feature use".

Live `bats` / Playwright / Pytest-against-docker-compose are the homes. Pure-unit "E2E" via mocks does NOT count.

Zero true E2E → 🔴. The system is "tested in pieces" and unverified as a whole.

### Regression-after-fix ratio

For the last 10 closed bug milestones / commits with `fix:` or `bug:` prefixes, count how many added a test that PINS the fix.

```sh
git log --grep="^fix:\|^bug:" --pretty=format:"%H %s" | head -10 \
  | while read sha msg; do
      added_tests=$(git show --name-only --pretty=format:'' "$sha" \
        | grep -E "_test\.|Test\.php|\.test\.|\.spec\." | wc -l)
      echo "$sha  tests=$added_tests  $msg"
    done
```

Ratio:
- ≥80% → ✅
- 50-79% → 🟡 (the team mostly does it, codify in PR template)
- <50% → 🔴 (the team doesn't do it; each future bug re-occurs eventually)

### Mock smell

What's mocked is what's least trusted. For every mock, trace whether the mocked dependency has its own real-infra test elsewhere.

```sh
grep -rE "Mock\(|mock\(|@patch|sinon\.stub|fake[A-Z]" tests/ test/ | head -30
```

Mock-only on a critical path → 🔴 (the unit test passes but the real component might still be broken).

### Edge-case fuzz

For auth + JWT + tenant_scope paths, the suite must include feeds of:

- Empty strings (`""`)
- Null bytes (`"\x00"`)
- Very long strings (1MB+)
- Unicode boundary cases (surrogate pairs, RTL marks, zero-width joiners)
- Locale-specific inputs (codice fiscale, IBAN, hiragana, ...)
- Legacy / migration values (old enum values, deprecated formats)
- SQL/XSS payload corpus

Property-based: `hypothesis` (Python), Pest datasets (PHP), fast-check (TS).

At least one such test per critical path → 🟡 if missing.

### Domain-specific regression corpus (when applicable)

If the product makes a domain promise (e.g. PII detection, currency conversion, language detection), maintain a **fixed corpus** of inputs + expected outputs as a regression test.

Example for PII detection: `tests/fixtures/pii_corpus.yaml` with codici fiscali, IBAN IT, P.IVA, email IT, indirizzi IT, piped through the analyzer in CI. Fail if recall drops below the recorded baseline.

Missing corpus when the product promise demands one → 🟡.

### Flake rate

Re-run the test suite 3× back-to-back. Any test that fails 1/3 → 🔴 (it's lying about reality every third run, which means it'll surprise the team eventually).

```sh
for i in 1 2 3; do
  ./run-tests.sh --auto 2>&1 | tail -1 > /tmp/run-$i.txt
done
diff /tmp/run-1.txt /tmp/run-2.txt && diff /tmp/run-2.txt /tmp/run-3.txt
```

## PoC bar

- Every critical path: happy + negative + edge-case test.
- ≥1 true E2E with real infra (not mocked).
- Regression-after-fix ratio ≥50%.
- Zero flakes across 3 consecutive runs.

## Production bar

- Coverage report ≥70% for service layer.
- Mutation testing on billing + auth paths.
- Continuous fuzzer running against tenant_scope.
- Regression-after-fix ratio ≥80%, enforced via PR template.

## Cross-references

- `threat-models/pii-data-flow.md` — for the PII corpus pattern.
- `threat-models/multi-tenant-isolation.md` — for the cross-tenant probe suite.
- `tools/pgtap.md` — for DB-level test pattern.
