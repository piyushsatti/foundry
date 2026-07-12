"""Build gates: determinism + vendored-copy fidelity.

Replaces the retired plugins/manifold/tests/test_vendor_parity.py — the
vendored tree is now produced fresh by scripts/build.py, so the guards are
(1) build twice -> byte-identical trees, and (2) the vendored package (incl.
sidecars like schema.sql) matches packages/ source byte-for-byte.

Run: python3 -m unittest tests.test_build_determinism  (from repo root)
"""
import filecmp
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BUILD = REPO / "scripts" / "build.py"


def _run_build(out: Path) -> None:
    subprocess.run(
        [sys.executable, str(BUILD), "--out", str(out)],
        check=True,
        capture_output=True,
        cwd=REPO,
    )


def _rel_files(root: Path) -> set:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


class TestBuildDeterminism(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        cls.out1, cls.out2 = tmp / "a" / "plugins", tmp / "b" / "plugins"
        _run_build(cls.out1)
        _run_build(cls.out2)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_two_builds_identical(self):
        files1, files2 = _rel_files(self.out1), _rel_files(self.out2)
        self.assertEqual(files1, files2, "file sets differ between two builds")
        diff = [p for p in sorted(files1) if not filecmp.cmp(self.out1 / p, self.out2 / p, shallow=False)]
        self.assertEqual(diff, [], f"content differs between two builds: {diff}")

    def test_vendored_manifold_matches_source(self):
        src = REPO / "packages" / "manifold" / "manifold"
        dst = self.out1 / "manifold" / "server" / "_vendor" / "manifold"
        self.assertTrue(dst.is_dir(), "vendored manifold package missing from build")
        src_files = {
            str(p.relative_to(src)) for p in src.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".pyo")
        }
        dst_files = {str(p.relative_to(dst)) for p in dst.rglob("*") if p.is_file()}
        self.assertEqual(src_files, dst_files, "vendored file set drifted from packages/manifold")
        diff = [p for p in sorted(src_files) if not filecmp.cmp(src / p, dst / p, shallow=False)]
        self.assertEqual(diff, [], f"vendored content drifted: {diff}")

    def test_schema_sidecar_shipped(self):
        src = REPO / "packages" / "manifold" / "schema.sql"
        dst = self.out1 / "manifold" / "server" / "_vendor" / "schema.sql"
        self.assertTrue(dst.is_file(), "schema.sql sidecar missing — MCP would fail at schema.bootstrap")
        self.assertTrue(filecmp.cmp(src, dst, shallow=False), "schema.sql sidecar drifted from source")

    def test_marketplace_catalog(self):
        mp = self.out1 / ".claude-plugin" / "marketplace.json"
        self.assertTrue(mp.is_file(), "release marketplace catalog not generated")
        catalog = json.loads(mp.read_text())
        names = [p["name"] for p in catalog["plugins"]]
        self.assertEqual(names, sorted(names), "catalog not sorted")
        self.assertNotIn("cartographer", names, "parked bundle leaked into the catalog")
        for entry in catalog["plugins"]:
            self.assertNotIn("version", entry, f"{entry['name']}: version key in marketplace entry (plugin.json is sole source)")

    def test_excludes_applied(self):
        leaked = [str(p) for p in self.out1.rglob("bundle.yaml")] + [str(p) for p in self.out1.rglob("evals")]
        self.assertEqual(leaked, [], f"excluded dev files leaked into build: {leaked}")


if __name__ == "__main__":
    unittest.main()
