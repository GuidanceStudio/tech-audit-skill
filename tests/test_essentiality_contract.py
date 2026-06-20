"""Contract tests for the D1 essentiality ladder."""

from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "tech-audit"
D1 = SKILL / "dimensions" / "D01-code-essentiality.md"
PHRASING = SKILL / "templates" / "finding-phrasing.md"
QUICK = SKILL / "cuts" / "quick.md"
FULL = SKILL / "cuts" / "full.md"
README = REPO / "README.md"
ROUTER = SKILL / "SKILL.md"

PREFIXES = ("delete:", "stdlib:", "native:", "yagni:", "shrink:")


def test_d1_defines_the_ordered_essentiality_ladder_once() -> None:
    d1 = D1.read_text()

    positions = [d1.index(prefix) for prefix in PREFIXES]
    assert positions == sorted(positions)
    # All prefixes must appear at least once; shrink: may appear >1×
    # (ladder definition + comment-weight scan both reference it).
    assert all(d1.count(p) >= 1 for p in PREFIXES)
    for p in ("delete:", "stdlib:", "native:", "yagni:"):
        assert d1.count(p) == 1, f"{p} must be single-sourced"


def test_d1_taxonomy_is_wired_into_review_output() -> None:
    assert "D1 essentiality prefixes" in PHRASING.read_text()
    assert "essentiality taxonomy" in QUICK.read_text()
    assert "essentiality taxonomy" in FULL.read_text()


def test_minimalism_has_non_negotiable_boundaries() -> None:
    d1 = D1.read_text().lower()
    for boundary in (
        "correctness",
        "tests",
        "trust-boundary validation",
        "security",
        "accessibility",
        "data-loss",
        "explicit requirement",
    ):
        assert boundary in d1


def test_readme_attributes_ponytail_without_requiring_the_plugin() -> None:
    readme = " ".join(README.read_text().split())
    assert "DietrichGebert/ponytail" in readme
    assert "MIT" in readme
    assert "plugin is not required" in readme


def test_d1_remains_mandatory_in_registry_and_quick_review() -> None:
    router = ROUTER.read_text()
    quick = QUICK.read_text()

    assert "| D1 | Code essentiality | always-deep |" in router
    assert "Always: D14" in quick
    assert "D1 (essentiality on the diff)" in quick


def test_repository_does_not_expose_duplicate_ponytail_skills() -> None:
    skill_frontmatters = [
        path.read_text().split("---", 2)[1]
        for path in REPO.rglob("SKILL.md")
        if path.read_text().startswith("---")
    ]
    assert not any(
        "name: ponytail-review" in frontmatter
        or "name: ponytail-audit" in frontmatter
        for frontmatter in skill_frontmatters
    )


def test_readme_has_an_explicit_integration_boundary() -> None:
    readme = README.read_text()
    assert "### Ponytail integration boundary" in readme
    assert "Concepts imported" in readme
    assert "Runtime dependency" in readme


# ---- M17-M19: comment essentiality, ponytail: scan, debt cross-reference ----


def test_d1_has_comment_weight_scan() -> None:
    d1 = D1.read_text()
    assert "Comment-weight scan" in d1
    assert "why" in d1.lower()
    assert "shrink:" in d1  # comment findings use shrink: prefix
    assert "public-API" in d1  # boundary: never flag API docs


def test_d1_has_ponytail_scan_method() -> None:
    d1 = D1.read_text()
    assert "ponytail: scan" in d1
    assert "Ceiling exceeded" in d1
    assert "Ceiling not yet reached" in d1
    assert "upgrade:" in d1.lower()
    assert "measurable" in d1.lower()


def test_d1_has_debt_register_cross_reference() -> None:
    d1 = D1.read_text()
    assert "Debt-register cross-reference" in d1
    assert ".tech-audit/debt.tsv" in d1
    assert "revisit_by" in d1
    assert "expired" in d1.lower()  # reactivates expired debt
    assert "suppressed:" in d1.lower()  # reports suppressed count
