"""Formatters for presentation view-models (Topic K)."""
from __future__ import annotations

import re


def _safe_id(node_ref: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", node_ref)


def _label(title: str, node_ref: str) -> str:
    text = (title or node_ref).replace('"', "'")
    if len(text) > 40:
        text = text[:37] + "..."
    return text


def format_mermaid_flowchart(view: dict) -> str:
    """Diagram view-model → Mermaid flowchart LR source."""
    lines = ["flowchart LR"]
    for node in view.get("nodes") or []:
        nid = _safe_id(node["node_ref"])
        lines.append(f'  {nid}["{_label(node.get("title", ""), node["node_ref"])}"]')
    for edge in view.get("edges") or []:
        src = _safe_id(edge["from_ref"])
        dst = _safe_id(edge["to_ref"])
        arrow = "-.->|" + edge.get("kind", "") + "|" if edge.get("kind") else "-->"
        if edge.get("kind") == "blocks":
            lines.append(f"  {src} --> {dst}")
        else:
            lines.append(f"  {src} --> {dst}")
    if view.get("truncated"):
        lines.append('  trunc["… truncated"]')
    return "\n".join(lines) + "\n"


def _mindmap_lines(node: dict, depth: int = 0) -> list[str]:
    indent = "  " * depth
    label = _label(node.get("label", ""), node.get("node_ref", ""))
    lines = [f"{indent}{label}"]
    for child in node.get("children") or []:
        lines.extend(_mindmap_lines(child, depth + 1))
    return lines


def format_mermaid_mindmap(view: dict) -> str:
    """Mindmap view-model → Mermaid mindmap source."""
    tree = view.get("tree")
    if not tree:
        return "mindmap\n  root((empty))\n"
    lines = ["mindmap"]

    def add_node(node: dict, depth: int) -> None:
        pad = "  " * depth
        label = _label(node.get("label", ""), node.get("node_ref", ""))
        if depth == 0:
            lines.append(f"{pad}root(({label}))")
        else:
            lines.append(f"{pad}{label}")
        for child in node.get("children") or []:
            add_node(child, depth + 1)

    add_node(tree, 0)
    if view.get("truncated"):
        lines.append("    … truncated")
    return "\n".join(lines) + "\n"


def format_markdown(view: dict) -> str:
    """View-model → markdown export."""
    if view.get("view_kind") == "status_brief":
        return format_status_brief_markdown(view)
    kind = view.get("view_kind", "diagram")
    pid = view.get("project_id", "")
    generated = view.get("generated_at", "")
    if kind == "mindmap":
        mermaid = format_mermaid_mindmap(view)
        title = f"Mindmap — `{pid}`"
    else:
        dtype = view.get("diagram_type", "diagram")
        mermaid = format_mermaid_flowchart(view)
        title = f"Diagram ({dtype}) — `{pid}`"

    lines = [
        f"# {title}",
        "",
        f"- **Generated:** {generated}",
        f"- **Focus:** `{view.get('focus_node_id') or '—'}`",
    ]
    if view.get("truncated"):
        lines.append("- **Note:** subgraph truncated (node cap)")
    if view.get("warnings"):
        lines.append(f"- **Warnings:** {', '.join(view['warnings'])}")
    lines += ["", "```mermaid", mermaid.rstrip(), "```", ""]
    return "\n".join(lines)


def format_terminal(view: dict) -> str:
    """Plain-text summary for CLI."""
    if view.get("view_kind") == "status_brief":
        return format_status_brief_terminal(view)
    kind = view.get("view_kind", "diagram")
    lines = [
        f"Presentation {kind} — {view.get('project_id', '')}",
        f"  generated_at: {view.get('generated_at', '')}",
        f"  nodes: {len(view.get('nodes') or [])}",
    ]
    if kind == "diagram":
        lines.append(f"  diagram_type: {view.get('diagram_type', '')}")
        lines.append(f"  edges: {len(view.get('edges') or [])}")
    else:
        lines.append(f"  mindmap_type: {view.get('mindmap_type', '')}")
    if view.get("truncated"):
        lines.append("  truncated: yes")
    if view.get("warnings"):
        lines.append(f"  warnings: {', '.join(view['warnings'])}")
    lines.append("")
    lines.append(format_mermaid_mindmap(view) if kind == "mindmap"
                 else format_mermaid_flowchart(view))
    return "\n".join(lines) + "\n"


_OVERALL_LABELS = {
    "shipped": "Shipped",
    "in_flight": "In flight",
    "blocked": "Blocked",
    "at_risk": "At risk",
    "paused": "Paused",
}


def format_status_brief_markdown(view: dict) -> str:
    """Status-brief view-model → GFM for CI / PR summaries."""
    pid = view.get("project_id", "")
    label = view.get("project_label") or pid
    overall = view.get("overall") or {}
    status = overall.get("status", "in_flight")
    lines = [
        f"# Status brief — {label}",
        "",
        f"**Overall:** {_OVERALL_LABELS.get(status, status)} — "
        f"{overall.get('headline', '')}",
        "",
        f"- **Generated:** {view.get('generated_at', '')}",
        f"- **Project:** `{pid}`",
    ]
    if view.get("stale_warning"):
        lines.append(f"- **Stale:** {view['stale_warning']}")
    theme = view.get("theme_link")
    if theme:
        lines.append(f"- **Theme:** {theme.get('label', '')} (`{theme.get('portfolio_id', '')}`)")
    drift = view.get("drift_summary") or {}
    lines.append(
        f"- **Drift:** {drift.get('high', 0)} high / "
        f"{drift.get('medium', 0)} medium / {drift.get('low', 0)} low "
        f"([report]({drift.get('link', '')}))"
    )
    lines.append("")

    def _section(title: str, items: list[dict], extra_fn=None) -> None:
        if not items:
            return
        lines.append(f"## {title}")
        lines.append("")
        for item in items:
            ref = item.get("node_ref", "")
            row = f"- **{item.get('label', ref)}** (`{ref}`)"
            if extra_fn:
                row += extra_fn(item)
            lines.append(row)
        lines.append("")

    _section("Shipped", view.get("shipped") or [],
             lambda i: f" — {i.get('shipped_at', '')}" if i.get("shipped_at") else "")
    _section("In flight", view.get("in_flight") or [])
    _section("Blocked", view.get("blocked") or [],
             lambda i: " — blocked by " + ", ".join(
                 b.get("label", b.get("node_ref", "")) for b in (i.get("blocked_by") or [])
             ) if i.get("blocked_by") else "")
    _section("At risk", view.get("at_risk") or [],
             lambda i: f" ({i.get('reason', '')})" if i.get("reason") else "")

    changes = view.get("changes_since") or []
    if changes:
        lines.append("## Recent changes")
        lines.append("")
        for ch in changes:
            lines.append(f"- {ch.get('when', '')}: {ch.get('what', '')} ({ch.get('who', '')})")
        lines.append("")

    return "\n".join(lines)


def format_status_brief_terminal(view: dict) -> str:
    """Status-brief view-model → plain text."""
    overall = view.get("overall") or {}
    lines = [
        f"Status brief — {view.get('project_label') or view.get('project_id', '')}",
        f"  generated_at: {view.get('generated_at', '')}",
        f"  overall: {overall.get('status', '')} — {overall.get('headline', '')}",
    ]
    if view.get("stale_warning"):
        lines.append(f"  stale: {view['stale_warning']}")
    for key, title in (
        ("shipped", "shipped"),
        ("in_flight", "in_flight"),
        ("blocked", "blocked"),
        ("at_risk", "at_risk"),
    ):
        items = view.get(key) or []
        if items:
            lines.append(f"  {title}: {len(items)}")
            for item in items[:5]:
                lines.append(f"    - {item.get('label', item.get('node_ref', ''))}")
    return "\n".join(lines) + "\n"
