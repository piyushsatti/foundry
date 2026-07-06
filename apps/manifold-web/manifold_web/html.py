"""
HTML template helpers for manifold's web surface.

Stdlib only. No Jinja. Plain string templates with `html.escape` everywhere.
Inline CSS for portability; the only external asset is CodeMirror under
/static/codemirror/. Diagram/mindmap pages render SVG server-side; Mermaid
source is shown in a collapsible export block (no CDN).
"""
import json
from html import escape
from typing import Iterable, Optional


BASE_CSS = """
:root {
  --bg: #f4f3ef;
  --surface: #ffffff;
  --fg: #1a1814;
  --muted: #6b6560;
  --accent: #1d4ed8;
  --accent-soft: #dbeafe;
  --border: #ddd9d0;
  --code-bg: #f0eeea;
  --warn: #b45309;
  --ok: #15803d;
  --err: #b91c1c;
  --target: #6d28d9;
  --radius: 8px;
  --shadow: 0 1px 3px rgba(26, 24, 20, 0.06);
}
.primary-parent { font-weight: 600; }
.other-parents { color: var(--muted); font-size: 0.9em; }
* { box-sizing: border-box; }
body {
  font: 15px/1.6 "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--fg);
  background: var(--bg);
  margin: 0;
}
header {
  border-bottom: 1px solid var(--border);
  padding: 14px 28px;
  background: var(--surface);
  box-shadow: var(--shadow);
}
header a { text-decoration: none; color: var(--muted); margin-right: 18px; font-size: 0.92em; font-weight: 500; }
header a:hover { color: var(--accent); text-decoration: none; }
main { max-width: 960px; margin: 0 auto; padding: 28px 24px 48px; }
main.page-wide { max-width: 1120px; }
.page-hero { margin-bottom: 24px; }
.page-hero h1 { font-size: 1.75rem; font-weight: 600; letter-spacing: -0.02em; margin: 0 0 8px; line-height: 1.25; }
.page-hero .subtitle { color: var(--muted); font-size: 0.95em; margin: 0; }
.viz-nav {
  display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0 24px;
  padding: 4px; background: var(--code-bg); border-radius: var(--radius);
}
.viz-nav a {
  padding: 6px 14px; border-radius: 6px; text-decoration: none;
  color: var(--muted); font-size: 0.88em; font-weight: 500;
}
.viz-nav a:hover { background: var(--surface); color: var(--accent); }
.viz-nav a.is-active { background: var(--surface); color: var(--accent); box-shadow: var(--shadow); }
.viz-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px 24px; margin: 20px 0;
  box-shadow: var(--shadow);
}
.viz-card h2 { margin-top: 0; border-bottom: none; font-size: 1.05rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
h1 { font-size: 1.6rem; margin: 0.2em 0 0.6em; }
h2 { font-size: 1.15rem; margin: 1.4em 0 0.6em; border-bottom: 1px solid var(--border); padding-bottom: 6px; font-weight: 600; }
h3 { font-size: 1.05rem; margin: 1em 0 0.4em; }
a { color: var(--accent); }
code, pre { background: var(--code-bg); border-radius: 4px; font-family: "IBM Plex Mono", "SF Mono", Menlo, monospace; font-size: 0.88em; }
code { padding: 2px 6px; }
pre { padding: 14px; overflow-x: auto; border: 1px solid var(--border); }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 0.94em; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }
th { background: var(--code-bg); font-weight: 600; font-size: 0.82em; text-transform: uppercase; letter-spacing: 0.03em; color: var(--muted); }
.muted { color: var(--muted); }
.badge { display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 0.78em; font-weight: 600; }
.badge-status-satisfied { background: #dcfce7; color: var(--ok); }
.badge-status-violated  { background: #fee2e2; color: var(--err); }
.badge-status-unknown   { background: #eee; color: #555; }
.badge-target           { background: #ede9fe; color: var(--target); }
.error-banner { background: #fef3c7; border: 1px solid #fcd34d; padding: 12px 16px; border-radius: var(--radius); margin-bottom: 16px; }
form label { display: block; margin-top: 12px; font-weight: 500; }
form input[type=text], form textarea, form select {
  width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 4px;
  font: inherit; background: var(--surface);
}
form textarea { min-height: 200px; font-family: "IBM Plex Mono", Menlo, monospace; }
form button {
  padding: 8px 16px; background: var(--accent); color: white;
  border: 0; border-radius: 6px; cursor: pointer; margin-top: 16px; margin-right: 8px;
  font: inherit; font-weight: 500;
}
form button.secondary { background: #57534e; }
form button:hover { opacity: 0.92; }
.CodeMirror { border: 1px solid var(--border); border-radius: var(--radius); height: 400px; }
.timeline { border-left: 2px solid var(--border); padding-left: 16px; margin-top: 12px; }
.timeline-item { margin-bottom: 12px; }
.timeline-ts { color: var(--muted); font-size: 0.85em; }
.stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 20px 0; }
.stat-box { border: 1px solid var(--border); padding: 14px 16px; border-radius: var(--radius); background: var(--surface); box-shadow: var(--shadow); }
.stat-box h4 { margin: 0 0 8px 0; font-size: 0.72em; text-transform: uppercase; color: var(--muted); letter-spacing: 0.05em; font-weight: 600; }
.stat-box .stat-row { display: flex; justify-content: space-between; padding: 2px 0; }
.stat-box .stat-num { font-weight: 600; }
.stat-box .stat-big { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.1; }
.stat-box .stat-ctx { color: var(--muted); font-size: 0.82em; margin-top: 4px; }
.diff-line-add { background: #e6ffed; display: block; }
.diff-line-del { background: #ffeef0; display: block; }
.diff-line-ctx { color: #6a737d; display: block; }
.diff-table td.diff-line-add, .diff-table td.diff-line-del { padding: 6px 10px; }
.badge-violated, .badge-invalidated_by_descendant { background: #d73a49; color: white; }
.badge-satisfied { background: #28a745; color: white; }
.badge-judge_required, .badge-deferred_external { background: #ffc107; color: black; }
.badge-unknown, .badge-no_mechanism { background: #6a737d; color: white; }
.trigger-form { background: var(--code-bg); padding: 10px 14px; border-radius: var(--radius); margin: 12px 0; }
.trigger-form label { display: inline-block; margin-right: 12px; font-weight: normal; }
.trigger-form button { margin: 0 0 0 8px; padding: 4px 12px; }
.mindmap-tree ul { margin: 0.35em 0 0.35em 1.4em; list-style: disc; }
.mindmap-tree li { margin: 0.35em 0; line-height: 1.45; }
.presentation-svg {
  overflow-x: auto; padding: 8px 0;
  background: linear-gradient(180deg, #fafaf8 0%, var(--surface) 100%);
  border-radius: var(--radius); border: 1px solid var(--border);
}
.presentation-svg svg { max-width: 100%; height: auto; display: block; margin: 0 auto; min-width: 320px; }
.presentation-export { margin-top: 20px; }
.presentation-export summary { cursor: pointer; color: var(--muted); font-size: 0.9em; font-weight: 500; }
.presentation-export pre { background: var(--surface); margin-top: 8px; }
.json-collapse summary { cursor: pointer; color: var(--muted); font-weight: 500; }
.pill { display: inline-block; padding: 3px 12px; border-radius: 999px; font-size: 0.82em; font-weight: 600; }
.pill--shipped { background: #dcfce7; color: var(--ok); }
.pill--in-flight { background: var(--accent-soft); color: var(--accent); }
.pill--blocked { background: #fee2e2; color: var(--err); }
.pill--at-risk { background: #fef3c7; color: #92400e; }
.pill--paused { background: #eee; color: #555; }
.brief-meta dl { display: grid; grid-template-columns: max-content 1fr; gap: 6px 20px; margin: 0; font-size: 0.92em; }
.brief-meta dt { font-weight: 600; color: var(--muted); }
.brief-section { margin: 0; }
.brief-section + .brief-section { margin-top: 8px; }
.brief-list { list-style: none; padding: 0; margin: 0.5em 0; }
.brief-list li { padding: 10px 0; border-bottom: 1px solid var(--border); line-height: 1.45; }
.brief-list li:last-child { border-bottom: none; }
.brief-stale { background: #fef3c7; border: 1px solid #fcd34d; padding: 12px 16px; border-radius: var(--radius); margin: 12px 0; }
.lod-hidden { display: none; }
.edit-fields { width: auto; }
.edit-fields td { padding: 4px 8px; border-bottom: none; }
.edit-fields td:first-child { font-family: "IBM Plex Mono", Menlo, monospace; font-size: 0.85em; color: var(--muted); }
.reason-badge { display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 0.78em; font-weight: 500; margin-left: 6px; }
.reason-pivot         { background: #fde8e8; color: #c41e3a; }
.reason-drift         { background: #fde8e8; color: #c41e3a; }
.reason-clarification{ background: #d4edd9; color: #1a7f37; }
.reason-correction   { background: #d4edd9; color: #1a7f37; }
.reason-evolution    { background: #dce8f8; color: #2c5aa0; }
.reason-refactor     { background: #dce8f8; color: #2c5aa0; }
.reason-other        { background: #eee; color: #555; }
.headline { font-size: 1.1rem; margin: 12px 0 0; line-height: 1.5; }
.status-glyph { font-weight: 700; margin-right: 2px; }
.focus-picker {
  display: flex; flex-wrap: wrap; align-items: center; gap: 10px 16px;
  margin: 0 0 20px; padding: 12px 16px; background: var(--surface);
  border: 1px solid var(--border); border-radius: var(--radius);
}
.focus-picker label { margin: 0; font-size: 0.88em; color: var(--muted); font-weight: 600; }
.focus-picker select { width: auto; min-width: 220px; max-width: 100%; flex: 1; }
.presentation-svg[data-pan-zoom] {
  overflow: hidden; cursor: grab; touch-action: none; position: relative;
  min-height: 200px;
}
.presentation-svg[data-pan-zoom]:active { cursor: grabbing; }
.pan-zoom-inner { transform-origin: 0 0; will-change: transform; }
.pan-zoom-hint { font-size: 0.82em; margin: 8px 0 0; }
.svg-legend {
  display: flex; flex-wrap: wrap; gap: 16px; font-size: 0.82em; color: var(--muted);
  margin: 0 0 12px;
}
.svg-legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend-line { display: inline-block; width: 28px; height: 0; border-top: 2px solid; vertical-align: middle; }
.legend-line--blocks { border-color: var(--err); border-top-style: dashed; }
.legend-line--parent { border-color: #64748b; }
.legend-line--then { border-color: var(--accent); border-top-style: dashed; }
.brief-hero {
  padding: 20px 24px; border-radius: var(--radius); margin: 0 0 20px;
  border: 1px solid var(--border); background: var(--surface);
}
.brief-hero--shipped { border-left: 4px solid var(--ok); }
.brief-hero--in-flight { border-left: 4px solid var(--accent); }
.brief-hero--blocked { border-left: 4px solid var(--err); background: #fffbfb; }
.brief-hero--at-risk { border-left: 4px solid #d97706; background: #fffbeb; }
.brief-hero--paused { border-left: 4px solid #78716c; }
.brief-hero .headline { margin: 8px 0 0; }
.brief-hero time { font-size: 0.82em; color: var(--muted); }
.stat-link { text-decoration: none; color: inherit; transition: border-color 0.15s; }
.stat-link:hover { border-color: var(--accent); }
.stat-link:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.mindmap-split {
  display: grid; grid-template-columns: 1fr minmax(240px, 320px); gap: 16px;
  align-items: start;
}
@media (max-width: 860px) {
  .mindmap-split { grid-template-columns: 1fr; }
}
.mindmap-split .mindmap-tree { font-size: 0.92em; max-height: 480px; overflow-y: auto; }
.mindmap-tree details { margin: 0.2em 0; }
.mindmap-tree summary { cursor: pointer; list-style: none; }
.mindmap-tree summary::-webkit-details-marker { display: none; }
.mindmap-tree summary::before { content: "▸ "; color: var(--muted); }
.mindmap-tree details[open] > summary::before { content: "▾ "; }
"""

