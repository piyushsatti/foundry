"""
Write functions for manifold.

Every write produces a revisions row with change_summary computed at write time.
Optimistic concurrency via expected_revision_id; STRICT_CONCURRENCY env var
controls server-side enforcement (default strict).

Target-state transitions enforce the spec state machine; invalid transitions
raise InvalidTransition.

with_batch wraps multiple ops in a single SQLite transaction; failure rolls back.
"""
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Optional


# ============================================================
# Errors
# ============================================================

class WritesError(Exception):
    """Base for write errors."""


class NodeAlreadyExists(WritesError): pass
class NodeNotFound(WritesError): pass
class ProjectNotFound(WritesError): pass
class StaleRevision(WritesError):
    def __init__(self, message, current_revision_id=None):
        super().__init__(message)
        self.current_revision_id = current_revision_id


class MissingActor(WritesError): pass
class InvalidTransition(WritesError): pass
class BatchFailed(WritesError): pass


# Documented change_reason enum (stored as TEXT; not DB-enforced).
DOCUMENTED_CHANGE_REASONS = (
    "correction", "evolution", "clarification", "refactor", "pivot", "other",
)


def _require_change_reason(change_reason: Optional[str]) -> str:
    """Content edits must declare why — no silent default; enum enforced."""
    if change_reason is None or not str(change_reason).strip():
        raise WritesError(
            "change_reason is required on update_node; "
            "use correction | evolution | clarification | refactor | pivot | other"
        )
    value = str(change_reason).strip()
    if value not in DOCUMENTED_CHANGE_REASONS:
        allowed = " | ".join(DOCUMENTED_CHANGE_REASONS)
        raise WritesError(
            f"invalid change_reason {value!r}; use {allowed}"
        )
    return value


# ============================================================
# Configuration helpers
# ============================================================

def _strict_concurrency() -> bool:
    return os.environ.get("MANIFOLD_STRICT_CONCURRENCY", "true").strip().lower() != "false"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_actor(actor: str) -> str:
    actor = (actor or "").strip()
    if not actor:
        raise MissingActor("actor must be a non-empty string")
    return actor


def _ensure_project(conn: sqlite3.Connection, project_id: str) -> None:
    row = conn.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,)).fetchone()
    if row is None:
        raise ProjectNotFound(project_id)


# ============================================================
# Target state machine
# ============================================================

TARGET_TRANSITIONS = {
    "": {"planned"},
    None: {"planned"},
    "planned": {"in_progress", "abandoned", "achieved"},
    "in_progress": {"achieved", "abandoned"},
    "achieved": {"superseded"},
    "abandoned": {"planned"},
    "superseded": set(),
}


def validate_target_transition(
    from_status: Optional[str],
    to_status: str,
    *,
    superseded_by: Optional[str] = None,
) -> None:
    """Raise InvalidTransition if to_status is not allowed from from_status."""
    from_key = from_status if from_status is not None else ""
    allowed = TARGET_TRANSITIONS.get(from_key, set())
    if to_status not in allowed:
        raise InvalidTransition(
            f"cannot transition target_status from {from_key!r} to {to_status!r}; "
            f"allowed: {sorted(allowed) or 'none'}"
        )
    if to_status == "superseded" and not superseded_by:
        raise InvalidTransition("target_status='superseded' requires superseded_by")


# ============================================================
# Snapshot + edges
# ============================================================

def _build_snapshot(fields: dict) -> str:
    return json.dumps(fields, sort_keys=True, default=str)


def _read_current_snapshot(conn: sqlite3.Connection, project_id: str, node_id: str) -> dict:
    """Reconstruct a serializable snapshot of the current node state for revision storage."""
    row = conn.execute(
        "SELECT * FROM nodes WHERE project_id = ? AND node_id = ?",
        (project_id, node_id),
    ).fetchone()
    if row is None:
        raise NodeNotFound(f"{project_id}:{node_id}")
    d = dict(row)
    # Include current parents/peers/blocks via edges for snapshot completeness
    d["parents"] = _list_edge_targets(conn, project_id, node_id, "parent")
    d["peers_depends_on"] = _list_edge_targets(conn, project_id, node_id, "depends_on")
    d["target_blocks"] = _list_edge_targets(conn, project_id, node_id, "blocks")
    return d


