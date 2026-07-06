"""Server-side SVG renderers for presentation view-models (no CDN / no Mermaid runtime)."""
from __future__ import annotations

import html
import math
from typing import Optional

_STATUS_STROKE = {
    "achieved": "#15803d",
    "in_progress": "#1d4ed8",
    "planned": "#94a3b8",
    "deferred": "#a8a29e",
    "unset": "#d6d3d1",
}
_STATUS_FILL = {
    "achieved": "#f0fdf4",
    "in_progress": "#eff6ff",
    "planned": "#fafaf9",
    "deferred": "#f5f5f4",
    "unset": "#ffffff",
}
_STATUS_GLYPH = {
    "achieved": "✓",
    "in_progress": "◐",
    "planned": "○",
    "deferred": "◌",
    "unset": "·",
}
_EDGE_STYLE = {
    "blocks": ("#b91c1c", "6 4", "#b91c1c", 2.0),
    "parent": ("#64748b", "", "#64748b", 1.5),
    "then": ("#1d4ed8", "4 3", "#1d4ed8", 1.5),
}


def render_view_svg(view: dict) -> str:
    if view.get("view_kind") == "mindmap":
        return render_mindmap_svg(view)
    return render_diagram_svg(view)


def _esc(text: str) -> str:
    return html.escape(text or "")


def _status_glyph(node: dict) -> str:
    status = (node.get("status") or node.get("target_status") or "planned").lower()
    return _STATUS_GLYPH.get(status, "·")


def _node_label(node: dict, *, with_glyph: bool = True) -> str:
    title = (node.get("title") or node.get("label") or node.get("node_id") or "").strip()
    if len(title) > 40:
        title = title[:37] + "..."
    ref = node.get("node_ref") or ""
    base = title if title else ref
    if with_glyph and base:
        return f"{_status_glyph(node)} {base}"
    return base


def _edge_stroke(kind: str) -> tuple[str, str, float]:
    stroke, dash, _marker, sw = _EDGE_STYLE.get(kind, ("#1d4ed8", "", "#1d4ed8", 1.5))
    return stroke, dash, sw


def _status_style(node: dict, *, focus: bool = False) -> tuple[str, str, float]:
    status = (node.get("status") or node.get("target_status") or "planned").lower()
    stroke = _STATUS_STROKE.get(status, "#64748b")
    fill = _STATUS_FILL.get(status, "#ffffff")
    width = 2.5 if focus else 1.5
    if focus:
        stroke = "#1d4ed8"
        fill = "#eff6ff"
        width = 2.5
    return stroke, fill, width


