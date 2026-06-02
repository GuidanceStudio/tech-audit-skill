# Stack detection

Quick algorithm to figure out which `languages/*.md` files to load.

## Algorithm

Scan the repo root + first level for markers:

| Marker file/glob | Load |
|---|---|
| `composer.json` | `languages/php-laravel.md` |
| `pyproject.toml`, `requirements.txt`, `setup.py`, `Pipfile` | `languages/python-fastapi.md` |
| `package.json` | `languages/typescript-node.md` |
| `*.sh` files in the repo root | `languages/shell.md` |
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

## When no markers exist

If detection returns empty (rare — usually the repo is at least one
of the five), ask the user: "I couldn't detect the stack from
common markers. What language(s) and frameworks are in use?"
