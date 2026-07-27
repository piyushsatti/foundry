"""
Minimal markdown → HTML renderer for manifold node body display.

Stdlib only. Handles the subset that matters for spec node bodies:
- ATX headings (# .. ######)
- Paragraphs (blank-line separated)
- Fenced code blocks (```...```)
- Inline code (`text`)
- Bold (**text**)
- Italic (*text*)
- Links ([text](url)) — href restricted to a safe-scheme allowlist
- Unordered lists (- item or * item)
- Ordered lists (1. item)
- Horizontal rules (---)
- HTML escaping everywhere

Does NOT handle: tables, footnotes, images, blockquotes, nested lists,
HTML passthrough, reference-style links. Those are non-goals for spec bodies.
"""
import re
from html import escape


_FENCE_RE = re.compile(r"^```(\w*)\s*$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_HRULE_RE = re.compile(r"^-{3,}\s*$")
_UL_ITEM_RE = re.compile(r"^[-*]\s+(.+)$")
_OL_ITEM_RE = re.compile(r"^\d+\.\s+(.+)$")

# Inline transforms (applied in order; each operates on already-escaped HTML).
_INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
_BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_LINK_RE = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")

# Link href safety: only these schemes may appear in an <a href>. A relative
# URL (no scheme) is allowed. Anything else — javascript:, data:, vbscript: — is
# dropped to plain text. HTML-escaping already blocks attribute breakout (" ->
# &quot;); this allowlist blocks script-executing schemes, the other XSS vector.
_ALLOWED_SCHEMES = frozenset({"http", "https", "mailto", "tel"})
# A leading scheme is letters/digits/+-. up to the first colon. If the regex
# matches, a real scheme is present (the char class excludes / ? #, so
# "path:with:colon" style relative refs won't false-match here).
_SCHEME_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):")
# Browsers strip ASCII whitespace/control chars from within a scheme before
# dispatching it, so "java\tscript:" executes. Strip the same set before the
# scheme check so those can't smuggle a blocked scheme past the allowlist.
_URL_STRIP_RE = re.compile(r"[\x00-\x20]")


def _safe_href(url: str) -> str | None:
    """Return the href if its scheme is safe to emit, else None.

    ``url`` is already HTML-escaped. Relative URLs (no scheme) pass; a URL whose
    scheme is not in _ALLOWED_SCHEMES is rejected so the caller can drop the link.
    """
    probe = _URL_STRIP_RE.sub("", url)
    m = _SCHEME_RE.match(probe)
    if m and m.group(1).lower() not in _ALLOWED_SCHEMES:
        return None
    return url.strip()


def _link_sub(m: "re.Match[str]") -> str:
    text, url = m.group(1), m.group(2)
    href = _safe_href(url)
    if href is None:
        return text  # unsafe scheme — keep the visible text, drop the link
    return f'<a href="{href}">{text}</a>'


def _inline(text: str) -> str:
    """Apply inline transforms to already-escaped text."""
    text = _INLINE_CODE_RE.sub(r"<code>\1</code>", text)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)
    text = _LINK_RE.sub(_link_sub, text)
    return text


def render(md: str) -> str:
    """Render a markdown string to HTML. Returns a string of safe HTML."""
    if not md:
        return ""
    lines = md.splitlines()
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Fenced code block
        m = _FENCE_RE.match(line)
        if m:
            lang = m.group(1)
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not _FENCE_RE.match(lines[i]):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1  # consume closing fence
            code_html = escape("\n".join(code_lines))
            lang_class = f' class="lang-{escape(lang)}"' if lang else ""
            out.append(f"<pre><code{lang_class}>{code_html}</code></pre>")
            continue

        # Heading
        m = _HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            content = _inline(escape(m.group(2)))
            out.append(f"<h{level}>{content}</h{level}>")
            i += 1
            continue

        # Horizontal rule
        if _HRULE_RE.match(line):
            out.append("<hr>")
            i += 1
            continue

        # Unordered list (consecutive `-` or `*` items)
        if _UL_ITEM_RE.match(line):
            items: list[str] = []
            while i < len(lines) and _UL_ITEM_RE.match(lines[i]):
                items.append(_UL_ITEM_RE.match(lines[i]).group(1))
                i += 1
            out.append("<ul>")
            for it in items:
                out.append(f"<li>{_inline(escape(it))}</li>")
            out.append("</ul>")
            continue

        # Ordered list
        if _OL_ITEM_RE.match(line):
            items = []
            while i < len(lines) and _OL_ITEM_RE.match(lines[i]):
                items.append(_OL_ITEM_RE.match(lines[i]).group(1))
                i += 1
            out.append("<ol>")
            for it in items:
                out.append(f"<li>{_inline(escape(it))}</li>")
            out.append("</ol>")
            continue

        # Blank line — paragraph separator
        if not line.strip():
            i += 1
            continue

        # Paragraph: collect lines until blank or block element
        para: list[str] = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if not nxt.strip():
                break
            if (_FENCE_RE.match(nxt) or _HEADING_RE.match(nxt) or
                    _HRULE_RE.match(nxt) or _UL_ITEM_RE.match(nxt) or
                    _OL_ITEM_RE.match(nxt)):
                break
            para.append(nxt)
            i += 1
        joined = " ".join(para)
        out.append(f"<p>{_inline(escape(joined))}</p>")

    return "\n".join(out)
