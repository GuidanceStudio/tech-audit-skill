# D1 — Code essentiality ⚙️

**Question**: "Is the code the smallest, clearest version of itself that a future engineer can read in one sitting? Or has it grown abstract layers, dead branches, and parallel implementations of the same idea?"

Always-deep. The most decay-prone dimension between audits. LLM-assisted code amplifies both sides — clean snippets *and* over-engineered boilerplate.

**North star**: would removing this make the code *worse* or just *shorter*? If "shorter", it's a 🟡.

## Essentiality ladder

Run these checks in order and stop at the first replacement that fully
preserves the required behavior:

1. **`delete:`** the requirement, branch, flag, wrapper, or dead
   flexibility is not needed; nothing replaces it.
2. **`stdlib:`** the language standard library already provides the
   behavior; name the exact function or module.
3. **`native:`** the browser, runtime, framework, database, or operating
   platform already provides the behavior; name the exact feature.
4. **`yagni:`** an abstraction is speculative or has only one real use;
   inline it until a second implementation or caller exists.
5. **`shrink:`** custom code is still necessary but the same contract
   can be expressed with fewer files, branches, dependencies, or lines;
   describe the smaller form.

Use the matching prefix at the start of the finding title. The ladder
chooses the smallest **correct** implementation, not the smallest diff
at any cost.

### Non-negotiable boundaries

Essentiality findings must not weaken correctness, required tests,
trust-boundary validation, security controls, accessibility, error
handling that prevents data-loss, or an explicit requirement. When a
shorter implementation conflicts with one of these constraints, the
constraint wins and the finding is dropped. Route defects in those
areas to D14, D3, D4, or D15 instead of presenting deletion as the fix.

## Method

### Big-file scan

```sh
git ls-files | xargs wc -l 2>/dev/null | sort -rn | head -20
```

- Files >800 LOC without a documented "why" in the file's docstring → 🟡.
- Files >1500 LOC → 🔴 unless it's a generated artifact, a config-as-code file, or a single-file library.

### Linter presence + enforcement

| Stack | Expected config file | If missing |
|---|---|---|
| PHP | `phpstan.neon`, `pint.json`, `.php-cs-fixer.php` | 🟡 |
| Python | `pyproject.toml` with `[tool.ruff]` or `[tool.mypy]` | 🟡 |
| TypeScript | `biome.json` or `.eslintrc*` + `tsconfig.json --strict` | 🟡 |
| Shell | `.shellcheckrc` or shellcheck in CI | 🟡 |
| Any | `.editorconfig` | 🟢 |

A linter that exists but is never enforced (no CI step, no pre-commit) is **worse** than no linter — flag as 🟡 with the suggested fix being "wire it in `D8`".

### TODO density

```sh
grep -rIn "TODO\|FIXME\|XXX\|HACK" --include="*.{php,py,sh,ts,js,go,rs}" | wc -l
```

>20 untracked TODOs → 🟡. TODOs that link to an issue tracker or devplan milestone don't count.

### Dead-tree scan

For every class / module that *should* have callers:

```sh
# PHP
for cls in $(grep -rh "^class " app/ | awk '{print $2}'); do
  refs=$(grep -rlw "$cls" . --include="*.php" | grep -v "/$(echo $cls | tr A-Z a-z).php" | wc -l)
  [ "$refs" = "0" ] && echo "DEAD: $cls"
done

# Python
ruff check --select F401,F841 .   # unused imports + unused vars
vulture . --min-confidence 80     # broader dead code

# TypeScript
ts-prune
```

Cross-check before deleting: Laravel auto-discovers via `EventServiceProvider`, route binding, Filament `discover*()`. FastAPI auto-imports modules via `__init__`. TS may export via `index.ts` re-exports.

