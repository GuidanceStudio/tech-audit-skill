# DEVPLAN — code-review skill

Findings from the 2026-06-10 self-audit of the skill (content + pipeline
review). Milestones ordered by priority. Source analysis: bugs verified
empirically (detect-stack miss on cerase-core, milestone-ID ordering,
tracked `__pycache__`), pipeline gaps (no fan-out, no finding
verification, no checkpointing), content gaps (correctness dimension,
AI-runtime threat model).

After any milestone that touches `claude/code-review/`, redeploy with
`./install.sh --force` (the installed copy at `~/.claude/skills/` is a
copy, not a symlink).

Recommended execution order (minimises re-touching the same files):
M1 → M2 → M9 (tests pin the fixes + guard the rename) → M7 (slim/dedup
before adding content) → M5 → M3 → M4 → M6 → M8.

---

## M1 — Bug fixes + repo hygiene

Status: **DONE** (2026-06-10) — TDD: `tests/test_scripts.py` written
first (nested-monorepo detection + unsorted-ID pairing seen red), then
fixes to green (6/6). Done-when verified: detect on cerase-core emits
`docker php php-laravel python shell typescript typescript-vite`;
no tracked pycache. Dev-only tests live in repo-root `tests/`
(not shipped by install.sh).

- [x] **Recursive stack detection.** `scripts/_detect_stack.py` only
  checks the repo root, so nested layouts are missed entirely
  (verified: on `cerase-core` it returns `docker shell` and misses
  PHP/Laravel in `control-plane/`). Walk markers recursively with a
  depth limit (~3), pruning `vendor/`, `node_modules/`, `.git/`,
  `storage/`, `dist/`, `build/`. Update `routing/detect-stack.md`
  ("root + first level" → recursive w/ depth) and the marker table in
  `SKILL.md` § Step 2 to match.
- [x] **Fix milestone-ID assignment.** In
  `scripts/_findings_to_milestones.py`, `render_triage_table` builds
  the ID map from a severity-sorted copy while `render_milestone_stubs`
  receives the unsorted list and does positional lookup — 🔴 findings
  can get crossed IDs when stdin isn't pre-sorted. Sort once in
  `main()` and pass the same sorted list to both renderers; key the map
  by finding identity, not position.
- [x] **Repo hygiene.** Add `.gitignore` (`__pycache__/`, `*.pyc`),
  `git rm -r --cached` the four tracked `.pyc` files. Make
  `install.sh` exclude `__pycache__` when copying.
- [x] **De-leak skill layout from D13 grep.** The hidden-step grep in
  `dimensions/D13-setup-replicability.md` excludes
  `tools/|examples/|threat-models/` — directories of the skill, not of
  the target repo. Replace with target-repo-relevant exclusions
  (recovery/runbook dirs, which the same section already whitelists).

Exit gate: `_detect_stack.py` on `cerase-core` emits
`docker php php-laravel shell` (+ any other true markers); a TSV with
unsorted severities round-trips through `_findings_to_milestones.py`
with correct IDs; `git ls-files | grep pycache` is empty.

## M2 — Rename to de-conflict from the builtin `/code-review`

Status: **DONE** (2026-06-10) — IDD (rename/content; regression guard =
M1 tests, path-agnostic via glob, still green 6/6). Done-when verified:
installed at `~/.claude/skills/code-audit/`, old `code-review/` copy
removed, install excludes `__pycache__`. Legit `code-review` mentions
survive only as upstream project names + the builtin reference.

Claude Code now ships a builtin `code-review` skill; two registered
skills share the name and routing is ambiguous. New name:
**`code-audit`** — the distinctive value is the audit/tech-DD
framework, not PR review, which the builtin already covers.

- [x] Rename `claude/code-review/` → `claude/code-audit/`, update
  `name:` in SKILL.md frontmatter and every self-reference
  (README.md, install.sh paths, cross-references inside the skill).
- [x] Rename the per-project extension dir too: `.code-review/extras/`
  → `.code-audit/extras/` (extensions/README.md, SKILL.md, cuts/full).
  No external users yet (v0.1.0) — no back-compat shim needed.
