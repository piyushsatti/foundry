"""Status-brief view-model builder (Topic K1) — graph → dict for human surfaces."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from .constants import PORTFOLIO_PROJECT_ID
from .node_ref import format_node_ref
from . import queries
from .presentation_views import _now_iso

SCHEMA = "manifold/status-brief.v1"
STALE_HOURS = 24
CHANGES_DEFAULT_DAYS = 7
CHANGES_DEFAULT_LIMIT = 10


def build_status_brief_view(conn: sqlite3.Connection, project_id: str, *,
                            since_days: int = CHANGES_DEFAULT_DAYS,
                            changes_limit: int = CHANGES_DEFAULT_LIMIT) -> dict:
    """Build the canonical status-brief view-model for a project."""
    generated_at = _now_iso()
    project = queries.get_project(conn, project_id)
    project_label = (project or {}).get("label") or project_id

    base = {
        "$schema": SCHEMA,
        "view_kind": "status_brief",
        "project_id": project_id,
        "project_label": project_label,
        "team": project_label,
        "generated_at": generated_at,
        "stale_warning": None,
        "overall": {"status": "in_flight", "headline": ""},
        "shipped": [],
        "in_flight": [],
        "blocked": [],
        "at_risk": [],
        "changes_since": [],
        "theme_link": None,
        "drift_summary": {
            "high": 0,
            "medium": 0,
            "low": 0,
            "link": f"/projects/{project_id}/drift-report",
        },
        "warnings": [],
    }

    if project is None:
        base["warnings"].append("project_not_found")
        base["overall"] = {"status": "paused", "headline": "Project not found."}
        return base

    base["stale_warning"] = _stale_warning(conn, project_id)
    base["theme_link"] = _theme_link(conn, project_id)
    base["drift_summary"] = _drift_summary(conn, project_id)

    shipped, in_flight, blocked, at_risk = _categorize_work(conn, project_id)
    base["shipped"] = shipped
    base["in_flight"] = in_flight
    base["blocked"] = blocked
    base["at_risk"] = at_risk
    base["changes_since"] = _recent_changes(
        conn, project_id, since_days=since_days, limit=changes_limit,
    )
    base["overall"] = _overall(shipped, in_flight, blocked, at_risk, project_label)
    return base


def _stale_warning(conn: sqlite3.Connection, project_id: str) -> Optional[str]:
    row = conn.execute(
        "SELECT finished_at FROM validations WHERE project_id = ? "
        "AND finished_at IS NOT NULL ORDER BY validation_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    if row is None or not row["finished_at"]:
        return (
            f"No validation or drift run in the last {STALE_HOURS}h — "
            "run validation or drift-report before trusting verdict counts"
        )
    try:
        finished = datetime.fromisoformat(str(row["finished_at"]).replace("Z", "+00:00"))
        if finished.tzinfo is None:
            finished = finished.replace(tzinfo=timezone.utc)
    except ValueError:
        return "Last validation timestamp unreadable — re-run validation"
    age = datetime.now(timezone.utc) - finished
    if age > timedelta(hours=STALE_HOURS):
        return f"Data older than {STALE_HOURS}h (last validation {row['finished_at']})"
    return None


def _theme_link(conn: sqlite3.Connection, project_id: str) -> Optional[dict]:
    links = queries.list_portfolio_links(conn, project_id=project_id)
    if not links:
        return None
    theme_id = links[0]["theme_node_id"]
    theme = queries.get_node(conn, PORTFOLIO_PROJECT_ID, theme_id)
    return {
        "portfolio_id": theme_id,
        "label": (theme or {}).get("title") or theme_id,
        "theme_node_ref": format_node_ref(PORTFOLIO_PROJECT_ID, theme_id),
    }


def _drift_summary(conn: sqlite3.Connection, project_id: str) -> dict:
    rows = conn.execute(
        "SELECT verdict_status, verdict_mechanism FROM nodes "
        "WHERE project_id = ? AND deleted_at IS NULL",
        (project_id,),
    ).fetchall()
    high = medium = low = 0
    for row in rows:
        status = (row["verdict_status"] or "").strip()
        mechanism = (row["verdict_mechanism"] or "").strip()
        if status in ("violated", "judge_required"):
            high += 1
        elif status in ("errored", "invalidated_by_descendant"):
            medium += 1
        elif not mechanism or status in ("unknown", ""):
            low += 1
    return {
        "high": high,
        "medium": medium,
        "low": low,
        "link": f"/projects/{project_id}/drift-report",
    }


def _item_label(node: dict, project_id: str, node_id: str) -> dict:
    return {
        "node_ref": format_node_ref(project_id, node_id),
        "label": node.get("title") or node_id,
        "project_id": project_id,
        "node_id": node_id,
    }


def _categorize_work(conn: sqlite3.Connection, project_id: str) -> tuple[list, list, list, list]:
    shipped: list[dict] = []
    in_flight: list[dict] = []
    blocked: list[dict] = []
    at_risk: list[dict] = []

    for node in queries.list_targets(conn, project_id, limit=200):
        nid = node["node_id"]
        status = (node.get("target_status") or "").strip()
        entry = _item_label(node, project_id, nid)
        if status == "achieved":
            entry["shipped_at"] = node.get("target_achieved_at") or ""
            shipped.append(entry)
            continue
        if status in ("abandoned", "superseded"):
            continue
        if queries.is_cross_blocked(conn, project_id, nid):
            blockers = []
            for b in queries.list_cross_blocking_chain(conn, project_id, nid):
                bp, bn = b["project_id"], b["node_id"]
                bnode = queries.get_node(conn, bp, bn) or {}
                bproj = queries.get_project(conn, bp)
                blockers.append({
                    "node_ref": format_node_ref(bp, bn),
                    "team": (bproj or {}).get("label") or bp,
                    "label": bnode.get("title") or bn,
                })
            entry["blocked_by"] = blockers
            blocked.append(entry)

    excluded_ids = {b["node_id"] for b in blocked}
    for leaf in queries.next_leaves(conn, project_id):
        nid = leaf["node_id"]
        if nid in excluded_ids:
            continue
        status = (leaf.get("target_status") or "").strip()
        if status == "achieved":
            continue
        entry = _item_label(leaf, project_id, nid)
        in_flight.append(entry)

    for node in queries.list_nodes(conn, project_id, limit=500):
        vs = (node.get("verdict_status") or "").strip()
        if vs not in ("violated", "judge_required", "invalidated_by_descendant"):
            continue
        entry = _item_label(node, project_id, node["node_id"])
        entry["reason"] = f"drift:{vs}"
        at_risk.append(entry)

    return shipped, in_flight, blocked, at_risk


def _recent_changes(conn: sqlite3.Connection, project_id: str, *,
                    since_days: int, limit: int) -> list[dict]:
    since_ts = (
        datetime.now(timezone.utc) - timedelta(days=since_days)
    ).isoformat()
    try:
        rows = queries.list_changes_since(
            conn, project_id=project_id, since_ts=since_ts, limit=limit,
        )
    except ValueError:
        return []
    out = []
    for rev in rows[-limit:]:
        out.append({
            "when": rev.get("ts") or "",
            "what": _change_text(rev),
            "who": rev.get("actor") or "",
        })
    out.reverse()
    return out


def _change_text(rev: dict) -> str:
    ctype = rev.get("change_type") or "updated"
    nid = rev.get("node_id") or ""
    if ctype == "created":
        return f"created node {nid}"
    summary = rev.get("change_summary")
    if isinstance(summary, list) and summary:
        fields = ", ".join(str(s.get("field", "")) for s in summary[:3])
        return f"updated {nid}: {fields}" if fields else f"updated {nid}"
    return f"{ctype} {nid}"


def _overall(shipped: list, in_flight: list, blocked: list, at_risk: list,
             project_label: str) -> dict:
    total_active = len(shipped) + len(in_flight) + len(blocked)
    if blocked:
        blocker = blocked[0]
        by = blocker.get("blocked_by") or []
        by_label = by[0]["label"] if by else "dependency"
        headline = (
            f"{len(blocked)} blocked on {by_label}; "
            f"{len(in_flight)} in flight of {max(total_active, 1)} tracked leaves."
        )
        return {"status": "blocked", "headline": headline}
    if at_risk:
        headline = (
            f"{len(at_risk)} at risk from drift; "
            f"{len(in_flight)} in flight for {project_label}."
        )
        return {"status": "at_risk", "headline": headline}
    if in_flight:
        headline = (
            f"In flight: {len(in_flight)} leaf"
            f"{'ves' if len(in_flight) != 1 else ''}"
            f"{'; ' + str(len(shipped)) + ' shipped' if shipped else ''}."
        )
        return {"status": "in_flight", "headline": headline}
    if shipped:
        return {
            "status": "shipped",
            "headline": f"All tracked leaves shipped ({len(shipped)}).",
        }
    return {
        "status": "in_flight",
        "headline": f"No active leaves with targets for {project_label}.",
    }
