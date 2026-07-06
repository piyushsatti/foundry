"""Tests for server-side presentation SVG renderers."""
import unittest

from manifold import presentation_format, presentation_svg, presentation_views
from tests.conftest import fresh_db, seed_portfolio_fixture


class TestPresentationSvg(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)

    def test_diagram_svg_contains_nodes(self):
        view = presentation_views.build_diagram_view(
            self.conn, "product-app", focus_node_id="R.12",
        )
        svg = presentation_svg.render_diagram_svg(view)
        self.assertIn("<svg", svg)
        self.assertIn("Blocked leaf", svg)
        self.assertIn("AI cap", svg)

    def test_mindmap_svg_contains_root(self):
        view = presentation_views.build_mindmap_view(
            self.conn, "product-app", focus_node_id="I.1",
        )
        svg = presentation_svg.render_mindmap_svg(view)
        self.assertIn("<svg", svg)
        self.assertIn("App intent", svg)

    def test_render_view_svg_dispatches(self):
        view = presentation_views.build_diagram_view(
            self.conn, "product-app", focus_node_id="R.12",
        )
        self.assertIn("<rect", presentation_svg.render_view_svg(view))

    def test_html_pages_no_cdn_mermaid(self):
        """SVG path must not depend on jsDelivr."""
        view = presentation_views.build_diagram_view(
            self.conn, "product-app", focus_node_id="R.12",
        )
        mmd = presentation_format.format_mermaid_flowchart(view)
        svg = presentation_svg.render_view_svg(view)
        self.assertNotIn("jsdelivr", svg.lower())
        self.assertIn("flowchart", mmd)


if __name__ == "__main__":
    unittest.main()
