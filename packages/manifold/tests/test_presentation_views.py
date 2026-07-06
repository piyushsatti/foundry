"""Tests for Topic K presentation view-models."""
import json
import unittest

from manifold import presentation_format, presentation_views
from tests.conftest import fresh_db, seed_portfolio_fixture


class TestPresentationViews(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)

    def test_blockers_diagram_cross_block(self):
        view = presentation_views.build_diagram_view(
            self.conn, "product-app",
            diagram_type="blockers",
            focus_node_id="R.12",
        )
        self.assertEqual(view["diagram_type"], "blockers")
        self.assertEqual(view["focus_node_id"], "R.12")
        refs = {n["node_ref"] for n in view["nodes"]}
        self.assertIn("product-app/R.12", refs)
        self.assertIn("ai-platform/C.4", refs)
        self.assertTrue(any(
            e["from_ref"] == "ai-platform/C.4" and e["to_ref"] == "product-app/R.12"
            for e in view["edges"]
        ))

    def test_mindmap_tree_from_focus(self):
        view = presentation_views.build_mindmap_view(
            self.conn, "product-app",
            focus_node_id="I.1",
        )
        self.assertIsNotNone(view["tree"])
        self.assertEqual(view["tree"]["node_ref"], "product-app/I.1")
        self.assertGreaterEqual(len(view["nodes"]), 1)

    def test_golden_blockers_fixture_stable(self):
        view = presentation_views.build_diagram_view(
            self.conn, "product-app",
            diagram_type="blockers",
            focus_node_id="R.12",
        )
        view.pop("generated_at", None)
        expected = {
            "project_id": "product-app",
            "view_kind": "diagram",
            "diagram_type": "blockers",
            "focus_node_id": "R.12",
            "trajectory_id": None,
            "truncated": False,
            "warnings": [],
            "nodes": [
                {
                    "node_ref": "product-app/R.12",
                    "project_id": "product-app",
                    "node_id": "R.12",
                    "title": "Blocked leaf",
                    "layer": "realizations",
                    "target_status": "planned",
                },
                {
                    "node_ref": "ai-platform/C.4",
                    "project_id": "ai-platform",
                    "node_id": "C.4",
                    "title": "AI cap",
                    "layer": "capability",
                    "target_status": "planned",
                },
            ],
            "edges": [{
                "from_ref": "ai-platform/C.4",
                "to_ref": "product-app/R.12",
                "kind": "blocks",
                "scope": "cross_project",
            }],
        }
        self.assertEqual(view, expected)

    def test_mermaid_formatters_nonempty(self):
        view = presentation_views.build_diagram_view(
            self.conn, "product-app", focus_node_id="R.12")
        mmd = presentation_format.format_mermaid_flowchart(view)
        self.assertIn("flowchart LR", mmd)
        self.assertIn("product_app_R_12", mmd)
        md = presentation_format.format_markdown(view)
        self.assertIn("```mermaid", md)


if __name__ == "__main__":
    unittest.main()