- [x] Rewrite the SKILL.md frontmatter `description:` — it is injected
  into EVERY session's context, used or not. Make it audit-first (so
  model routing doesn't compete with the builtin) and cut it to ~40
  words without losing the trigger surface.
- [x] Narrow the trigger keywords in SKILL.md: drop bare
  "review this PR/file" (let the builtin own quick diff review); keep
  audit / tech-DD / security review / release check / `/code-audit`.
  Keep the `quick` cut itself (still useful when explicitly invoked).
- [x] Install under the new name; remove the old
  `~/.claude/skills/code-review/` copy.
- [x] Note the rename + rationale in README.md.

Exit gate: `/code-audit` invokes this skill; no name collision warning;
old installed copy gone.

## M3 — Pipeline: persistent findings + adversarial verification

Status: **DONE** (2026-06-10) — IDD (process docs; crossref linter
green 11/11). Pipeline defined once in SKILL.md § Findings pipeline
(incremental findings.tsv per dimension, resume, 🔴 refutation,
ID-scheme match) and referenced from deep/full/release cuts; provenance
line added to both report templates; .code-audit/work/ gitignored.

The two highest-value/lowest-cost pipeline upgrades. Both are edits to
cuts + SKILL.md, no new scripts.

- [x] **Incremental findings file.** Define a canonical working file
  `.code-audit/work/<YYYY-MM-DD>/findings.tsv` (same TSV schema
  `_findings_to_milestones.py` consumes: severity, dim, location,
  title, fix, effort). `deep`, `full`, and `release` cuts append to it
  **at the close of each dimension** — the audit survives context
  compaction and is resumable; the final report is assembled from the
  file, not from conversational memory. `quick` and `security` stay
  inline (short enough). Document the resume flow: on re-invocation,
  if today's findings.tsv exists, skip completed dims and continue.
