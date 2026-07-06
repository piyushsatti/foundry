#!/usr/bin/env python3
"""Regenerate the plugin's vendored copy of the manifold library.

The manifold MCP server imports the `manifold` package. In the repo it resolves
via a pip install or the sibling packages/manifold tree, but a marketplace
install ships only plugins/manifold/ — so a copy of the library is vendored
under server/_vendor/ to keep that install self-contained.

This script rebuilds that copy from the canonical source (packages/manifold).
Run it whenever packages/manifold changes; tests/test_vendor_parity.py fails if
the vendored copy has drifted.

    python3 plugins/manifold/scripts/vendor_sync.py
"""
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = REPO_ROOT / "packages" / "manifold"
VENDOR = REPO_ROOT / "plugins" / "manifold" / "server" / "_vendor"

# (source, destination) pairs the runtime needs. schema.sql sits beside the
# package (schema.py reads it via parent.parent), so it must be vendored too.
PACKAGE_SRC = PKG_ROOT / "manifold"
PACKAGE_DST = VENDOR / "manifold"
SCHEMA_SRC = PKG_ROOT / "schema.sql"
SCHEMA_DST = VENDOR / "schema.sql"

_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def sync() -> None:
    if not PACKAGE_SRC.exists():
        sys.exit(f"source package not found: {PACKAGE_SRC}")
    VENDOR.mkdir(parents=True, exist_ok=True)
    if PACKAGE_DST.exists():
        shutil.rmtree(PACKAGE_DST)
    shutil.copytree(PACKAGE_SRC, PACKAGE_DST, ignore=_IGNORE)
    shutil.copy2(SCHEMA_SRC, SCHEMA_DST)
    n = sum(1 for p in PACKAGE_DST.rglob("*") if p.is_file())
    print(f"vendored {n} package files + schema.sql -> {VENDOR.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    sync()
