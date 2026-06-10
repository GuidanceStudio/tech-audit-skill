# code-repository-audit-skill

A Claude skill for **honest, actionable software audits**. The skill
installs as **`code-audit`** (renamed from `code-review` in v0.2:
Claude Code now ships a builtin `code-review` skill for PR diff
review, and the two names collided — this skill's distinctive value is
the audit/tech-DD framework, so it took the audit name). Routes by intent (quick PR review, security pass, pre-release check, deep dimension, or full tech-DD) across a 13-dimension framework.

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
- OWASP Top 10, OWASP ASVS L1
- A generalized **13-dimension tech-DD framework** forged on a multi-stack production codebase

…and adds dimensions and patterns that AI-assisted-code workflows specifically need: setup replicability, LLM-clone density, regression-after-fix discipline, async-pool tenant-context leaks.

## Install

### Local (clone + install)

```sh
git clone git@github.com:GuidanceStudio/code-repository-audit-skill.git
cd code-repository-audit-skill
./install.sh
```

### Remote (one-liner)

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/GuidanceStudio/code-repository-audit-skill/main/install.sh)
```

The installer copies `code-audit/` to `~/.claude/skills/code-audit/`. Pass `--force` to overwrite an existing installation.

## Use

Invoke the skill however your assistant invokes skills, then describe
what you want:

| Assistant | How to invoke |
|---|---|
| Claude Code | `/code-audit`, or just ask ("audit my codebase") |
| Codex CLI | `/code-audit` (same SKILL.md standard), or ask |
| opencode | `/code-audit`, or ask |
| Gemini CLI | `/code-audit` (installed as a TOML command) |
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

**Quick PR review**:

```
You: /code-audit on https://github.com/our-org/our-repo/pull/143

Claude: [scans the diff, picks dims based on what was touched, emits a
quick-scan output with severity-tagged findings + ship/hold verdict]
```

**Security pass on a service**:

```
You: security review on the gateway/ folder

Claude: [runs D4, D5, D7-security-subset; loads matching threat-models;
emits a security-pass output with top risk + ranked findings + tool output
summary + ship/hold recommendation]
```

**Full audit, quarterly**:

```
You: full audit of this repo, write the report

Claude: [walks all 13 dimensions per cuts/full.md; writes
docs/internal/tech-audit-2026-06-15.md with executive summary, status
overview, per-dim findings, and proposed follow-up milestones]
```

## The 13 dimensions

| # | Title | Tag |
|---|---|---|
| D1 | Code essentiality | always-deep |
| D2 | Docs integrity | always-deep |
| D3 | Tests as adversaries | always-deep |
| D4 | Security posture | ⚠️ default-deep |
| D5 | Multi-tenant isolation | ⚠️ default-deep |
| D6 | Operational readiness | scan |
| D7 | Dependency hygiene | scan |
| D8 | Build / CI / dev-loop | ⚠️ default-deep |
| D9 | Data model integrity | scan |
| D10 | Performance & cost baseline | release-only deep |
| D11 | Legal / compliance | scan |
| D12 | Admin surface consistency | scan |
| D13 | Setup replicability | always-deep |

D1, D2, D3, D13 are **always-deep** — they decay invisibly between audits. Nobody notices code rot, doc drift, test homogeneity, or replicability regression until someone tries to clone fresh and the build fails for reasons that weren't in the README.

D4, D5, D8 carry the ⚠️ default-deep mark because they're the high-blast-radius dimensions for B2B SaaS — auth, multi-tenant, CI.

## Cadence (what to run when)

| Tier | Cuts | When |
|---|---|---|
| Per-push CI | (automated tools only) | Every PR + push to main |
| Per-release-tag | `release` cut | Before tagging `v0.x.y` (~30 min human) |
| Quarterly | `full` cut + restore-from-backup drill | Every 3 months (~5-7 h) |
| Triggered | `deep`, `security` cuts | New integration; post-incident; pre-VC |

See [`code-audit/playbooks/operations.md`](code-audit/playbooks/operations.md) for the full cadence + 5-week starter pack + anti-patterns to avoid + things-that-bite-if-skipped.

## Severity scheme

| Mark | Meaning | Example |
|---|---|---|
| 🔴 | **Ship-blocker** — fix before next audit pass | Secret in git history; cross-tenant data leak; SQLi in admin panel |
| 🟡 | **Fix soon** — defensible to leave; real auditor will note | Healthcheck missing; dep 6mo behind; doc claim mismatches code |
| 🟢 | **Nice-to-have** — acceptable, document, move on | TODO in dev tooling; non-pinned base image tag |

## Per-project extensions

Drop `.code-audit/extras/*.md` files in your repo to add project-specific dimensions, threat models, or stack files. The skill loads them after the defaults. See [`code-audit/extensions/README.md`](code-audit/extensions/README.md) for the schema.

## Repository layout

```
code-repository-audit-skill/
├── install.sh                       # multi-assistant installer
├── README.md                        # this file
├── LICENSE                          # Apache-2.0
├── docs/examples/                   # worked example reports (not shipped)
└── code-audit/                      # the flat, assistant-neutral skill payload
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

`code-audit/` is the whole skill — copy it anywhere your assistant
reads skills, or use `install.sh` (next section).

Each file has one clear purpose. Files cross-reference rather than duplicate — updating a fact happens in one place. The skill itself follows the rules it audits (D1 + D2).

## Design principles

1. **Lazy load** — the spine (`SKILL.md`) is ~250 lines; sub-files are loaded only when their cut / dimension / language matches. A `quick` cut on a TypeScript PR loads ~5-7 files, not all 40+.
2. **Generalist core, stack-aware extensions** — dimensions are stack-agnostic; `languages/` carry stack-specific gotchas.
3. **Provenance tracked** — each concept notes its source (Anthropic skill, OWASP, internal framework). Future updates traceable.
4. **No bloat** — every file earns its place. Files >300 lines are split. The skill eats its own dogfood on D1.
5. **Severity discipline** — 🔴 / 🟡 / 🟢 calibrated to "what would a real auditor say at a VC pitch?". No alarmism, no padding.
6. **Output template-driven** — every cut has a matching template. Reports are consistent across audits + comparable over time.

## Anti-patterns this skill explicitly rejects

- **SOC2 readiness program at PoC stage.** Wait for first enterprise prospect.
- **PR review with 2+ approvers for 1-3 engineers.** Strong CI is the reviewer.
- **100% line-coverage targets.** Branch coverage on tenancy + billing only.
- **External pen-test before product-market fit.** €5-15k for findings CI would catch.
- **Snyk / SonarCloud paid tier.** Trivy + Semgrep + native deps audits cover ~90% for €0.
- **STRIDE threat-model documents per feature.** Nobody reads them. A 5-line release-time "what changed in trust boundaries?" note works.

See [`code-audit/playbooks/operations.md`](code-audit/playbooks/operations.md) § Anti-patterns for the full list.

## Contributing

Open an issue or PR against [GuidanceStudio/code-repository-audit-skill](https://github.com/GuidanceStudio/code-repository-audit-skill).

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

Apache-2.0. See [LICENSE](LICENSE).

Built on the prior art of the projects listed in [Why this exists](#why-this-exists); each retains its own license. The skill's own framework + glue + dimensions are Apache-2.0.
