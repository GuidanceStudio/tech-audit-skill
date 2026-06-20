# Stack detection

Quick algorithm to figure out which `languages/*.md` files to load.

## Algorithm

Scan the repo **recursively** for markers (depth ≤3, pruning
dependency/build dirs: `vendor/`, `node_modules/`, `.git/`,
`storage/`, `dist/`, `build/`, virtualenvs) — nested layouts
(monorepos with services in subdirectories) are the norm, not the
exception:

| Marker file/glob | Load |
|---|---|
| `composer.json` | `languages/php-laravel.md` |
| `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile` | `languages/python-fastapi.md` |
| `package.json` | `languages/typescript-node.md` |
| `*.sh` files | `languages/shell.md` |
| `Dockerfile`, `docker-compose.yml`, `compose.yml` | `languages/docker.md` |

Multiple matches → load multiple files. Polyglot is the norm.

## Helper script

`scripts/_detect_stack.py` emits a space-separated list of stack
tags:

```sh
$ python3 scripts/_detect_stack.py /path/to/repo
php python typescript shell docker
```

Use this when you need precise inputs to later steps (e.g. when
deciding which Semgrep rule packs to apply).

## Sub-detection (within a stack)

After identifying the stack, look for sub-framework signals to
sharpen the language file's relevance:

| Stack | Sub-marker | Profile |
|---|---|---|
| PHP | `artisan` / `Illuminate\\` in composer.json | Laravel — full attention to `languages/php-laravel.md`. |
| PHP | `bin/symfony` / `symfony/framework-bundle` | Symfony — load `php-laravel.md` (overlapping concerns), flag differences inline. |
| Python | `fastapi` in deps | FastAPI — full attention. |
| Python | `django` in deps | Django — load `python-fastapi.md`, note ORM differences. |
| Python | `flask` in deps | Flask — minimal subset of `python-fastapi.md`. |
| TS/JS | `next.config.*` | Next.js — additional SSR concerns. |
| TS/JS | `vite.config.*` | Vite-driven SPA. |
| TS/JS | nothing | Plain Node service. |

For a framework the skill ships no `languages/*.md` for (Symfony,
Django, Flask, Rails, Go, Rust, …): run the generic dimension methods,
state in the report that no stack file exists for it, and point the
user to `.tech-audit/extras/language-<name>.md` to add one. Don't load
a sibling framework's file and "note the differences" — that smuggles
in wrong-stack assumptions.

## UI-surface sub-marker (cross-cutting)

Flag the product as having a UI surface — which makes **D15 (UX)** and
**D16 (UI)** default-deep (`ui-deep` tag) — when any of these are
present:

- a frontend framework dep (`react`, `vue`, `svelte`, `@angular/*`,
  `solid-js`, `next`, `nuxt`, `astro`) in `package.json`
- view templates: `.tsx` / `.jsx` / `.vue` / `.svelte` / `.blade.php`
  / `.erb` / `.razor`
- a styling system: Tailwind config, CSS-in-JS, a `design-tokens` /
  `theme` file, or a component-library dep

No UI surface (pure API / CLI / library) → skip D15 + D16 and note "no
UI surface" in the report.

## Agentic-product sub-marker (cross-cutting)

Independent of language, flag the product as embedding an AI runtime
when any of these are present — it makes `threat-models/ai-runtime.md`
a default load for D4:

- MCP config (`mcp.json`, `*mcp*` server/client config)
- agent SDK deps (`@anthropic-ai/*`, `openai`, `litellm`,
  `langchain`, agent frameworks)
- a model client pointed at OpenRouter / Anthropic / OpenAI
- a chat-bridge service or a model-callable tool/function registry

## When no markers exist

If detection returns empty (rare — usually the repo is at least one
of the five), ask the user: "I couldn't detect the stack from
common markers. What language(s) and frameworks are in use?"