NAV_LINKS = [
    ("/", "Projects"),
    ("/projects/archived", "Archived"),
    ("/reports/targets", "Targets"),
    ("/reports/flips", "Flips"),
    ("/reports/portfolio", "Portfolio"),
]

VIZ_PAN_ZOOM_JS = """
<script>
(function () {
  function initPanZoom(wrap) {
    var inner = wrap.querySelector('.pan-zoom-inner');
    var svg = inner ? inner.querySelector('svg') : wrap.querySelector('svg');
    if (!svg) return;
    if (!inner) {
      inner = document.createElement('div');
      inner.className = 'pan-zoom-inner';
      inner.appendChild(svg);
      wrap.appendChild(inner);
    }
    var scale = 1, tx = 0, ty = 0, dragging = false, lastX = 0, lastY = 0;
    function apply() {
      inner.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
    }
    wrap.addEventListener('wheel', function (e) {
      e.preventDefault();
      var rect = wrap.getBoundingClientRect();
      var mx = e.clientX - rect.left;
      var my = e.clientY - rect.top;
      var prev = scale;
      scale = Math.min(4, Math.max(0.25, scale * (e.deltaY < 0 ? 1.1 : 0.9)));
      tx = mx - (mx - tx) * (scale / prev);
      ty = my - (my - ty) * (scale / prev);
      apply();
    }, { passive: false });
    wrap.addEventListener('mousedown', function (e) {
      if (e.button !== 0) return;
      dragging = true;
      lastX = e.clientX;
      lastY = e.clientY;
      wrap.setAttribute('data-dragging', '1');
    });
    window.addEventListener('mousemove', function (e) {
      if (!dragging) return;
      tx += e.clientX - lastX;
      ty += e.clientY - lastY;
      lastX = e.clientX;
      lastY = e.clientY;
      apply();
    });
    window.addEventListener('mouseup', function () {
      dragging = false;
      wrap.removeAttribute('data-dragging');
    });
  }
  document.querySelectorAll('[data-pan-zoom]').forEach(initPanZoom);
})();
</script>
"""

