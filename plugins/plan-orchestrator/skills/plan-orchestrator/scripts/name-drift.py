#!/usr/bin/env python3
"""name-drift.py — identifier names declared in contracts must be used
EXACTLY (same spelling and casing) in phase plans.

Approach:
- Extract canonical identifier names from contract headers like
  `## signature.<NAME>` / `## error.<NAME>` / `## behaviour.<NAME>`,
  plus backtick-quoted code identifiers in contract bodies (e.g.
  `validateMove(`).
- Find identifier usages in phase plans (backtick-quoted code idents).
- Flag any plan usage that is a close-but-not-exact match to a canonical
  name (e.g., axialDistance vs canonical hexDistance, or canonicalize vs
  serializeStateCanonical).

Caveats: heuristic; will produce false-negatives (won't catch genuinely
new identifiers) and rare false-positives (one project's identifier
collides with another's after normalization). Treat as advisory.

Usage:  python3 name-drift.py <work-dir>
"""
import sys
import re
from pathlib import Path


def extract_canonical_names(contracts_dir):
    """Collect identifier names from contract headers and backtick-quoted idents."""
    names = set()
    if not contracts_dir.exists():
        return names
    for f in contracts_dir.glob("*.md"):
        text = f.read_text()
        # Headers like `## signature.foo` / `## error.foo` / `## behaviour.foo`
        for m in re.finditer(
            r"^##\s+(?:signature|error|behaviour|behavior|api|endpoint)\.([\w]+)",
            text,
            re.MULTILINE,
        ):
            names.add(m.group(1))
        # Backtick-quoted code identifiers like `validateMove(` or `validateMove`
        for m in re.finditer(r"`([a-zA-Z_][a-zA-Z0-9_]+)`?\s*[\(`]", text):
            names.add(m.group(1))
    return names


def normalize(s):
    """Lowercase, strip non-alphanumeric — for similarity comparison."""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def find_drift_in_plans(work_dir, canonical):
    """Scan phase plans for identifiers that are close-but-not-exact to canonical names."""
    issues = set()
    phases_dir = work_dir / "phases"
    if not phases_dir.exists():
        return issues
    norm_map = {normalize(n): n for n in canonical}
    for f in phases_dir.rglob("plan.md"):
        text = f.read_text()
        for m in re.finditer(r"`([a-zA-Z_][a-zA-Z0-9_]+)`?\s*[\(`]", text):
            used = m.group(1)
            if used in canonical:
                continue  # exact match — clean
            n = normalize(used)
            if n in norm_map and norm_map[n] != used:
                issues.add((f.relative_to(work_dir), used, norm_map[n]))
    return issues


def main():
    if len(sys.argv) != 2:
        print("Usage: name-drift.py <work-dir>", file=sys.stderr)
        return 2

    work_dir = Path(sys.argv[1])
    canonical = extract_canonical_names(work_dir / "contracts")
    issues = find_drift_in_plans(work_dir, canonical)

    if not issues:
        print(f"OK ({len(canonical)} canonical names; no drift detected)")
        return 0

    print(f"FAIL: {len(issues)} potential name drift(s):")
    for f, used, closest in sorted(issues):
        print(f"  {f}: '{used}' — possibly should be '{closest}'")
    return 1


if __name__ == "__main__":
    sys.exit(main())