def _list_edge_targets(conn: sqlite3.Connection, project_id: str,
                       src_node_id: str, edge_kind: str) -> list[str]:
    rows = conn.execute(
        "SELECT dst_node_id FROM node_edges "
        "WHERE project_id = ? AND src_node_id = ? AND edge_kind = ? "
        "ORDER BY dst_node_id",
        (project_id, src_node_id, edge_kind),
    ).fetchall()
    return [r["dst_node_id"] for r in rows]


def _replace_edges(conn: sqlite3.Connection, project_id: str, src_node_id: str,
                   edge_kind: str, targets: list[str]) -> None:
    """Replace all edges of `edge_kind` from `src_node_id` with the given targets."""
    conn.execute(
        "DELETE FROM node_edges WHERE project_id = ? AND src_node_id = ? AND edge_kind = ?",
        (project_id, src_node_id, edge_kind),
    )
    now = _now_iso()
    for t in targets or []:
        conn.execute(
            "INSERT INTO node_edges (project_id, src_node_id, dst_node_id, "
            "edge_kind, created_at) VALUES (?, ?, ?, ?, ?)",
            (project_id, src_node_id, t, edge_kind, now),
        )


def _write_revision(conn, project_id, node_id, change_type, snapshot_dict,
                    change_summary, source, actor,
                    prev_revision_id=None, batch_id=None,
                    git_sha=None, note=None, change_reason=None) -> int:
    cur = conn.execute(
        "INSERT INTO revisions (project_id, node_id, ts, change_type, "
        "prev_revision_id, snapshot, change_summary, change_reason, "
        "batch_id, source, actor, git_sha, note) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (project_id, node_id, _now_iso(), change_type, prev_revision_id,
         _build_snapshot(snapshot_dict),
         json.dumps(change_summary) if change_summary is not None else None,
         change_reason,
         batch_id, source, actor, git_sha, note),
    )
    return cur.lastrowid


def _compute_change_summary(prev: dict, curr: dict) -> list:
    diff = []
    for key in sorted(set(prev) | set(curr)):
        if prev.get(key) != curr.get(key):
            diff.append({"field": key, "old": prev.get(key), "new": curr.get(key)})
    return diff


# ============================================================
# Project lifecycle
# ============================================================

def register_project(conn: sqlite3.Connection, project_id: str,
                     spec_config: dict, *, label: Optional[str] = None) -> dict:
    existing = conn.execute(
        "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
    ).fetchone()
    if existing:
        return {"project_id": project_id, "created": False}
    conn.execute(
        "INSERT INTO projects (project_id, label, spec_config, created_at) "
        "VALUES (?, ?, ?, ?)",
        (project_id, label, json.dumps(spec_config), _now_iso()),
    )
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'project_registered', ?)",
        (_now_iso(), project_id, json.dumps({"label": label})),
    )
    return {"project_id": project_id, "created": True}


def archive_project(conn: sqlite3.Connection, project_id: str) -> dict:
    _ensure_project(conn, project_id)
    conn.execute(
        "UPDATE projects SET archived_at = ? WHERE project_id = ?",
        (_now_iso(), project_id),
    )
    return {"project_id": project_id, "archived": True}


def unarchive_project(conn: sqlite3.Connection, project_id: str) -> dict:
    _ensure_project(conn, project_id)
    conn.execute(
        "UPDATE projects SET archived_at = NULL WHERE project_id = ?",
        (project_id,),
    )
    return {"project_id": project_id, "archived": False}


# ============================================================
# Node lifecycle
# ============================================================