_OVERALL_GLYPH = {
    "shipped": "✓",
    "in_flight": "→",
    "blocked": "✕",
    "at_risk": "!",
    "paused": "‖",
}


def render_page(title: str, body: str, *, error: Optional[str] = None,
                extra_head: str = "", extra_body_end: str = "",
                main_class: str = "") -> str:
    """Wrap `body` (already-HTML) in the standard layout."""
    nav = " ".join(f'<a href="{escape(href)}">{escape(text)}</a>'
                    for href, text in NAV_LINKS)
    error_html = (f'<div class="error-banner">{escape(error)}</div>'
                  if error else "")
    main_attr = f' class="{escape(main_class)}"' if main_class else ""
    return (
        f"<!DOCTYPE html>\n"
        f"<html lang='en'>\n<head>\n"
        f"<meta charset='utf-8'>\n"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        f"<title>{escape(title)}</title>\n"
        f"<style>{BASE_CSS}</style>\n"
        f"{extra_head}\n"
        f"</head>\n<body>\n"
        f"<header>{nav}</header>\n"
        f"<main{main_attr}>\n{error_html}{body}\n</main>\n"
        f"{extra_body_end}\n"
        f"</body>\n</html>\n"
    )


def link(href: str, text: str, *, css_class: str = "") -> str:
    cls = f' class="{escape(css_class)}"' if css_class else ""
    return f'<a href="{escape(href)}"{cls}>{escape(text)}</a>'


def badge(text: str, kind: str = "status-unknown") -> str:
    return f'<span class="badge badge-{escape(kind)}">{escape(text)}</span>'


def table(headers: list[str], rows: Iterable[list]) -> str:
    head_html = "".join(f"<th>{escape(h)}</th>" for h in headers)
    body_rows = []
    for row in rows:
        cells = "".join(
            f"<td>{cell if isinstance(cell, _Raw) else escape(str(cell or ''))}</td>"
            for cell in row
        )
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head_html}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>"


class _Raw(str):
    """Marker for pre-escaped HTML to pass through table()."""


def raw(html: str) -> _Raw:
    return _Raw(html)


def parents_panel(parents: list) -> str:
    """Render the parents panel for a node detail page.

    Primary-parent convention: the first entry in `parents` is the primary
    parent for narrative rendering.  Subsequent parents surface as cross-reference
    annotations.  Returns an empty string when there are no parents.
    """
    if not parents:
        return ""
    primary = parents[0]
    others = parents[1:]
    out = '<div class="parents-panel">'
    out += (
        f'<div class="primary-parent">'
        f'<strong>Primary parent:</strong> '
        f'<a href="{escape(primary)}">{escape(primary)}</a>'
        f'</div>'
    )
    if others:
        links = ", ".join(
            f'<a href="{escape(p)}">{escape(p)}</a>' for p in others
        )
        out += f'<div class="other-parents">Also satisfies: {links}</div>'
    out += "</div>"
    return out


def codemirror_edit_form(action: str, body: str, expected_revision_id: int,
                          structural_html: str = "") -> str:
    """Render the body edit form with CodeMirror wiring.

    If `structural_html` is non-empty, it's injected above the body editor as
    part of the same form — fields submit together so one POST can update
    multiple things atomically (with optimistic concurrency via
    expected_revision_id).
    """
    body_escaped = escape(body)
    return (
        f'<form method="post" action="{escape(action)}">\n'
        f'<input type="hidden" name="expected_revision_id" '
        f'value="{int(expected_revision_id)}">\n'
        f'{structural_html}\n'
        f'<label for="body">Body (markdown)</label>\n'
        f'<textarea id="body" name="body" spellcheck="false">'
        f'{body_escaped}</textarea>\n'
        f'<button type="submit">Save</button>\n'
        f'<a href="../{escape(action.rsplit("/", 1)[-1].replace("/edit", ""))}" '
        f'style="margin-left:8px;color:#555;">Cancel</a>\n'
        f'</form>\n'
        f'<link rel="stylesheet" href="/static/codemirror/codemirror.min.css">\n'
        f'<script src="/static/codemirror/codemirror.min.js"></script>\n'
        f'<script src="/static/codemirror/mode/markdown/markdown.min.js"></script>\n'
        f'<script src="/static/codemirror/addon/edit/continuelist.min.js"></script>\n'
        f'<script>\n'
        f'(function() {{\n'
        f'  var ta = document.getElementById("body");\n'
        f'  var cm = CodeMirror.fromTextArea(ta, {{\n'
        f'    mode: "markdown",\n'
        f'    lineNumbers: false,\n'
        f'    lineWrapping: true,\n'
        f'    extraKeys: {{ Enter: "newlineAndIndentContinueMarkdownList" }}\n'
        f'  }});\n'
        f'  document.addEventListener("keydown", function(e) {{\n'
        f'    if ((e.metaKey || e.ctrlKey) && e.key === "s") {{\n'
        f'      e.preventDefault();\n'
        f'      cm.save();\n'
        f'      ta.form.submit();\n'
        f'    }}\n'
        f'  }});\n'
        f'}})();\n'
        f'</script>\n'
    )


# ============================================================
# dashboard cards
# ============================================================

