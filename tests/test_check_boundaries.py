"""check_boundaries must pass on the real repo AND fail on a planted violation.

The fixture test is the point: a guard never shown to fire on a true positive
is a silent no-op (red-vs-blue coverage gap 6).
"""
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import check_boundaries  # noqa: E402


class TestCheckBoundaries(unittest.TestCase):
    def test_repo_is_clean(self):
        self.assertEqual(check_boundaries.violations(REPO), [], "real repo has cross-bundle path reach")

    def test_planted_violation_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            offender = root / "bundles" / "alpha" / "skills" / "x"
            offender.mkdir(parents=True)
            (offender / "SKILL.md").write_text("steal from bundles/beta/skills/y/SKILL.md\n")
            (root / "bundles" / "beta").mkdir(parents=True)
            bad = check_boundaries.violations(root)
            self.assertEqual(len(bad), 1, f"expected exactly one violation, got: {bad}")
            self.assertIn("references bundles/beta/", bad[0])

    def test_own_bundle_reference_legal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "bundles" / "alpha"
            d.mkdir(parents=True)
            (d / "README.md").write_text("see bundles/alpha/skills/x for details\n")
            self.assertEqual(check_boundaries.violations(root), [])


if __name__ == "__main__":
    unittest.main()
