# Biome

**What it catches**: TypeScript / JavaScript lint + format in one fast Rust binary. Replaces ESLint + Prettier with ~100× speed. Reasonable defaults.

## Install

```sh
npm install --save-dev --save-exact @biomejs/biome
```

## Config

```json
// biome.json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "suspicious": {
        "noExplicitAny": "error",
        "noFloatingPromises": "error"
      },
      "style": {
        "useImportType": "warn"
      }
    }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  }
}
```

## Usage

```sh
# Check (lint + format)
npx biome check .

# Apply fixes
npx biome check --apply .

# Format only
npx biome format --write .
```

## CI snippet

```yaml
- name: Biome
  run: npx biome ci .
```

## What `noFloatingPromises` catches

Promises that aren't awaited or explicitly fire-and-forgotten:

```ts
async function bad() {
  doSomethingAsync();          // ← rule fires
}
async function good() {
  await doSomethingAsync();
}
async function explicit() {
  void doSomethingAsync();     // ← OK, marked as intentional
}
```

This is the single most-impactful TS rule for Node services. Unhandled rejections used to crash the process; `void` is the explicit "I know" marker.

## Cross-references

- `languages/typescript-node.md`.
- `dimensions/D04-security-posture.md` (no-floating-promises overlap).