- [x] **Refutation pass for 🔴.** Add to every cut's procedure (and as
  a top-level rule in SKILL.md § Step 4): before emitting, each 🔴
  finding must survive an explicit refutation attempt — re-read the
  actual code path and try to prove the finding wrong (auth check
  present in middleware? scope applied by a parent? dead path?).
  Refuted → drop or downgrade with the reason noted. Unverifiable
  (can't read the relevant code / would need runtime) → keep but mark
  confidence (see M6).
- [x] **Update templates** (`triage-and-summary.md`,
  `full-audit-report.md`) with a one-line provenance note: findings
  source file path + "all 🔴 survived refutation".
- [x] **Match the target repo's milestone convention.** When emitting
  milestone stubs, detect the target devplan's existing ID scheme
  (e.g. `M<N>` with checkbox tasks) and pass the matching `--prefix` /
  formatting to `_findings_to_milestones.py` instead of the `AUDIT`
  default.

Exit gate: a deep cut on any repo writes findings.tsv incrementally; a
manufactured false-🔴 (auth check actually present upstream) gets
dropped by the refutation step.

## M4 — Pipeline: multi-agent fan-out for deep/full

Status: **DONE** (2026-06-10) — IDD (orchestration docs; crossref
linter green 11/11). full.md § Execution replaces the hour-budget table
with subagent fan-out (shared pre-scan computed once, one agent per
dimension returning TSV + coverage note, model tiering, merge, per-🔴
verifier, assemble) + sequential fallback + dedup rule + scope-not-clock
stop. deep.md fans out for multi-dim requests, inline for one.

Dimensions are near-independent; the `full` cut currently prescribes a
sequential 5-7 h human-calibrated pass that a single context cannot
hold.

- [x] **Fan-out orchestration in `cuts/full.md` and `cuts/deep.md`
  (multi-dim case).** When the harness supports subagents (Agent /
  Workflow tools), spawn one agent per dimension; each loads ONLY its
  `dimensions/D<N>-*.md` + the detected `languages/*.md` + threat
  models its methods reference, and returns findings as structured TSV
  rows. Orchestrator merges into findings.tsv, deduplicates
  cross-dimension overlaps, runs the M3 refutation pass (independent
  verifier agents — one per 🔴), then assembles the report.
- [x] **Sequential fallback** stays documented for harnesses without
  subagents (current cut text, trimmed).
- [x] **Replace hour budgets with operational units.** The per-dim
  time table in `cuts/full.md` ("D1: 1 h") is human-calibrated and
  meaningless to the model. Reframe as scope units: which methods are
  mandatory vs sample-N, max files to deep-read per method, when to
  stop ("stop after the method catalog is exhausted, not after N
  minutes").
- [x] **Dedup rule.** Same file+line surfaced by two dims → keep under
  the dim whose method is most specific, cross-reference the other.
- [x] **Shared pre-scan, computed once.** The orchestrator runs stack
  detection, the git-churn heatmap, and the file inventory ONCE and
  passes them in each agent's prompt — dimension agents must not each
  re-discover the repo (token waste + inconsistent scoping).
- [x] **Model tiering.** Scan-tier dimensions (D6, D7, D9, D11, D12)
  may run on a smaller/cheaper model when the harness supports a model
  override; always-deep dims and 🔴 verifiers stay on the main model.
- [x] **Coverage honesty.** Each dimension agent reports what it
  examined vs sampled-out (files deep-read, methods skipped and why);
  the report's scope section aggregates this — no silent truncation.

Exit gate: a full audit on a mid-size repo completes with per-dim
agents, produces one merged findings.tsv, and the report's status table
covers all 13 dims.

## M5 — Content: correctness dimension + AI-runtime threat model

Status: **DONE** (2026-06-10) — IDD (content; crossref linter guards
reachability, green 11/11). Done-when verified: D14 + ai-runtime.md
follow the dimension/threat-model file shape; registry lists D14
always-deep so every cut that honors tags runs it; quick cut runs D14
on every diff; detect-stack agentic sub-marker + D4/security loaders
default-load ai-runtime.md.

The two real content gaps.

- [x] **`dimensions/D14-correctness-robustness.md`.** The framework
  audits essentiality, docs, tests, security… but no dimension
  catalogs functional-bug hunting: unhandled error paths, race
  conditions / TOCTOU, idempotency of retried operations, transaction
  boundaries (partial-write on failure), resource leaks (connections,
  file handles, unbounded queues), off-by-one / boundary conditions,
  input validation at trust boundaries, timezone/encoding pitfalls.
  Method catalog with greppable patterns per stack + PoC/Production
  bars, same file shape as D1-D13.
- [x] **Wire D14 into cuts**: `quick` runs it ALWAYS on the diff
  (correctness is the #1 ask for a PR review — currently only D1
  essentiality is mandatory); `full` treats it as always-deep;
  `deep` topic map gets "bugs / correctness / robustness" → D14.
- [x] **`threat-models/ai-runtime.md`.** `llm-assisted-code.md` covers
  code *written by* LLMs; nothing covers LLMs *in the product*: prompt
  injection → unintended tool calls, confused-deputy through MCP/tool
  gateways, secrets/PII leaking into prompts or model logs, exfil via
  outbound channels (chat bridges, webhooks), missing human-approval
  gates on destructive tools, tenant context bleeding through shared
  agent runtimes. Referenced from D4 (security) and D5 (multi-tenant)
  when the product embeds an LLM/agent surface.
- [x] **Stack detection hook**: add an "agentic product" sub-marker
  (MCP config files, agent SDK deps, LiteLLM/OpenRouter clients) in
  `routing/detect-stack.md` that flags the ai-runtime threat model as
  default-load for D4.

Exit gate: D14 file follows the dimension template; a security cut on
an MCP-bearing repo auto-loads `ai-runtime.md`.

## M6 — Content: smaller upgrades

Status: **DONE** (2026-06-10) — IDD + TDD for the script change
(7-column confidence tests written red-then-green; suite 12/12).
Done-when verified: templates/finding-phrasing.md documents the
confidence axis + secret-redaction rule; D12 has the API↔UI parity
method + ui-review cross-ref; SKILL.md documents workspace mode; D3
flake check gated to release/full; unknown-stack fallback already
landed in M5. install --check OK.

Grouped low-effort improvements; each is one focused edit.

- [x] **Confidence axis on findings.** Add `confidence:
  certain / probable / needs-verification` to the finding schema
  (templates + TSV format gains a 7th column; keep
  `_findings_to_milestones.py` backward-compatible with 6-column
  input). Severity says "how bad if true", confidence says "how sure".
  Pairs with the M3 refutation pass.
- [x] **API↔UI parity method in D12.** Mechanical check: diff the
  admin-surface actions (Filament resources/pages) against `/api/v1`
  routes; every admin-doable mutation without an API equivalent → 🟡.
  Generalize beyond Filament (admin routes vs public API routes).
- [x] **Workspace / multi-repo mode.** In SKILL.md routing: when the
  target directory contains multiple git checkouts (sibling-repo
  workspace), enumerate them, confirm scope with the user, run stack
  detection per repo, and produce per-repo findings with one merged
  summary. One paragraph in SKILL.md + a note in `cuts/full.md`.
- [x] **Gate the expensive D3 flake check.** Running the full suite 3×
  is costly; mark it opt-in (release/full cuts, or when the user
  reports flakiness), not part of the default deep pass.
- [x] **Honest unknown-stack fallback.** Replace "Django → load
  python-fastapi.md and note ORM differences" style mappings with: run
  the generic dimension methods, state that no stack file exists for
  the framework, and point to `.code-review/extras/language-*.md`.
- [x] **Cross-reference the ui-review skill.** D12 currently stops at
  render/empty-state checks; add a pointer: rendered-UI/UX depth is
  `ui-review`'s job, not this skill's.
- [x] **Secret-redaction rule in `finding-phrasing.md`.** Findings
  about leaked secrets (gitleaks hits, hardcoded tokens) must reference
  the location only — never quote the secret value into the report or
  the findings.tsv (reports get committed/shared).

Exit gate: templates show the confidence column; D12 includes the
parity method; SKILL.md documents workspace mode and the fallback.

## M7 — Token & maintenance efficiency pass

Status: **DONE** (2026-06-10) — IDD (content restructuring; guard =
crossref/reachability tests, green 11/11). SKILL.md now 103 lines (98
body + frontmatter) hosting the single-source dimension registry with
Topics column; deep-cut topic map, full-cut treatment lists and
operations cadence groups all reference registry tags. Tool-order and
paid-skip facts live only in tools/_matrix.md. examples/ moved out of
the shipped skill to docs/examples/. Execution-discipline block added.

The skill ships ~4.9k lines across 46 files; lazy-loading is the right
architecture but the loaded surface and the duplication can both
shrink. Run BEFORE M5 (new content lands on the deduped structure).

- [x] **Slim SKILL.md (the always-loaded file).** Keep only what
  routing needs: cut table, stack table, dimension registry, severity
  scheme, extension hook. Move "What this skill does NOT do",
  provenance, and the cadence/onboarding pointers to README.md.
  Target ≤100 lines.
- [x] **Single-source dimension registry.** The dim list (id, title,
  tag, topic keywords) currently repeats across SKILL.md, `cuts/full`,
  `cuts/deep` (topic map), `playbooks/operations.md` (cadence groups)
  — adding one dimension touches ~6 files. Canonical registry lives in
  the SKILL.md table only (add a topic-keywords column absorbing the
  deep-cut map); cuts and playbooks reference *tags* (always-deep,
  scan, …) instead of re-listing IDs.
- [x] **Dedup repeated facts.** One home each, cross-referenced
  elsewhere: tool execution order (now in both `cuts/security.md` and
  `tools/_matrix.md`), what-to-skip list (now in both
  `playbooks/operations.md` §3 and `tools/_matrix.md`).
- [x] **One home for examples.** Templates already embed full inline
  examples; the separate `examples/` dir duplicates the pattern and is
  referenced by no cut. Drop `examples/` (or fold anything unique into
  the templates).
- [x] **Execution-time token discipline** — a short (~10 line) block
  in SKILL.md, applying to every cut:
  - Tool output goes to a file (`--format json -o`), then summarize
    counts + top findings; never dump raw scanner output into context.
  - Grep/heatmap-first sampling: deep-read only the top-N candidate
    files per method, never whole-repo reads.
  - Intermediate notes stay terse (TSV rows); prose only in the final
    report; cite `file:line`, don't paste code blocks unless the hunk
    is the finding.

Exit gate: SKILL.md ≤100 lines; each duplicated fact has exactly one
home; `examples/` gone or referenced; the discipline block exists.

## M8 — Repeat-audit memory: accepted-findings baseline + deltas

Status: **DONE** (2026-06-10) — IDD (process docs; crossref linter
green 12/12). SKILL.md § Repeat-audit memory defines
.code-audit/accepted.tsv (suppression baseline with revisit-by) and
mechanical findings.tsv deltas; false-positives.md gains the
audit-level acceptance flow that writes the baseline; full cut trend is
now generated from the diff (replacing read-the-old-report), release
cut filters the ship-block list through the baseline.

Today every audit re-surfaces the same accepted 🟡s, and trend
tracking means "re-read the previous report and eyeball it". Make
repeat audits incremental — solidity AND token savings.

- [x] **`.code-audit/accepted.tsv`** in the target repo: one row per
  dismissed/accepted finding (stable key = dim + location + title
  slug, severity, reason, date, optional revisit-by). Every cut
  filters its findings against it before reporting; the report shows
  "suppressed: N accepted findings" with expired `revisit-by` entries
  resurfacing automatically.
- [x] **Wire `playbooks/false-positives.md` to it.** The dismissal
  flow ends with appending a row to accepted.tsv, not just a verbal
  dismissal that evaporates.
- [x] **Mechanical deltas.** `full` and `release` cuts diff the
  current findings.tsv against the most recent prior
  `.code-audit/work/<date>/findings.tsv`: new / fixed / still-open per
  severity. The report's trend section is generated from that diff,
  replacing the read-the-old-report instruction in `cuts/full.md` § 1.

Exit gate: re-running a cut after accepting a finding suppresses it
(visible in the suppressed count); a full audit after a fix shows the
finding under "fixed since last audit".

## M9 — Skill self-tests, CI, drift check

Status: **DONE** (2026-06-10) — TDD: crossref linter + --check tests
written first (red: 3 real dead refs found and fixed — SKILL.md
threat-model shorthand names, D05 phantom probe script, README D{01..13}
pattern; --check unimplemented). Then install.sh --check + .installed-from
SHA stamp + GitHub Actions (repo is PUBLIC → free runners, no billing
fallback needed). Suite: 11 green + ruff clean. 7-col TSV test deferred
to M6 with the feature.

The skill preaches tests-as-adversaries and has zero tests. Dev-only
material lives in repo-root `tests/` — NOT under `claude/`, so the
installed skill stays lean.

- [x] **pytest suite** (`tests/` + fixture mini-repos):
  - `_detect_stack.py`: root markers, nested monorepo (the
    cerase-core regression from M1), no markers (exit 2).
  - `_findings_to_milestones.py`: round-trip with unsorted severities
    (the M1 ID bug), 6-column and 7-column (M6 confidence) input.
  - Cross-reference linter: every relative `.md` path referenced from
    a skill file exists, and every shipped `.md` is reachable from
    SKILL.md (dead-link + dead-content check — enforce the skill's own
    "no dead content" rule mechanically).
- [x] **CI**: GitHub Action running ruff + pytest on push. Caveat: if
  the repo is private and org Actions are billing-blocked, fall back
  to a documented local pre-push hook instead.
- [x] **Install drift check.** `install.sh --check`: compare the
  installed copy against the dev tree (checksum diff, `__pycache__`
  excluded) and report drift; on install, stamp the installed dir with
  the source git SHA so "what version is deployed?" has an answer.

Exit gate: `pytest` green locally; cross-ref linter passes on the
current tree; `install.sh --check` detects a hand-edited installed
file.
