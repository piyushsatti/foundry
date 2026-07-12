#!/usr/bin/env python3
"""Boundary guard: no bundle may reference another bundle's internals by path.

Structure: scans every text file under bundles/<X>/ for the literal pattern
`bundles/<Y>/...` where Y != X. Cross-bundle *path* reach couples bundles and
breaks after materialization (an installed plugin has no sibling bundles) —
the legal route to reuse is promoting the capability to library/ and pulling
it via compose in bundle.yaml.

Why paths, not the dep graph: namespaced runtime dispatch (a skill suggesting
or dispatching another plugin's skill by name, e.g. `dispatches: [hats]` in
skills/manifest.yaml) is legal composition — only filesystem reach is the
violation, so only paths are checked.

Operate: python3 scripts/check_boundaries.py [ROOT]   (ROOT defaults to repo;
tests pass a fixture tree). Exit 0 clean, 1 with a report on violations.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".js", ".ts", ".html", ".css", ".txt", ".sql", ".toml"}
REF_RE = re.compile(r"bundles/([A-Za-z0-9_-]+)/")


def violations(root: Path) -> list[str]:
    bundles_dir = root / "bundles"
    if not bundles_dir.is_dir():
        return []
    found = []
    for bundle in sorted(p for p in bundles_dir.iterdir() if p.is_dir()):
        for f in bundle.rglob("*"):
            if not f.is_file() or f.suffix not in TEXT_SUFFIXES:
                continue
            try:
                text = f.read_text(errors="ignore")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                for m in REF_RE.finditer(line):
                    target = m.group(1)
                    if target != bundle.name:
                        found.append(f"{f.relative_to(root)}:{lineno}: references bundles/{target}/ (own bundle: {bundle.name})")
    return found


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
    bad = violations(root)
    if bad:
        print("check_boundaries: VIOLATIONS — promote shared capabilities to library/ instead of cross-bundle reach:")
        print("  " + "\n  ".join(bad))
        return 1
    print("check_boundaries: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
