"""Trajectory (Topic J): propose → show (impact preview) → accept."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from . import queries, writes

TRAJECTORY_STATUSES = frozenset({"draft", "accepted", "rejected", "partial"})
LEG_STATUSES = frozenset({"pending", "accepted", "rejected", "skipped"})
LEG_KINDS = frozenset({"update_node", "create_node", "transition_target"})


class TrajectoryError(Exception):
    """Invalid trajectory operation."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_trajectory_id() -> str:
    return f"tr-{uuid.uuid4().hex[:8]}"


def _new_leg_id(trajectory_id: str, seq: int) -> str:
    return f"{trajectory_id}-L{seq}"


def _parse_payload(raw: str | dict) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        raise TrajectoryError(f"invalid leg payload JSON: {exc}") from exc


def _row_trajectory(row: sqlite3.Row) -> dict:
    d = dict(row)
    if d.get("scope_json"):
        try:
            d["scope"] = json.loads(d["scope_json"])
        except json.JSONDecodeError:
            d["scope"] = {}
    else:
        d["scope"] = {}
    return d


def _row_leg(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["payload"] = _parse_payload(d.pop("payload_json", "{}"))
    return d


def get_trajectory(conn: sqlite3.Connection, trajectory_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM trajectories WHERE trajectory_id = ?",
        (trajectory_id,),
    ).fetchone()
    if row is None:
        return None
    traj = _row_trajectory(row)
    legs = conn.execute(
        "SELECT * FROM trajectory_legs WHERE trajectory_id = ? ORDER BY seq",
        (trajectory_id,),
    ).fetchall()
    traj["legs"] = [_row_leg(r) for r in legs]
    return traj


def list_trajectories(conn: sqlite3.Connection, project_id: str,
                      *, status: Optional[str] = None) -> list[dict]:
    sql = "SELECT * FROM trajectories WHERE project_id = ?"
    params: list[Any] = [project_id]
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    rows = conn.execute(sql, params).fetchall()
    out = []
    for row in rows:
        traj = _row_trajectory(row)
        legs = conn.execute(
            "SELECT leg_id, seq, leg_kind, node_ref, status FROM trajectory_legs "
            "WHERE trajectory_id = ? ORDER BY seq",
            (traj["trajectory_id"],),
        ).fetchall()
        traj["leg_count"] = len(legs)
        traj["legs_summary"] = [dict(r) for r in legs]
        out.append(traj)
    return out


def _validate_leg_spec(spec: dict, seq: int) -> dict:
    kind = (spec.get("leg_kind") or "").strip()
    if kind not in LEG_KINDS:
        raise TrajectoryError(
            f"leg {seq}: leg_kind must be one of {sorted(LEG_KINDS)}"
        )
    payload = spec.get("payload")
    if payload is None:
        raise TrajectoryError(f"leg {seq}: missing payload")
    payload = _parse_payload(payload)
    if kind == "update_node":
        if not payload.get("node_id"):
            raise TrajectoryError(f"leg {seq}: update_node requires node_id")
        if not payload.get("change_reason"):
            raise TrajectoryError(f"leg {seq}: update_node requires change_reason")
        if not payload.get("fields"):
            raise TrajectoryError(f"leg {seq}: update_node requires fields")
    elif kind == "create_node":
        for key in ("layer", "node_id", "title"):
            if not payload.get(key):
                raise TrajectoryError(f"leg {seq}: create_node requires {key}")
    elif kind == "transition_target":
        if not payload.get("node_id") or not payload.get("to_status"):
            raise TrajectoryError(
                f"leg {seq}: transition_target requires node_id and to_status"
            )
    node_ref = spec.get("node_ref") or payload.get("node_id") or ""
    return {
        "leg_kind": kind,
        "node_ref": node_ref,
        "payload": payload,
    }


def _validate_legs_against_graph(
    conn: sqlite3.Connection,
    project_id: str,
    legs: list[dict],
) -> None:
    """Reject legs that reference missing nodes or illegal target transitions."""
    for seq, norm in enumerate(legs, start=1):
        kind = norm["leg_kind"]
        payload = norm["payload"]
        node_id = payload.get("node_id")
        if kind in ("update_node", "transition_target"):
            if not node_id:
                continue
            node = queries.get_node(conn, project_id, node_id)
            if node is None:
                raise TrajectoryError(
                    f"leg {seq}: node not found: {project_id}:{node_id}"
                )
            if kind == "transition_target":
                try:
                    writes.validate_target_transition(
                        node.get("target_status"),
                        payload["to_status"],
                        superseded_by=payload.get("superseded_by"),
                    )
                except writes.InvalidTransition as exc:
                    raise TrajectoryError(f"leg {seq}: {exc}") from exc


def propose_trajectory(
    conn: sqlite3.Connection,
    project_id: str,
    target_brief: str,
    legs: list[dict],
    *,
    proposed_by: str,
    scope: Optional[dict] = None,
) -> dict:
    """Create draft trajectory + legs. Does not mutate the spec graph."""
    if not (target_brief or "").strip():
        raise TrajectoryError("target_brief is required")
    if not legs:
        raise TrajectoryError("at least one leg is required")
    proposed_by = (proposed_by or "").strip()
    if not proposed_by:
        raise TrajectoryError("proposed_by is required")

    if queries.get_project(conn, project_id) is None:
        raise writes.ProjectNotFound(project_id)

    normalized = [_validate_leg_spec(raw, seq) for seq, raw in enumerate(legs, start=1)]
    _validate_legs_against_graph(conn, project_id, normalized)

    trajectory_id = _new_trajectory_id()
    now = _now_iso()
    conn.execute(
        "INSERT INTO trajectories "
        "(trajectory_id, project_id, status, target_brief, scope_json, "
        " proposed_by, created_at, resolved_at) "
        "VALUES (?, ?, 'draft', ?, ?, ?, ?, NULL)",
        (
            trajectory_id,
            project_id,
            target_brief.strip(),
            json.dumps(scope or {}),
            proposed_by,
            now,
        ),
    )
    inserted = []
    for seq, norm in enumerate(normalized, start=1):
        leg_id = _new_leg_id(trajectory_id, seq)
        conn.execute(
            "INSERT INTO trajectory_legs "
            "(leg_id, trajectory_id, seq, leg_kind, node_ref, payload_json, "
            " status, applied_revision_id) "
            "VALUES (?, ?, ?, ?, ?, ?, 'pending', NULL)",
            (
                leg_id,
                trajectory_id,
                seq,
                norm["leg_kind"],
                norm["node_ref"],
                json.dumps(norm["payload"]),
            ),
        )
        inserted.append({
            "leg_id": leg_id,
            "seq": seq,
            "leg_kind": norm["leg_kind"],
            "node_ref": norm["node_ref"],
            "status": "pending",
        })
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'trajectory_proposed', ?)",
        (now, project_id, json.dumps({"trajectory_id": trajectory_id})),
    )
    return {
        "trajectory_id": trajectory_id,
        "project_id": project_id,
        "status": "draft",
        "target_brief": target_brief.strip(),
        "proposed_by": proposed_by,
        "created_at": now,
        "legs": inserted,
    }


