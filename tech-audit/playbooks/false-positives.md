# False positives

Tools generate noise. Triaging dismisses honestly without rubber-stamping. Heuristics + escalation pattern.

This file covers two kinds of dismissal: **tool-generated** false
positives (suppress at the tool's config, below) and **audit-level**
findings the team consciously accepts (record in the repeat-audit
baseline, next section) so the next audit doesn't re-surface them.

## Accepting an audit finding (the baseline)

When you (or the user) decide an audit finding is a false positive or
an accepted risk, don't just say so in chat — it evaporates and the
next audit raises it again. Append a row to `.tech-audit/accepted.tsv`
in the target repo:

```
dim␟location␟title-slug⇥severity⇥reason⇥date⇥revisit-by
```

- **key** (`dim␟location␟title-slug`) is what each cut matches fresh
  findings against to suppress them.
- **reason** is mandatory — "accepted: legacy module, rewrite tracked
  in M52" / "false positive: scope applied by parent middleware".
- **revisit-by** is optional; past that date the finding resurfaces
  automatically (use it for "accept until the next release").

A cut reports `suppressed: N accepted findings` so the suppression is
visible, never silent. This is the audit-level analogue of the
tool-config suppressions below.

## The decision tree

For every tool-generated finding:

1. **Is the finding factually correct?** (The tool's analysis matches reality.)
   - **No** → it's a false positive. Suppress with justification.
   - **Yes** → continue.

2. **Is the impact real given the context?** (Could a malicious actor exploit this in *this* deployment?)
   - **No** → suppress with justification.
   - **Yes** → continue.

3. **Is fixing cheaper than suppressing?**
   - **Yes** → fix.
   - **No** → suppress with justification + open follow-up if upstream might fix.

## Suppression discipline

Every suppression needs a justification COMMENT or DOC LINK, not a silent skip.

### Gitleaks

```sh
# In source: comment on the offending line
api_key = "sk_test_50charssomething"   # gitleaks:allow - example credential in docs
```

```toml
# .gitleaksignore
# Repo-level allowlist with reason
sk_test_50charssomething  # docs/getting-started.md example credential
```

### Semgrep

```python
# Inline suppress with rule ID + reason
result = eval(safe_expr)  # nosemgrep: python.lang.security.audit.eval-detected — safe_expr is whitelist-validated above
```

```yaml
# .semgrepignore — paths
tests/fixtures/
**/migrations/legacy/
```

### Trivy

```yaml
# .trivyignore
# Each entry: CVE ID + reason + review date
CVE-2024-1234   # libxml2 — vulnerable function not called in our code, re-review 2026-09
```

### PHPStan / Psalm

```neon
# phpstan.neon — per-path ignore
parameters:
    ignoreErrors:
        - identifier: 'argument.type'
          path: 'app/Legacy/OldController.php'
          reason: 'Legacy module flagged for rewrite in Q3'
```

### mypy

```python
result = legacy_call()  # type: ignore[no-untyped-call]  # legacy_call is third-party-untyped, see issue #X
```

## When NOT to suppress

- "The CI is failing and we want to ship today" — open a follow-up, don't suppress.
- "The tool is annoying" — tune the rule (severity, path filters), don't blanket-disable.
- "I don't understand the finding" — investigate. If after investigation it's still unclear, suppress with `unclear, investigate later — issue #X` and open the issue.

## Tool-specific false-positive patterns

| Tool | Common false positives |
|---|---|
| Gitleaks | Long random-looking strings (image digests, UUIDs). Usually auto-filtered. |
| Trivy | CVEs in transitive deps not actually exercised at runtime. |
| Semgrep | Test fixtures looking like real credentials. |
| PHPStan | Generic types from Eloquent at higher levels. |
| mypy | Third-party libraries without stubs. |
| Hadolint | DL3008 (apt-get pinning) — pinning every apt package is overkill for dev images. |

## Drift watch

Suppressions decay. Once a year, review the suppression list:

```sh
# Count suppressions per file
grep -rn "nosemgrep\|gitleaks:allow\|type: ignore" --include="*.py" --include="*.php" --include="*.ts" \
  | awk -F: '{print $1}' | sort | uniq -c | sort -rn
```

Files with >5 suppressions → likely the codebase shape has drifted from the tool's expectations; consider whether the suppression is still needed or whether to remove the file from the tool's scope entirely.

## Cross-references

- `tools/*.md` — per-tool tuning sections.
- `playbooks/operations.md` — cadence (quarterly suppression review).
