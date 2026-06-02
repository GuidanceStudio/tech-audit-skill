# Threat model — PII data flow

When the product's contract includes privacy / PII protection, the audit must trace PII end-to-end. A single unmasked egress to a third-party API can violate the contract.

## The egress map

Every external network call is an egress candidate. Build the map:

```sh
# Find external HTTP calls
grep -rnE 'http\.(post|get)|requests\.(post|get)|HttpClient\.|->post\(|->get\(|fetch\(' \
  --include="*.py" --include="*.php" --include="*.ts" \
  | grep -vE 'localhost|127\.0\.0\.1|internal\.|cluster\.local'
```

For each external call:
- What inputs does it carry? (request body, query params, headers)
- Could user-supplied content (chat message, uploaded document, form field) appear in those inputs?
- If yes: does the request go through the PII de-identification layer FIRST?

External egress carrying user content WITHOUT PII de-id → 🔴.

## The de-identification pipeline

Standard architecture: every egress proxies through a PII gateway that:

1. Detects PII spans (Presidio, AWS Macie, custom regex, ...).
2. Substitutes spans with speaking-label tokens (`<EMAIL_1>`, `<PHONE_1>`).
3. Forwards the masked text upstream.
4. On response, re-substitutes the original spans back so the user-visible reply reads naturally.
5. Persists the (token → original-span) map for audit + un-masking.

Audit checks:
- Step 1 — what detectors are active? Are they appropriate for the product's locale?
- Step 2 — what's the token scheme? Are tokens stable (same input → same token) or per-call?
- Step 3 — what fields are forwarded? Could the model leak the token-→-span correlation by quoting back the token?
- Step 4 — under what conditions is re-substitution NOT done? (e.g. if the user is sharing a transcript externally.)
- Step 5 — where does the map live? How long is it retained? Who can read it?

## Detector quality regression — fixed corpus

PII detection is statistical. Quality regresses silently when the upstream library or model updates. Pin a fixed test corpus:

```yaml
# tests/fixtures/pii_corpus.yaml
- input: "Mi chiamo Mario Rossi, codice fiscale RSSMRA80A01H501Z."
  expected_spans:
    - { type: PERSON, value: "Mario Rossi" }
    - { type: IT_FISCAL_CODE, value: "RSSMRA80A01H501Z" }
- input: "IBAN: IT60X0542811101000000123456"
  expected_spans:
    - { type: IBAN_CODE, value: "IT60X0542811101000000123456" }
# ... more, covering the locale's PII categories
```

CI step:

```sh
python -m pytest tests/test_pii_corpus.py --strict-recall
```

Fails if recall drops below the recorded baseline. New release upstream that "improves" detection but misses old types → caught immediately.

## Log egress hygiene

Production logs must not contain raw PII. The de-id pipeline doesn't help if the LOGGER bypasses it:

```sh
# Search for logger calls that may include PII
grep -rnE 'logger\.[a-z]+\(.*\$.*email|logger\.[a-z]+\(.*\$.*name|console\.log.*request\.body' .
```

Each match → manual triage. If the field could contain PII → 🔴 unless masked first.

Pattern fix: structured logger with field-level redaction (`pino` `redact`, Python `structlog` processors, `monolog` filters).

## Backup encryption — PII at rest

Backups carrying PII at rest must be encrypted with a key NOT in the same blob. See D4.

Backup that contains the audit log (which contains rehydrated text) → 🔴 if unencrypted.

## Cross-references

- `dimensions/D04-security-posture.md`.
- `dimensions/D11-legal-compliance.md` — GDPR posture.
- `dimensions/D03-tests-as-adversaries.md` — corpus regression pattern.