def render_diagram_svg(view: dict, *, width: int = 760, height: int = 420) -> str:
    """Layered left-to-right flowchart SVG from nodes + edges."""
    nodes = view.get("nodes") or []
    edges = view.get("edges") or []
    if not nodes:
        return _empty_svg(width, height, "No nodes")

    focus_ref = None
    focus_id = view.get("focus_node_id")
    pid = view.get("project_id") or ""
    if focus_id:
        focus_ref = f"{pid}/{focus_id}" if "/" not in focus_id else focus_id

    by_ref = {n["node_ref"]: n for n in nodes}
    if focus_id and focus_ref not in by_ref:
        for n in nodes:
            if n.get("node_id") == focus_id:
                focus_ref = n["node_ref"]
                break

    sources = {e["from_ref"] for e in edges}
    sinks = {e["to_ref"] for e in edges}
    left_nodes = [n for n in nodes if n["node_ref"] in sources and n["node_ref"] not in sinks]
    if not left_nodes:
        left_nodes = [n for n in nodes if n["node_ref"] != focus_ref]
    right_nodes = [n for n in nodes if focus_ref and n["node_ref"] == focus_ref]
    if not right_nodes:
        right_nodes = [n for n in nodes if n["node_ref"] in sinks and n["node_ref"] not in sources]
    middle_nodes = [
        n for n in nodes
        if n not in left_nodes and n not in right_nodes
    ]

    ordered = left_nodes + middle_nodes + right_nodes
    if not ordered:
        ordered = nodes

    box_w, box_h, gap_y, margin = 220, 48, 14, 28
    positions: dict[str, tuple[float, float]] = {}

    if focus_ref and focus_ref in by_ref:
        others = [n for n in ordered if n["node_ref"] != focus_ref]
        stack_h = margin * 2 + max(1, len(others)) * (box_h + gap_y)
        height = max(height, stack_h)
        positions[focus_ref] = (width - margin - box_w, height / 2 - box_h / 2)
        for i, n in enumerate(others):
            positions[n["node_ref"]] = (
                margin,
                margin + i * (box_h + gap_y),
            )
    else:
        cols = max(1, min(3, len(ordered)))
        per_col = math.ceil(len(ordered) / cols)
        stack_h = margin * 2 + per_col * (box_h + gap_y)
        height = max(height, stack_h)
        for i, n in enumerate(ordered):
            col = i // per_col
            row = i % per_col
            positions[n["node_ref"]] = (
                margin + col * (box_w + 48),
                margin + row * (box_h + gap_y),
            )
        width = max(width, margin * 2 + cols * (box_w + 48))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="Diagram">',
        '<defs>'
        '<marker id="arrow-blocks" markerWidth="8" markerHeight="8" refX="7" refY="3" '
        'orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#b91c1c"/></marker>'
        '<marker id="arrow-parent" markerWidth="8" markerHeight="8" refX="7" refY="3" '
        'orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#64748b"/></marker>'
        '<marker id="arrow-then" markerWidth="8" markerHeight="8" refX="7" refY="3" '
        'orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#1d4ed8"/></marker>'
        '<marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" '
        'orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#1d4ed8"/></marker>'
        '</defs>',
    ]

    for ref, (x, y) in positions.items():
        node = by_ref.get(ref, {})
        label = _esc(_node_label(node))
        sub = _esc(node.get("node_ref", ""))
        is_focus = ref == focus_ref
        stroke, fill, sw = _status_style(node, focus=is_focus)
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{box_w}" height="{box_h}" '
            f'rx="8" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
        parts.append(
            f'<text x="{x + 12:.1f}" y="{y + 20:.1f}" font-size="13" font-weight="600" '
            f'font-family="system-ui,sans-serif" fill="#1a1814">{label}</text>'
        )
        parts.append(
            f'<text x="{x + 12:.1f}" y="{y + 38:.1f}" font-size="10" '
            f'font-family="monospace" fill="#6b6560">{sub}</text>'
        )

    for edge in edges:
        fr, tr = edge.get("from_ref"), edge.get("to_ref")
        if fr not in positions or tr not in positions:
            continue
        x1, y1 = positions[fr]
        x2, y2 = positions[tr]
        sx = x1 + box_w
        sy = y1 + box_h / 2
        ex = x2
        ey = y2 + box_h / 2
        mx = (sx + ex) / 2
        kind = edge.get("kind") or "then"
        stroke, dash, sw = _edge_stroke(kind)
        marker_id = {"blocks": "arrow-blocks", "parent": "arrow-parent"}.get(kind, "arrow-then")
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(
            f'<path d="M{sx:.1f},{sy:.1f} C{mx:.1f},{sy:.1f} {mx:.1f},{ey:.1f} {ex:.1f},{ey:.1f}" '
            f'fill="none" stroke="{stroke}" stroke-width="{sw}"{dash_attr} '
            f'marker-end="url(#{marker_id})" opacity="0.9"/>'
        )

    if view.get("truncated"):
        parts.append(
            f'<text x="{margin}" y="{height - 14}" font-size="11" fill="#b45309">'
            f'… truncated (narrow focus or raise max_nodes)</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def render_mindmap_svg(view: dict, *, width: int = 760, height: int = 420) -> str:
    tree = view.get("tree")
    if not tree:
        return _empty_svg(width, height, "Empty mindmap")

    margin = 28
    row_h = 40
    col_w = 200
    positions: list[tuple[float, float, dict]] = []
    max_depth = [0]

    def layout(node: dict, depth: int, y_index: list[int]) -> None:
        max_depth[0] = max(max_depth[0], depth)
        y = margin + y_index[0] * row_h
        y_index[0] += 1
        x = margin + depth * col_w
        positions.append((x, y, node))
        for child in node.get("children") or []:
            layout(child, depth + 1, y_index)

    layout(tree, 0, [0])
    h = max(height, margin * 2 + len(positions) * row_h)
    width = max(width, margin * 2 + (max_depth[0] + 1) * col_w + 80)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {h}" '
        f'role="img" aria-label="Mindmap">',
    ]

    by_ref = {p[2].get("node_ref"): (p[0], p[1]) for p in positions}
    box_w = col_w - 24

    def draw_edges(node: dict, px: float, py: float) -> None:
        for child in node.get("children") or []:
            cref = child.get("node_ref")
            if cref in by_ref:
                cx, cy = by_ref[cref]
                parts.append(
                    f'<path d="M{px + box_w:.1f},{py + 16:.1f} '
                    f'C{px + box_w + 24:.1f},{py + 16:.1f} '
                    f'{cx - 24:.1f},{cy + 16:.1f} {cx:.1f},{cy + 16:.1f}" '
                    f'fill="none" stroke="#cbd5e1" stroke-width="1.5"/>'
                )
                draw_edges(child, cx, cy)

    for x, y, node in positions:
        label = _esc(_node_label(node))
        stroke, fill, sw = _status_style(node, focus=(x == margin))
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{box_w}" height="32" rx="6" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
        parts.append(
            f'<text x="{x + 10:.1f}" y="{y + 20:.1f}" font-size="12" font-weight="500" '
            f'font-family="system-ui,sans-serif" fill="#1a1814">{label}</text>'
        )

    if tree.get("node_ref") in by_ref:
        tx, ty = by_ref[tree["node_ref"]]
        draw_edges(tree, tx, ty)

    if view.get("truncated"):
        parts.append(
            f'<text x="{margin}" y="{h - 14}" font-size="11" fill="#b45309">'
            f'… truncated</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def _empty_svg(width: int, height: int, message: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
        f'<text x="24" y="48" font-size="14" fill="#6b6560">{_esc(message)}</text>'
        f"</svg>"
    )
