# mypy

**What it catches**: Python type errors. Strict mode forces explicit types; catches contract violations the test suite would only find at runtime.

## Install

```sh
pip install mypy
```

## Config

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
warn_unused_configs = true

# Per-module override (e.g. third-party lib without stubs)
[[tool.mypy.overrides]]
module = "untyped_lib.*"
ignore_missing_imports = true
```

## Usage

```sh
# First run — generate baseline of existing errors
mypy --strict app/ > /tmp/mypy-baseline.txt

# CI mode
mypy --strict app/
```

## CI snippet

```yaml
- name: mypy
  run: mypy --strict app/
```

## Strict mode gotchas

When migrating an existing codebase to `--strict`:

1. Run once, count errors per module.
2. Pick the smallest module — fix to clean.
3. Add the cleanest modules to `[tool.mypy]` files list incrementally.
4. Use `# type: ignore[error-code]` for cases that genuinely can't be typed (with an issue link).

## Cross-references

- `languages/python-fastapi.md`.
- `dimensions/D01-code-essentiality.md` — type density as essentiality signal.