def create_node(conn: sqlite3.Connection, project_id: str, layer: str,
                node_id: str, title: str, *,
                body: str = "", kind: str = "spec",
                parents: Optional[list[str]] = None,
                peers_depends_on: Optional[list[str]] = None,
                target_blocks: Optional[list[str]] = None,
                target_status: Optional[str] = None,
                rationale: Optional[str] = None,
                alternatives_considered: Optional[str] = None,
                actor: str = "", source: str = "cli",
                batch_id: Optional[str] = None) -> dict:
    actor = _require_actor(actor)
    _ensure_project(conn, project_id)

    dup = conn.execute(
        "SELECT 1 FROM nodes WHERE project_id = ? AND node_id = ?",
        (project_id, node_id),
    ).fetchone()
    if dup:
        raise NodeAlreadyExists(f"{project_id}:{node_id}")

    # default target_status to "planned" when not explicitly set
    if target_status is None:
        target_status = "planned"

    now = _now_iso()
    snapshot = {
        "node_id": node_id, "layer": layer, "title": title, "kind": kind,
        "body": body, "parents": parents or [],
        "peers_depends_on": peers_depends_on or [],
        "target_blocks": target_blocks or [],
        "target_status": target_status,
        "rationale": rationale,
        "alternatives_considered": alternatives_considered,
    }
    revision_id = _write_revision(
        conn, project_id, node_id, "created", snapshot,
        change_summary=None, source=source, actor=actor, batch_id=batch_id,
    )
    conn.execute(
        "INSERT INTO nodes (project_id, node_id, layer, title, kind, body, "
        "target_status, rationale, alternatives_considered, "
        "current_revision_id, last_modified_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (project_id, node_id, layer, title, kind, body, target_status,
         rationale, alternatives_considered, revision_id, now),
    )
    _replace_edges(conn, project_id, node_id, "parent", parents or [])
    _replace_edges(conn, project_id, node_id, "depends_on", peers_depends_on or [])
    _replace_edges(conn, project_id, node_id, "blocks", target_blocks or [])
    conn.execute(
        "UPDATE projects SET last_revision_id = ? WHERE project_id = ?",
        (revision_id, project_id),
    )
    return {"project_id": project_id, "node_id": node_id, "revision_id": revision_id}


# Columns the client may update via update_node (denormalized fields).
_UPDATABLE_FIELDS = {
    "title", "body", "kind", "realized_by_external", "delegate_to",
    "verdict_mechanism", "verdict_check", "verdict_assertion",
    "verdict_judge_prompt", "verdict_evidence_ref", "verdict_evidence_hash",
    "verdict_last_checked", "verdict_status",
    "contract",          # JSON field — caller passes dict, we store JSON
    "applies_to",        # JSON
    # anti-drift fields
    "rationale", "alternatives_considered",
    # Edge collections handled separately:
    "parents", "peers_depends_on", "target_blocks",
}
_JSON_FIELDS = {"contract", "applies_to"}
_EDGE_FIELDS = {
    "parents": "parent",
    "peers_depends_on": "depends_on",
    "target_blocks": "blocks",
}


