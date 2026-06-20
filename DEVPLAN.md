# DEVPLAN — tech-audit skill

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

## M2 — Rename to `code-audit`

Status: **DONE** (2026-06-10) — IDD (rename/content; regression guard =
M1 tests, path-agnostic via glob, still green 6/6). Done-when verified:
installed at `~/.claude/skills/code-audit/`, old `code-review/` copy
removed, install excludes `__pycache__`. Legit `code-review` mentions
survive only as upstream project names + the builtin reference.

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

---

# v0.3 — Generic packaging + UX/UI depth

Two arcs from the 2026-06-10 discussion. **Packaging:** the skill is
nested under `claude/code-audit/` and worded for Claude; research
confirmed `SKILL.md` is a cross-assistant standard (agentskills.io —
Claude Code, Codex CLI, opencode all read the same folder verbatim),
so flattening + de-Claudizing makes one payload installable everywhere,
with a root installer that targets each assistant. **Content:** the
framework has no dedicated UX or UI dimension (D12 is admin-surface
source only and defers rendered review to the `ui-review` skill); add a
UX level and a UI level, each source-level by default with an advanced
rendered pass (Playwright, delegated to `ui-review`) so we can audit
"the real thing".

User decisions (2026-06-10): installer = **broad** (native SKILL.md for
Claude+Codex+opencode, TOML for Gemini, generated AGENTS.md for the
Cursor/Windsurf/Copilot/Aider/Continue tier, + manual-copy path); UX/UI
= **hybrid** (base source-level always; advanced fires Playwright via
`ui-review`).

Recommended order: M10 → M11 → M12 (packaging first, so content lands
on the flat generic layout) → M13 → M14.

## Phase I — Generic packaging

### M10: Flatten the layout ✅

**Why:** A nested `claude/code-audit/` path fights manual installation
(people want to drop one folder where they like) and signals
"Claude-only". A top-level flat skill folder is the agentskills.io
shape and copies anywhere.

**Approach:** Move `claude/code-audit/` → top-level `code-audit/` (the
installable payload: `SKILL.md` + `cuts/ dimensions/ threat-models/
templates/ tools/ languages/ playbooks/ routing/ scripts/ extensions/`).
Update everything that assumes the old path: `install.sh`
(`SRC_ROOT`), the test SKILL-discovery globs in `tests/`, the
crossref linter, README layout + paths. `docs/examples/` stays out of
the payload. Tests stay green throughout.

**Tasks:**
- [x] `git mv claude/code-audit code-audit`; remove the now-empty `claude/`
- [x] Update `install.sh` source-dir detection to the flat path
- [x] Update `tests/*.py` skill-dir discovery to the flat path
- [x] Update README layout tree + all `claude/code-audit/` references
- [x] `pytest` + ruff green; `install.sh --force` then `--check` OK

**Done when:** the skill payload is a single top-level `code-audit/`
folder, the suite is green, and a bare `cp -r code-audit ~/somewhere`
yields a self-contained skill.

### M11: De-Claudize the content ✅

**Why:** The payload should read as assistant-neutral so Codex/opencode/
Gemini users aren't told to press Claude-specific buttons. The
`SKILL.md` frontmatter stays (it IS the shared standard), but harness-
and tool-specific wording should generalize.

**Approach:** Genericize the few Claude-isms: `cuts/full.md` fan-out
("the harness has subagents (Agent / Workflow tools)" → "your assistant
can run parallel subagents"); any `AskUserQuestion`/tool-name mentions →
"ask a structured question if your assistant supports it"; reviewer
strings "Claude code-audit skill" in templates → "code-audit skill";
`/code-audit` invocation phrased as "invoke the skill (slash command or
@-mention, per your assistant)". Add a short **"Using this skill"**
section to README mapping invocation per assistant. Keep severity
emojis, dimension IDs, method shell snippets unchanged.

**Tasks:**
- [x] Genericize `cuts/full.md` fan-out wording (subagents, model tiering)
- [x] Sweep templates + SKILL.md for "Claude"/tool-name strings; neutralize
- [x] Phrase invocation assistant-agnostically in SKILL.md
- [x] README "Using this skill" per-assistant invocation note
- [x] crossref linter green (no broken refs introduced)

