"""install.sh behavior: install, pycache exclusion, --check drift detection."""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_NAME = next((REPO / "claude").glob("*/SKILL.md")).parent.name


def run_install(home: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(REPO / "install.sh"), *args],
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )


def installed_dir(home: Path) -> Path:
    return home / ".claude" / "skills" / SKILL_NAME


def test_install_and_check_clean(tmp_path: Path) -> None:
    assert run_install(tmp_path, "--force").returncode == 0
    assert (installed_dir(tmp_path) / "SKILL.md").is_file()
    assert not list(installed_dir(tmp_path).rglob("__pycache__"))
    res = run_install(tmp_path, "--check")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "OK" in res.stdout


def test_check_detects_drift(tmp_path: Path) -> None:
    run_install(tmp_path, "--force")
    with (installed_dir(tmp_path) / "SKILL.md").open("a") as fh:
        fh.write("\nlocal hand-edit\n")
    res = run_install(tmp_path, "--check")
    assert res.returncode == 1
    assert "DRIFT" in res.stdout


def test_check_reports_missing_install(tmp_path: Path) -> None:
    res = run_install(tmp_path, "--check")
    assert res.returncode == 1
    assert "DRIFT" in res.stdout
