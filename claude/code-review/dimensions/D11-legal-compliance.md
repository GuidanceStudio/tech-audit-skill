# D11 — Legal / compliance ⚖️

**Question**: "GDPR posture (export, delete, data location)? License compliance? Third-party data flows documented?"

Scan dimension. The minimum-credible-baseline level. SOC2 / ISO27001 readiness is out of scope for this skill — those are months-long programs, not an audit pass.

## Method

### GDPR rights — data export

Does the product implement Article 20 (data portability)?

```sh
grep -rnE "export.*user.*data|user.*export|gdpr.*export|right_to_portability" .
```

Documented + implemented + tested → ✅.
Documented but not tested → 🟡.
No mention → 🔴 if the product serves EU data subjects.

### GDPR rights — data deletion

Does the product implement Article 17 (right to erasure)?

```sh
grep -rnE "delete.*user|user.*delete|gdpr.*delete|right_to_erasure" .
```

- A "delete user" endpoint that does soft-delete only is fine for short windows but must hard-delete (or anonymize) after a retention period.
- The audit log poses a tension: GDPR-delete vs append-only audit. The standard fix is: keep audit entries but anonymize the PII fields.

No deletion path → 🔴 if EU data subjects.

### Data location

Where does tenant data actually live?

- Primary DB: which region?
- Backups: which region(s)?
- Third-party processing (LLM, payments, analytics): which regions?

Required:
- A `docs/privacy/data-flow.md` (or equivalent) that maps each data category to its physical storage location.
- A documented sub-processor list — third parties that process tenant data, what data category, what purpose, where.

No data-flow doc → 🔴.
Sub-processor list missing → 🔴.
Sub-processor list >6 months stale → 🟡.

### License posture vs commercial intent

Cross-reference with D7's license inventory:

- Any AGPL / SSPL dep in a closed-source product → 🔴.
- Any GPL v2/v3 in a closed-source product → 🔴 (LGPL is usually OK with dynamic linking).
- Any license that requires source disclosure → 🔴 unless the team chose this knowingly.

### Privacy policy + ToS

```sh
ls -la docs/legal/ docs/privacy/ docs/terms/ 2>/dev/null
ls -la PRIVACY.md TERMS.md 2>/dev/null
```

Stub privacy policy → 🟡.
No privacy policy at all → 🔴 if the product is live with paying customers.

### Cross-border data transfer

If the product transfers data EU → US (or vice versa) — typical with US-hosted LLM providers — the legal basis must be documented:

- Standard Contractual Clauses (SCCs)?
- Adequacy decision?
- Specific user consent per call?

Undocumented EU→US transfer in a B2B product → 🟡 (often, the customer's DPA handles this, but the team should know which one).

### DPIA (Data Protection Impact Assessment)

For high-risk processing (PII at scale, automated decision-making, biometrics):

```sh
ls -la docs/legal/dpia* docs/privacy/dpia* 2>/dev/null
```

DPIA done at least once → 🟢.
DPIA never done for a product that processes PII → 🟡 (PoC bar) / 🔴 (production bar).

## PoC bar

- DPIA done at least once.
- Privacy policy stub exists.
- Sub-processor list exists in `docs/`.
- Cross-border transfer legal basis documented.
- GDPR data export + delete paths exist (implementation can be manual).

## Production bar

- DPA template ready for prospects, with sub-processor flow-down.
- EU/US data residency selectable per tenant.
- GDPR export + delete are self-service (user can trigger from the UI).
- Annual privacy review documented.
- SOC2 / ISO27001 trajectory mapped (out of scope for this skill).

## Cross-references

- D4 — security posture (PII enforcement layer).
- D7 — license inventory.
- `threat-models/pii-data-flow.md` — concrete PII pipeline patterns.