**Done when:** `grep -ri 'claude\|AskUserQuestion\|Workflow tool' code-audit/`
returns only the agentskills.io-standard frontmatter and legitimate
upstream-project citations; the content reads tool-neutral.

### M12: Root multi-assistant installer ✅

**Why:** One installer that places the payload correctly for whichever
assistant the user runs, and prints the flat path for manual copy.

**Approach:** Rewrite root `install.sh` to prompt (or take a flag) for
the target and act per the research:
- **Claude Code** → copy `code-audit/` verbatim to `~/.claude/skills/code-audit/`.
- **Codex CLI** → copy verbatim to `~/.codex/skills/code-audit/` (same SKILL.md standard).
- **opencode** → copy verbatim to `~/.config/opencode/skills/code-audit/` (verify singular `skill`/`skills` dir against installed version; fall back to documented path).
- **Gemini CLI** → generate `~/.gemini/commands/code-audit.toml` wrapping the router (`prompt = """…"""`), since Gemini uses TOML not SKILL.md.
- **AGENTS.md tier** (Cursor/Windsurf/Copilot/Aider/Continue) → write/append a thin `AGENTS.md` pointer section that references the installed skill location + how to invoke the audit.
- **manual** → print the absolute path of the flat `code-audit/` folder and the one-line "copy it wherever your tool reads skills".
Keep `--force`, `--check` (per target), remote-clone mode, and the
`.installed-from` SHA stamp. Default with no target = interactive menu;
`--target <name>` / `all` non-interactive.

**Tasks:**
- [x] Target selection: interactive menu + `--target claude|codex|opencode|gemini|agents|manual|all`
- [x] Per-target placement (verbatim copy / TOML emitter / AGENTS.md writer / print-path)
- [x] Gemini TOML wrapper generation from the router
- [x] `--check` works per target; `.installed-from` stamp retained
- [x] Tests: install + `--check` for claude/codex/opencode (verbatim), gemini (toml present), agents (pointer present)
- [x] README install section rewritten for the multi-assistant flow

**Done when:** `install.sh --target <x>` installs correctly for each of
claude/codex/opencode/gemini/agents, `--check` detects drift per target,
and `--target manual` prints a copy-anywhere path. Suite green.

## Phase J — UX & UI depth

### M13: D15 — UX & interaction design ✅

**Why:** No dimension audits user experience. D12 covers admin-surface
source coherence only; rendered review lives in `ui-review`. A
product-wide UX dimension is missing.

**Approach:** New `dimensions/D15-ux-interaction.md`, same file shape as
D1–D14. **Base (source-level, always, no browser):** flow completeness
(every CTA has a destination, every error a recovery path in code),
interaction-state coverage in components (loading/empty/error/success
branches present), form UX (validation feedback wiring, disabled/in-
flight states, destructive-action confirmation), information
architecture & navigation structure, accessibility-in-markup (semantic
elements, alt text, labels, ARIA, focus-management code), i18n
readiness (hardcoded user-facing strings vs translation keys),
perceived-performance patterns (skeletons, suspense). **Advanced
(rendered, opt-in):** when the app is runnable and Node+Playwright are
available, hand off to the `ui-review` skill (or run its
`scripts/capture.mjs`) to screenshot real surfaces and apply its
usability/state/responsive checks — don't reimplement capture. Without
a runnable app, stay source-level and record the rendered pass as
deferred. PoC/Production bars + cross-refs (D12 admin-surface, D16,
`ui-review`). Tag in the SKILL.md registry as default-deep when a UI
surface is detected; add a frontend sub-marker to `routing/detect-stack.md`
(react/vue/svelte/angular deps, `.tsx/.vue/.blade.php` templates).

**Tasks:**
- [x] Write `dimensions/D15-ux-interaction.md` (base + advanced sections)
- [x] Add D15 to the SKILL.md dimension registry with its tag + topics
- [x] Frontend sub-marker in `routing/detect-stack.md` (flags D15/D16 default-deep)
- [x] Wire into cuts: `quick` (touched UI → D15), `deep` topic map via registry, `full` via tags
- [x] Cross-reference D12 + `ui-review` with a clear who-owns-what boundary
- [x] crossref linter green

**Done when:** D15 exists in the registry and cuts, runs source-level
with no browser, and its advanced section delegates the rendered pass
to `ui-review`/Playwright.

