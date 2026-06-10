# Hadolint

**What it catches**: Dockerfile lint — latest-tag base images, root USER, missing healthcheck, ineffective layer caching, apt-get without `--no-install-recommends`.

## Install

```sh
brew install hadolint
# OR Docker
docker pull hadolint/hadolint
```

## Usage

```sh
# Lint a single Dockerfile
hadolint Dockerfile

# Lint all Dockerfiles in the repo
find . -name "Dockerfile*" -exec hadolint {} \;

# Strict mode (fail on any warning)
hadolint --no-fail Dockerfile && echo OK
hadolint --error-only Dockerfile
```

## CI snippet

```yaml
- name: Hadolint
  uses: hadolint/hadolint-action@v3.1.0
  with:
    dockerfile: Dockerfile
    failure-threshold: warning
```

## Common findings

| Rule | Issue |
|---|---|
| DL3007 | `FROM` uses `latest` tag |
| DL3008 | `apt-get install` without version pin |
| DL3009 | `apt-get install` without `--no-install-recommends` |
| DL3022 | `COPY --chown` instead of `RUN chown` (smaller layer) |
| DL3025 | use exec form (`CMD ["..."]`) not shell form |
| DL3059 | multiple consecutive `RUN` (collapse into one) |

## Cross-references

- `languages/docker.md`.
- `dimensions/D04-security-posture.md` — non-root USER requirement.
- `dimensions/D08-build-ci-devloop.md` — reproducible builds.
