# Finding phrasing

How to communicate findings. Used across every cut. Tone calibration matters as much as content.

## The three tones to avoid

### 1. Alarmist

> "🔴 CRITICAL VULNERABILITY: SQL injection at `routes.php:42`!!! This could expose ALL customer data!!! Fix IMMEDIATELY!!!"

Problem: every finding sounds the same. The reader stops trusting your severity ratings.

Better:

> "🔴 `routes/web.php:42` — `DB::raw($_GET['id'])` reads request input into a raw query. An unauthenticated user can read any row by altering the URL. Fix: parameterize the query or use the model layer."

### 2. Patronizing

> "It would probably be a good idea to maybe consider adding a test for this. You might want to think about whether..."

Problem: hedging dilutes the recommendation. The reader can't tell what to do.

Better:

> "🟡 `app/Models/User.php:14` — no test covers the cascade-delete behavior. Add `tests/Feature/UserDeletionTest.php` with the 3 cascade scenarios."

### 3. Smug

> "Obviously you forgot to validate input here. This is a basic security mistake."

Problem: the reader stops listening. Audit reports are read by humans who care about their work.

Better:

> "🟡 `controllers/Form.php:23` — input from `request()->all()` is mass-assigned without `$fillable` enforcement. Add `$user->fill($request->validated())` instead."

---

## The phrasing template

Every finding has three parts:

1. **Where** — `path:line` (or short symbol).
2. **What** — one-line factual statement of the issue.
3. **Why it matters** + **suggested fix** — one or two lines each, in plain language.

```
🔴 path:line — <what, neutral, factual>.
_Why it matters_: <impact in plain language, 1 line>.
_Suggested fix_: <concrete, implementable in 30 min, 1-2 lines>.
```

Optional fourth part for 🔴 only:

4. **Threat model** — one-line link to `threat-models/<file>.md` if the finding fits a known pattern.

---

## Specific calibrations

### When the code is correct but the test is missing

🟡, not 🔴. The bug doesn't exist yet — the regression risk does.

### When a style preference is being argued

🟢 if argued at all. Don't manufacture 🟡 to look thorough on a clean PR.

### When the same pattern repeats 50× in the codebase

ONE finding ("pattern X appears 50× — see appendix") + an appendix listing each occurrence. Not 50 individual findings (drowns the report).

### When a finding is real but recovery is genuinely "fix later"

Triage explicitly:

> "🟡 D6-2 — backup never restored in living memory. Acceptable risk until the next release; document in `docs/runbook/known-gaps.md`. Effort to drill: 2 h."

The reader knows it's been thought about, not forgotten.

### When the user asked "is this OK?" and the answer is yes

Say yes. Don't pad with three nits to justify your existence.

> "Quick scan — `PR #143`: ship. The diff is correct, scoped, and tested. No findings."

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

## Examples — translation of bad to good

| Bad | Good |
|---|---|
| "Consider improving error handling here." | "Wrap the API call in `try/catch` — current code crashes the request on a 500 response from the upstream." |
| "Code quality could be better." | "Function `handle()` is 280 lines. Split into 3-4 methods along the auth-check / business / persistence boundary." |
| "Security issue." | "`X-Forwarded-For` is trusted without verification. An attacker can spoof their IP for the rate limiter by setting this header." |
| "Missing tests." | "No test covers the timezone DST transition in `BookingService::compute`. Add a test that creates a booking spanning the DST boundary." |

---

## When emitting Italian or other locale

If the project's docs are in Italian (or another language), match the finding phrasing's language but keep the technical terms in English (function names, framework concepts). The PR review goes to engineers; mixed lexicon is normal.

Severity emojis (🔴🟡🟢) and structural words (Where / What / Why) stay constant for grep-ability across audits.
