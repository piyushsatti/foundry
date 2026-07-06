"""Tests for status-brief view-model (Topic K1–K7)."""
import unittest

from manifold import presentation_format, status_brief
from tests.conftest import fresh_db, seed_portfolio_fixture


class TestStatusBrief(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)

    def test_blocked_overall_with_cross_block(self):
        view = status_brief.build_status_brief_view(self.conn, "product-app")
        self.assertEqual(view["overall"]["status"], "blocked")
        self.assertEqual(len(view["blocked"]), 1)
        self.assertEqual(view["blocked"][0]["node_id"], "R.12")
        self.assertEqual(view["blocked"][0]["blocked_by"][0]["node_ref"], "ai-platform/C.4")
        self.assertEqual(len(view["in_flight"]), 1)

    def test_theme_link_from_portfolio(self):
        view = status_brief.build_status_brief_view(self.conn, "product-app")
        theme = view.get("theme_link")
        self.assertIsNotNone(theme)
        self.assertEqual(theme["portfolio_id"], "T.1")
        self.assertEqual(theme["label"], "Q3 Reliability")

    def test_stale_warning_without_validation(self):
        view = status_brief.build_status_brief_view(self.conn, "product-app")
        self.assertIsNotNone(view.get("stale_warning"))

    def test_golden_structure_stable(self):
        view = status_brief.build_status_brief_view(self.conn, "product-app")
        view.pop("generated_at", None)
        view.pop("changes_since", None)
        expected = {
            "$schema": "manifold/status-brief.v1",
            "view_kind": "status_brief",
            "project_id": "product-app",
            "project_label": "Test Project",
            "team": "Test Project",
            "stale_warning": (
                "No validation or drift run in the last 24h — "
                "run validation or drift-report before trusting verdict counts"
            ),
            "overall": {
                "status": "blocked",
                "headline": "1 blocked on AI cap; 1 in flight of 2 tracked leaves.",
            },
            "shipped": [],
            "in_flight": [{
                "node_ref": "product-app/I.1",
                "label": "App intent",
                "project_id": "product-app",
                "node_id": "I.1",
            }],
            "blocked": [{
                "node_ref": "product-app/R.12",
                "label": "Blocked leaf",
                "project_id": "product-app",
                "node_id": "R.12",
                "blocked_by": [{
                    "node_ref": "ai-platform/C.4",
                    "team": "Test Project",
                    "label": "AI cap",
                }],
            }],
            "at_risk": [],
            "theme_link": {
                "portfolio_id": "T.1",
                "label": "Q3 Reliability",
                "theme_node_ref": "portfolio/T.1",
            },
            "drift_summary": {
                "high": 0,
                "medium": 0,
                "low": 2,
                "link": "/projects/product-app/drift-report",
            },
            "warnings": [],
        }
        self.assertEqual(view, expected)

    def test_markdown_export_nonempty(self):
        view = status_brief.build_status_brief_view(self.conn, "product-app")
        md = presentation_format.format_status_brief_markdown(view)
        self.assertIn("# Status brief", md)
        self.assertIn("Blocked", md)
        self.assertIn("App intent", md)

    def test_project_not_found(self):
        view = status_brief.build_status_brief_view(self.conn, "missing")
        self.assertIn("project_not_found", view.get("warnings") or [])


if __name__ == "__main__":
    unittest.main()