def dashboard_cards(stats: dict, project_id: str) -> str:
    """Render the six-card dashboard from queries.project_dashboard_stats output."""
    def _layer_rows():
        items = stats.get("nodes_per_layer") or []
        if not items:
            return '<div class="stat-row"><span class="stat-ctx">(no nodes)</span></div>'
        return "".join(
            f'<div class="stat-row"><span>{escape(r["layer"])}</span>'
            f'<span class="stat-num">{r["count"]}</span></div>'
            for r in items
        )

    def _dict_rows(d):
        if not d:
            return '<div class="stat-row"><span class="stat-ctx">(none)</span></div>'
        return "".join(
            f'<div class="stat-row"><span>{escape(str(k))}</span>'
            f'<span class="stat-num">{v}</span></div>'
            for k, v in sorted(d.items())
        )

    last_mod = stats.get("last_modified")
    if last_mod:
        last_mod_html = (
            f'<div class="stat-row"><a href="/projects/{escape(project_id)}/nodes/{escape(last_mod["node_id"])}">'
            f'{escape(last_mod["node_id"])}</a></div>'
            f'<div class="stat-row stat-ctx">{escape(last_mod.get("title") or "")}</div>'
            f'<div class="stat-row stat-ctx">{escape(last_mod.get("last_modified_at") or "")}</div>'
        )
    else:
        last_mod_html = '<div class="stat-row stat-ctx">(none)</div>'

    lv = stats.get("last_validation")
    if lv:
        last_val_html = (
            f'<div class="stat-row"><a href="/projects/{escape(project_id)}/validations/{lv["validation_id"]}">'
            f'#{lv["validation_id"]} {escape(lv.get("status") or "")}</a></div>'
            f'<div class="stat-row stat-ctx">{lv.get("issues_total") or 0} issues, '
            f'{lv.get("verdicts_run") or 0} verdicts</div>'
            f'<div class="stat-row stat-ctx">{escape(lv.get("finished_at") or "")}</div>'
        )
    else:
        last_val_html = '<div class="stat-row stat-ctx">(never run)</div>'

    rev_7d = stats.get("revisions_7d", 0)

    return (
        '<div class="stat-grid">'
        f'<div class="stat-box"><h4>Nodes per layer</h4>{_layer_rows()}</div>'
        f'<div class="stat-box"><h4>Target status</h4>{_dict_rows(stats.get("target_distribution"))}</div>'
        f'<div class="stat-box"><h4>Verdict status</h4>{_dict_rows(stats.get("verdict_distribution"))}</div>'
        f'<div class="stat-box"><h4>Last modified</h4>{last_mod_html}</div>'
        f'<div class="stat-box"><h4>Last validation</h4>{last_val_html}</div>'
        f'<div class="stat-box"><h4>Revisions (7d)</h4>'
        f'<div class="stat-row"><span class="stat-big">{rev_7d}</span></div></div>'
        '</div>'
    )


def validation_trigger_form(project_id: str) -> str:
    """Render the small trigger form that POSTs to /projects/<p>/validations."""
    return (
        f'<form class="trigger-form" method="post" '
        f'action="/projects/{escape(project_id)}/validations">'
        f'<label><input type="checkbox" name="with_verdicts" checked> with verdicts</label>'
        f'<label><input type="checkbox" name="with_targets"> with targets</label>'
        f'<button type="submit">Run validation</button>'
        f'</form>'
    )


def filter_form(action: str, fields: list) -> str:
    """Render a GET filter form for report pages.

    fields: list of (name, label, options, current_value). options is a list
    of strings; the field renders as a <select> with a leading "(all)" option.
    """
    parts = [f'<form class="trigger-form" method="get" action="{escape(action)}">']
    for name, label, options, current in fields:
        opts = ['<option value="">(all)</option>']
        for o in options:
            sel = ' selected' if str(o) == (current or "") else ''
            opts.append(f'<option value="{escape(str(o))}"{sel}>{escape(str(o))}</option>')
        parts.append(
            f'<label>{escape(label)}: '
            f'<select name="{escape(name)}">{"".join(opts)}</select></label>'
        )
    parts.append('<button type="submit">Filter</button>')
    parts.append('</form>')
    return "".join(parts)


# ============================================================
# diff helpers
# ============================================================

def unified_body_diff(prev_body: str, curr_body: str) -> str:
    """Return an HTML <pre> with a unified diff. Empty when bodies match."""
    import difflib
    prev = (prev_body or "").splitlines()
    curr = (curr_body or "").splitlines()
    if prev == curr:
        return ""
    lines = list(difflib.unified_diff(prev, curr, lineterm="", n=3,
                                        fromfile="prev", tofile="curr"))
    out = ['<pre class="diff">']
    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            cls = "diff-line-add"
        elif line.startswith("-") and not line.startswith("---"):
            cls = "diff-line-del"
        else:
            cls = "diff-line-ctx"
        out.append(f'<span class="{cls}">{escape(line)}</span>')
    out.append("</pre>")
    return "".join(out)


def revision_diff_table(change_summary) -> str:
    """Render `change_summary` (list of {field, old, new}) as a table.

    `change_summary` is None for 'created' revisions — returns empty string.
    Long values are truncated to 500 chars per cell.
    """
    if not change_summary:
        return ""
    rows = []
    for entry in change_summary:
        field = entry.get("field", "")
        old = entry.get("old")
        new = entry.get("new")
        old_str = "" if old is None else str(old)
        new_str = "" if new is None else str(new)
        if len(old_str) > 500:
            old_str = old_str[:500] + "…"
        if len(new_str) > 500:
            new_str = new_str[:500] + "…"
        rows.append(
            f"<tr><td><code>{escape(field)}</code></td>"
            f"<td class='diff-line-del'>{escape(old_str)}</td>"
            f"<td class='diff-line-add'>{escape(new_str)}</td></tr>"
        )
    return (
        '<table class="diff-table"><thead><tr>'
        '<th>Field</th><th>Old</th><th>New</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table>'
    )


# ============================================================
# structural-field editor panel
# ============================================================

def structural_fields_panel(node: dict, project_layers, current_parents,
                              current_peers) -> str:
    """Render the collapsible structural-fields panel.

    Submitted within the same form as the body editor. The target_status
    dropdown is state-machine-aware (only legal next states are offered;
    blank means 'no change').
    """
    from manifold.writes import TARGET_TRANSITIONS

    def _opts(values, current, *, blank_first=False, blank_label=""):
        out = []
        if blank_first:
            sel = ' selected' if (current in (None, "", "(none)")) else ''
            out.append(f'<option value=""{sel}>{escape(blank_label or "(none)")}</option>')
        for v in values:
            sel = ' selected' if v == current else ''
            out.append(f'<option value="{escape(v)}"{sel}>{escape(v)}</option>')
        return "".join(out)

    layer = node.get("layer") or ""
    kind = node.get("kind") or "spec"
    cur_status = node.get("target_status") or ""
    legal_next = sorted(TARGET_TRANSITIONS.get(cur_status, set()))
    mech = node.get("verdict_mechanism") or ""

    layer_opts = _opts(list(project_layers), layer)
    kind_opts = _opts(["spec", "constraint"], kind)
    target_opts = ['<option value="" selected>(no change)</option>'] + [
        f'<option value="{escape(s)}">{escape(s)}</option>' for s in legal_next
    ]
    mech_opts = _opts(["", "automated_check", "python_assertion",
                        "human_signoff", "llm_judge"], mech,
                       blank_first=False)
    # _opts treats first "" as a regular value; reformat for the (none) label
    mech_opts = "".join(
        f'<option value="{escape(m)}"{" selected" if m == mech else ""}>'
        f'{escape(m or "(none)")}</option>'
        for m in ("", "automated_check", "python_assertion",
                  "human_signoff", "llm_judge")
    )
    reason_opts = (
        '<option value="" selected>(required if editing content)</option>'
        + "".join(
            f'<option value="{escape(r)}">{escape(r)}</option>'
            for r in ("correction", "evolution", "clarification",
                      "refactor", "pivot", "other")
        )
    )

    def _input(name, value, size=60):
        return (f'<input type="text" name="{escape(name)}" '
                f'value="{escape(str(value or ""))}" size="{size}"/>')

    rows = [
        ("title", _input("title", node.get("title"))),
        ("layer", f'<select name="layer">{layer_opts}</select>'),
        ("kind", f'<select name="kind">{kind_opts}</select>'),
        ("target_status",
         f'current: <code>{escape(cur_status or "(none)")}</code> → '
         f'<select name="target_status">{"".join(target_opts)}</select>'),
        ("achieved_when", _input("target_achieved_when",
                                   node.get("target_achieved_when"))),
        ("verdict_mechanism", f'<select name="verdict_mechanism">{mech_opts}</select>'),
        ("verdict_check", _input("verdict_check", node.get("verdict_check"))),
        ("verdict_assertion", _input("verdict_assertion", node.get("verdict_assertion"))),
        ("parents", _input("parents", ", ".join(current_parents or []))),
        ("peers_depends_on", _input("peers_depends_on",
                                      ", ".join(current_peers or []))),
        ("realized_by_external", _input("realized_by_external",
                                          node.get("realized_by_external"))),
        ("change_reason",
         f'<select name="change_reason" required>{reason_opts}</select>'),
    ]
    rows_html = "".join(
        f"<tr><td>{escape(name)}</td><td>{cell}</td></tr>" for name, cell in rows
    )
    return (
        '<details style="margin-bottom: 12px"><summary><strong>Structural fields</strong> '
        '(title, layer, target, verdict, edges)</summary>'
        f'<table class="edit-fields"><tbody>{rows_html}</tbody></table>'
        '</details>'
    )