def apply_leg(
    conn: sqlite3.Connection,
    project_id: str,
    leg: dict,
    *,
    actor: str,
    source: str = "trajectory",
) -> dict:
    """Apply one leg via existing write APIs."""
    kind = leg["leg_kind"]
    payload = leg.get("payload") or _parse_payload(leg.get("payload_json", "{}"))
    actor = (actor or "").strip()
    if not actor:
        raise writes.MissingActor("actor is required")

    if kind == "update_node":
        node_id = payload["node_id"]
        node = queries.get_node(conn, project_id, node_id)
        if node is None:
            raise writes.NodeNotFound(f"{project_id}:{node_id}")
        return writes.update_node(
            conn,
            project_id,
            node_id,
            payload["fields"],
            expected_revision_id=node["current_revision_id"],
            actor=actor,
            source=source,
            change_reason=payload["change_reason"],
        )
    if kind == "create_node":
        return writes.create_node(
            conn,
            project_id,
            payload["layer"],
            payload["node_id"],
            payload["title"],
            body=payload.get("body", ""),
            kind=payload.get("kind", "spec"),
            parents=payload.get("parents"),
            peers_depends_on=payload.get("peers_depends_on"),
            target_blocks=payload.get("target_blocks"),
            target_status=payload.get("target_status"),
            rationale=payload.get("rationale"),
            alternatives_considered=payload.get("alternatives_considered"),
            actor=actor,
            source=source,
        )
    if kind == "transition_target":
        node_id = payload["node_id"]
        node = queries.get_node(conn, project_id, node_id)
        if node is None:
            raise writes.NodeNotFound(f"{project_id}:{node_id}")
        return writes.transition_target(
            conn,
            project_id,
            node_id,
            payload["to_status"],
            achieved_at=payload.get("achieved_at"),
            superseded_by=payload.get("superseded_by"),
            note=payload.get("note"),
            expected_revision_id=node["current_revision_id"],
            actor=actor,
            source=source,
        )
    raise TrajectoryError(f"unknown leg_kind: {kind}")