def update_node(conn: sqlite3.Connection, project_id: str, node_id: str,
                fields: dict, expected_revision_id: int, *,
                actor: str, source: str = "cli",
                batch_id: Optional[str] = None,
                note: Optional[str] = None,
                change_reason: Optional[str] = None) -> dict:
    actor = _require_actor(actor)
    current = _read_current_snapshot(conn, project_id, node_id)
    if _strict_concurrency() and current.get("current_revision_id") != expected_revision_id:
        raise StaleRevision(
            f"node {node_id} has revision {current.get('current_revision_id')}, "
            f"expected {expected_revision_id}",
            current_revision_id=current.get("current_revision_id"),
        )

    # Compute changes
    column_sets: dict = {}
    edge_changes: dict = {}
    for field, value in fields.items():
        if field not in _UPDATABLE_FIELDS:
            raise WritesError(f"field {field!r} is not updatable via update_node")
        if field in _EDGE_FIELDS:
            edge_changes[field] = value
        elif field in _JSON_FIELDS:
            column_sets[field] = json.dumps(value) if value is not None else None
        else:
            column_sets[field] = value

    # Build new snapshot
    new_snapshot = {k: current.get(k) for k in current
                    if not k.startswith("_")}
    for k, v in column_sets.items():
        if k in _JSON_FIELDS:
            new_snapshot[k] = json.loads(v) if v else None
        else:
            new_snapshot[k] = v
    for edge_field, new_targets in edge_changes.items():
        new_snapshot[edge_field] = list(new_targets or [])

    change_summary = _compute_change_summary(current, new_snapshot)
    if not change_summary:
        return {"project_id": project_id, "node_id": node_id,
                "revision_id": current.get("current_revision_id"),
                "unchanged": True}

    change_reason = _require_change_reason(change_reason)

    now = _now_iso()
    revision_id = _write_revision(
        conn, project_id, node_id, "updated", new_snapshot,
        change_summary=change_summary, source=source, actor=actor,
        prev_revision_id=current.get("current_revision_id"),
        batch_id=batch_id, note=note, change_reason=change_reason,
    )

    # Apply column updates
    if column_sets:
        assignments = ", ".join(f"{k} = ?" for k in column_sets)
        values = list(column_sets.values()) + [now, revision_id, project_id, node_id]
        conn.execute(
            f"UPDATE nodes SET {assignments}, last_modified_at = ?, "
            f"current_revision_id = ? WHERE project_id = ? AND node_id = ?",
            values,
        )
    else:
        conn.execute(
            "UPDATE nodes SET last_modified_at = ?, current_revision_id = ? "
            "WHERE project_id = ? AND node_id = ?",
            (now, revision_id, project_id, node_id),
        )
    # Apply edge changes
    for edge_field, new_targets in edge_changes.items():
        _replace_edges(conn, project_id, node_id, _EDGE_FIELDS[edge_field],
                       new_targets or [])
    return {"project_id": project_id, "node_id": node_id,
            "revision_id": revision_id}


def transition_target(conn: sqlite3.Connection, project_id: str, node_id: str,
                      to_status: str, *,
                      achieved_at: Optional[str] = None,
                      superseded_by: Optional[str] = None,
                      note: Optional[str] = None,
                      expected_revision_id: int, actor: str,
                      source: str = "cli",
                      batch_id: Optional[str] = None) -> dict:
    actor = _require_actor(actor)
    current = _read_current_snapshot(conn, project_id, node_id)
    if _strict_concurrency() and current.get("current_revision_id") != expected_revision_id:
        raise StaleRevision(
            f"node {node_id} has revision {current.get('current_revision_id')}, "
            f"expected {expected_revision_id}",
            current_revision_id=current.get("current_revision_id"),
        )

    from_status = current.get("target_status")
    validate_target_transition(
        from_status, to_status, superseded_by=superseded_by,
    )

    column_sets = {"target_status": to_status}
    if to_status == "achieved":
        column_sets["target_achieved_at"] = achieved_at or _now_iso()
    if to_status == "superseded":
        column_sets["target_superseded_by"] = superseded_by

    new_snapshot = {k: current.get(k) for k in current if not k.startswith("_")}
    new_snapshot.update(column_sets)

    change_summary = _compute_change_summary(current, new_snapshot)
    now = _now_iso()
    revision_id = _write_revision(
        conn, project_id, node_id, "updated", new_snapshot,
        change_summary=change_summary, source=source, actor=actor,
        prev_revision_id=current.get("current_revision_id"),
        batch_id=batch_id, note=note,
        change_reason="evolution",  # mechanical status transition — relax vs update_node
    )
    assignments = ", ".join(f"{k} = ?" for k in column_sets)
    values = list(column_sets.values()) + [now, revision_id, project_id, node_id]
    conn.execute(
        f"UPDATE nodes SET {assignments}, last_modified_at = ?, "
        f"current_revision_id = ? WHERE project_id = ? AND node_id = ?",
        values,
    )
    return {"project_id": project_id, "node_id": node_id,
            "revision_id": revision_id,
            "from": from_status, "to": to_status}


