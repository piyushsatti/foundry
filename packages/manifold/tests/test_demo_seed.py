"""Tests for Acme Checkout demo seed."""
import unittest

from manifold import demo_seed, queries
from tests.conftest import fresh_db


class TestDemoSeed(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)

    def test_seed_creates_graph(self):
        result = demo_seed.seed_acme_checkout_demo(self.conn)
        self.conn.commit()
        self.assertEqual(result["status"], "seeded")
        self.assertIsNotNone(queries.get_node(self.conn, "acme-checkout", "I.1"))
        self.assertIsNotNone(queries.get_node(self.conn, "acme-checkout", "R.12"))
        self.assertTrue(
            queries.is_cross_blocked(self.conn, "acme-checkout", "R.12")
        )

    def test_idempotent(self):
        demo_seed.seed_acme_checkout_demo(self.conn)
        self.conn.commit()
        result = demo_seed.seed_acme_checkout_demo(self.conn)
        self.assertEqual(result["status"], "already_seeded")

    def test_brief_would_show_blocked(self):
        from manifold import status_brief

        demo_seed.seed_acme_checkout_demo(self.conn)
        self.conn.commit()
        view = status_brief.build_status_brief_view(self.conn, "acme-checkout")
        self.assertEqual(view["overall"]["status"], "blocked")
        self.assertGreaterEqual(len(view["shipped"]), 1)


if __name__ == "__main__":
    unittest.main()
