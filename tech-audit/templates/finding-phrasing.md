# Finding phrasing

How to communicate findings. Used across every cut. Tone calibration matters as much as content.

## Tone rules
1. No exclamation marks or ALL-CAPS — severity is the emphasis.
2. No hedging ("consider", "might want to") — say "Fix:" or "Do X".
3. No judgment words ("obviously", "basic mistake") — state facts.
4. One finding = one issue. Don't bundle "fix the whole page".

---

## Finding format
🔴 path:line — <factual what>. _Why_: <1-line impact>. _Fix_: <1-2 lines concrete change>. For 🔴 only: _Threat_: link to threat-models/<file>.md.

Location cites where the defect *originates* — trace the bad value/config back through the boundary — not the site where it surfaces; name the symptom site in the fix when useful.

## D1 essentiality prefixes

D1 finding titles start with exactly one prefix from the essentiality
taxonomy defined in `dimensions/D01-code-essentiality.md`. Follow the
prefix with the concrete construct to remove, then name the exact
replacement in the suggested fix. Do not redefine the taxonomy here;
D1 is its single source of truth.

Example:

> `native: custom modal wrapper for one confirmation dialog. Replace
> it with the platform dialog element and keep the existing focus and
> accessibility behavior.`

---

## Security findings (D4, D5)

A security finding states the lower-trust principal, the input it controls, the control it bypasses, the affected resource and the observed or owner-observable result. A deviation from a checklist with no such path is hardening: it goes to the separate Hardening list, without a severity above 🟢.

A finding that depends on a control outside the repository (proxy, provider setting, response header, ACL, identity policy) assumes neither its presence nor its absence. It is `needs-verification` and names the missing fact and a check the owner can run.

---

## Severity vs confidence
Severity (0-4) = how bad if true. Confidence (certain/probable/needs-verification) = how sure. Independent axes. A 4 tagged needs-verification is still a 4: triage can usually verify against the source, so discounting severity for uncertainty would only hide impact. Never inflate confidence. Optional 7th TSV column.

Findings about secrets cite only path:line + variable name — never paste the value. Reports get committed.

---

## Calibrations
- Hedge words in the body ("probably", "likely", "may", "seems") force confidence: needs-verification — or rewrite to the observed fact.
- Correct code but missing test → 🟡 (not 🔴). The bug doesn't exist yet.
- Style preference → 🟢 if at all. Don't manufacture findings on a clean PR.
- Pattern repeated ×50 → ONE finding + appendix, not 50 individual items.
- Deferred fix → document it. "Acceptable risk until next release."
- Asked "is this OK" and it is → say yes. Don't pad with nits.

---

## Words to avoid

- **"Best practice"** — vague, religious. Say "the standard in this stack is X because Y" or just give the concrete change.
- **"Industry standard"** — same. Cite the source if you mean it (OWASP, RFC, vendor doc).
- **"Should consider"** — use "should" or "should not". The reader doesn't need permission to act.
- **"Refactor"** as a verb in a fix — too vague. Name the specific structural change.
- **"Cleanup"** as a verb — same.

---

## Words to use

- **"Fix"** — concrete change.
- **"Risk"** — possible bad outcome.
- **"Track"** — open follow-up, don't fix now.
- **"Accept"** — decide not to fix, with reason.
- **"Document"** — capture in writing so the next reader doesn't re-debate.

---

## When emitting Italian or other locale

If the project's docs are in Italian (or another language), match the finding phrasing's language but keep the technical terms in English (function names, framework concepts). The PR review goes to engineers; mixed lexicon is normal.

Severity emojis (4🔴 / 3🟡 / 0-2🟢) and structural words (Where / What / Why) stay constant for grep-ability across audits.