def revert(conn: sqlite3.Connection, project_id: str, node_id: str,
           to_revision_id: int, *, actor: str, source: str = "cli",
           batch_id: Optional[str] = None) -> dict:
    actor = _require_actor(actor)
    row = conn.execute(
        "SELECT snapshot FROM revisions WHERE project_id = ? AND node_id = ? "
        "AND revision_id = ?",
        (project_id, node_id, int(to_revision_id)),
    ).fetchone()
    if row is None:
        raise WritesError(f"revision {to_revision_id} not found for {project_id}:{node_id}")
    snap = json.loads(row["snapshot"])
    current = _read_current_snapshot(conn, project_id, node_id)
    change_summary = _compute_change_summary(current, snap)
    new_rev = _write_revision(
        conn, project_id, node_id, "reverted", snap,
        change_summary=change_summary, source=source, actor=actor,
        prev_revision_id=current.get("current_revision_id"),
        batch_id=batch_id,
        note=f"reverted to revision {to_revision_id}",
        change_reason="correction",
    )

    # Apply to nodes row
    column_sets = {
        "title": snap.get("title", ""),
        "body": snap.get("body", ""),
        "kind": snap.get("kind", "spec"),
        "layer": snap.get("layer", current.get("layer")),
        "target_status": snap.get("target_status"),
        "target_achieved_at": snap.get("target_achieved_at"),
        "target_superseded_by": snap.get("target_superseded_by"),
    }
    assignments = ", ".join(f"{k} = ?" for k in column_sets)
    values = list(column_sets.values()) + [_now_iso(), new_rev, project_id, node_id]
    conn.execute(
        f"UPDATE nodes SET {assignments}, last_modified_at = ?, "
        f"current_revision_id = ? WHERE project_id = ? AND node_id = ?",
        values,
    )
    # Restore edges
    _replace_edges(conn, project_id, node_id, "parent", snap.get("parents") or [])
    _replace_edges(conn, project_id, node_id, "depends_on", snap.get("peers_depends_on") or [])
    _replace_edges(conn, project_id, node_id, "blocks", snap.get("target_blocks") or [])
    return {"project_id": project_id, "node_id": node_id, "revision_id": new_rev,
            "reverted_to": to_revision_id}


def soft_delete_node(conn: sqlite3.Connection, project_id: str, node_id: str,
                     expected_revision_id: int, *, actor: str,
                     source: str = "cli", batch_id: Optional[str] = None) -> dict:
    actor = _require_actor(actor)
    current = _read_current_snapshot(conn, project_id, node_id)
    if current.get("deleted_at"):
        raise WritesError(f"node {node_id} already deleted")
    if _strict_concurrency() and current.get("current_revision_id") != expected_revision_id:
        raise StaleRevision(
            f"node {node_id} has revision {current.get('current_revision_id')}, "
            f"expected {expected_revision_id}",
            current_revision_id=current.get("current_revision_id"),
        )
    new_rev = _write_revision(
        conn, project_id, node_id, "deleted", current,
        change_summary=[{"field": "deleted_at", "old": None, "new": _now_iso()}],
        source=source, actor=actor,
        prev_revision_id=current.get("current_revision_id"),
        batch_id=batch_id,
        change_reason="other",
    )
    conn.execute(
        "UPDATE nodes SET deleted_at = ?, current_revision_id = ? "
        "WHERE project_id = ? AND node_id = ?",
        (_now_iso(), new_rev, project_id, node_id),
    )
    return {"project_id": project_id, "node_id": node_id, "revision_id": new_rev,
            "deleted": True}


def restore_node(conn: sqlite3.Connection, project_id: str, node_id: str, *,
                 actor: str, source: str = "cli",
                 batch_id: Optional[str] = None) -> dict:
    actor = _require_actor(actor)
    row = conn.execute(
        "SELECT * FROM nodes WHERE project_id = ? AND node_id = ?",
        (project_id, node_id),
    ).fetchone()
    if row is None:
        raise NodeNotFound(f"{project_id}:{node_id}")
    if row["deleted_at"] is None:
        raise WritesError(f"node {node_id} is not deleted")
    snap = dict(row)
    snap["deleted_at"] = None
    new_rev = _write_revision(
        conn, project_id, node_id, "restored", snap,
        change_summary=[{"field": "deleted_at", "old": row["deleted_at"], "new": None}],
        source=source, actor=actor,
        prev_revision_id=row["current_revision_id"],
        batch_id=batch_id,
        change_reason="correction",
    )
    conn.execute(
        "UPDATE nodes SET deleted_at = NULL, current_revision_id = ? "
        "WHERE project_id = ? AND node_id = ?",
        (new_rev, project_id, node_id),
    )
    return {"project_id": project_id, "node_id": node_id, "revision_id": new_rev,
            "deleted": False}


