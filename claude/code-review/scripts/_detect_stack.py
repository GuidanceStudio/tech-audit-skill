#!/usr/bin/env python3
"""Detect which language/framework stacks are present in a repo.

Emits a space-separated list of stack tags to stdout, suitable for piping
into shell case-statements or passing as args to subsequent steps.

Usage:
    python3 _detect_stack.py [REPO_ROOT]

Tags emitted (sorted for stable output):
    php, python, typescript, shell, docker

Sub-detection (when applicable) appended after the primary tag:
    php-laravel, python-fastapi, python-django, typescript-node, ...
"""
from __future__ import annotations

import sys
from pathlib import Path


def detect(root: Path) -> list[str]:
    """Walk known marker files. Return sorted list of stack tags."""
    tags: set[str] = set()

    # PHP
    composer = root / "composer.json"
    if composer.is_file():
        tags.add("php")
        content = composer.read_text(errors="ignore")
        if '"laravel/framework"' in content or '"illuminate/' in content:
            tags.add("php-laravel")
        elif '"symfony/' in content:
            tags.add("php-symfony")

    # Python
    pyproject = root / "pyproject.toml"
    reqs = root / "requirements.txt"
    setup = root / "setup.py"
    pipfile = root / "Pipfile"
    if pyproject.is_file() or reqs.is_file() or setup.is_file() or pipfile.is_file():
        tags.add("python")
        combined = ""
        for p in (pyproject, reqs, setup, pipfile):
            if p.is_file():
                combined += p.read_text(errors="ignore")
        if "fastapi" in combined.lower():
            tags.add("python-fastapi")
        if "django" in combined.lower():
            tags.add("python-django")
        if "flask" in combined.lower():
            tags.add("python-flask")

    # TypeScript / Node
    if (root / "package.json").is_file():
        tags.add("typescript")
        pkg = (root / "package.json").read_text(errors="ignore")
        if '"next"' in pkg:
            tags.add("typescript-nextjs")
        if '"vite"' in pkg:
            tags.add("typescript-vite")

    # Shell (any .sh in repo root or top-level dirs)
    for p in list(root.glob("*.sh")) + list(root.glob("scripts/*.sh")) + list(root.glob("bin/*.sh")):
        if p.is_file():
            tags.add("shell")
            break

    # Docker
    if any(
        (root / f).is_file()
        for f in ("Dockerfile", "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
    ):
        tags.add("docker")

    return sorted(tags)


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        sys.exit(1)
    tags = detect(root)
    if not tags:
        print("error: no known stack markers found", file=sys.stderr)
        sys.exit(2)
    print(" ".join(tags))


if __name__ == "__main__":
    main()
