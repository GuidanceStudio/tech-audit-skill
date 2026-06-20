"""Cross-reference linter: no dead links, no unreachable shipped content.

Scope: references whose first path segment is a skill top-level dir
(after stripping an optional `claude/tech-audit/` prefix), plus
bare-filename references that resolve next to the referencing file.
`<placeholder>` segments are treated as globs; `{a,b}` braces expand.
Target-repo paths (docs/, .tech-audit/extras/, app/, ...) are out of
scope by construction.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL = next(p.parent for p in REPO.glob("*/SKILL.md"))
PREFIX = f"{SKILL.name}/"
TOP_DIRS = {
    "cuts", "dimensions", "threat-models", "templates", "tools",
    "languages", "playbooks", "examples", "extensions", "routing",
    "scripts",
}
def expand_braces(token: str) -> list[str]:
    m = re.search(r"\{([^}]*)\}", token)
    if not m:
        return [token]
    out: list[str] = []
    for alt in m.group(1).split(","):
        out.extend(expand_braces(token[: m.start()] + alt.strip() + token[m.end():]))
    return out


def extract_refs(md_file: Path) -> list[str]:
    out = []
    for raw in re.findall(r"[A-Za-z0-9_./{},<>*-]+\.(?:md|py|ya?ml)", md_file.read_text()):
        raw = re.sub(r"<[^>]*>", "*", raw)  # <N>, <stack> → glob
        out.extend(expand_braces(raw))
    return out


def resolve(ref: str, referencing: Path) -> list[Path]:
    """Return matching skill files for a reference, [] if none/out-of-scope."""
    ref = ref.lstrip("(").rstrip(").")
    if ref.startswith(PREFIX):
        ref = ref[len(PREFIX):]
    ref = ref.lstrip("./")
    first = ref.split("/")[0]
    if "/" in ref and first in TOP_DIRS or ref == "SKILL.md":
        matches = sorted(SKILL.glob(ref)) if any(c in ref for c in "*?[") else (
            [SKILL / ref] if (SKILL / ref).is_file() else []
        )
        return matches or [Path("MISSING:" + ref)]
    if "/" not in ref:  # bare filename — same-dir resolution, best effort
        local = referencing.parent / ref
        return [local] if local.is_file() else []
    return []  # out-of-scope (target-repo path, external)


def all_md_sources() -> list[Path]:
    return sorted(SKILL.rglob("*.md")) + [REPO / "README.md"]


def test_no_dead_references() -> None:
    dead: list[str] = []
    for src in all_md_sources():
        for ref in extract_refs(src):
            for hit in resolve(ref, src):
                if str(hit).startswith("MISSING:"):
                    dead.append(f"{src.relative_to(REPO)} → {ref}")
    assert not dead, "Dead references:\n" + "\n".join(sorted(set(dead)))


def test_all_shipped_md_reachable_from_skill_or_readme() -> None:
    shipped = {p for p in SKILL.rglob("*.md")}
    reached: set[Path] = set()
    frontier = [SKILL / "SKILL.md", REPO / "README.md"]
    reached.add(SKILL / "SKILL.md")
    while frontier:
        src = frontier.pop()
        if not src.is_file():
            continue
        for ref in extract_refs(src):
            for hit in resolve(ref, src):
                if hit.is_file() and hit not in reached:
                    reached.add(hit)
                    if hit.suffix == ".md":
                        frontier.append(hit)
    unreachable = sorted(
        str(p.relative_to(SKILL)) for p in shipped - reached
    )
    assert not unreachable, (
        "Shipped but unreachable from SKILL.md/README.md (dead content):\n"
        + "\n".join(unreachable)
    )
