# Trivy

**What it catches**: container CVE + filesystem CVE + IaC misconfig + SBOM + secrets. The OSS swiss-army knife — one binary, all the layers.

## Install

```sh
brew install trivy
# OR Docker
docker pull aquasec/trivy
```

## Usage

```sh
# Scan a built image
trivy image YOUR_IMAGE

# Scan filesystem (catches lockfile CVEs, IaC issues, secrets in files)
trivy fs .

# Scan a Dockerfile / compose file for misconfig
trivy config .

# Generate SBOM (CycloneDX format)
trivy image YOUR_IMAGE --format cyclonedx > sbom.json

# Block CI on severity threshold
trivy fs . --severity HIGH,CRITICAL --exit-code 1
```

## CI snippet

```yaml
- name: Trivy filesystem scan
  uses: aquasecurity/trivy-action@master
  with:
    scan-type: 'fs'
    scan-ref: '.'
    severity: 'HIGH,CRITICAL'
    exit-code: '1'

- name: Trivy image scan
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'ghcr.io/${{ github.repository }}:${{ github.sha }}'
    severity: 'HIGH,CRITICAL'
    exit-code: '1'
```

## Tuning

- `.trivyignore` — list CVE IDs to suppress (with justification comment).
- `--timeout` if scans are slow on large images.
- `--skip-dirs` to exclude `node_modules`, `vendor`, `.git`.
- DB cache: Trivy downloads vuln DB at startup; cache `~/.cache/trivy` in CI to speed up.

## False positives

- CVE in a transitive dep that's not actually exposed at runtime → 🟢 with `.trivyignore` entry + note.
- Outdated base image where the upstream hasn't released a patched version → 🟡 (track upstream).

## Cross-references

- `dimensions/D04-security-posture.md`.
- `dimensions/D07-dependency-hygiene.md`.
- `languages/docker.md`.
