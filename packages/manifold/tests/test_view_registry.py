"""Tests for presentation view registry."""
import unittest

from manifold import presentation_views, view_registry
from tests.conftest import fresh_db, seed_portfolio_fixture


class TestViewRegistry(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)

    def test_list_views_includes_blockers(self):
        ids = {v["view_id"] for v in view_registry.list_views()}
        self.assertIn("blockers", ids)
        self.assertIn("mindmap-flow", ids)

    def test_build_registered_blockers(self):
        view = view_registry.build_registered_view(
            self.conn, "product-app", "blockers", focus_node_id="R.12",
        )
        self.assertEqual(view["view_id"], "blockers")
        self.assertEqual(view["diagram_type"], "blockers")
        refs = {n["node_ref"] for n in view["nodes"]}
        self.assertIn("ai-platform/C.4", refs)

    def test_unknown_view_id_warns(self):
        view = view_registry.build_registered_view(
            self.conn, "product-app", "no-such-view",
        )
        self.assertIn("unknown_view_id", view.get("warnings") or [])

    def test_registry_matches_direct_builder(self):
        direct = presentation_views.build_diagram_view(
            self.conn, "product-app", focus_node_id="R.12",
        )
        via_reg = view_registry.build_registered_view(
            self.conn, "product-app", "blockers", focus_node_id="R.12",
        )
        direct.pop("generated_at", None)
        via_reg.pop("generated_at", None)
        via_reg.pop("view_id", None)
        via_reg.pop("view_description", None)
        self.assertEqual(direct, via_reg)


if __name__ == "__main__":
    unittest.main()
