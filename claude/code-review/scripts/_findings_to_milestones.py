#!/usr/bin/env python3
"""Convert audit findings into devplan milestone stubs.

Reads findings from stdin (one per line, format below) and emits a
markdown table + per-milestone stubs suitable for pasting into a
project's devplan / issue tracker.

Findings input format (TSV):
    <severity>\t<dim>\t<location>\t<title>\t<suggested-fix>\t<effort>

Or pipe a JSON array of objects with the same keys.

Usage:
    cat findings.tsv | python3 _findings_to_milestones.py --prefix SEC --start 7

Outputs:
    1. A triage table (markdown).
    2. One milestone stub per 🔴 finding (sub-tasks for 🟡 grouped under their dim).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass


@dataclass
class Finding:
    severity: str
    dim: str
    location: str
    title: str
    fix: str
    effort: str


def parse_tsv(stream) -> list[Finding]:
    out: list[Finding] = []
    for line in stream:
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 6:
            print(f"skip (wrong field count): {line[:80]}", file=sys.stderr)
            continue
        out.append(Finding(*parts))
    return out


def parse_json(stream) -> list[Finding]:
    data = json.load(stream)
    return [Finding(**d) for d in data]


def sev_order(s: str) -> int:
    return {"🔴": 0, "red": 0, "🟡": 1, "yellow": 1, "🟢": 2, "green": 2}.get(s, 99)


def render_triage_table(findings: list[Finding], prefix: str, start: int) -> tuple[str, dict[str, str]]:
    """Return (markdown table, map from finding-id → milestone-id)."""
    findings = sorted(findings, key=lambda f: (sev_order(f.severity), f.dim))
    rows: list[str] = ["| Finding | Suggested milestone | Effort |", "|---|---|---|"]
    milestone_map: dict[str, str] = {}
    counter = start
    for f in findings:
        if f.severity in ("🔴", "red"):
            mid = f"{prefix}-{counter}"
            milestone_map[f"{f.dim}-{counter}"] = mid
            rows.append(
                f"| {f.severity} {f.dim} @ `{f.location}` — {f.title} | "
                f"**{mid}**: {f.title} | {f.effort} |"
            )
            counter += 1
        else:
            rows.append(
                f"| {f.severity} {f.dim} @ `{f.location}` — {f.title} | "
                f"(group under {f.dim} follow-up milestone) | {f.effort} |"
            )
    return "\n".join(rows), milestone_map


def render_milestone_stubs(findings: list[Finding], milestone_map: dict[str, str]) -> str:
    """One milestone stub per 🔴; a single grouped stub per dim for 🟡."""
    reds = [f for f in findings if f.severity in ("🔴", "red")]
    yellows = [f for f in findings if f.severity in ("🟡", "yellow")]

    out: list[str] = []

    for i, f in enumerate(reds):
        mid = list(milestone_map.values())[i] if i < len(milestone_map) else f"AUDIT-{i + 1}"
        out.append(
            f"## {mid} — {f.title}\n\n"
            f"**Source**: audit finding {f.severity} @ `{f.location}` (dim {f.dim}).\n\n"
            f"**Why**: <one paragraph explaining the impact in plain language>\n\n"
            f"**Scope**:\n"
            f"- [ ] {f.fix}\n"
            f"- [ ] Add a regression test that pins this fix.\n"
            f"- [ ] Update related docs if the change affects operator behavior.\n\n"
            f"**Exit gate**: the audit re-runs clean on this finding.\n\n"
            f"**Effort**: {f.effort}.\n"
        )

    # Group yellows by dim
    yellows_by_dim: dict[str, list[Finding]] = {}
    for f in yellows:
        yellows_by_dim.setdefault(f.dim, []).append(f)

    for dim, items in sorted(yellows_by_dim.items()):
        out.append(f"## AUDIT-{dim}-followup — {dim} 🟡 cleanup\n")
        out.append("**Source**: audit pass.\n\n**Scope**:\n")
        for f in items:
            out.append(f"- [ ] `{f.location}` — {f.title}. Fix: {f.fix}. ({f.effort})")
        out.append("")

    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="AUDIT", help="Milestone prefix (e.g. SEC, OPT, AUDIT)")
    ap.add_argument("--start", type=int, default=1, help="Starting milestone number")
    ap.add_argument("--format", choices=["tsv", "json"], default="tsv")
    args = ap.parse_args()

    if args.format == "json":
        findings = parse_json(sys.stdin)
    else:
        findings = parse_tsv(sys.stdin)

    if not findings:
        print("no findings on stdin", file=sys.stderr)
        sys.exit(1)

    table, mmap = render_triage_table(findings, args.prefix, args.start)
    stubs = render_milestone_stubs(findings, mmap)

    print("# Triage\n")
    print(table)
    print("\n# Milestone stubs\n")
    print(stubs)


if __name__ == "__main__":
    main()
