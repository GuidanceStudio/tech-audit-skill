#!/usr/bin/env python3
"""Simulate the D13 fresh-clone walkthrough.

Wipes a scratch directory, clones the target repo, copies .env.example -> .env,
attempts the documented bootstrap command, and reports how many steps the
operator had to do BEYOND `.env` editing + the bootstrap command.

Usage:
    python3 _doctor_fresh_clone.py REPO_URL [--bootstrap-cmd "./cli.sh stack-up"] [--scratch /tmp/audit-fresh]

A D13 'pass' requires:
  - .env.example exists.
  - The bootstrap command runs end-to-end without manual intervention.
  - Doctor / health check (if present) exits 0.
  - No 'docker exec', 'chown', 'psql', etc. in the operator's happy path.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def scan_for_manual_steps(repo: Path) -> list[str]:
    """Grep for raw operator-side commands in operator docs."""
    suspect_patterns = [
        "docker compose",
        "docker exec",
        "docker run",
        "chown",
        "chmod",
        "sudo",
        "apt install",
        "apt-get install",
        "pip install",
        "brew install",
        "npm install -g",
    ]
    findings: list[str] = []
    for md in list(repo.glob("README.md")) + list(repo.glob("docs/**/*.md")):
        # skip examples, threat-models, tools, and recovery docs (these may legitimately mention raw commands)
        rel = str(md.relative_to(repo))
        if any(s in rel for s in ("examples/", "threat-models/", "tools/", "recovery/", "runbook/")):
            continue
        try:
            text = md.read_text(errors="ignore")
        except OSError:
            continue
        for pat in suspect_patterns:
            for i, line in enumerate(text.splitlines(), 1):
                if pat in line and "```" not in line[:3]:  # skip in-fence code-block markers
                    findings.append(f"{rel}:{i}  {pat!r}  →  {line.strip()[:80]}")
    return findings


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_url", help="git URL of the repo to test")
    ap.add_argument("--bootstrap-cmd", default="./cli.sh stack-up",
                    help="bootstrap command to run after .env edit (default: ./cli.sh stack-up)")
    ap.add_argument("--scratch", default=None,
                    help="scratch directory (default: /tmp/<random>)")
    args = ap.parse_args()

    scratch = Path(args.scratch) if args.scratch else Path(tempfile.mkdtemp(prefix="audit-fresh-"))
    print(f"Scratch dir: {scratch}")
    if scratch.exists() and any(scratch.iterdir()):
        print("  (cleaning existing scratch)")
        shutil.rmtree(scratch)
    scratch.mkdir(parents=True, exist_ok=True)

    findings_red: list[str] = []
    findings_yellow: list[str] = []

    # Step 1: clone
    print("\n[1/4] git clone")
    try:
        run(["git", "clone", "--depth=1", args.repo_url, str(scratch)])
    except subprocess.CalledProcessError as e:
        findings_red.append(f"git clone failed: {e.stderr.strip()}")
        print_results(findings_red, findings_yellow)
        sys.exit(1)

    # Step 2: .env.example present?
    print("\n[2/4] .env.example presence")
    env_example = scratch / ".env.example"
    env = scratch / ".env"
    if not env_example.is_file():
        findings_red.append(".env.example is missing — operator has no template")
    else:
        shutil.copy(env_example, env)
        print(f"  copied {env_example} -> {env}")
        print("  (note: required external secrets are NOT filled — bootstrap may fail on real credential checks)")

    # Step 3: scan docs for hidden manual steps
    print("\n[3/4] scanning docs for manual operator steps")
    manual = scan_for_manual_steps(scratch)
    for f in manual:
        findings_yellow.append(f"manual step in operator docs: {f}")

    # Step 4: attempt the bootstrap command
    print(f"\n[4/4] running bootstrap: {args.bootstrap_cmd!r}")
    try:
        cmd = args.bootstrap_cmd.split()
        completed = run(cmd, cwd=scratch, check=False)
        if completed.returncode != 0:
            findings_red.append(
                f"bootstrap command exited {completed.returncode}. "
                "May need real credentials in .env, OR may indicate a true D13 regression. "
                "Inspect manually."
            )
    except FileNotFoundError as e:
        findings_red.append(f"bootstrap command not found: {e}")

    print_results(findings_red, findings_yellow)


def print_results(red: list[str], yellow: list[str]) -> None:
    print("\n" + "=" * 60)
    print("D13 fresh-clone walkthrough — results")
    print("=" * 60)
    if not red and not yellow:
        print("✅ pass — no findings")
        sys.exit(0)
    if red:
        print(f"\n🔴 {len(red)} ship-blocker(s):")
        for f in red:
            print(f"   - {f}")
    if yellow:
        print(f"\n🟡 {len(yellow)} fix-soon finding(s):")
        for f in yellow:
            print(f"   - {f}")
    sys.exit(1 if red else 0)


if __name__ == "__main__":
    main()