# ============================================================
# Batch
# ============================================================

# Operation dispatch table for with_batch.
_OPERATION_DISPATCH = {
    "create_node": create_node,
    "update_node": update_node,
    "transition_target": transition_target,
    "revert": revert,
    "soft_delete_node": soft_delete_node,
    "restore_node": restore_node,
}


def with_batch(conn: sqlite3.Connection, label: str, ops: list[dict], *,
               actor: str, source: str = "mcp") -> dict:
    """Execute a list of operations under a shared batch_id, atomically.

    Each op is `{"op": <name>, "args": <kwargs>}`. Returns
    `{batch_id, revision_ids, label}`. Rolls back on any exception.
    """
    actor = _require_actor(actor)
    batch_id = str(uuid.uuid4())
    revision_ids = []
    conn.execute("BEGIN")
    try:
        for entry in ops:
            op_name = entry.get("op")
            args = dict(entry.get("args") or {})
            args.setdefault("actor", actor)
            args.setdefault("source", source)
            args["batch_id"] = batch_id
            fn = _OPERATION_DISPATCH.get(op_name)
            if fn is None:
                raise BatchFailed(f"unknown op: {op_name}")
            result = fn(conn, **args)
            if result.get("revision_id"):
                revision_ids.append(result["revision_id"])
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return {"batch_id": batch_id, "revision_ids": revision_ids, "label": label}


# ============================================================
# Validation
# ============================================================

def run_validation(conn: sqlite3.Connection, project_id: str, *,
                   with_verdicts: bool = False, with_targets: bool = False,
                   force: bool = False, actor: str,
                   framework_version: str = "0.1.0") -> dict:
    """Run structural checks (always) and verdict checks (if with_verdicts).

    Structural: layer membership, tree property, intra-layer DAG, external
    realization, coverage. with_targets=True also runs target-state checks
    (block DAG cycles + stale planned targets).

    Verdicts: each node's mechanism (automated_check / python_assertion /
    human_signoff / llm_judge) is run. Results land in `verdicts` rows;
    nodes.verdict_status is updated to the resolved (post-propagation) status.

    Returns dict with validation_id, status='finished', issues list, counts.
    """
    from . import validate

    actor = _require_actor(actor)
    _ensure_project(conn, project_id)

    project_row = conn.execute(
        "SELECT spec_config FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    try:
        spec_config = json.loads(project_row["spec_config"]) if project_row else {}
    except (json.JSONDecodeError, TypeError):
        spec_config = {}
    layer_names = [L.get("name", "") for L in (spec_config.get("layers") or [])]
    project_root = spec_config.get("project_root", "") or ""

    started = _now_iso()
    cur = conn.execute(
        "INSERT INTO validations (project_id, started_at, status, "
        "verdicts_run, targets_run, framework_version) "
        "VALUES (?, ?, 'in_progress', ?, ?, ?)",
        (project_id, started,
         1 if with_verdicts else 0, 1 if with_targets else 0,
         framework_version),
    )
    validation_id = cur.lastrowid
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'validation_started', ?)",
        (started, project_id,
         json.dumps({"validation_id": validation_id, "actor": actor})),
    )

    nbi = validate._build_nodes_by_id(conn, project_id)
    issues = []
    issues.extend(validate.check_layer_membership(layer_names, nbi))
    issues.extend(validate.check_tree_property(layer_names, nbi))
    issues.extend(validate.check_intra_layer_dag(nbi))
    ext_issues, children_of = validate.check_external_realization(nbi)
    issues.extend(ext_issues)
    issues.extend(validate.check_coverage(layer_names, nbi, children_of))
    issues.extend(validate.check_rationale(nbi))  # advisory on missing rationale
    if with_targets:
        issues.extend(validate.check_targets(nbi))
    issues.extend(validate.check_cross_project_edges(conn))

    verdicts_written = 0
    verdicts_map: dict = {}
    if with_verdicts:
        judge_cmd = validate._resolve_judge_command(spec_config)
        verdicts_map = validate.run_verdicts(conn, project_id, nbi,
                                              project_root, force,
                                              judge_cmd=judge_cmd)
        validate.resolve_external(verdicts_map, nbi)
        validate.propagate_failures(verdicts_map, nbi)
        for nid, v in verdicts_map.items():
            conn.execute(
                "INSERT INTO verdicts (validation_id, project_id, node_id, "
                "mechanism, status, source, evidence_ref, evidence_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (validation_id, project_id, nid,
                 nbi[nid].get("verdict_mechanism") or "",
                 v["status"], v["source"], v.get("evidence_ref", ""),
                 v.get("evidence_hash", "")),
            )
            conn.execute(
                "UPDATE nodes SET verdict_status = ?, verdict_last_checked = ? "
                "WHERE project_id = ? AND node_id = ?",
                (v["status"], v.get("last_checked"), project_id, nid),
            )
            verdicts_written += 1

    finished = _now_iso()
    conn.execute(
        "UPDATE validations SET finished_at = ?, status = ?, "
        "nodes_total = ?, issues_total = ?, verdicts_run = ? "
        "WHERE validation_id = ?",
        (finished, "finished", len(nbi), len(issues), verdicts_written,
         validation_id),
    )
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'validation_finished', ?)",
        (finished, project_id, json.dumps({
            "validation_id": validation_id, "actor": actor,
            "issues_total": len(issues), "verdicts_run": verdicts_written,
        })),
    )
    return {"project_id": project_id, "validation_id": validation_id,
            "status": "finished", "issues": issues,
            "verdicts_run": verdicts_written,
            "issues_total": len(issues),
            "nodes_total": len(nbi)}