### M14: D16 — UI & design-system craft ✅

**Why:** No dimension audits visual/UI craft at the source level, and
the user wants a "Western scale-up" aesthetic bar made explicit.

**Approach:** New `dimensions/D16-ui-design-system.md`. **Base
(source-level):** design-token discipline (spacing/type/color scales vs
hardcoded hex/px magic numbers), component reuse vs one-off styling,
variant consistency, responsive breakpoints defined in code, theme/
dark-mode handling, motion/transition discipline, icon-system
consistency, typographic hierarchy in markup/CSS. Name the **reference
bar explicitly: "Western scale-up" = Linear / Stripe / Vercel / Notion-
class craft** — systematic spacing & type scale, restrained neutral
palette + one accent, generous whitespace, crisp hierarchy, purposeful
(not decorative) motion, density tuned to the user (dense for B2B power
tools, airy for marketing). Findings cite the gap to that bar.
**Advanced (rendered, opt-in):** same Playwright/`ui-review` hand-off as
D15 for visual-design + responsive checks on real screenshots.
PoC/Production bars + cross-refs. Same registry tag as D15.

**Tasks:**
- [x] Write `dimensions/D16-ui-design-system.md` (base + advanced; Western-scale-up bar named)
- [x] Add D16 to the SKILL.md registry; share the frontend sub-marker with D15
- [x] Wire into cuts (quick/deep/full) alongside D15
- [x] Cross-reference D15 + D12 + `ui-review`; de-duplicate the rendered-pass hand-off (one shared note, not two)
- [x] crossref linter green; full suite green; `install.sh --check` OK after redeploy

**Done when:** D16 exists with base + advanced passes, names the
Western-scale-up reference bar, shares the rendered hand-off with D15,
and the registry/report status table covers all 16 dimensions.

## Out of scope for v0.3

- Reimplementing screenshot capture in code-audit (the advanced pass
  delegates to `ui-review`, single source of truth).
- Native non-SKILL.md integrations beyond Gemini TOML + AGENTS.md
  (Cline `.clinerules`, Continue blocks) — covered by AGENTS.md or
  skipped until asked.
- A `uninstall` command; auto-update; telemetry.

---

# Follow-up — Ponytail essentiality integration

