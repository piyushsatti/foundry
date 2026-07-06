"""Tests for cross-project edges (Topic I)."""
import unittest

from manifold import queries, writes
from manifold.constants import PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER
from manifold.node_ref import format_node_ref, parse_node_ref
from tests.conftest import fresh_db, seed_project


class TestNodeRef(unittest.TestCase):
    def test_parse_and_format(self):
        self.assertEqual(parse_node_ref("ai-platform/C.4"),
                         ("ai-platform", "C.4"))
        self.assertEqual(format_node_ref("ai-platform", "C.4"),
                         "ai-platform/C.4")

    def test_rejects_bare_node_id(self):
        with self.assertRaises(ValueError):
            parse_node_ref("C.4")


class TestCrossProjectEdges(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "product-app",
                     layers=[{"name": "realizations"}])
        seed_project(self.conn, "ai-platform",
                     layers=[{"name": "capability"}])
        writes.create_node(
            self.conn, "product-app", "realizations", "R.12",
            "Product realization", actor="test",
        )
        writes.create_node(
            self.conn, "ai-platform", "capability", "C.4",
            "AI capability", actor="test",
        )

    def test_create_and_list_cross_edge(self):
        writes.create_cross_edge(
            self.conn, "product-app", "R.12", "ai-platform", "C.4",
            "blocks", actor="test",
        )
        edges = queries.list_cross_edges(self.conn, project_id="product-app")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["dst_ref"], "ai-platform/C.4")

    def test_create_cross_edge_rejects_self_edge(self):
        with self.assertRaisesRegex(ValueError, "cannot connect.*itself"):
            writes.create_cross_edge(
                self.conn, "product-app", "R.12", "product-app", "R.12",
                "blocks", actor="test",
            )

    def test_create_cross_edge_rejects_archived_project(self):
        writes.archive_project(self.conn, "ai-platform")
        with self.assertRaisesRegex(ValueError, "archived"):
            writes.create_cross_edge(
                self.conn, "product-app", "R.12", "ai-platform", "C.4",
                "blocks", actor="test",
            )

    def test_next_leaves_excluded_reports_blockers(self):
        writes.create_cross_edge(
            self.conn, "product-app", "R.12", "ai-platform", "C.4",
            "blocks", actor="test",
        )
        excluded = queries.next_leaves_excluded(self.conn, "product-app")
        self.assertEqual(len(excluded), 1)
        self.assertEqual(excluded[0]["node_id"], "R.12")
        self.assertEqual(excluded[0]["reason"], "cross_blocked")
        self.assertEqual(excluded[0]["blocked_by"], ["ai-platform/C.4"])

    def test_next_leaves_excludes_cross_blocked(self):
        writes.create_cross_edge(
            self.conn, "product-app", "R.12", "ai-platform", "C.4",
            "blocks", actor="test",
        )
        leaves = queries.next_leaves(self.conn, "product-app")
        ids = [l["node_id"] for l in leaves]
        self.assertNotIn("R.12", ids)
        ai_ids = [l["node_id"] for l in queries.next_leaves(self.conn, "ai-platform")]
        self.assertIn("C.4", ai_ids)

        writes.transition_target(
            self.conn, "ai-platform", "C.4", "achieved",
            expected_revision_id=queries.get_node(
                self.conn, "ai-platform", "C.4")["current_revision_id"],
            actor="test",
        )
        leaves_after = queries.next_leaves(self.conn, "product-app")
        self.assertIn("R.12", [l["node_id"] for l in leaves_after])

    def test_list_cross_blocking_chain(self):
        writes.create_cross_edge(
            self.conn, "product-app", "R.12", "ai-platform", "C.4",
            "blocks", actor="test",
        )
        chain = queries.list_cross_blocking_chain(
            self.conn, "product-app", "R.12")
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0]["node_ref"], "ai-platform/C.4")

    def test_is_cross_blocked(self):
        writes.create_cross_edge(
            self.conn, "product-app", "R.12", "ai-platform", "C.4",
            "blocks", actor="test",
        )
        self.assertTrue(
            queries.is_cross_blocked(self.conn, "product-app", "R.12"))

    def test_portfolio_report_blocked_by(self):
        seed_project(self.conn, PORTFOLIO_PROJECT_ID,
                     layers=[{"name": PORTFOLIO_THEME_LAYER}])
        writes.create_node(
            self.conn, PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER, "T.1",
            "Theme", actor="test",
        )
        writes.link_portfolio(
            self.conn, "T.1", "product-app", "R.12", actor="test")
        writes.create_cross_edge(
            self.conn, "product-app", "R.12", "ai-platform", "C.4",
            "blocks", actor="test",
        )
        report = queries.portfolio_report(self.conn)
        link = report["themes"][0]["links"][0]
        self.assertEqual(link["blocked_by"], ["ai-platform/C.4"])
        self.assertEqual(report["themes"][0]["summary"]["blocked"], 1)

    def test_validate_cross_edge_invalid_ref(self):
        from manifold import validate

        self.conn.execute(
            "INSERT INTO cross_project_edges "
            "(src_project_id, src_node_id, dst_project_id, dst_node_id, "
            "edge_kind, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            ("product-app", "R.12", "ai-platform", "MISSING", "blocks"),
        )
        issues = validate.check_cross_project_edges(self.conn)
        kinds = {i["kind"] for i in issues}
        self.assertIn("cross_project_edge_invalid_ref", kinds)


if __name__ == "__main__":
    unittest.main()
