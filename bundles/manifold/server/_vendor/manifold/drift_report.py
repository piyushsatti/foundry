"""Formatters and helpers for drift-report (M4 spec↔code)."""


def classify_finding(status: str, source: str, mechanism: str) -> str:
    """Map a verdict run result to a drift-report bucket."""
    mechanism = (mechanism or "").strip()
    status = (status or "").strip()
    source = (source or "").strip()

    if source == "no_mechanism" or not mechanism:
        return "unverified"
    if status == "deferred_external" or source.startswith("external:"):
        return "deferred_external"
    if status == "errored":
        return "errored"
    if status in ("violated", "judge_required"):
        return "violated"
    if status == "satisfied":
        return "satisfied"
    return "other"


def format_terminal(report: dict, *, verbose: bool = False) -> str:
    lines = [
        f"Intent Drift Report — {report.get('project_id', '')}",
        f"  layer scope:  {report.get('layer_scope', '')}",
        f"  project root: {report.get('project_root') or '(unset)'}",
    ]
    for warning in report.get("warnings") or []:
        lines.append(f"  warning:      {warning}")
    s = report.get("summary") or {}
    lines.append(
        f"  summary:      {s.get('total', 0)} nodes — "
        f"{s.get('violated', 0)} violated, "
        f"{s.get('errored', 0)} errored, "
        f"{s.get('unverified', 0)} unverified, "
        f"{s.get('satisfied', 0)} satisfied"
    )

    def _section(title, findings):
        if not findings:
            return
        lines.append("")
        lines.append(title + ":")
        for f in findings:
            ev = (f.get("verdict_evidence") or "")[:80]
            lines.append(
                f"  {f.get('node_id', ''):<14} "
                f"{(f.get('title') or '')[:40]}"
            )
            if f.get("rationale"):
                lines.append(f"    rationale: {(f['rationale'])[:120]}")
            if ev:
                lines.append(f"    evidence:  {ev}")

    _section("VIOLATED", report.get("violated") or [])
    _section("ERRORED", report.get("errored") or [])
    _section("UNVERIFIED", report.get("unverified") or [])
    if verbose:
        _section("SATISFIED", report.get("satisfied") or [])
    return "\n".join(lines) + "\n"


def format_markdown(report: dict) -> str:
    pid = report.get("project_id", "")
    lines = [
        f"# Intent drift report — `{pid}`",
        "",
        f"- **Layer scope:** {report.get('layer_scope', '')}",
        f"- **Project root:** `{report.get('project_root') or '(unset)'}`",
        "",
    ]
    s = report.get("summary") or {}
    lines += [
        "## Summary",
        "",
        f"| Status | Count |",
        f"|--------|------:|",
        f"| Violated | {s.get('violated', 0)} |",
        f"| Errored | {s.get('errored', 0)} |",
        f"| Unverified | {s.get('unverified', 0)} |",
        f"| Satisfied | {s.get('satisfied', 0)} |",
        f"| Total | {s.get('total', 0)} |",
        "",
    ]
    for warning in report.get("warnings") or []:
        lines.append(f"> **Warning:** {warning}")
        lines.append("")

    def _md_section(title, findings):
        if not findings:
            lines.append(f"## {title}")
            lines.append("")
            lines.append("_None._")
            lines.append("")
            return
        lines.append(f"## {title}")
        lines.append("")
        for f in findings:
            lines.append(f"### `{f.get('node_id', '')}` — {f.get('title') or ''}")
            if f.get("rationale"):
                lines.append(f"> {f['rationale'][:300]}")
            lines.append("")
            lines.append(f"- **Status:** `{f.get('verdict_status', '')}`")
            lines.append(f"- **Mechanism:** `{f.get('verdict_mechanism') or '(none)'}`")
            if f.get("verdict_evidence"):
                lines.append(f"- **Evidence:** {f['verdict_evidence'][:400]}")
            lines.append(f"- **Peek:** `manifold show {pid} {f.get('node_id', '')}`")
            lines.append("")

    _md_section("Violated", report.get("violated") or [])
    _md_section("Errored", report.get("errored") or [])
    _md_section("Unverified", report.get("unverified") or [])
    return "\n".join(lines)
