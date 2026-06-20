"""install.sh behavior: per-target install, pycache exclusion, --check drift."""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_NAME = next(p.parent.name for p in REPO.glob("*/SKILL.md"))


def run_install(home: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(REPO / "install.sh"), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )


def claude_dir(home: Path) -> Path:
    return home / ".claude" / "skills" / SKILL_NAME


# --- default / claude ---

def test_default_target_installs_claude_clean(tmp_path: Path) -> None:
    assert run_install(tmp_path, "--force").returncode == 0  # no TTY → defaults to claude
    assert (claude_dir(tmp_path) / "SKILL.md").is_file()
    assert not list(claude_dir(tmp_path).rglob("__pycache__"))
    res = run_install(tmp_path, "--check", "--target", "claude")
    assert res.returncode == 0, res.stdout + res.stderr
    assert "OK" in res.stdout


def test_check_detects_drift(tmp_path: Path) -> None:
    run_install(tmp_path, "--force")
    with (claude_dir(tmp_path) / "SKILL.md").open("a") as fh:
        fh.write("\nlocal hand-edit\n")
    res = run_install(tmp_path, "--check", "--target", "claude")
    assert res.returncode == 1
    assert "DRIFT" in res.stdout


def test_check_reports_missing_install(tmp_path: Path) -> None:
    res = run_install(tmp_path, "--check", "--target", "claude")
    assert res.returncode == 1
    assert "DRIFT" in res.stdout


# --- codex / opencode verbatim ---

def test_codex_and_opencode_verbatim(tmp_path: Path) -> None:
    run_install(tmp_path, "--force", "--target", "codex")
    run_install(tmp_path, "--force", "--target", "opencode")
    assert (tmp_path / ".codex" / "skills" / SKILL_NAME / "SKILL.md").is_file()
    assert (tmp_path / ".config" / "opencode" / "skills" / SKILL_NAME / "SKILL.md").is_file()
    assert run_install(tmp_path, "--check", "--target", "codex").returncode == 0
    assert run_install(tmp_path, "--check", "--target", "opencode").returncode == 0


# --- gemini TOML wrapper ---

def test_gemini_emits_toml_and_payload(tmp_path: Path) -> None:
    res = run_install(tmp_path, "--force", "--target", "gemini")
    assert res.returncode == 0
    toml = tmp_path / ".gemini" / "commands" / "tech-audit.toml"
    assert toml.is_file()
    body = toml.read_text()
    assert "prompt" in body and "SKILL.md" in body
    assert (tmp_path / ".config" / "tech-audit" / "SKILL.md").is_file()
    assert run_install(tmp_path, "--check", "--target", "gemini").returncode == 0


# --- agents pointer ---

def test_agents_writes_pointer_idempotently(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    proj.mkdir()
    run_install(tmp_path, "--force", "--target", "agents", "--agents-dir", str(proj))
    agents = proj / "AGENTS.md"
    assert agents.is_file()
    assert "tech-audit:start" in agents.read_text()
    # Second run must not duplicate the block.
    run_install(tmp_path, "--force", "--target", "agents", "--agents-dir", str(proj))
    assert agents.read_text().count("tech-audit:start") == 1


# --- manual ---

def test_manual_prints_payload_path(tmp_path: Path) -> None:
    res = run_install(tmp_path, "--target", "manual")
    assert res.returncode == 0
    assert "tech-audit" in res.stdout
    # manual writes nothing
    assert not (tmp_path / ".claude").exists()