Confirmed dead class with no caller and no auto-discovery → 🔴 (it's lying weight).

### Over-abstraction scan

```sh
# PHP single-impl interfaces
grep -rnE 'interface .*(Repository|Service|Manager|Factory)\b' app/

# Deep namespacing
find app/ -mindepth 5 -type f -name '*.php'

# Python factories with one product
grep -rn "def create_" --include="*.py" | head
```

Each hit: "is this earned?" — single concrete impl behind an interface with no test seam is the canonical LLM-generated-bloat smell. Flag 🟡 with the suggested fix being "inline the interface, the test seam can use a regular mock".

### Clone density (LLM-assisted-code addendum)

Codebases with 30-70% AI-assisted code show ~4× duplicate-block density vs human-only. See `threat-models/llm-assisted-code.md`.

```sh
npx jscpd . --min-tokens 50 --reporters consoleFull
# or
pmd cpd --minimum-tokens 50 --files . --language $LANG
```

Duplicated block >50 contiguous tokens → 🟡. >200 tokens or repeated >3× → 🔴.

### Directory hygiene

```sh
# Dirs with ≤1 file
find . -type d -not -path '*/node_modules/*' -not -path '*/.git/*' \
  | while read d; do
      n=$(find "$d" -maxdepth 1 -type f | wc -l)
      [ "$n" -le 1 ] && echo "$n  $d"
    done | sort
```

Twin "Concerns" / "Helpers" / "Utils" dirs that could merge → 🟡.

### Orphan migration check

Tables stay (D9 invariant), but tables whose model is gone need a `// deprecated: see X` comment in the migration. Each orphan without a note → 🟡.

### Recently-touched-surface heatmap

```sh
git log --since="3 months ago" --pretty=format: --name-only | sort | uniq -c | sort -rn | head -30
```

Files at the top are where drift is likeliest — bias the deep review here.

### Debt-register cross-reference

Before emitting findings, load `.tech-audit/debt.tsv` if it exists in
the target repo. For each D01 finding:

- If a debt row matches (same file + same topic) AND `revisit_by` is in
  the future or absent → suppress the finding, increment a suppressed
  counter. Record the matching debt row as the suppression reason.
- If a debt row matches AND `revisit_by` is in the past → promote the
  finding to 🔴 with the note: "intentional debt expired on <date>.
  Upgrade: <path>."

In the D01 dimension summary, include `suppressed: N findings covered
by active debt (see .tech-audit/debt.tsv)`.

### Comment-weight scan

```sh
grep -rn '^[[:space:]]*//\|^[[:space:]]*#\|^[[:space:]]*/\*\*' \
  --include="*.{py,ts,js,php,go,rs}" | head -50
```

For each comment block found in the sample:

- Does it say **why** (intent, trade-off) or just **what** (restates the
  code)? If "what" and the code is already clear → 🟢 `shrink:`.
- Is the docstring longer than the function signature it decorates and
  adds no information beyond the parameter names? → 🟢 `shrink:`.
- Does it explain a non-obvious behavior, a gotcha, or a deliberate
  trade-off? → keep (these are the comments that earn their place).
- Is it a `ponytail:` structured comment? → skip (handled by the
  ponytail: scan below).

This method never flags public-API documentation (the contract layer),
only inline and docstring comments that restate the implementation.

### ponytail: scan

```sh
grep -rn 'ponytail:' --include="*.{py,ts,js,php,go,rs}"
```

For each hit, parse the simplification description, ceiling value with
unit, and upgrade path. Then:

- **Ceiling exceeded** given current state (e.g. ">10k records" but the
  table has 50k) → 🔴 with note: "intentional shortcut outgrew its
  ceiling. Upgrade: <path>."
- **Ceiling not yet reached** → suppress any related essentiality
  finding for this code (the simplification is intentional and within
  limits). Record the suppression with the ponytail: location as
  justification.
- **Ceiling not measurable automatically** (e.g. "when latency >100ms")
  → 🟡 with note: "verify the ponytail: ceiling manually."

When a ponytail: comment suppresses a finding, the finding is excluded
from the report and counted separately from debt-register suppressions.

## PoC bar

- Linter configured + enforced (CI step) on every language present.
- Files >800 LOC justified inline.
- <20 untracked TODOs total.
- Zero dead classes.
- Repository / Manager / Factory abstractions absent unless ≥2 concrete implementations OR a test seam.

## Production bar

- Lint + format enforced in CI.
- Dead-code CI step (`phpstan-deprecation`, `composer unused`, `ts-prune`, `vulture`) blocks PRs introducing orphan classes.
- Cyclomatic complexity budget per function.
- Clone density target: <2% duplication.

## Cross-references

- `threat-models/llm-assisted-code.md` for the clone-density + single-impl-interface anti-pattern detail.
- `tools/jscpd.md` for clone detection setup.
- `languages/<stack>.md` for stack-specific dead-code patterns.
