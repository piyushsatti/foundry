"""Tests for portfolio (Topic H)."""
import unittest

from manifold import queries, writes
from tests.conftest import fresh_db, seed_portfolio_fixture


class TestPortfolioLinks(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn)

    def test_list_portfolio_links(self):
        links = queries.list_portfolio_links(self.conn, theme_node_id="T.1")
        self.assertEqual(len(links), 3)
        projects = {l["project_id"] for l in links}
        self.assertEqual(projects, {"product-app", "ai-platform", "pipeline"})

    def test_portfolio_report_roll_up(self):
        report = queries.portfolio_report(self.conn)
        self.assertEqual(len(report["themes"]), 1)
        theme = report["themes"][0]
        self.assertEqual(theme["theme_node_id"], "T.1")
        self.assertEqual(len(theme["links"]), 3)
        refs = {l["node_ref"] for l in theme["links"]}
        self.assertIn("product-app/I.1", refs)
        self.assertEqual(theme["summary"]["planned"], 3)

    def test_portfolio_report_theme_filter(self):
        report = queries.portfolio_report(self.conn, theme_node_id="T.1")
        self.assertEqual(len(report["themes"]), 1)
        report_empty = queries.portfolio_report(self.conn, theme_node_id="T.99")
        self.assertEqual(report_empty["themes"], [])

    def test_portfolio_report_empty_when_no_portfolio_project(self):
        conn, _ = fresh_db(self)
        report = queries.portfolio_report(conn)
        self.assertEqual(report["themes"], [])

    def test_unlink_portfolio(self):
        writes.unlink_portfolio(
            self.conn, "T.1", "pipeline", "I.2", actor="test")
        links = queries.list_portfolio_links(self.conn, theme_node_id="T.1")
        self.assertEqual(len(links), 2)

    def test_link_portfolio_rejects_missing_theme(self):
        with self.assertRaises(ValueError):
            writes.link_portfolio(
                self.conn, "T.99", "product-app", "I.1", actor="test")


class TestPortfolioReportFormat(unittest.TestCase):
    def test_formatters(self):
        from manifold.portfolio_report import (
            format_markdown, format_terminal, render_quarter_roadmap,
        )

        report = {
            "themes": [{
                "theme_node_id": "T.1",
                "title": "Q3 Reliability",
                "summary": {"planned": 1, "in_progress": 0,
                            "achieved": 0, "blocked": 0},
                "links": [{
                    "node_ref": "product-app/I.1",
                    "project_id": "product-app",
                    "node_id": "I.1",
                    "title": "App",
                    "target_status": "planned",
                    "verdict_status": "",
                    "blocked_by": [],
                }],
            }],
        }
        self.assertIn("T.1", format_terminal(report))
        self.assertIn("product-app/I.1", format_markdown(report))
        self.assertIn("Quarter roadmap", render_quarter_roadmap(report))


if __name__ == "__main__":
    unittest.main()
