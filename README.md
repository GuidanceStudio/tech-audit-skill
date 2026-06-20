# tech-audit-skill

A skill for **honest, actionable software audits**. Installs as
**`tech-audit`**. Routes by intent (quick PR review, security pass,
pre-release check, deep dimension, or full tech-DD) across a
13-dimension framework.

Built for fast-but-solid startups. Generalist core, stack-aware extensions for **PHP/Laravel, Python/FastAPI, TypeScript/Node, shell, and Docker**.

## Why this exists

Generic "review this code" prompts produce three failure modes:

- **Soft** — "looks good, here are 3 style nits" on a PR with a real auth bug.
- **Alarmist** — every finding is 🔴 CRITICAL, severity dilutes.
- **Generic** — output reads the same regardless of stack, repo, or product context.

This skill replaces all three with **methodical, severity-calibrated, context-aware** reviews. It absorbs the best of:

- [`anthropics/knowledge-work-plugins/engineering/skills/code-review`](https://github.com/anthropics/knowledge-work-plugins) (Apache-2.0)
- [`anthropics/claude-code-security-review`](https://github.com/anthropics/claude-code-security-review) (MIT)
- [`VoltAgent/awesome-claude-code-subagents`](https://github.com/VoltAgent/awesome-claude-code-subagents) (MIT)
- [`awesome-skills/code-review-skill`](https://github.com/awesome-skills/code-review-skill) (MIT)
- [`DietrichGebert/ponytail`](https://github.com/DietrichGebert/ponytail) (MIT), adapted as the D1 essentiality ladder
- OWASP Top 10, OWASP ASVS L1
- A generalized **13-dimension tech-DD framework** forged on a multi-stack production codebase

…and adds dimensions and patterns that AI-assisted-code workflows specifically need: setup replicability, LLM-clone density, regression-after-fix discipline, async-pool tenant-context leaks.

### Ponytail integration boundary

**Concepts imported:** the ordered D1 essentiality ladder and its
finding taxonomy. **Runtime dependency:** none; the Ponytail plugin is
not required. This project does not install its lifecycle hooks,
persistent modes, or duplicate review/audit skills. Code-audit remains
authoritative for routing, severity, safety boundaries, findings, and
forge-flow hand-off.

## Install

```sh
git clone git@github.com:GuidanceStudio/tech-audit-skill.git
cd tech-audit-skill
./install.sh --target claude      # ~/.claude/skills/tech-audit/
./install.sh --target codex       # ~/.codex/skills/tech-audit/
./install.sh --target opencode    # ~/.config/opencode/skills/tech-audit/
./install.sh --target gemini      # ~/.gemini/commands/tech-audit.toml
./install.sh --target agents      # AGENTS.md pointer for Cursor/Windsurf/...
./install.sh --target all         # claude + codex + opencode
```

Remote one-liner:
```sh
bash <(curl -fsSL https://raw.githubusercontent.com/GuidanceStudio/tech-audit-skill/main/install.sh) --target claude
```

Flags: `--force` (overwrite), `--check` (report drift), `--agents-dir DIR`. Or skip the installer — `tech-audit/` is self-contained, copy it anywhere your tool reads skills.

## Use

Invoke the skill however your assistant invokes skills, then describe
what you want:

| Assistant | How to invoke |
|---|---|
| Claude Code | `/tech-audit`, or just ask ("audit my codebase") |
| Codex CLI | `/tech-audit` (same SKILL.md standard), or ask |
| opencode | `/tech-audit`, or ask |
| Gemini CLI | `/tech-audit` (installed as a TOML command) |
| Cursor / Windsurf / Copilot / Aider | reference the skill from `AGENTS.md`, then ask |

Typical phrasings: `"audit my codebase"`, `"security review"`,
`"is this ready to ship?"`, `"deep audit on D5"`.

The skill picks the right **cut** based on your phrasing, or asks if it's ambiguous:

| Cut | When | Output | Effort |
|---|---|---|---|
| **quick** | "review this file/PR" | Inline findings table on the diff | 5-10 min |
| **security** | "security review", "OWASP" | OWASP-flavoured pass, D4 + D5 + deps | 30 min |
| **release** | "ready to ship?" | Per-release-tag gate: scan all dims, deep on diff since previous tag | 30 min |
| **deep** | "deep audit on D5" | One or more dimensions, full method run | 1-2 h per dim |
| **full** | "full audit" | Whole 13-dim report, written to `docs/internal/tech-audit-YYYY-MM-DD.md` | 5-7 h |

### Example sessions

- **Quick PR:** `/tech-audit on ...pull/143` → scans the diff, emits severity-tagged findings + ship/hold verdict.
- **Security pass:** `security review on gateway/` → runs D4, D5, D7; outputs top risk + ranked findings + recommendation.
- **Full audit:** `full audit, write the report` → walks all dimensions, writes `docs/internal/tech-audit-YYYY-MM-DD.md` with executive summary, findings, and milestones.

## The 13 dimensions

The full D1–D16 registry with title + treatment tag lives in `tech-audit/SKILL.md` § Dimension registry — the single source of truth. D1, D2, D3, D13, D14 are always-deep (decay invisibly); D4, D5, D8 are default-deep (high blast radius for B2B SaaS); D15, D16 are ui-deep; the rest scan or release-only.

## Cadence

| Tier | When | Effort |
|---|---|---|
| Per-push CI | Every PR + push | 0 min (automated) |
| Per-release-tag | Before `v0.x.y` | ~30 min |
| Quarterly | Every 3 months | ~5-7 h |
| Triggered | New integration, post-incident, pre-VC | Variable |

See [`tech-audit/playbooks/operations.md`](tech-audit/playbooks/operations.md) for full cadence + starter pack + anti-patterns.

## Severity

🔴 = ship-blocker, 🟡 = fix soon, 🟢 = nice-to-have. Full 0-4 scheme in `SKILL.md` § Severity and status.

## Per-project extensions

Drop `.tech-audit/extras/*.md` files in your repo to add project-specific dimensions, threat models, or stack files. The skill loads them after the defaults. See [`tech-audit/extensions/README.md`](tech-audit/extensions/README.md) for the schema.

## Repository layout

```
tech-audit-skill/
├── install.sh                       # multi-assistant installer
├── README.md                        # this file
├── LICENSE                          # Apache-2.0
├── docs/examples/                   # worked example reports (not shipped)
└── tech-audit/                      # the flat, assistant-neutral skill payload
    ├── SKILL.md                     # routing spine (agentskills.io standard)
    ├── routing/detect-stack.md
    ├── cuts/{quick,security,release,deep,full}.md
    ├── dimensions/D*-*.md
    ├── languages/{php-laravel,python-fastapi,typescript-node,shell,docker}.md
    ├── threat-models/{multi-tenant-isolation,secret-management,
    │                  llm-assisted-code,pii-data-flow,auth-model,
    │                  ai-runtime,data-loss}.md
    ├── tools/{_matrix,gitleaks,trivy,semgrep,phpstan-larastan,
    │         ruff,mypy,biome,hadolint,jscpd,pgtap,auto-dep-updates}.md
    ├── templates/{full-audit-report,quick-scan-output,
    │             security-pass-output,triage-and-summary,
    │             finding-phrasing,ci-github-actions.yml,
    │             ci-pre-commit.yaml}
    ├── playbooks/{operations,false-positives}.md
    ├── extensions/README.md
    └── scripts/{_detect_stack,_bootstrap_tooling,
                _doctor_fresh_clone,_findings_to_milestones}.py
```

`tech-audit/` is the whole skill — copy it anywhere your assistant
reads skills, or use `install.sh` (next section).

Each file has one clear purpose. Files cross-reference rather than duplicate — updating a fact happens in one place. The skill itself follows the rules it audits (D1 + D2).

## Design principles

1. **Lazy load** — `SKILL.md` is ~250 lines; sub-files loaded only when their cut/dimension/language matches.
2. **Generalist core, stack-aware extensions** — dimensions stack-agnostic; `languages/` carry gotchas.
3. **Provenance tracked** — each concept notes its source. Future updates traceable.
4. **No bloat** — every file earns its place. Files >300 lines split. Dogfoods D1.
5. **Severity discipline** — 🔴/🟡/🟢 calibrated to "what would a real auditor say?". No alarmism, no padding.
6. **Output template-driven** — every cut has a matching template. Reports consistent + comparable.

## Anti-patterns this skill explicitly rejects

SOC2 readiness at PoC stage, PR review with 2+ approvers for 1-3 engineers, 100% line-coverage targets, external pen-test before product-market fit, Snyk/SonarCloud paid tier, STRIDE threat-model docs per feature. Full list: [`tech-audit/playbooks/operations.md`](tech-audit/playbooks/operations.md) § Anti-patterns.

## Contributing

Open an issue or PR against [GuidanceStudio/tech-audit-skill](https://github.com/GuidanceStudio/tech-audit-skill).

A finding that recurs across projects might warrant a default dimension or threat-model — propose it. A stack-specific gotcha that isn't in `languages/` — add it. Keep additions in the same style: short, concrete, cross-referenced.

## What this skill does NOT do

- It doesn't replace your test runner — it tells you what to test.
- It doesn't auto-fix — it produces findings + suggested milestones.
- It doesn't run paid SaaS (Snyk, FOSSA) — it points at OSS
  equivalents (Trivy, Semgrep) and explains why.
- It doesn't drive SOC2 / ISO27001 programs — it covers the ASVS-L1
  baseline that gets you to a real conversation.

## Worked examples

Two complete example reports live in [`docs/examples/`](docs/examples/)
(not shipped with the installed skill).

## Maintaining the skill

The skill follows the rules it audits: small modular files, each fact
in exactly one place (the dimension registry lives only in `SKILL.md`),
no dead content — `tests/test_crossrefs.py` enforces the last two
mechanically. Updating the skill should be a 5-minute edit, not a hunt
across near-duplicates.

## License

MIT. See [LICENSE](LICENSE).

Built on the prior art of the projects listed in [Why this exists](#why-this-exists); each retains its own license.
