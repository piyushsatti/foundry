"""Tests for per-idea database registry and seeds."""
import tempfile
import unittest
from pathlib import Path

from manifold import idea_registry, queries
from tests.conftest import fresh_db


class TestIdeaRegistry(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)

    def test_seed_product_idea_idempotent(self):
        spec = idea_registry.IDEAS["chronicler"]
        r1 = idea_registry.seed_product_idea(self.conn, spec, actor="test")
        r2 = idea_registry.seed_product_idea(self.conn, spec, actor="test")
        self.conn.commit()
        self.assertEqual(r1["project_id"], "chronicler")
        self.assertEqual(r2["status"], "seeded")
        self.assertEqual(r1["node_count"], r2["node_count"])
        self.assertIsNotNone(queries.get_node(self.conn, "chronicler", "I.1"))

    def test_foundry_solo_no_portfolio(self):
        result = idea_registry.seed_foundry_idea(
            self.conn, repo_root=Path("/tmp/ai-foundry"), actor="test",
        )
        self.conn.commit()
        self.assertEqual(result["project_id"], "ai-foundry")
        self.assertNotIn("theme_id", result)
        self.assertIsNone(queries.get_project(self.conn, "portfolio"))

    def test_init_idea_db_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "chronicler.db"
            result = idea_registry.init_idea_db(
                "chronicler", db_path, actor="test",
            )
            self.assertTrue(db_path.exists())
            self.assertEqual(result["main_project"], "chronicler")
            self.assertGreaterEqual(result["total_nodes"], 45)


if __name__ == "__main__":
    unittest.main()
