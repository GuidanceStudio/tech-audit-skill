"""Regression tests for the helper scripts (M1 fixes)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = next((REPO / "claude").glob("*/scripts"))
sys.path.insert(0, str(SCRIPTS))

import _detect_stack  # noqa: E402


def test_detect_root_markers(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"dependencies": {"next": "14"}}')
    tags = _detect_stack.detect(tmp_path)
    assert "typescript" in tags
    assert "typescript-nextjs" in tags


def test_detect_nested_monorepo(tmp_path: Path) -> None:
    """The cerase-core regression: markers live one level down."""
    cp = tmp_path / "control-plane"
    cp.mkdir()
    (cp / "composer.json").write_text('{"require": {"laravel/framework": "^11"}}')
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "deploy.sh").write_text("#!/bin/bash\n")
    (tmp_path / "docker-compose.yml").write_text("services: {}\n")
    tags = _detect_stack.detect(tmp_path)
    assert "php" in tags
    assert "php-laravel" in tags
    assert "shell" in tags
    assert "docker" in tags


def test_detect_prunes_dependency_dirs(tmp_path: Path) -> None:
    vendor = tmp_path / "vendor" / "some" / "pkg"
    vendor.mkdir(parents=True)
    (vendor / "composer.json").write_text("{}")
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "package.json").write_text("{}")
    assert _detect_stack.detect(tmp_path) == []


def test_detect_empty_repo(tmp_path: Path) -> None:
    assert _detect_stack.detect(tmp_path) == []


def run_milestones(tsv: str, *args: str) -> str:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "_findings_to_milestones.py"), *args],
        input=tsv,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def test_milestone_ids_track_findings_on_unsorted_input() -> None:
    """Reds arriving out of severity/dim order must keep their own IDs."""
    tsv = (
        "🟡\tD2\tdocs/x.md\tDoc drift\tfix doc\t1h\n"
        "🔴\tD5\tapp/q.php\tCross-tenant read\tadd scope\t2h\n"
        "🔴\tD1\tapp/dead.php\tDead class\tdelete it\t30m\n"
    )
    out = run_milestones(tsv, "--prefix", "AUDIT", "--start", "7")
    # Sorted by (severity, dim): the D1 red is AUDIT-7, the D5 red is AUDIT-8.
    assert "## AUDIT-7 — Dead class" in out
    assert "## AUDIT-8 — Cross-tenant read" in out


def test_milestones_six_column_tsv_roundtrip() -> None:
    tsv = "🔴\tD4\tapp/a.php\tSQL injection\tparametrize\t1h\n"
    out = run_milestones(tsv, "--prefix", "SEC", "--start", "1")
    assert "## SEC-1 — SQL injection" in out
    assert "Add a regression test" in out
    assert "confidence" not in out  # no 7th column → no confidence noise


def test_milestones_seven_column_tsv_with_confidence() -> None:
    tsv = "🔴\tD4\tapp/a.php\tSQL injection\tparametrize\t1h\tneeds-verification\n"
    out = run_milestones(tsv, "--prefix", "SEC", "--start", "1")
    assert "## SEC-1 — SQL injection" in out
    assert "confidence: needs-verification" in out