def _legs_for_preview(traj: dict, leg_seqs: Optional[list[int]]) -> list[dict]:
    pending = [lg for lg in traj["legs"] if lg["status"] == "pending"]
    if leg_seqs is None:
        return pending
    wanted = set(leg_seqs)
    return [lg for lg in pending if lg["seq"] in wanted]


def compute_impact_preview(
    conn: sqlite3.Connection,
    project_id: str,
    legs: list[dict],
) -> dict:
    """Simulate applying legs; return next-leaves delta without persisting."""
    before = queries.next_leaves(conn, project_id)
    before_ids = {n["node_id"] for n in before}
    touched: list[str] = []

    conn.execute("SAVEPOINT trajectory_preview")
    try:
        for leg in legs:
            ref = leg.get("node_ref") or (leg.get("payload") or {}).get("node_id")
            if ref:
                touched.append(ref)
            apply_leg(conn, project_id, leg, actor="preview:trajectory", source="trajectory_preview")
        after = queries.next_leaves(conn, project_id)
        after_ids = {n["node_id"] for n in after}
        removed = [
            n for n in before if n["node_id"] in (before_ids - after_ids)
        ]
        return {
            "next_leaves_after": after,
            "next_leaves_removed": removed,
            "nodes_touched": sorted(set(touched)),
            "portfolio_delta": [],
            "blocked_by_delta": [],
        }
    finally:
        conn.execute("ROLLBACK TO trajectory_preview")
        conn.execute("RELEASE trajectory_preview")


def peek_trajectory(
    conn: sqlite3.Connection,
    trajectory_id: str,
    *,
    leg_seqs: Optional[list[int]] = None,
) -> dict:
    """Full trajectory + impact preview for selected pending legs."""
    traj = get_trajectory(conn, trajectory_id)
    if traj is None:
        raise TrajectoryError(f"trajectory not found: {trajectory_id}")
    preview_legs = _legs_for_preview(traj, leg_seqs)
    preview = compute_impact_preview(conn, traj["project_id"], preview_legs)
    return {
        **traj,
        "impact_preview": preview,
        "preview_leg_seqs": [lg["seq"] for lg in preview_legs],
    }