def spec_audit_body(project_id: str, flagged: list, rationale_changes: list,
                    since: Optional[str] = None) -> str:
    """Render the spec-audit page body (no <html> wrapper)."""
    since_str = escape(since) if since else "beginning of time"
    header = (
        f"<h1>Spec Audit — <a href='/projects/{escape(project_id)}'>"
        f"{escape(project_id)}</a></h1>"
        f"<p class='muted'>Since: <code>{since_str}</code></p>"
    )

    if flagged:
        flagged_rows = "".join(
            f"<tr>"
            f"<td><a href='/projects/{escape(project_id)}/nodes/{escape(r.get('node_id',''))}'>"
            f"{escape(r.get('node_id', ''))}</a></td>"
            f"<td><code>{escape(r.get('change_reason') or '(unset)')}</code></td>"
            f"<td>{escape(r.get('ts') or '')}</td>"
            f"<td>{escape((r.get('change_summary') or '')[:200])}</td>"
            f"</tr>"
            for r in flagged
        )
        flagged_section = (
            f"<h2>Flagged Revisions</h2>"
            f"<p class='muted'>{len(flagged)} revision(s) need review.</p>"
            f"<table><thead><tr>"
            f"<th>Node</th><th>Reason</th><th>Timestamp</th><th>Summary</th>"
            f"</tr></thead><tbody>{flagged_rows}</tbody></table>"
        )
    else:
        flagged_section = (
            "<h2>Flagged Revisions</h2>"
            "<p class='muted'>(none in this range)</p>"
        )

    if rationale_changes:
        rat_rows = "".join(
            f"<tr>"
            f"<td><a href='/projects/{escape(project_id)}/nodes/{escape(r.get('node_id',''))}'>"
            f"{escape(r.get('node_id', ''))}</a></td>"
            f"<td><code>{escape(r.get('change_reason') or '(unset)')}</code></td>"
            f"<td>{escape(r.get('ts') or '')}</td>"
            f"<td>{escape((r.get('change_summary') or '')[:200])}</td>"
            f"</tr>"
            for r in rationale_changes
        )
        rat_section = (
            f"<h2>Unclarified Rationale Changes</h2>"
            f"<p class='muted'>{len(rationale_changes)} revision(s) where rationale changed "
            f"without clarification or correction.</p>"
            f"<table><thead><tr>"
            f"<th>Node</th><th>Reason</th><th>Timestamp</th><th>Summary</th>"
            f"</tr></thead><tbody>{rat_rows}</tbody></table>"
        )
    else:
        rat_section = (
            "<h2>Unclarified Rationale Changes</h2>"
            "<p class='muted'>(none in this range)</p>"
        )

    return header + flagged_section + rat_section


def drift_report_body(project_id: str, report: dict) -> str:
    """Render the drift-report page body (no <html> wrapper)."""
    layer_scope = escape(report.get("layer_scope") or "")
    project_root = escape(report.get("project_root") or "(unset)")
    s = report.get("summary") or {}
    header = (
        f"<h1>Drift Report — <a href='/projects/{escape(project_id)}'>"
        f"{escape(project_id)}</a></h1>"
        f"<p class='muted'>Layer scope: <code>{layer_scope}</code> · "
        f"Project root: <code>{project_root}</code></p>"
        f"<h2>Summary</h2>"
        f"<p>{s.get('total', 0)} nodes — "
        f"{s.get('violated', 0)} violated, "
        f"{s.get('unverified', 0)} unverified, "
        f"{s.get('satisfied', 0)} satisfied</p>"
    )

    def _finding_rows(findings):
        return "".join(
            f"<tr>"
            f"<td><a href='/projects/{escape(project_id)}/nodes/{escape(f.get('node_id', ''))}'>"
            f"{escape(f.get('node_id', ''))}</a></td>"
            f"<td>{escape(f.get('title') or '')}</td>"
            f"<td>{badge(f.get('verdict_status') or 'unknown', f.get('verdict_status') or 'unknown')}</td>"
            f"<td>{escape((f.get('verdict_evidence') or '')[:200])}</td>"
            f"</tr>"
            for f in findings
        )

    violated = report.get("violated") or []
    if violated:
        violated_section = (
            f"<h2>Violated</h2>"
            f"<p class='muted'>{len(violated)} node(s) with violated verdicts.</p>"
            f"<table><thead><tr>"
            f"<th>Node</th><th>Title</th><th>Status</th><th>Evidence</th>"
            f"</tr></thead><tbody>{_finding_rows(violated)}</tbody></table>"
        )
    else:
        violated_section = (
            "<h2>Violated</h2>"
            "<p class='muted'>(none)</p>"
        )

    unverified = report.get("unverified") or []
    if unverified:
        unverified_section = (
            f"<h2>Unverified</h2>"
            f"<p class='muted'>{len(unverified)} node(s) without verification.</p>"
            f"<table><thead><tr>"
            f"<th>Node</th><th>Title</th><th>Status</th><th>Evidence</th>"
            f"</tr></thead><tbody>{_finding_rows(unverified)}</tbody></table>"
        )
    else:
        unverified_section = (
            "<h2>Unverified</h2>"
            "<p class='muted'>(none)</p>"
        )

    return header + violated_section + unverified_section