# ============================================================
# Portfolio links (Topic H)
# ============================================================

def link_portfolio(conn: sqlite3.Connection, theme_node_id: str,
                   project_id: str, node_id: str, *, actor: str) -> dict:
    """A theme tracks a team node via portfolio_links (L20)."""
    from .constants import PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER

    actor = _require_actor(actor)
    _ensure_project(conn, project_id)

    theme = conn.execute(
        "SELECT 1 FROM nodes WHERE project_id = ? AND node_id = ? "
        "AND layer = ? AND deleted_at IS NULL",
        (PORTFOLIO_PROJECT_ID, theme_node_id, PORTFOLIO_THEME_LAYER),
    ).fetchone()
    if theme is None:
        raise ValueError(
            f"theme node {theme_node_id!r} not found in project "
            f"{PORTFOLIO_PROJECT_ID!r} layer {PORTFOLIO_THEME_LAYER!r}"
        )

    target = conn.execute(
        "SELECT 1 FROM nodes WHERE project_id = ? AND node_id = ? "
        "AND deleted_at IS NULL",
        (project_id, node_id),
    ).fetchone()
    if target is None:
        raise ValueError(f"team node {project_id}/{node_id} not found")

    now = _now_iso()
    conn.execute(
        "INSERT OR IGNORE INTO portfolio_links "
        "(theme_node_id, project_id, node_id, created_at) "
        "VALUES (?, ?, ?, ?)",
        (theme_node_id, project_id, node_id, now),
    )
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'portfolio_link', ?)",
        (now, PORTFOLIO_PROJECT_ID, json.dumps({
            "theme_node_id": theme_node_id,
            "project_id": project_id,
            "node_id": node_id,
            "actor": actor,
        })),
    )
    return {
        "theme_node_id": theme_node_id,
        "project_id": project_id,
        "node_id": node_id,
    }


def unlink_portfolio(conn: sqlite3.Connection, theme_node_id: str,
                     project_id: str, node_id: str, *, actor: str) -> dict:
    actor = _require_actor(actor)
    from .constants import PORTFOLIO_PROJECT_ID

    conn.execute(
        "DELETE FROM portfolio_links "
        "WHERE theme_node_id = ? AND project_id = ? AND node_id = ?",
        (theme_node_id, project_id, node_id),
    )
    now = _now_iso()
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'portfolio_unlink', ?)",
        (now, PORTFOLIO_PROJECT_ID, json.dumps({
            "theme_node_id": theme_node_id,
            "project_id": project_id,
            "node_id": node_id,
            "actor": actor,
        })),
    )
    return {
        "theme_node_id": theme_node_id,
        "project_id": project_id,
        "node_id": node_id,
        "removed": True,
    }


