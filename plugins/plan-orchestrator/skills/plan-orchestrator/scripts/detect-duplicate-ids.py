#!/usr/bin/env python3
"""detect-duplicate-ids.py — flag duplicate identifiers.

Rules:
- E-numbers in `escalations.md` must be globally unique.
- A-numbers within a single file must be unique. (A-numbers may repeat
  ACROSS files — e.g., each phase plan starts numbering at A21 — but
  not within one file.)

Usage:  python3 detect-duplicate-ids.py <work-dir>
"""
import sys
import re
from collections import Counter
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print("Usage: detect-duplicate-ids.py <work-dir>", file=sys.stderr)
        return 2

    work_dir = Path(sys.argv[1])
    issues = []

    # E-numbers: globally unique across escalations.md
    esc = work_dir / "escalations.md"
    if esc.exists():
        ids = re.findall(r"^## (E\d+)", esc.read_text(), re.MULTILINE)
        counts = Counter(ids)
        for ident, n in counts.items():
            if n > 1:
                issues.append(f"escalations.md: {ident} appears {n} times")

    # A-numbers: unique within each file
    candidates = [work_dir / "assumptions.md"]
    phases_dir = work_dir / "phases"
    if phases_dir.exists():
        candidates.extend(phases_dir.rglob("plan.md"))
    for f in candidates:
        if not f.exists():
            continue
        ids = re.findall(r"^\s*-\s+id:\s+(A\d+)", f.read_text(), re.MULTILINE)
        counts = Counter(ids)
        for ident, n in counts.items():
            if n > 1:
                issues.append(f"{f.relative_to(work_dir)}: {ident} appears {n} times")

    if not issues:
        print("OK (no duplicate IDs)")
        return 0

    print(f"FAIL: {len(issues)} duplicate ID(s):")
    for i in issues:
        print(f"  {i}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