def project_viz_nav(project_id: str, *, active: str = "",
                    focus_node_id: str = "I.1") -> str:
    """Sub-nav for human presentation surfaces on a project."""
    fq = f"focus={escape(focus_node_id)}"
    tabs = [
        ("project", f"/projects/{project_id}", "Overview"),
        ("brief", f"/projects/{project_id}/brief", "Brief"),
        ("mindmap", f"/projects/{project_id}/mindmap?{fq}", "Mindmap"),
        ("decomposition", f"/projects/{project_id}/views/decomposition?{fq}", "Decomposition"),
        ("blockers", f"/projects/{project_id}/views/blockers?{fq}", "Blockers"),
        ("drift", f"/projects/{project_id}/drift-report", "Drift"),
    ]
    parts = ['<nav class="viz-nav" aria-label="Project views">']
    for key, href, label in tabs:
        cls = ' class="is-active"' if key == active else ""
        parts.append(f'<a href="{escape(href)}"{cls}>{escape(label)}</a>')
    parts.append("</nav>")
    return "".join(parts)


def focus_picker_form(form_action: str, focus_options: list[dict],
                      current_focus: str, *, extra_hidden: Optional[dict] = None) -> str:
    """GET form to change focus node; auto-submits on select change."""
    if not focus_options:
        return ""
    opts = []
    for opt in focus_options:
        nid = opt.get("node_id") or ""
        title = opt.get("title") or nid
        layer = opt.get("layer") or ""
        label = f"{nid} — {title}" if title != nid else nid
        if layer:
            label = f"[{layer}] {label}"
        selected = ' selected' if nid == current_focus else ""
        opts.append(f'<option value="{escape(nid)}"{selected}>{escape(label)}</option>')
    hidden = ""
    if extra_hidden:
        for k, v in extra_hidden.items():
            if v is not None:
                hidden += f'<input type="hidden" name="{escape(k)}" value="{escape(str(v))}">'
    return (
        f'<form class="focus-picker" method="get" action="{escape(form_action)}">'
        f'{hidden}'
        f'<label for="focus-select">Focus node</label>'
        f'<select id="focus-select" name="focus" onchange="this.form.submit()">'
        f'{"".join(opts)}'
        f'</select>'
        f'</form>'
    )


def _diagram_svg_legend() -> str:
    return (
        '<div class="svg-legend" aria-label="Edge legend">'
        '<span><span class="legend-line legend-line--blocks"></span> blocks</span>'
        '<span><span class="legend-line legend-line--parent"></span> parent</span>'
        '<span><span class="legend-line legend-line--then"></span> then</span>'
        '</div>'
    )


def _svg_pan_zoom_block(svg_html: str, *, legend: str = "") -> str:
    return (
        f"{legend}"
        f"<div class='presentation-svg' data-pan-zoom tabindex='0' "
        f"role='region' aria-label='Pan and zoom diagram'>"
        f"<div class='pan-zoom-inner'>{svg_html}</div>"
        f"</div>"
        f"<p class='muted pan-zoom-hint'>Scroll to zoom · drag to pan</p>"
    )


def _brief_stat_grid(view: dict) -> str:
    shipped = len(view.get("shipped") or [])
    in_flight = len(view.get("in_flight") or [])
    blocked = len(view.get("blocked") or [])
    at_risk = len(view.get("at_risk") or [])
    return (
        f'<div class="stat-grid">'
        f'<a href="#section-shipped" class="stat-box stat-link">'
        f'<h4>Shipped</h4><div class="stat-big">{shipped}</div></a>'
        f'<a href="#section-in-flight" class="stat-box stat-link">'
        f'<h4>In flight</h4><div class="stat-big">{in_flight}</div></a>'
        f'<a href="#section-blocked" class="stat-box stat-link">'
        f'<h4>Blocked</h4><div class="stat-big">{blocked}</div></a>'
        f'<a href="#section-at-risk" class="stat-box stat-link">'
        f'<h4>At risk</h4><div class="stat-big">{at_risk}</div></a>'
        f"</div>"
    )


def _brief_hero_banner(view: dict) -> str:
    overall = view.get("overall") or {}
    status = overall.get("status", "in_flight")
    headline = escape(overall.get("headline") or "")
    generated = escape(view.get("generated_at") or "")
    css = status.replace("_", "-")
    time_html = f'<time datetime="{generated}">Updated {generated[:19]}</time>' if generated else ""
    return (
        f'<div class="brief-hero brief-hero--{css}" role="status">'
        f'{_overall_pill(status)}'
        f'<p class="headline">{headline}</p>'
        f'{time_html}'
        f'</div>'
    )


def _mindmap_tree_html(node: Optional[dict], *, depth: int = 0) -> str:
    if not node:
        return "<p class='muted'>(empty tree)</p>"

    def render(n: dict, d: int) -> str:
        label = escape(n.get("label") or n.get("node_ref") or "")
        status = n.get("status") or ""
        badge_html = f' {badge(status, status)}' if status else ""
        children = n.get("children") or []
        if not children:
            return f"<li><strong>{label}</strong>{badge_html}</li>"
        inner = "".join(render(c, d + 1) for c in children)
        if d >= 1:
            open_attr = " open" if d < 2 else ""
            return (
                f"<li><details{open_attr}>"
                f"<summary><strong>{label}</strong>{badge_html}</summary>"
                f"<ul>{inner}</ul></details></li>"
            )
        return f"<li><strong>{label}</strong>{badge_html}<ul>{inner}</ul></li>"

    return f"<ul class='mindmap-tree'>{render(node, depth)}</ul>"