Integrate the useful part of
[`DietrichGebert/ponytail`](https://github.com/DietrichGebert/ponytail)
into the existing D1 review path without installing or vendoring its
plugin, lifecycle hooks, persistent modes, or duplicate review/audit
skills. Ponytail is conceptual prior art under the MIT license; this
repository remains the single source of truth for audit routing,
severity, findings, and devplan hand-off.

Recommended order: M15 → M16. These milestones are independent of the
completed v0.3 packaging and UI work.

## M15: Add the Ponytail essentiality ladder to D1 ✅

**Why:** D1 already owns dead code, over-abstraction, duplication, and
repository hygiene, but it does not give reviewers a compact,
deterministic order for finding the smallest correct replacement.
Installing Ponytail separately would duplicate `quick`/`full` review
routing and introduce always-on behavior outside code-audit's scope.

**Approach:** Extend `code-audit/dimensions/D01-code-essentiality.md`
with an essentiality ladder adapted from Ponytail: delete an unneeded
requirement or branch; prefer the standard library; prefer a native
platform feature; reuse an already-installed dependency; then shrink
the custom implementation. D1 findings use the compact title prefixes
`delete:`, `stdlib:`, `native:`, `yagni:`, and `shrink:` inside the
existing finding-title field, so the TSV schema and milestone bridge
remain compatible. Wire the taxonomy into the quick-scan phrasing and
the full-audit over-engineering companion report. State the ownership
boundary explicitly: D1 may remove incidental complexity, but it may
not weaken correctness, required tests, trust-boundary validation,
security, accessibility, data-loss handling, or an explicit user
requirement. Add Ponytail to README prior-art attribution with its MIT
license; do not copy its hooks or persistent-mode machinery.

**Tasks:**
- [x] Add the ordered essentiality ladder and five finding prefixes to `code-audit/dimensions/D01-code-essentiality.md`
- [x] Add D1-specific prefix guidance and concrete replacement wording to `code-audit/templates/finding-phrasing.md`
- [x] Update `code-audit/cuts/quick.md` and `code-audit/cuts/full.md` so D1 output uses the taxonomy consistently on diffs and repo-wide audits
- [x] Document the non-negotiable correctness, test, security, accessibility, and explicit-requirement boundaries
- [x] Add Ponytail to `README.md` prior art with repository link and MIT attribution
- [x] Test: add the initial D1 essentiality contract before changing the skill content
- [x] Test: run the existing cross-reference and full pytest suite
- [x] Commit & push

**Done when:** a quick or full D1 pass emits ranked, location-specific
essentiality findings with one of the five prefixes and a concrete
replacement, while the documented boundaries prevent minimalism from
overriding D3, D4, D14, D15, or explicit requirements; no Ponytail
plugin or hook is required.

**Notes:** Executed in TDD mode. The four content-contract tests failed
before the skill changes and passed afterward; the complete pytest
suite is green (20 tests). Done-when was verified by the D1 ladder,
quick/full routing references, boundary assertions, and README
attribution. Ruff was not available locally; M15 does not require it.

## M16: Lock the integration contract with content tests ✅

**Why:** The value of the integration is the boundary between
"smallest correct implementation" and indiscriminate deletion. Without
mechanical checks, later edits could drop a prefix, bypass D1 routing,
or accidentally turn Ponytail into a second review system.

**Approach:** Extend the focused content-contract test introduced in
M15. It verifies that the five prefixes have one canonical
definition, D1 remains mandatory in `quick` and always-deep in the
registry, the safety/test exclusions remain present, README attribution
is retained, and no new `ponytail-review` or `ponytail-audit` skill
frontmatter is introduced. Add a milestone-bridge regression proving a
D1 title such as `delete: unused adapter` survives
`_findings_to_milestones.py` unchanged, preserving the hand-off to
devplan without creating a runtime dependency between the repositories.

**Tasks:**
- [x] Extend `tests/test_essentiality_contract.py` with registry and no-duplicate-skill assertions
- [x] Extend `tests/test_scripts.py` with a D1 prefixed-title round-trip through `_findings_to_milestones.py`
- [x] Keep the taxonomy single-sourced in D1 and reference it from cuts/templates rather than duplicating its definitions
- [x] Update `README.md` with the integration boundary: concepts imported, plugin not required
- [x] Test: run ruff and the complete pytest suite
- [x] Commit & push

**Done when:** CI fails if D1 loses a prefix, its mandatory routing, its
safety boundaries, its attribution, or the devplan round-trip; the
repository still exposes only the `tech-audit` skill.

**Notes:** Executed in TDD mode. The expanded suite was red on the
missing explicit README integration boundary, then green after the
documentation change. Verification: 24 pytest tests pass, `uvx ruff
check code-audit/scripts/ tests/` passes, the prefixed D1 title
round-trips unchanged, and the contract rejects duplicate Ponytail
skill frontmatter.

---

## Follow-up — Comment essentiality, ponytail: scan, debt cross-reference

Complete the Ponytail integration with the three remaining concepts
identified in the 2026-06-20 gap analysis: flagging comments that don't
carry their weight, recognizing `ponytail:` structured comments during
audit, and cross-referencing the debt-tracking file populated by devplan.

Recommended order: M17 → M18 → M19.

### M17: Comment essentiality — flag dead-weight comments in D01

**Why:** D01 already hunts dead code, unearned abstractions, and
duplication. But a comment that restates the code verbatim is debt too:
it occupies cognitive space, must be maintained, and lies when the code
changes. D01 must recognize comments that don't carry their weight and
flag them with the same `shrink:` prefix used for verbose code.

**Approach:** Add a **Comment-weight scan** method to
`code-audit/dimensions/D01-code-essentiality.md`:

```
### Comment-weight scan

grep -rn '^[[:space:]]*//\|^[[:space:]]*#\|^[[:space:]]*/\*\*' \
  --include="*.{py,ts,js,php,go,rs}" | head -50

For each comment block:
- Does it say *why* (intent, trade-off) or just *what* (restates the
  code)? If "what" and the code is already clear → 🟢 shrink:.
- Is the docstring longer than the function signature it decorates and
  adds no information beyond the parameter names? → 🟢 shrink:.
- Does it explain a non-obvious behavior, a gotcha, or a deliberate
  trade-off? → keep (these are the comments that earn their place).
- Is it a ponytail: structured comment? → skip (handled by M18).

The method never flags public-API documentation (the contract layer),
only inline and docstring comments that restate the implementation.
```

**Tasks:**
- [x] Add the Comment-weight scan method to `code-audit/dimensions/D01-code-essentiality.md`
- [x] Extend `tests/test_essentiality_contract.py` to assert the comment-weight method exists in D01
- [x] Run the full pytest suite; crossref linter green
- [x] Commit & push

**Done when:** a D01 pass on a codebase with verbose comments emits
`shrink:` findings for comments that restate the code, and CI verifies
the method is present.

### M18: `ponytail:` recognition — audit-aware intentional shortcuts

**Why:** Today D01 doesn't know `ponytail:` comments exist. If it finds
an O(n) linear scan, it flags it as a potential problem — even when the
adjacent `ponytail:` comment documents it as intentional with a known
ceiling. D01 must become smarter: parse the comment, compare against the
ceiling, and act accordingly. This closes the loop between devplan's
simplification step (M22) and the audit: intentional shortcuts are no
longer false positives.

**Approach:** Add a **ponytail: scan** method to D01:

```
### ponytail: scan

grep -rn 'ponytail:' --include="*.{py,ts,js,php,go,rs}"

For each hit, parse: the simplification description, ceiling value with
unit, and upgrade path. Then:
- Ceiling exceeded given current state (e.g. ">10k records" but the
  table has 50k) → 🔴 with note: "intentional shortcut outgrew its
  ceiling on <date>. Upgrade: <path>."
- Ceiling not yet reached → suppress any related essentiality finding
  for this code (the O(n) scan is intentional and within limits).
  Record the suppression with the ponytail: location as justification.
- Ceiling not measurable automatically (e.g. "when latency >100ms")
  → 🟡 with note: "verify the ponytail: ceiling manually."
```

**Tasks:**
- [x] Add the ponytail: scan method to `code-audit/dimensions/D01-code-essentiality.md`
- [x] Extend `tests/test_essentiality_contract.py` to assert the scan method exists and documents ceiling-gating
- [x] Full pytest suite + crossref linter green
- [x] Commit & push

**Done when:** a D01 pass finds ponytail: comments and either suppresses
related findings (ceiling not reached) or promotes them to 🔴 (ceiling
exceeded), and CI verifies the method contract.

### M19: Debt tracking cross-reference — `.code-audit/debt.tsv` in the audit loop

**Why:** The `.code-audit/debt.tsv` file populated by devplan (M23) is
useless if the audit doesn't read it. D01 must cross-reference its
findings against the debt register: suppress those covered by active
debt, reactivate those whose revisit date has passed. This is the
mechanical bridge between the two skills — design-time decisions feed
audit-time verification without manual hand-off.

**Approach:** Add a **Debt-register cross-reference** step at the start
of D01's method execution, before findings are emitted:

```
### Debt-register cross-reference

Before emitting findings, load `.code-audit/debt.tsv` if it exists.
For each D01 finding:
- If a debt row matches (same file + same topic) AND revisit_by is in
  the future OR absent → suppress the finding, increment a suppressed
  counter. Record the matching debt row as the suppression reason.
- If a debt row matches AND revisit_by is in the past → promote the
  finding to 🔴 with note: "intentional debt expired on <date>.
  Upgrade: <path>."
```

In the D01 dimension summary: `suppressed: N findings covered by active
debt (see .code-audit/debt.tsv)`. The suppressed count lets the
reviewer see how much intentional debt is currently active versus how
many real findings need attention.

**Tasks:**
- [x] Add the Debt-register cross-reference step to `code-audit/dimensions/D01-code-essentiality.md`
- [x] Extend `tests/test_essentiality_contract.py` to assert the cross-reference step exists and handles both active and expired debt
- [x] Full pytest suite + crossref linter green
- [x] Install + `--check` OK
- [x] Commit & push

**Done when:** a D01 pass on a repo with `.code-audit/debt.tsv`
suppresses findings covered by active debt, reactivates expired debt
as 🔴, and reports the suppressed count; CI verifies the contract.
