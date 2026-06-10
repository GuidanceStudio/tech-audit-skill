# Per-project extensions

Drop project-specific audit material in `.code-audit/extras/` at the repo root. The skill loads every `*.md` file from that directory AFTER the default 13 dimensions.

## When to use

- Add a 14th dimension specific to your product (e.g. "voice quality" for a telephony product).
- Add a stack-specific gotcha file for a stack the default `languages/` doesn't cover.
- Override or extend a default dimension with project-specific findings or methods.
- Document recurring custom findings that the team has agreed to track.

## Layout

```
your-repo/
├── .code-audit/
│   ├── extras/
│   │   ├── D14-voice-quality.md         # additional dim
│   │   ├── language-elixir.md           # stack the skill doesn't ship
│   │   ├── D04-extra-our-jwt-scheme.md  # extension of D04 with company-specific JWT format
│   │   └── recurring-findings.md        # team-agreed list of "this keeps surfacing"
│   └── (other project conventions)
├── src/
├── tests/
└── ...
```

## File conventions

Each extra file should have:

1. **Heading** matching the framework style (`# D14 — <Title>` or `# Threat model — <name>` or similar).
2. **Question** statement.
3. **Method** with concrete shell snippets / code patterns.
4. **PoC bar** and **Production bar**.
5. **Cross-references** to default dims / threat-models that connect.

This mirrors the default `dimensions/D<N>-*.md` shape so the audit report flows uniformly.

## Severity + status scheme

Custom dims use the same 🔴/🟡/🟢 + ✅/⚠️/❌ schemes as the default ones. Don't invent new severity levels.

## Naming numerals

For additional dimensions beyond D13:

- Numeric: `D14`, `D15`, ... — continues the framework's sequence.
- Or thematic with a prefix: `T01-tone-of-voice`, `K01-domain-knowledge-rot`, ... — useful when extras don't fit the "what to check" mental model.

Either works. The audit report's status table lists them after the default 13.

## When to upstream

If an extension you've written would be useful to other projects (not specific to your product), consider:

- Opening an issue / PR against `github:GuidanceStudio/code-repository-audit-skill` proposing it as a default dimension or threat-model.
- Or sharing as a community extension repo for others to copy.

## Example — additional dimension

```markdown
# D14 — Voice quality 🎙️

**Question**: "Are voice prompts intelligible, locale-appropriate, latency-acceptable?"

Project-specific to telephony products. Default 13 dims don't cover this.

## Method

### Latency budget
- TTS round-trip < 800ms p95.
- STT recognition latency < 300ms.

### Locale accuracy
- Speech samples in target locale must pass human review.
- Number / date / address pronunciation tested via fixture corpus.

[... etc ...]

## Cross-references
- D10 (Performance baseline) — overlaps on latency.
- D3 (Tests as adversaries) — the locale corpus pattern matches PII corpus from threat-models/pii-data-flow.md.
```