# ============================================================
# Cross-project edges (Topic I)
# ============================================================

_CROSS_EDGE_KINDS = frozenset({"blocks", "depends_on"})


def _require_active_project(conn: sqlite3.Connection, project_id: str) -> None:
    row = conn.execute(
        "SELECT archived_at FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if row is None:
        raise ValueError(f"project {project_id!r} not found")
    if row["archived_at"]:
        raise ValueError(
            f"project {project_id!r} is archived; cannot create cross-project edge"
        )


def create_cross_edge(conn: sqlite3.Connection,
                      src_project_id: str, src_node_id: str,
                      dst_project_id: str, dst_node_id: str,
                      edge_kind: str, *, actor: str) -> dict:
    actor = _require_actor(actor)
    edge_kind = (edge_kind or "").strip()
    if edge_kind not in _CROSS_EDGE_KINDS:
        raise ValueError(
            f"edge_kind must be one of {sorted(_CROSS_EDGE_KINDS)}, got {edge_kind!r}"
        )

    if (src_project_id == dst_project_id and src_node_id == dst_node_id):
        raise ValueError(
            f"cross-project edge cannot connect {src_project_id}/{src_node_id} to itself"
        )

    _require_active_project(conn, src_project_id)
    _require_active_project(conn, dst_project_id)

    for pid, nid in ((src_project_id, src_node_id),
                     (dst_project_id, dst_node_id)):
        row = conn.execute(
            "SELECT 1 FROM nodes WHERE project_id = ? AND node_id = ? "
            "AND deleted_at IS NULL",
            (pid, nid),
        ).fetchone()
        if row is None:
            raise ValueError(f"node {pid}/{nid} not found")

    now = _now_iso()
    conn.execute(
        "INSERT OR IGNORE INTO cross_project_edges "
        "(src_project_id, src_node_id, dst_project_id, dst_node_id, "
        "edge_kind, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (src_project_id, src_node_id, dst_project_id, dst_node_id,
         edge_kind, now),
    )
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'cross_edge_created', ?)",
        (now, src_project_id, json.dumps({
            "src_project_id": src_project_id,
            "src_node_id": src_node_id,
            "dst_project_id": dst_project_id,
            "dst_node_id": dst_node_id,
            "edge_kind": edge_kind,
            "actor": actor,
        })),
    )
    return {
        "src_project_id": src_project_id,
        "src_node_id": src_node_id,
        "dst_project_id": dst_project_id,
        "dst_node_id": dst_node_id,
        "edge_kind": edge_kind,
    }


def delete_cross_edge(conn: sqlite3.Connection,
                      src_project_id: str, src_node_id: str,
                      dst_project_id: str, dst_node_id: str,
                      edge_kind: str, *, actor: str) -> dict:
    actor = _require_actor(actor)
    edge_kind = (edge_kind or "").strip()
    conn.execute(
        "DELETE FROM cross_project_edges "
        "WHERE src_project_id = ? AND src_node_id = ? "
        "AND dst_project_id = ? AND dst_node_id = ? AND edge_kind = ?",
        (src_project_id, src_node_id, dst_project_id, dst_node_id, edge_kind),
    )
    now = _now_iso()
    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'cross_edge_deleted', ?)",
        (now, src_project_id, json.dumps({
            "src_project_id": src_project_id,
            "src_node_id": src_node_id,
            "dst_project_id": dst_project_id,
            "dst_node_id": dst_node_id,
            "edge_kind": edge_kind,
            "actor": actor,
        })),
    )
    return {
        "src_project_id": src_project_id,
        "src_node_id": src_node_id,
        "dst_project_id": dst_project_id,
        "dst_node_id": dst_node_id,
        "edge_kind": edge_kind,
        "removed": True,
    }