def accept_trajectory_legs(
    conn: sqlite3.Connection,
    trajectory_id: str,
    *,
    leg_seqs: Optional[list[int]] = None,
    actor: str,
) -> dict:
    """Apply pending legs and update trajectory/leg status."""
    traj = get_trajectory(conn, trajectory_id)
    if traj is None:
        raise TrajectoryError(f"trajectory not found: {trajectory_id}")
    if traj["status"] not in ("draft", "partial"):
        raise TrajectoryError(
            f"trajectory {trajectory_id} status is {traj['status']!r}; cannot accept"
        )

    to_apply = _legs_for_preview(traj, leg_seqs)
    if not to_apply:
        raise TrajectoryError("no pending legs to accept")

    project_id = traj["project_id"]
    results = []
    for leg in to_apply:
        result = apply_leg(conn, project_id, leg, actor=actor, source="trajectory_accept")
        rev = result.get("revision_id")
        conn.execute(
            "UPDATE trajectory_legs SET status = 'accepted', "
            "applied_revision_id = ? WHERE leg_id = ?",
            (rev, leg["leg_id"]),
        )
        results.append({
            "leg_id": leg["leg_id"],
            "seq": leg["seq"],
            "revision_id": rev,
        })

    pending_left = conn.execute(
        "SELECT COUNT(*) AS c FROM trajectory_legs "
        "WHERE trajectory_id = ? AND status = 'pending'",
        (trajectory_id,),
    ).fetchone()["c"]
    new_status = "accepted" if pending_left == 0 else "partial"
    resolved_at = _now_iso() if pending_left == 0 else None
    conn.execute(
        "UPDATE trajectories SET status = ?, resolved_at = COALESCE(?, resolved_at) "
        "WHERE trajectory_id = ?",
        (new_status, resolved_at, trajectory_id),
    )
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'trajectory_accepted', ?)",
        (
            _now_iso(),
            project_id,
            json.dumps({"trajectory_id": trajectory_id, "legs": results}),
        ),
    )
    return {
        "trajectory_id": trajectory_id,
        "project_id": project_id,
        "status": new_status,
        "accepted": results,
        "pending_remaining": pending_left,
    }


def reject_trajectory(
    conn: sqlite3.Connection,
    trajectory_id: str,
    *,
    actor: str,
) -> dict:
    """Mark a draft trajectory rejected. Does not apply legs or mutate the graph."""
    traj = get_trajectory(conn, trajectory_id)
    if traj is None:
        raise TrajectoryError(f"trajectory not found: {trajectory_id}")
    if traj["status"] != "draft":
        raise TrajectoryError(
            f"trajectory {trajectory_id} status is {traj['status']!r}; "
            "only draft trajectories can be rejected"
        )

    actor = (actor or "").strip()
    if not actor:
        raise TrajectoryError("actor is required")

    now = _now_iso()
    conn.execute(
        "UPDATE trajectories SET status = 'rejected', resolved_at = ? "
        "WHERE trajectory_id = ?",
        (now, trajectory_id),
    )
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'trajectory_rejected', ?)",
        (
            now,
            traj["project_id"],
            json.dumps({"trajectory_id": trajectory_id, "actor": actor}),
        ),
    )
    return {
        "trajectory_id": trajectory_id,
        "project_id": traj["project_id"],
        "status": "rejected",
        "resolved_at": now,
    }


def format_show_markdown(report: dict) -> str:
    """Human-readable plan output for trajectory show."""
    tid = report["trajectory_id"]
    lines = [
        f"# Trajectory {tid} ({report['status']}) — impact preview",
        "",
        f"**Project:** `{report['project_id']}`",
        f"**Proposed by:** {report['proposed_by']}",
        "",
        "## Target brief",
        report.get("target_brief") or "",
        "",
        f"## Legs ({len(report.get('legs') or [])} total)",
    ]
    for leg in report.get("legs") or []:
        lines.append(
            f"- **L{leg['seq']}** `{leg['leg_kind']}` {leg.get('node_ref') or ''} "
            f"— _{leg['status']}_"
        )
    prev = report.get("impact_preview") or {}
    lines.extend(["", "## Impact preview"])
    if report.get("preview_leg_seqs"):
        lines.append(f"_Simulating legs: {report['preview_leg_seqs']}_")
    lines.append("")
    lines.append("### next_leaves_after")
    for leaf in prev.get("next_leaves_after") or []:
        lines.append(
            f"- `{leaf['node_id']}` {leaf.get('layer', '')} "
            f"{leaf.get('target_status', '')} — {leaf.get('title', '')[:60]}"
        )
    removed = prev.get("next_leaves_removed") or []
    if removed:
        lines.extend(["", "### next_leaves_removed"])
        for leaf in removed:
            lines.append(f"- `{leaf['node_id']}` — {leaf.get('title', '')[:60]}")
    touched = prev.get("nodes_touched") or []
    if touched:
        lines.extend(["", f"### nodes_touched ({len(touched)})"])
        for nid in touched:
            lines.append(f"- `{nid}`")
    return "\n".join(lines) + "\n"
