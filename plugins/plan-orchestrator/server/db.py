"""
db.py — SQLite helpers for progress-tracker.

Thin functional API; no ORM. Every write also appends to the events table for audit.
All times are ISO-8601 UTC. Idempotent where reasonable (same state set twice = no-op).
"""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_DB = Path(os.environ.get("PROGRESS_TRACKER_DB", str(Path.home() / ".claude" / "progress.db")))
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def connect(db_path=None):
    """Open a connection with WAL mode + foreign keys + row factory."""
    db_path = Path(db_path or DEFAULT_DB)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    fresh = not db_path.exists()
    conn = sqlite3.connect(str(db_path), isolation_level=None, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    if fresh:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
            conn.executescript(fh.read())
    return conn


# ============================================================
# Write side
# ============================================================

def _add_event(conn, event_type, detail=None, project_id=None, phase_id=None, dispatch_id=None):
    conn.execute(
        "INSERT INTO events (ts, project_id, phase_id, dispatch_id, event_type, detail) "
        "VALUES (?,?,?,?,?,?)",
        (now_iso(), project_id, phase_id, dispatch_id, event_type, detail),
    )


def _touch_project(conn, project_id):
    conn.execute("UPDATE projects SET last_update = ? WHERE project_id = ?", (now_iso(), project_id))


def ensure_project(conn, project_id, label=None, work_dir=None):
    """Create a project row if absent. Idempotent."""
    existing = conn.execute(
        "SELECT project_id FROM projects WHERE project_id = ?", (project_id,)
    ).fetchone()
    if existing:
        if label or work_dir:
            conn.execute(
                "UPDATE projects SET label = COALESCE(?, label), work_dir = COALESCE(?, work_dir), last_update = ? "
                "WHERE project_id = ?",
                (label, work_dir, now_iso(), project_id),
            )
        return
    ts = now_iso()
    conn.execute(
        "INSERT INTO projects (project_id, label, work_dir, started_at, last_update) VALUES (?,?,?,?,?)",
        (project_id, label or project_id, work_dir, ts, ts),
    )


def ensure_phase(conn, project_id, phase_id, name=None):
    """Create a phase row if absent. Idempotent."""
    existing = conn.execute(
        "SELECT phase_id FROM phases WHERE project_id = ? AND phase_id = ?",
        (project_id, phase_id),
    ).fetchone()
    if existing:
        if name:
            conn.execute(
                "UPDATE phases SET name = COALESCE(?, name) WHERE project_id = ? AND phase_id = ?",
                (name, project_id, phase_id),
            )
        return
    conn.execute(
        "INSERT INTO phases (project_id, phase_id, name) VALUES (?,?,?)",
        (project_id, phase_id, name),
    )


def init_dispatch(conn, dispatch_id, project_id, phase_id, role, agent_model, items):
    """Create or replace a dispatch with its initial TODO items.

    `items` is a list of strings (descriptions). All start in state 'pending'.
    Re-initializing the same dispatch_id REPLACES the previous TODO (intended for
    redispatch; the prior state is preserved in the events table).
    """
    ts = now_iso()
    ensure_project(conn, project_id)
    ensure_phase(conn, project_id, phase_id)
    # Delete prior items (CASCADE handles dispatches->items)
    conn.execute("DELETE FROM dispatches WHERE dispatch_id = ?", (dispatch_id,))
    conn.execute(
        "INSERT INTO dispatches "
        "(dispatch_id, project_id, phase_id, role, agent_model, status, started_at, last_update) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (dispatch_id, project_id, phase_id, role, agent_model, "IN_PROGRESS", ts, ts),
    )
    for i, desc in enumerate(items):
        conn.execute(
            "INSERT INTO todo_items (dispatch_id, item_idx, description, state, updated_at) "
            "VALUES (?,?,?,?,?)",
            (dispatch_id, i, desc, "pending", ts),
        )
    _add_event(conn, "init", detail=f"{len(items)} items", project_id=project_id, phase_id=phase_id, dispatch_id=dispatch_id)
    _touch_project(conn, project_id)


def _dispatch_ids(conn, dispatch_id):
    row = conn.execute(
        "SELECT project_id, phase_id FROM dispatches WHERE dispatch_id = ?", (dispatch_id,)
    ).fetchone()
    if not row:
        raise KeyError(f"dispatch {dispatch_id} not found")
    return row["project_id"], row["phase_id"]


def start_item(conn, dispatch_id, item_idx):
    """Flip [ ] → [-]. Update last_update on dispatch."""
    ts = now_iso()
    project_id, phase_id = _dispatch_ids(conn, dispatch_id)
    row = conn.execute(
        "SELECT state FROM todo_items WHERE dispatch_id = ? AND item_idx = ?",
        (dispatch_id, item_idx),
    ).fetchone()
    if not row:
        raise KeyError(f"item {item_idx} not in {dispatch_id}")
    if row["state"] == "done":
        return  # idempotent: don't regress
    conn.execute(
        "UPDATE todo_items SET state = 'in_progress', updated_at = ? "
        "WHERE dispatch_id = ? AND item_idx = ?",
        (ts, dispatch_id, item_idx),
    )
    conn.execute("UPDATE dispatches SET last_update = ?, status = 'IN_PROGRESS', blocker = NULL WHERE dispatch_id = ?", (ts, dispatch_id))
    _add_event(conn, "start", detail=f"item {item_idx}", project_id=project_id, phase_id=phase_id, dispatch_id=dispatch_id)
    _touch_project(conn, project_id)


def done_item(conn, dispatch_id, item_idx):
    """Flip → [x]. Update last_update + auto-finish if all done."""
    ts = now_iso()
    project_id, phase_id = _dispatch_ids(conn, dispatch_id)
    conn.execute(
        "UPDATE todo_items SET state = 'done', updated_at = ? "
        "WHERE dispatch_id = ? AND item_idx = ?",
        (ts, dispatch_id, item_idx),
    )
    conn.execute("UPDATE dispatches SET last_update = ? WHERE dispatch_id = ?", (ts, dispatch_id))
    _add_event(conn, "done", detail=f"item {item_idx}", project_id=project_id, phase_id=phase_id, dispatch_id=dispatch_id)
    _touch_project(conn, project_id)


def block_dispatch(conn, dispatch_id, blocker):
    ts = now_iso()
    project_id, phase_id = _dispatch_ids(conn, dispatch_id)
    conn.execute(
        "UPDATE dispatches SET status = 'BLOCKED', blocker = ?, last_update = ? WHERE dispatch_id = ?",
        (blocker, ts, dispatch_id),
    )
    _add_event(conn, "block", detail=blocker, project_id=project_id, phase_id=phase_id, dispatch_id=dispatch_id)
    _touch_project(conn, project_id)


def halt_dispatch(conn, dispatch_id, reason):
    ts = now_iso()
    project_id, phase_id = _dispatch_ids(conn, dispatch_id)
    conn.execute(
        "UPDATE dispatches SET status = 'HALTED', halt_reason = ?, last_update = ? WHERE dispatch_id = ?",
        (reason, ts, dispatch_id),
    )
    _add_event(conn, "halt", detail=reason, project_id=project_id, phase_id=phase_id, dispatch_id=dispatch_id)
    _touch_project(conn, project_id)


def finish_dispatch(conn, dispatch_id):
    """Mark all items done and dispatch DONE."""
    ts = now_iso()
    project_id, phase_id = _dispatch_ids(conn, dispatch_id)
    conn.execute(
        "UPDATE todo_items SET state = 'done', updated_at = ? WHERE dispatch_id = ?",
        (ts, dispatch_id),
    )
    conn.execute(
        "UPDATE dispatches SET status = 'DONE', last_update = ?, blocker = NULL WHERE dispatch_id = ?",
        (ts, dispatch_id),
    )
    _add_event(conn, "finish", project_id=project_id, phase_id=phase_id, dispatch_id=dispatch_id)
    _touch_project(conn, project_id)


def add_note(conn, dispatch_id, text):
    project_id, phase_id = _dispatch_ids(conn, dispatch_id)
    _add_event(conn, "note", detail=text, project_id=project_id, phase_id=phase_id, dispatch_id=dispatch_id)
    _touch_project(conn, project_id)


# ============================================================
# Read side
# ============================================================

def _rollup_status(dispatch_statuses):
    """Phase status from agent statuses."""
    if not dispatch_statuses:
        return "PENDING"
    s = set(dispatch_statuses)
    if s == {"DONE"}:
        return "DONE"
    if "HALTED" in s:
        return "HALTED"
    if "BLOCKED" in s:
        return "BLOCKED"
    if "IN_PROGRESS" in s:
        return "IN_PROGRESS"
    return "PENDING" if "PENDING" in s else "DONE"


def _dispatch_dict(conn, row):
    progress = conn.execute(
        "SELECT "
        "  SUM(CASE WHEN state = 'done' THEN 1 ELSE 0 END) AS done, "
        "  COUNT(*) AS total "
        "FROM todo_items WHERE dispatch_id = ?",
        (row["dispatch_id"],),
    ).fetchone()
    return {
        "dispatch_id": row["dispatch_id"],
        "project_id": row["project_id"],
        "phase_id": row["phase_id"],
        "role": row["role"],
        "agent_model": row["agent_model"],
        "status": row["status"],
        "started_at": row["started_at"],
        "last_update": row["last_update"],
        "blocker": row["blocker"],
        "halt_reason": row["halt_reason"],
        "progress_done": progress["done"] or 0,
        "progress_total": progress["total"] or 0,
    }


def peek_dispatch(conn, dispatch_id):
    row = conn.execute("SELECT * FROM dispatches WHERE dispatch_id = ?", (dispatch_id,)).fetchone()
    if not row:
        return None
    d = _dispatch_dict(conn, row)
    items = conn.execute(
        "SELECT item_idx, description, state, updated_at FROM todo_items WHERE dispatch_id = ? ORDER BY item_idx",
        (dispatch_id,),
    ).fetchall()
    d["items"] = [dict(i) for i in items]
    return d


def peek_phase(conn, project_id, phase_id):
    phase_row = conn.execute(
        "SELECT phase_id, name FROM phases WHERE project_id = ? AND phase_id = ?",
        (project_id, phase_id),
    ).fetchone()
    if not phase_row:
        return None
    dispatch_rows = conn.execute(
        "SELECT * FROM dispatches WHERE project_id = ? AND phase_id = ? ORDER BY started_at",
        (project_id, phase_id),
    ).fetchall()
    dispatches = [_dispatch_dict(conn, r) for r in dispatch_rows]
    progress_done = sum(d["progress_done"] for d in dispatches)
    progress_total = sum(d["progress_total"] for d in dispatches)
    return {
        "project_id": project_id,
        "phase_id": phase_id,
        "name": phase_row["name"],
        "status": _rollup_status([d["status"] for d in dispatches]),
        "dispatches": dispatches,
        "dispatch_count": len(dispatches),
        "progress_done": progress_done,
        "progress_total": progress_total,
        "progress_pct": (progress_done * 100 // progress_total) if progress_total else 0,
        "last_update": max((d["last_update"] for d in dispatches), default=""),
        "blockers": [d["blocker"] for d in dispatches if d["status"] == "BLOCKED" and d["blocker"]],
    }


def peek_project(conn, project_id):
    p = conn.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone()
    if not p:
        return None
    phase_ids = [
        r["phase_id"]
        for r in conn.execute(
            "SELECT phase_id FROM phases WHERE project_id = ? ORDER BY phase_id", (project_id,)
        ).fetchall()
    ]
    phases = [peek_phase(conn, project_id, pid) for pid in phase_ids]
    progress_done = sum(ph["progress_done"] for ph in phases)
    progress_total = sum(ph["progress_total"] for ph in phases)
    return {
        "project_id": project_id,
        "label": p["label"],
        "work_dir": p["work_dir"],
        "started_at": p["started_at"],
        "last_update": p["last_update"],
        "phases": phases,
        "status": _rollup_status([ph["status"] for ph in phases]),
        "progress_done": progress_done,
        "progress_total": progress_total,
        "progress_pct": (progress_done * 100 // progress_total) if progress_total else 0,
    }


def peek_all(conn):
    project_ids = [
        r["project_id"]
        for r in conn.execute(
            "SELECT project_id FROM projects ORDER BY last_update DESC"
        ).fetchall()
    ]
    return [peek_project(conn, pid) for pid in project_ids]


def recent_events(conn, limit=50, project_id=None):
    if project_id:
        rows = conn.execute(
            "SELECT * FROM events WHERE project_id = ? ORDER BY event_id DESC LIMIT ?",
            (project_id, limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM events ORDER BY event_id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]
