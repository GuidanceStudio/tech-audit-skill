#!/usr/bin/env python3
"""Detect which language/framework stacks are present in a repo.

Emits a space-separated list of stack tags to stdout, suitable for piping
into shell case-statements or passing as args to subsequent steps.

Markers are searched recursively (depth limit, dependency/build dirs
pruned) so nested layouts — monorepos with services in subdirectories —
are detected too.

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

MAX_DEPTH = 3
PRUNE_DIRS = {
    ".git",
    "vendor",
    "node_modules",
    "storage",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}
PYTHON_MARKERS = {"pyproject.toml", "requirements.txt", "setup.py", "Pipfile"}
DOCKER_MARKERS = {
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
}


def iter_marker_files(root: Path, max_depth: int = MAX_DEPTH):
    """Yield files up to max_depth, pruning dependency/build directories."""

    def walk(directory: Path, depth: int):
        try:
            entries = sorted(directory.iterdir())
        except (PermissionError, OSError):
            return
        for path in entries:
            if path.is_dir():
                if depth < max_depth and path.name not in PRUNE_DIRS:
                    yield from walk(path, depth + 1)
            elif path.is_file():
                yield path

    yield from walk(root, 0)


def detect(root: Path) -> list[str]:
    """Scan known marker files recursively. Return sorted list of stack tags."""
    tags: set[str] = set()

    for path in iter_marker_files(root):
        name = path.name

        if name == "composer.json":
            tags.add("php")
            content = path.read_text(errors="ignore")
            if '"laravel/framework"' in content or '"illuminate/' in content:
                tags.add("php-laravel")
            elif '"symfony/' in content:
                tags.add("php-symfony")

        elif name in PYTHON_MARKERS:
            tags.add("python")
            content = path.read_text(errors="ignore").lower()
            if "fastapi" in content:
                tags.add("python-fastapi")
            if "django" in content:
                tags.add("python-django")
            if "flask" in content:
                tags.add("python-flask")

        elif name == "package.json":
            tags.add("typescript")
            content = path.read_text(errors="ignore")
            if '"next"' in content:
                tags.add("typescript-nextjs")
            if '"vite"' in content:
                tags.add("typescript-vite")

        elif name.endswith(".sh"):
            tags.add("shell")

        elif name in DOCKER_MARKERS:
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
