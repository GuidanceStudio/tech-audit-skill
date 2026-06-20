# TypeScript / Node — language-specific checks

Patterns beyond the universal D1-D13 methods.

## Type safety (D1, D4)

- `any` escape hatches around boundary payloads (webhooks, message handlers) → 🟡. Use `unknown` + narrow with type guards.
- `as` casts without runtime validation → 🟡. Pair with `zod` / `valibot` / `io-ts` validators.
- `tsconfig.json --strict` MUST be on. `--strict: false` → 🔴.
- `// @ts-ignore` / `// @ts-expect-error` without a comment → 🟡.

## Promise discipline (D4, D12)

- Unhandled promise rejection in event handlers → 🔴 (Node may crash; in `node --unhandled-rejections=strict` mode, the process exits).
- `no-floating-promises` ESLint / Biome rule must be on. `void promise()` is the explicit "I know I'm fire-and-forgetting" marker.
- `Promise.all([...])` for independent calls, `Promise.allSettled([...])` if one failure shouldn't abort the others.

## Secrets in logs (D4)

```sh
grep -rnE "console\.log.*token|logger\..*token|console\.log.*secret|console\.log.*key" --include="*.ts" --include="*.js"
```

Discord / Slack / OAuth tokens in logs → 🔴. Use a structured logger with field redaction (`pino` `redact`, `winston` `format.errors`).

## ReDoS via user-supplied regex (D4)

Same risk as Python — user-controlled patterns can cause catastrophic backtracking. Use `re2` (`re2-wasm`) for untrusted input, or constrain inputs.

## Express / Fastify gotchas (D4)

- Body parser size limit not set → DoS vector. Express defaults to 100KB; Fastify defaults to 1MB. Set explicitly.
- `app.use(cors())` with no options → permissive. See D4 + Python CORS notes (same issue).
- Trust-proxy misconfiguration — `X-Forwarded-For` from untrusted source rewriting `req.ip`. Set `app.set('trust proxy', NUM)` precisely.

## Discord / Slack adapter gotchas (when present)

For bridge / chat-bot projects:
- Bot token in env (not in code, not in logs) — D4.
- Allowlist of users / channels — D5 for multi-tenant.
- Idempotency on message handlers (re-delivery is normal in Discord / Slack) — D9.
- Backpressure on streaming responses (drain timeout, max queued chunks).

## Stack-specific dead-code patterns (D1)

```sh
ts-prune                 # unused exports
biome check --apply      # auto-fixable findings
knip                     # broader dead-code + dep
```

## Stack-specific anti-patterns (LLM-generated)

When 30-70% of code is AI-assisted, expect:
- `interface I<EntityName>` + a single concrete `<EntityName>Impl`.
- DTOs duplicating zod schemas duplicating type aliases (3 representations of the same thing).
- `Promise<Result<T, E>>` types when plain `Promise<T> | throw` would do.
- `enum`s used as object lookups (TS-enum semantics surprise consumers; prefer `as const` objects).

## Tools to run

- **Biome** (replaces ESLint + Prettier in one fast binary).
- **`tsc --noEmit --strict`** in CI.
- **`ts-prune`** for dead-export detection.
- **`npm audit --json`** for dep CVE.

## Cross-references

- `tools/biome.md`.
- `threat-models/secret-management.md` — bot-token discipline.
