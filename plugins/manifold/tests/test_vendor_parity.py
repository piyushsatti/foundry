"""Guard: the vendored manifold library must match packages/manifold exactly.

The plugin ships a copy of the library under server/_vendor/ so a marketplace
install (which has no packages/manifold) is self-contained. That copy is a
maintenance hazard if it drifts, so this test asserts byte-for-byte parity with
the canonical source. If it fails, run:

    python3 plugins/manifold/scripts/vendor_sync.py
"""
import filecmp
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = REPO_ROOT / "packages" / "manifold"
VENDOR = REPO_ROOT / "plugins" / "manifold" / "server" / "_vendor"


def _rel_files(root: Path) -> set[str]:
    return {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file()
        and not p.name.endswith((".pyc", ".pyo"))
        and "__pycache__" not in p.parts
    }


class VendorParityTest(unittest.TestCase):
    SYNC_HINT = "run: python3 plugins/manifold/scripts/vendor_sync.py"

    def test_vendor_exists(self):
        self.assertTrue(
            (VENDOR / "manifold" / "__init__.py").exists(),
            f"vendored package missing; {self.SYNC_HINT}",
        )
        self.assertTrue(
            (VENDOR / "schema.sql").exists(),
            f"vendored schema.sql missing; {self.SYNC_HINT}",
        )

    def test_package_file_set_matches(self):
        src = _rel_files(PKG_ROOT / "manifold")
        dst = _rel_files(VENDOR / "manifold")
        self.assertEqual(
            src, dst, f"vendored file set differs from source; {self.SYNC_HINT}"
        )

    def test_package_contents_match(self):
        for rel in _rel_files(PKG_ROOT / "manifold"):
            with self.subTest(file=rel):
                self.assertTrue(
                    filecmp.cmp(
                        PKG_ROOT / "manifold" / rel,
                        VENDOR / "manifold" / rel,
                        shallow=False,
                    ),
                    f"{rel} differs from source; {self.SYNC_HINT}",
                )

    def test_schema_matches(self):
        self.assertTrue(
            filecmp.cmp(
                PKG_ROOT / "schema.sql", VENDOR / "schema.sql", shallow=False
            ),
            f"schema.sql differs from source; {self.SYNC_HINT}",
        )


if __name__ == "__main__":
    unittest.main()
