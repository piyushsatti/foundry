"""Tests for ai-foundry init / purge seed."""
import unittest
from pathlib import Path

from manifold import foundry_seed, queries, status_brief
from tests.conftest import fresh_db


class TestFoundrySeed(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)

    def test_purge_and_seed(self):
        from tests.conftest import seed_project
        seed_project(self.conn, "junk", label="junk")
        removed = foundry_seed.purge_all_projects(self.conn)
        self.assertIn("junk", removed)
        result = foundry_seed.seed_ai_foundry(
            self.conn, repo_root=Path("/tmp/ai-foundry"), actor="test",
        )
        self.conn.commit()
        self.assertEqual(result["project_id"], "ai-foundry")
        self.assertGreaterEqual(result["node_count"], 10)
        self.assertIsNotNone(queries.get_node(self.conn, "ai-foundry", "I.1"))
        self.assertIsNotNone(queries.get_node(self.conn, "ai-foundry", "R.j3"))

    def test_brief_shows_in_flight_and_shipped(self):
        foundry_seed.init_foundry_db(
            self.conn, repo_root=Path("/tmp/ai-foundry"), actor="test",
        )
        self.conn.commit()
        view = status_brief.build_status_brief_view(self.conn, "ai-foundry")
        self.assertIn(view["overall"]["status"], ("in_flight", "shipped"))
        self.assertGreaterEqual(len(view["in_flight"]), 1)
        shipped_ids = {n["node_id"] for n in view["shipped"]}
        self.assertIn("R.core", shipped_ids)


if __name__ == "__main__":
    unittest.main()
