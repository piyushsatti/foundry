#!/usr/bin/env python3
"""
lint-assumptions.py — checks assumption format compliance across the work-dir.

Required fields per assumption: id, claim, rationale, confidence, risk_if_wrong,
status, validated_by, validated_at.

Also warns when a low-confidence + medium/high-risk assumption is still `pending`
(per decision 22, those MUST be resolved before T3).

Usage:  python3 lint-assumptions.py <work-dir>

Exit codes:
  0  clean
  1  hard format issues found
  2  warnings only (risky pending assumptions exist)
"""
import sys
import re
from pathlib import Path

REQUIRED = ["id", "claim", "rationale", "confidence", "risk_if_wrong",
            "status", "validated_by", "validated_at"]


def find_assumption_blocks(text):
    """Match list items beginning with '- id: A<n>' through to the next blank
    line or the next list item or end-of-text."""
    pattern = re.compile(
        r"-\s+id:\s+A\d+(?:\n(?:\s+\S.*|\s*))*?(?=\n-\s+id:\s+A\d+|\n[a-zA-Z_]+:|\n\s*\n|\Z)",
        re.MULTILINE,
    )
    return [m.group(0) for m in pattern.finditer(text)]


def field_value(block, field):
    m = re.search(rf"\b{field}\s*:\s*(.+)", block)
    return m.group(1).strip() if m else None


def main():
    if len(sys.argv) != 2:
        print("Usage: lint-assumptions.py <work-dir>", file=sys.stderr)
        return 2

    work_dir = Path(sys.argv[1])
    files = []
    root_a = work_dir / "assumptions.md"
    if root_a.exists():
        files.append(root_a)
    phases_dir = work_dir / "phases"
    if phases_dir.exists():
        for f in phases_dir.rglob("*.md"):
            files.append(f)

    hard_issues = []
    risky_pending = []

    for f in files:
        text = f.read_text()
        for block in find_assumption_blocks(text):
            id_m = re.search(r"id:\s+(A\d+)", block)
            aid = id_m.group(1) if id_m else "?"
            for field in REQUIRED:
                if not re.search(rf"\b{field}\s*:", block):
                    hard_issues.append(f"{f.relative_to(work_dir)}::{aid}: missing field '{field}'")

            conf = (field_value(block, "confidence") or "").lower()
            risk = (field_value(block, "risk_if_wrong") or "").lower()
            status = (field_value(block, "status") or "").lower()

            if "pending" in status and "low" in conf and ("high" in risk or "medium" in risk):
                risky_pending.append(f"{f.relative_to(work_dir)}::{aid} (confidence={conf}, risk={risk})")

    if hard_issues:
        print("FAIL: assumption format issues:")
        for h in hard_issues:
            print(f"  - {h}")
    if risky_pending:
        print("WARN: low-confidence + risky assumptions still pending:")
        for r in risky_pending:
            print(f"  - {r}")
        print("Per decision 22, these MUST be resolved before T3 (spec-tightened / scope-reduced / deferred).")

    if hard_issues:
        return 1
    if risky_pending:
        return 2
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
