# Ruff

**What it catches**: Python lint + format + Bandit security ruleset, all in one fast Rust binary. 10-100× faster than the alternatives it replaces.

## Install

```sh
pip install ruff
# OR uv
uv tool install ruff
```

## Config

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = [
  "E",   # pycodestyle errors
  "F",   # pyflakes (unused imports, undefined names)
  "I",   # isort
  "B",   # flake8-bugbear (likely bugs)
  "S",   # flake8-bandit (security)
  "UP",  # pyupgrade
]
ignore = [
  "S101",  # use of assert (fine in tests)
]
```

## Usage

```sh
# Lint
ruff check .

# Lint + auto-fix
ruff check --fix .

# Format (replaces black)
ruff format .

# CI mode
ruff check --output-format=github .
```

## What S codes catch

| Code | Catches |
|---|---|
| S101 | `assert` (disable in tests) |
| S102 | `exec()` |
| S301 | pickle deserialization |
| S307 | `eval()` |
| S506 | yaml.load (unsafe) |
| S602 | shell=True in subprocess |
| S605 | shell injection via os.system |

Replaces Bandit at much higher speed. Equivalent coverage for the common security gotchas.

## CI snippet

```yaml
- name: Ruff
  run: |
    ruff check --output-format=github .
    ruff format --check .
```

## Cross-references

- `languages/python-fastapi.md`.
- `dimensions/D04-security-posture.md`.
