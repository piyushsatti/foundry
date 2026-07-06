"""Formatters for portfolio-report (Topic H)."""


def format_terminal(report: dict) -> str:
    lines = ["Portfolio Report"]
    themes = report.get("themes") or []
    if not themes:
        lines.append("  (no themes — register project 'portfolio' and add theme nodes)")
        return "\n".join(lines) + "\n"

    for theme in themes:
        tid = theme.get("theme_node_id") or ""
        title = theme.get("title") or ""
        summary = theme.get("summary") or {}
        lines.append("")
        lines.append(f"Theme {tid}: {title}")
        lines.append(
            f"  summary: planned={summary.get('planned', 0)} "
            f"in_progress={summary.get('in_progress', 0)} "
            f"achieved={summary.get('achieved', 0)} "
            f"blocked={summary.get('blocked', 0)}"
        )
        for link in theme.get("links") or []:
            ref = link.get("node_ref") or ""
            status = link.get("target_status") or "(unset)"
            blocked = link.get("blocked_by") or []
            block_str = f"  blocked_by={','.join(blocked)}" if blocked else ""
            lines.append(
                f"  {ref:<28} {status:<14} {(link.get('title') or '')[:40]}{block_str}"
            )
    return "\n".join(lines) + "\n"


def format_markdown(report: dict) -> str:
    lines = ["# Portfolio report", ""]
    themes = report.get("themes") or []
    if not themes:
        lines.append("_No themes — register project `portfolio` and add theme nodes._")
        return "\n".join(lines) + "\n"

    for theme in themes:
        tid = theme.get("theme_node_id") or ""
        title = theme.get("title") or ""
        summary = theme.get("summary") or {}
        lines += [
            f"## {tid}: {title}",
            "",
            f"- Planned: {summary.get('planned', 0)}",
            f"- In progress: {summary.get('in_progress', 0)}",
            f"- Achieved: {summary.get('achieved', 0)}",
            f"- Blocked: {summary.get('blocked', 0)}",
            "",
            "| node_ref | title | target_status | verdict_status | blocked_by |",
            "|----------|-------|---------------|----------------|------------|",
        ]
        for link in theme.get("links") or []:
            blocked = ", ".join(link.get("blocked_by") or []) or "—"
            lines.append(
                f"| `{link.get('node_ref', '')}` | "
                f"{(link.get('title') or '').replace('|', '\\\\|')} | "
                f"{link.get('target_status') or ''} | "
                f"{link.get('verdict_status') or ''} | {blocked} |"
            )
        lines.append("")
    return "\n".join(lines)


def render_quarter_roadmap(report: dict) -> str:
    """Markdown table: Theme | Team | node_ref | Status | Blocked by."""
    lines = [
        "# Quarter roadmap",
        "",
        "| Theme | Team | node_ref | Status | Blocked by |",
        "|-------|------|----------|--------|------------|",
    ]
    for theme in report.get("themes") or []:
        tid = theme.get("theme_node_id") or ""
        ttitle = (theme.get("title") or tid).replace("|", "\\|")
        links = theme.get("links") or []
        if not links:
            lines.append(f"| {ttitle} | — | — | — | — |")
            continue
        for i, link in enumerate(links):
            theme_col = ttitle if i == 0 else ""
            blocked = ", ".join(link.get("blocked_by") or []) or "—"
            lines.append(
                f"| {theme_col} | `{link.get('project_id', '')}` | "
                f"`{link.get('node_ref', '')}` | "
                f"{link.get('target_status') or ''} | {blocked} |"
            )
    lines.append("")
    return "\n".join(lines)