def presentation_view_body(project_id: str, view: dict, mermaid_source: str,
                           *, view_label: str, svg_html: str = "",
                           focus_options: Optional[list] = None,
                           form_action: str = "",
                           current_focus: str = "") -> str:
    """HTML body for diagram or mindmap presentation views."""
    generated = escape(view.get("generated_at") or "")
    focus = escape(view.get("focus_node_id") or current_focus or "—")
    focus_id = view.get("focus_node_id") or current_focus or "I.1"
    truncated = view.get("truncated")
    warnings = ", ".join(view.get("warnings") or [])

    meta_rows = []
    if view.get("view_id"):
        meta_rows.append(["View id", f"<code>{escape(view['view_id'])}</code>"])
    if view.get("view_kind") == "diagram":
        meta_rows.append(["Diagram type", escape(view.get("diagram_type") or "")])
    else:
        meta_rows.append(["Mindmap type", escape(view.get("mindmap_type") or "")])
    meta_rows.extend([
        ["Generated", f"<code>{generated}</code>"],
        ["Focus node", f"<code>{focus}</code>"],
        ["Nodes", str(len(view.get("nodes") or []))],
    ])
    if truncated:
        meta_rows.append(["Truncated", "yes — drill into a narrower focus"])
    if warnings:
        meta_rows.append(["Warnings", escape(warnings)])

    meta = table(["Field", "Value"], meta_rows)
    svg_block = ""
    tree_block = ""
    is_mindmap = view.get("view_kind") == "mindmap"
    if svg_html:
        legend = "" if is_mindmap else _diagram_svg_legend()
        svg_inner = _svg_pan_zoom_block(svg_html, legend=legend)
        if is_mindmap:
            tree_html = _mindmap_tree_html(view.get("tree"))
            svg_block = (
                f"<div class='viz-card'>"
                f"<h2>Visual</h2>"
                f"<div class='mindmap-split'>"
                f"<div>{svg_inner}</div>"
                f"<div><h3>Outline</h3>{tree_html}</div>"
                f"</div>"
                f"</div>"
            )
        else:
            svg_block = (
                f"<div class='viz-card'>"
                f"<h2>Visual</h2>"
                f"{svg_inner}"
                f"</div>"
            )
    elif is_mindmap:
        tree_block = (
            f"<div class='viz-card'><h2>Tree</h2>{_mindmap_tree_html(view.get('tree'))}</div>"
        )

    mermaid_block = (
        f"<details class='presentation-export'>"
        f"<summary>Mermaid source (export to GitHub / docs)</summary>"
        f"<pre>{escape(mermaid_source.rstrip())}</pre>"
        f"</details>"
    )

    nav_key = "mindmap" if is_mindmap else (
        view.get("diagram_type") or "diagram"
    )
    if nav_key not in ("brief", "mindmap", "decomposition", "blockers", "project", "drift"):
        nav_key = "decomposition" if view.get("diagram_type") == "decomposition" else "blockers"

    json_block = (
        f"<details class='json-collapse'><summary>View JSON</summary>"
        f"<pre><code>{escape(json.dumps(view, indent=2))}</code></pre></details>"
    )

    picker = ""
    if form_action and focus_options:
        picker = focus_picker_form(form_action, focus_options, focus_id)

    return (
        f"<div class='page-hero'>"
        f"<h1>{escape(view_label)}</h1>"
        f"<p class='subtitle'><code>{escape(project_id)}</code> · focus <code>{focus}</code></p>"
        f"</div>"
        f"{project_viz_nav(project_id, active=nav_key, focus_node_id=focus_id)}"
        f"{picker}"
        f"<div class='viz-card'>{meta}</div>"
        f"{svg_block}"
        f"{tree_block}"
        f"{mermaid_block}"
        f"{json_block}"
    )


def render_presentation_page(title: str, body: str, *, with_pan_zoom: bool = True) -> str:
    """Presentation pages use server SVG — no external diagram runtime."""
    extra = VIZ_PAN_ZOOM_JS if with_pan_zoom else ""
    return render_page(title, body, main_class="page-wide", extra_body_end=extra)


def _overall_pill(status: str) -> str:
    labels = {
        "shipped": ("Shipped", "shipped"),
        "in_flight": ("In flight", "in-flight"),
        "blocked": ("Blocked", "blocked"),
        "at_risk": ("At risk", "at-risk"),
        "paused": ("Paused", "paused"),
    }
    text, css = labels.get(status, (status.replace("_", " ").title(), "paused"))
    glyph = _OVERALL_GLYPH.get(status, "·")
    return (
        f'<span class="pill pill--{css}" aria-label="{escape(text)}">'
        f'<span class="status-glyph" aria-hidden="true">{glyph}</span> '
        f'{escape(text)}</span>'
    )


def _default_viz_focus(view: dict) -> str:
    blocked = view.get("blocked") or []
    if blocked:
        return blocked[0].get("node_id") or "I.1"
    return "I.1"


def _brief_item_list(items: list, *, show_blocked_by: bool = False) -> str:
    if not items:
        return "<p class='muted'>(none)</p>"
    parts = ["<ul class='brief-list'>"]
    for item in items:
        ref = escape(item.get("node_ref") or "")
        pid, nid = item.get("project_id", ""), item.get("node_id", "")
        label = escape(item.get("label") or nid)
        link = (
            f"<a href='/projects/{escape(pid)}/nodes/{escape(nid)}'>{label}</a>"
            if pid and nid else label
        )
        extra = ""
        if show_blocked_by and item.get("blocked_by"):
            blockers = ", ".join(
                escape(b.get("label") or b.get("node_ref", ""))
                for b in item["blocked_by"]
            )
            extra = f" <span class='muted'>← blocked by {blockers}</span>"
        elif item.get("reason"):
            extra = f" <span class='muted'>({escape(item['reason'])})</span>"
        elif item.get("shipped_at"):
            extra = f" <span class='muted'>{escape(item['shipped_at'][:10])}</span>"
        parts.append(f"<li>{link} <code class='muted'>{ref}</code>{extra}</li>")
    parts.append("</ul>")
    return "".join(parts)


