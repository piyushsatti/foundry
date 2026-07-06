"""Tests for Chronicler visualization showcase seed."""
import unittest

from manifold import chronicler_seed, queries, status_brief
from tests.conftest import fresh_db


class TestChroniclerSeed(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)

    def test_rich_graph_node_count(self):
        result = chronicler_seed.seed_chronicler(self.conn, actor="test")
        self.conn.commit()
        self.assertEqual(result["status"], "seeded")
        self.assertGreaterEqual(result["total_nodes"], 45)
        self.assertIn("chronicler-ios", result["projects"])
        self.assertIn("chronicler-sync", result["projects"])

    def test_cross_edges_wired(self):
        chronicler_seed.seed_chronicler(self.conn, actor="test")
        self.conn.commit()
        edges = queries.list_cross_edges(self.conn, project_id="chronicler")
        self.assertGreaterEqual(len(edges), 3)
        blockers = [
            e for e in edges
            if e.get("src_node_id") == "R.5.1" and e.get("dst_project_id") == "chronicler-sync"
        ]
        self.assertEqual(len(blockers), 1)

    def test_brief_has_rich_sections(self):
        chronicler_seed.seed_chronicler(self.conn, actor="test")
        self.conn.commit()
        view = status_brief.build_status_brief_view(self.conn, "chronicler")
        self.assertGreaterEqual(len(view["shipped"]), 5)
        self.assertGreaterEqual(len(view["in_flight"]), 3)
        self.assertIn(view["overall"]["status"], ("in_flight", "shipped", "blocked"))

    def test_force_replaces_sparse_graph(self):
        from manifold import idea_registry

        idea_registry.seed_product_idea(
            self.conn, idea_registry.IDEAS["chronicler"], actor="test",
        )
        self.conn.commit()
        sparse = chronicler_seed._node_count(self.conn, "chronicler")
        self.assertLess(sparse, 10)

        chronicler_seed.seed_chronicler(self.conn, actor="test", force=True)
        self.conn.commit()
        rich = chronicler_seed._node_count(self.conn, "chronicler")
        self.assertGreaterEqual(rich, 35)


if __name__ == "__main__":
    unittest.main()
