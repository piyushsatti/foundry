"""
Unit tests for manifold html.py helper functions.
"""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pathsetup  # noqa: F401, E402

from manifold_web import html


class TestRationaleSection(unittest.TestCase):
    """html.rationale_section(node) — collapsible <details> for rationale + alternatives."""

    def test_returns_empty_when_both_fields_absent(self):
        node = {"rationale": None, "alternatives_considered": None}
        self.assertEqual(html.rationale_section(node), "")

    def test_returns_empty_when_both_fields_empty_string(self):
        node = {"rationale": "", "alternatives_considered": ""}
        self.assertEqual(html.rationale_section(node), "")

    def test_returns_empty_when_node_has_no_rationale_keys(self):
        node = {}
        self.assertEqual(html.rationale_section(node), "")

    def test_renders_rationale_when_set(self):
        node = {"rationale": "We chose this because of X.", "alternatives_considered": None}
        out = html.rationale_section(node)
        self.assertIn("We chose this because of X.", out)
        self.assertIn("<details", out)
        self.assertIn("rationale", out.lower())

    def test_renders_alternatives_when_set(self):
        node = {"rationale": None, "alternatives_considered": "Option A vs Option B."}
        out = html.rationale_section(node)
        self.assertIn("Option A vs Option B.", out)
        self.assertIn("<details", out)

    def test_renders_both_fields_when_both_set(self):
        node = {
            "rationale": "We chose X.",
            "alternatives_considered": "Considered Y and Z.",
        }
        out = html.rationale_section(node)
        self.assertIn("We chose X.", out)
        self.assertIn("Considered Y and Z.", out)

    def test_is_open_by_default(self):
        node = {"rationale": "some rationale", "alternatives_considered": None}
        out = html.rationale_section(node)
        # Must have open attribute on <details>
        self.assertIn("<details", out)
        self.assertIn(" open", out)

    def test_escapes_html_in_content(self):
        node = {"rationale": "<script>alert(1)</script>", "alternatives_considered": None}
        out = html.rationale_section(node)
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_returns_string(self):
        node = {"rationale": "reason", "alternatives_considered": "alt"}
        out = html.rationale_section(node)
        self.assertIsInstance(out, str)


class TestChangeReasonBadge(unittest.TestCase):
    """html.change_reason_badge(reason) — colored badge per change_reason value."""

    def test_returns_empty_string_for_none(self):
        self.assertEqual(html.change_reason_badge(None), "")

    def test_returns_empty_string_for_empty_string(self):
        self.assertEqual(html.change_reason_badge(""), "")

    def test_pivot_gets_red_class(self):
        out = html.change_reason_badge("pivot")
        self.assertIn("reason-pivot", out)
        self.assertIn("pivot", out)

    def test_drift_legacy_badge(self):
        out = html.change_reason_badge("drift")
        self.assertIn("reason-drift", out)

    def test_clarification_gets_green_class(self):
        out = html.change_reason_badge("clarification")
        self.assertIn("reason-clarification", out)
        self.assertIn("clarification", out)

    def test_correction_gets_green_class(self):
        out = html.change_reason_badge("correction")
        self.assertIn("reason-correction", out)
        self.assertIn("correction", out)

    def test_evolution_gets_blue_class(self):
        out = html.change_reason_badge("evolution")
        self.assertIn("reason-evolution", out)
        self.assertIn("evolution", out)

    def test_refactor_gets_blue_class(self):
        out = html.change_reason_badge("refactor")
        self.assertIn("reason-refactor", out)
        self.assertIn("refactor", out)

    def test_other_gets_badge(self):
        out = html.change_reason_badge("other")
        self.assertIn("reason-other", out)
        self.assertIn("other", out)

    def test_unknown_value_still_renders_badge(self):
        out = html.change_reason_badge("mystery_reason")
        self.assertIn("reason-badge", out)
        self.assertIn("mystery_reason", out)

    def test_badge_contains_reason_badge_class(self):
        out = html.change_reason_badge("drift")
        self.assertIn("reason-badge", out)

    def test_escapes_html_in_reason(self):
        out = html.change_reason_badge("<script>")
        self.assertNotIn("<script>", out)

    def test_returns_string(self):
        out = html.change_reason_badge("drift")
        self.assertIsInstance(out, str)


class TestBaseCSS(unittest.TestCase):
    """BASE_CSS must include the new reason badge CSS rules."""

    def test_reason_badge_class_defined(self):
        self.assertIn(".reason-badge", html.BASE_CSS)

    def test_reason_pivot_class_defined(self):
        self.assertIn(".reason-pivot", html.BASE_CSS)

    def test_reason_clarification_class_defined(self):
        self.assertIn(".reason-clarification", html.BASE_CSS)

    def test_reason_correction_class_defined(self):
        self.assertIn(".reason-correction", html.BASE_CSS)

    def test_reason_evolution_class_defined(self):
        self.assertIn(".reason-evolution", html.BASE_CSS)

    def test_reason_refactor_class_defined(self):
        self.assertIn(".reason-refactor", html.BASE_CSS)

    def test_reason_other_class_defined(self):
        self.assertIn(".reason-other", html.BASE_CSS)


if __name__ == "__main__":
    unittest.main()
