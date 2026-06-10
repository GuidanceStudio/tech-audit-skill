#!/usr/bin/env python3
"""Bootstrap audit tooling on a target repo per `playbooks/operations.md` § Starter pack.

Idempotent: re-running is safe. Reports what was added vs already-present.

Usage:
    python3 _bootstrap_tooling.py [REPO_ROOT] [--week N]

Without --week, runs all 5 weeks of the starter pack in order.

Each "week" adds one piece:
    1. Gitleaks (.pre-commit-config.yaml + .github/workflows/audit.yml)
    2. Trivy + auto-dep-updates (in audit.yml + .github/dependabot.yml)
    3. Semgrep (in audit.yml)
    4. Cross-tenant probe test stub (tests/integration/test_cross_tenant_probe.py)
    5. pgTAP RLS test stub (tests/db/test_rls.sql)
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SKILL_TEMPLATES = Path(__file__).resolve().parent.parent / "templates"


def ensure_dir(p: Path) -> bool:
    """Create dir if missing. Return True if it didn't exist before."""
    if p.is_dir():
        return False
    p.mkdir(parents=True)
    return True


def write_if_absent(path: Path, content: str) -> str:
    """Write content if file doesn't exist. Return 'added' / 'kept'."""
    if path.exists():
        return "kept"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return "added"


def week_1_gitleaks(repo: Path) -> list[str]:
    """Wire Gitleaks: pre-commit + CI."""
    results: list[str] = []

    pre_commit = repo / ".pre-commit-config.yaml"
    if not pre_commit.exists():
        src = SKILL_TEMPLATES / "ci-pre-commit.yaml"
        shutil.copy(src, pre_commit)
        results.append(f"added {pre_commit}")
    else:
        results.append(f"kept   {pre_commit} (review manually for Gitleaks hook)")

    audit_wf = repo / ".github" / "workflows" / "audit.yml"
    if not audit_wf.exists():
        src = SKILL_TEMPLATES / "ci-github-actions.yml"
        audit_wf.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, audit_wf)
        results.append(f"added {audit_wf}")
    else:
        results.append(f"kept   {audit_wf} (review manually for Gitleaks job)")

    return results


def week_2_trivy_renovate(repo: Path) -> list[str]:
    """Trivy already in audit.yml from week 1 template. Add Dependabot."""
    results: list[str] = []

    dep = repo / ".github" / "dependabot.yml"
    content = """version: 2
updates:
  - package-ecosystem: "composer"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5
  - package-ecosystem: "npm"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5
  - package-ecosystem: "docker"
    directory: "/"
    schedule: { interval: "weekly" }
    open-pull-requests-limit: 5
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "monthly" }
"""
    results.append(f"{write_if_absent(dep, content):6s} {dep}")
    return results


def week_3_semgrep(repo: Path) -> list[str]:
    """Semgrep is already in the audit.yml template. Just note it."""
    return ["note: Semgrep is included in templates/ci-github-actions.yml — already wired by week 1"]


def week_4_cross_tenant_probe(repo: Path) -> list[str]:
    """Stub a cross-tenant probe test."""
    results: list[str] = []
    target = repo / "tests" / "integration" / "test_cross_tenant_probe.py"
    stub = '''"""Cross-tenant probe — D5 regression net.

Authenticate as tenant A. Try every tenant-scoped endpoint with tenant B's
primary keys. Each must return 403 or 404. Any 200 is a tenant leak.

Adapt the imports + endpoints + fixtures to your stack.
"""
import pytest

# from your_app import test_client_for, create_tenant_with, ...

TENANT_A_EMAIL = "alice@a.example"
TENANT_B_EMAIL = "bob@b.example"


@pytest.fixture(scope="module")
def tenant_a_session():
    return ...  # session authenticated as tenant A's user


@pytest.fixture(scope="module")
def tenant_b_resources():
    """Pre-create resources owned by tenant B that should be inaccessible from A."""
    return {
        "agent_id": ...,  # UUID of an agent owned by tenant B
        "conversation_id": ...,
    }


@pytest.mark.parametrize("method,endpoint_tmpl", [
    ("GET", "/api/agents/{agent_id}"),
    ("PUT", "/api/agents/{agent_id}"),
    ("DELETE", "/api/agents/{agent_id}"),
    ("GET", "/api/agents/{agent_id}/messages"),
    ("GET", "/api/conversations/{conversation_id}"),
    # Add EVERY tenant-scoped resource × every verb the API exposes.
])
def test_tenant_a_cannot_touch_tenant_b(tenant_a_session, tenant_b_resources, method, endpoint_tmpl):
    url = endpoint_tmpl.format(**tenant_b_resources)
    resp = tenant_a_session.request(method, url)
    assert resp.status_code in (403, 404), \
        f"TENANT LEAK: {method} {url} returned {resp.status_code}"
'''
    results.append(f"{write_if_absent(target, stub):6s} {target}")
    return results


def week_5_pgtap(repo: Path) -> list[str]:
    """Stub pgTAP RLS assertions."""
    results: list[str] = []
    target = repo / "tests" / "db" / "test_rls.sql"
    stub = """-- pgTAP RLS assertions — D5 DB-level invariants.
--
-- Run with: psql -X -f tests/db/test_rls.sql -d $DB_NAME
-- Adapt the table names + tenant IDs to your schema.

BEGIN;
SELECT plan(4);

-- Setup: assume two tenants with IDs (replace with actual UUIDs in your fixtures)
\\set tenant_a_id '\\'00000000-0000-0000-0000-000000000a\\''
\\set tenant_b_id '\\'00000000-0000-0000-0000-000000000b\\''

-- Switch to tenant A's context
SET app.current_tenant TO :tenant_a_id;

SELECT isnt_empty(
    'SELECT * FROM conversations',
    'tenant A can see their own conversations'
);

SELECT bag_eq(
    'SELECT DISTINCT tenant_id FROM conversations',
    'SELECT ' || :tenant_a_id || '::uuid',
    'tenant A only sees their own tenant_id'
);

-- Switch to tenant B's context
SET app.current_tenant TO :tenant_b_id;

SELECT is_empty(
    'SELECT * FROM conversations WHERE tenant_id = ' || :tenant_a_id || '::uuid',
    'tenant B sees NO of tenant A''s conversations (RLS blocks)'
);

-- Negative: try to disable RLS as a non-superuser (should fail)
SELECT throws_ok(
    'ALTER TABLE conversations DISABLE ROW LEVEL SECURITY',
    '42501',
    NULL,
    'non-superuser cannot disable RLS'
);

SELECT * FROM finish();
ROLLBACK;
"""
    results.append(f"{write_if_absent(target, stub):6s} {target}")
    return results


WEEKS = {
    1: ("Gitleaks pre-commit + CI", week_1_gitleaks),
    2: ("Trivy + Dependabot", week_2_trivy_renovate),
    3: ("Semgrep", week_3_semgrep),
    4: ("Cross-tenant probe test stub", week_4_cross_tenant_probe),
    5: ("pgTAP RLS assertion stub", week_5_pgtap),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", nargs="?", default=".", help="Target repo root")
    ap.add_argument("--week", type=int, choices=range(1, 6), help="Run a single week only")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"error: {repo} is not a directory", file=sys.stderr)
        sys.exit(1)

    weeks_to_run = [args.week] if args.week else list(WEEKS.keys())

    for n in weeks_to_run:
        title, fn = WEEKS[n]
        print(f"\n=== Week {n}: {title} ===")
        for line in fn(repo):
            print(f"  {line}")

    print("\nDone. Review generated stubs before relying on them in CI.")


if __name__ == "__main__":
    main()
