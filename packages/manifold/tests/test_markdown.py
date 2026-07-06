"""Tests for the stdlib markdown subset renderer."""
import unittest
from manifold import markdown


class TestRender(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(markdown.render(""), "")

    def test_headings(self):
        out = markdown.render("# h1\n## h2\n### h3\n")
        self.assertIn("<h1>h1</h1>", out)
        self.assertIn("<h2>h2</h2>", out)
        self.assertIn("<h3>h3</h3>", out)

    def test_paragraph(self):
        out = markdown.render("hello world")
        self.assertEqual(out, "<p>hello world</p>")

    def test_two_paragraphs(self):
        out = markdown.render("first\n\nsecond")
        self.assertIn("<p>first</p>", out)
        self.assertIn("<p>second</p>", out)

    def test_bold(self):
        self.assertEqual(markdown.render("**bold**"), "<p><strong>bold</strong></p>")

    def test_italic(self):
        self.assertEqual(markdown.render("*x*"), "<p><em>x</em></p>")

    def test_inline_code(self):
        out = markdown.render("hit `enter` to save")
        self.assertIn("<code>enter</code>", out)

    def test_link(self):
        out = markdown.render("see [docs](https://example.com)")
        self.assertIn('<a href="https://example.com">docs</a>', out)

    def test_code_block(self):
        out = markdown.render("```python\nx = 1\n```")
        self.assertIn('<pre><code class="lang-python">x = 1</code></pre>', out)

    def test_code_block_no_lang(self):
        out = markdown.render("```\nplain\n```")
        self.assertIn("<pre><code>plain</code></pre>", out)

    def test_unordered_list(self):
        out = markdown.render("- a\n- b\n- c")
        self.assertIn("<ul>", out)
        self.assertIn("<li>a</li>", out)
        self.assertIn("<li>c</li>", out)
        self.assertIn("</ul>", out)

    def test_ordered_list(self):
        out = markdown.render("1. a\n2. b")
        self.assertIn("<ol>", out)
        self.assertIn("<li>a</li>", out)

    def test_horizontal_rule(self):
        self.assertIn("<hr>", markdown.render("---"))

    def test_escapes_html(self):
        out = markdown.render("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_escapes_in_code_block(self):
        out = markdown.render("```\n<bad>\n```")
        self.assertIn("&lt;bad&gt;", out)
        self.assertNotIn("<bad>", out)

    def test_mixed(self):
        md = "# Title\n\nA paragraph with **bold** and `code`.\n\n- item\n- item"
        out = markdown.render(md)
        self.assertIn("<h1>Title</h1>", out)
        self.assertIn("<strong>bold</strong>", out)
        self.assertIn("<code>code</code>", out)
        self.assertIn("<ul>", out)


if __name__ == "__main__":
    unittest.main()