def status_brief_body(project_id: str, view: dict, *, detail: str = "standard") -> str:
    """HTML body for status-brief (Topic K2). detail: summary | standard | full."""
    detail = detail if detail in ("summary", "standard", "full") else "standard"
    label = escape(view.get("project_label") or project_id)
    overall = view.get("overall") or {}
    status = overall.get("status", "in_flight")
    headline = escape(overall.get("headline") or "")
    generated = escape(view.get("generated_at") or "")

    stale_html = ""
    if view.get("stale_warning"):
        stale_html = (
            f"<div class='brief-stale'>{escape(view['stale_warning'])}</div>"
        )

    theme = view.get("theme_link")
    theme_html = ""
    if theme:
        theme_html = (
            f"<p class='muted'>Linked to theme "
            f"<a href='/reports/portfolio'>{escape(theme.get('label', ''))}</a> "
            f"(<code>{escape(theme.get('portfolio_id', ''))}</code>)</p>"
        )

    drift = view.get("drift_summary") or {}
    drift_link = escape(drift.get("link") or f"/projects/{project_id}/drift-report")

    meta = (
        f"<dl>"
        f"<dt>Generated</dt><dd><code>{generated}</code></dd>"
        f"<dt>Team</dt><dd>{escape(view.get('team') or project_id)}</dd>"
        f"<dt>Drift</dt><dd>{drift.get('high', 0)} high / "
        f"{drift.get('medium', 0)} medium / {drift.get('low', 0)} low — "
        f"<a href='{drift_link}'>drift report</a></dd>"
        f"</dl>"
    )

    lod_note = (
        f"<p class='muted'>Detail: "
        f"<a href='?detail=summary'>summary</a> · "
        f"<a href='?detail=standard'>standard</a> · "
        f"<a href='?detail=full'>full</a></p>"
    )

    changes_class = "" if detail in ("standard", "full") else "lod-hidden"
    risk_class = "" if detail == "full" else ("lod-hidden" if detail == "summary" else "")
    shipped_class = "" if detail != "summary" else "lod-hidden"

    sections = [
        f"<div class='viz-card brief-section {shipped_class}' id='section-shipped'>"
        f"<h2>Shipped</h2>{_brief_item_list(view.get('shipped') or [])}</div>",
        f"<div class='viz-card brief-section' id='section-in-flight'>"
        f"<h2>In flight</h2>{_brief_item_list(view.get('in_flight') or [])}</div>",
        f"<div class='viz-card brief-section' id='section-blocked'>"
        f"<h2>Blocked</h2>{_brief_item_list(view.get('blocked') or [], show_blocked_by=True)}</div>",
        f"<div class='viz-card brief-section {risk_class}' id='section-at-risk'>"
        f"<h2>At risk</h2>{_brief_item_list(view.get('at_risk') or [])}</div>",
    ]

    changes = view.get("changes_since") or []
    changes_html = ""
    if changes:
        rows = "".join(
            f"<li><code>{escape(c.get('when', '')[:19])}</code> "
            f"{escape(c.get('what', ''))} "
            f"<span class='muted'>({escape(c.get('who', ''))})</span></li>"
            for c in changes
        )
        changes_html = (
            f"<div class='viz-card brief-section {changes_class}'>"
            f"<h2>Recent changes</h2><ul class='brief-list'>{rows}</ul></div>"
        )

    json_block = ""
    if detail == "full":
        json_block = (
            f"<details class='json-collapse'><summary>View JSON</summary>"
            f"<pre><code>{escape(json.dumps(view, indent=2))}</code></pre></details>"
        )

    viz_focus = _default_viz_focus(view)

    return (
        f"<div class='page-hero'>"
        f"<h1>Status brief — {label}</h1>"
        f"<p class='subtitle'><code>{escape(project_id)}</code></p>"
        f"</div>"
        f"{project_viz_nav(project_id, active='brief', focus_node_id=viz_focus)}"
        f"{theme_html}"
        f"{lod_note}"
        f"{stale_html}"
        f"{_brief_hero_banner(view)}"
        f"{_brief_stat_grid(view)}"
        f"<div class='viz-card brief-meta'>{meta}</div>"
        f"{''.join(sections)}"
        f"{changes_html}"
        f"{json_block}"
    )


# ============================================================
# rationale section + change_reason badge
# ============================================================

def rationale_section(node: dict) -> str:
    """Render a collapsible <details> element for node.rationale and
    node.alternatives_considered.

    Returns an empty string when both fields are absent or empty.
    The element is OPEN by default so the content is immediately visible.
    """
    rationale = (node.get("rationale") or "").strip()
    alternatives = (node.get("alternatives_considered") or "").strip()
    if not rationale and not alternatives:
        return ""
    parts = ['<details open class="rationale-section">',
             '<summary><strong>Rationale &amp; Alternatives</strong></summary>']
    if rationale:
        parts.append(f'<p><strong>Rationale:</strong> {escape(rationale)}</p>')
    if alternatives:
        parts.append(
            f'<p><strong>Alternatives considered:</strong> {escape(alternatives)}</p>'
        )
    parts.append('</details>')
    return "\n".join(parts)


def change_reason_badge(reason: Optional[str]) -> str:
    """Render a small inline badge for a revision's change_reason value.

    Returns an empty string for None or empty reason.
    Known reasons map to distinct CSS classes:
      pivot          → red  (.reason-pivot)
      drift          → red  (.reason-drift, legacy stored value)
      clarification/ correction → green (.reason-clarification / .reason-correction)
      evolution / refactor → neutral blue (.reason-evolution / .reason-refactor)
      other        → grey (.reason-other)
    Unknown values fall back to just the base .reason-badge class.
    """
    if not reason:
        return ""
    known_extra = {
        "pivot", "drift", "clarification", "correction",
        "evolution", "refactor", "other",
    }
    extra_class = f" reason-{escape(reason)}" if reason in known_extra else ""
    return (
        f'<span class="reason-badge{extra_class}">'
        f'{escape(reason)}</span>'
    )


def validation_detail_body(project_id: str, validation: dict, verdicts: list,
                             issues: Optional[list] = None) -> str:
    """Render the validation detail page body (no <html> wrapper)."""
    val_id = validation["validation_id"]
    summary = (
        f'<h1>Validation #{val_id} — '
        f'<a href="/projects/{escape(project_id)}">{escape(project_id)}</a></h1>'
        f'<table><tbody>'
        f'<tr><th>Status</th><td><code>{escape(validation.get("status") or "")}</code></td></tr>'
        f'<tr><th>Started</th><td>{escape(validation.get("started_at") or "")}</td></tr>'
        f'<tr><th>Finished</th><td>{escape(validation.get("finished_at") or "")}</td></tr>'
        f'<tr><th>Nodes total</th><td>{validation.get("nodes_total") or 0}</td></tr>'
        f'<tr><th>Issues total</th><td>{validation.get("issues_total") or 0}</td></tr>'
        f'<tr><th>Verdicts run</th><td>{validation.get("verdicts_run") or 0}</td></tr>'
        f'</tbody></table>'
    )

    issues_html = ""
    if issues is not None:
        if issues:
            rows = "".join(
                f'<tr><td><code>{escape(i.get("kind",""))}</code></td>'
                f'<td>{escape(i.get("node") or "")}</td>'
                f'<td>{escape(i.get("message",""))}</td></tr>'
                for i in issues
            )
            issues_html = (
                '<h2>Issues</h2>'
                '<table><thead><tr><th>Kind</th><th>Node</th><th>Message</th></tr></thead>'
                f'<tbody>{rows}</tbody></table>'
            )
        else:
            issues_html = '<h2>Issues</h2><p class="muted">(no structural issues)</p>'

    if verdicts:
        rows = "".join(
            f'<tr><td><a href="/projects/{escape(project_id)}/nodes/{escape(v.get("node_id",""))}">'
            f'{escape(v.get("node_id") or "")}</a></td>'
            f'<td><code>{escape(v.get("mechanism") or "")}</code></td>'
            f'<td>{badge(v.get("status") or "unknown", v.get("status") or "unknown")}</td>'
            f'<td>{escape(v.get("source") or "")}</td>'
            f'<td>{escape((v.get("evidence_ref") or "")[:200])}</td></tr>'
            for v in verdicts
        )
        verdicts_html = (
            '<h2>Verdicts</h2>'
            '<table><thead><tr><th>Node</th><th>Mechanism</th><th>Status</th>'
            '<th>Source</th><th>Evidence</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
        )
    else:
        verdicts_html = '<h2>Verdicts</h2><p class="muted">(verdicts not run)</p>'

    return summary + issues_html + verdicts_html
