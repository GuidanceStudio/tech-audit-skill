# jscpd

**What it catches**: cross-language clone detection. Surfaces the LLM-pasted dead-code clusters that accrete in AI-assisted projects (see `threat-models/llm-assisted-code.md`).

## Install

```sh
npm install -g jscpd
# OR per-project
npm install --save-dev jscpd
```

## Usage

```sh
# Cross-language scan with sensible defaults
npx jscpd . --min-tokens 50 --reporters consoleFull

# JSON output for triage
npx jscpd . --reporters json --output ./jscpd-report
```

## Config

```json
// .jscpd.json
{
  "threshold": 5,
  "minTokens": 50,
  "minLines": 5,
  "ignore": [
    "**/node_modules/**",
    "**/vendor/**",
    "**/tests/**/fixtures/**",
    "**/migrations/**"
  ],
  "reporters": ["consoleFull", "json"]
}
```

## CI snippet

```yaml
- name: jscpd clone detection
  run: npx jscpd . --threshold 5 --reporters consoleFull
```

The `--threshold 5` flag fails the build if duplication exceeds 5% of the codebase.

## Reading the output

Duplicate block "$X tokens repeated Y times" — three thresholds:

| Tokens × repetitions | Severity |
|---|---|
| <50 × 2 | 🟢 noise |
| 50-200 × 2-3 | 🟡 candidate for extraction |
| >200 OR >3 repetitions | 🔴 likely LLM-paste — extract |

## Alternative: PMD CPD

For PHP / Java repos where you'd rather not bring in npm:

```sh
brew install pmd
pmd cpd --minimum-tokens 50 --files . --language php
```

Same idea, JVM tool.

## Cross-references

- `threat-models/llm-assisted-code.md`.
- `dimensions/D01-code-essentiality.md`.
