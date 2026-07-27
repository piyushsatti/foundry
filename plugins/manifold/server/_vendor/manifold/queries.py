"""
Read functions for manifold.

Each function accepts a sqlite3.Connection as first arg + named params. Returns
dicts (via Row factory) or lists of dicts. Never raises on "not found" — returns
None or empty list. Callers convert to MCP/HTTP error envelopes.

Pagination convention: `limit` and `cursor`. Cursors are opaque strings (we use
"id:<value>" form internally) so callers don't need to know the column.
"""
import difflib
import json
import sqlite3
from typing import Optional


NODE_COLUMNS = (
    "project_id, node_id, layer, title, kind, realized_by_external, body, "
    "contract, delegate_to, applies_to, target_status, target_shape, "
    "target_rationale_ref, target_achieved_when, target_achieved_at, "
    "target_superseded_by, verdict_mechanism, verdict_check, verdict_assertion, "
    "verdict_judge_prompt, verdict_status, verdict_evidence_ref, "
    "verdict_evidence_hash, verdict_last_checked, "
    "rationale, alternatives_considered, "
    "current_revision_id, last_modified_at, deleted_at"
)

JSON_NODE_FIELDS = ("contract", "applies_to")


def _parse_json_field(row: sqlite3.Row, field: str):
    raw = row[field]
    if raw is None or raw == "":
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def _row_to_node(row: sqlite3.Row) -> dict:
    d = dict(row)
    for f in JSON_NODE_FIELDS:
        d[f] = _parse_json_field(row, f)
    return d


def _cursor_value(cursor: str) -> str:
    if cursor and cursor.startswith("id:"):
        return cursor[3:]
    return cursor or ""


# ============================================================
# Projects
# ============================================================

def get_project(conn: sqlite3.Connection, project_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT project_id, label, spec_config, created_at, archived_at, last_revision_id "
        "FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["spec_config"] = _parse_json_field(row, "spec_config")
    return result


def list_projects(conn: sqlite3.Connection, include_archived: bool = False,
                  limit: int = 50, cursor: Optional[str] = None) -> list[dict]:
    sql = ("SELECT project_id, label, spec_config, created_at, archived_at, last_revision_id "
           "FROM projects")
    where = []
    params: list = []
    if not include_archived:
        where.append("archived_at IS NULL")
    if cursor:
        where.append("project_id > ?")
        params.append(_cursor_value(cursor))
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY project_id LIMIT ?"
    params.append(int(limit))
    rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["spec_config"] = _parse_json_field(r, "spec_config")
        out.append(d)
    return out


# ============================================================
# Nodes
# ============================================================

def get_node(conn: sqlite3.Connection, project_id: str, node_id: str,
             include_deleted: bool = False) -> Optional[dict]:
    sql = f"SELECT {NODE_COLUMNS} FROM nodes WHERE project_id = ? AND node_id = ?"
    if not include_deleted:
        sql += " AND deleted_at IS NULL"
    row = conn.execute(sql, (project_id, node_id)).fetchone()
    return _row_to_node(row) if row else None


def list_nodes(conn: sqlite3.Connection, project_id: str,
               layer: Optional[str] = None, limit: int = 50,
               cursor: Optional[str] = None,
               include_deleted: bool = False) -> list[dict]:
    sql = f"SELECT {NODE_COLUMNS} FROM nodes WHERE project_id = ?"
    params: list = [project_id]
    if not include_deleted:
        sql += " AND deleted_at IS NULL"
    if layer:
        sql += " AND layer = ?"
        params.append(layer)
    if cursor:
        sql += " AND node_id > ?"
        params.append(_cursor_value(cursor))
    sql += " ORDER BY node_id LIMIT ?"
    params.append(int(limit))
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_node(r) for r in rows]


# ============================================================
# Targets
# ============================================================

def list_targets(conn: sqlite3.Connection, project_id: Optional[str] = None,
                 status: Optional[str] = None,
                 layer: Optional[str] = None,
                 older_than_days: Optional[int] = None,
                 limit: int = 50, cursor: Optional[str] = None) -> list[dict]:
    sql = (f"SELECT {NODE_COLUMNS}, "
           "(julianday('now') - julianday(last_modified_at)) AS days_since "
           "FROM nodes WHERE deleted_at IS NULL")
    params: list = []
    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)
    if status is not None:
        sql += " AND target_status = ?"
        params.append(status)
    else:
        sql += " AND target_status IS NOT NULL AND target_status != ''"
    if layer:
        sql += " AND layer = ?"
        params.append(layer)
    if older_than_days is not None:
        sql += " AND (julianday('now') - julianday(last_modified_at)) > ?"
        params.append(int(older_than_days))
    if cursor:
        sql += " AND node_id > ?"
        params.append(_cursor_value(cursor))
    sql += " ORDER BY last_modified_at DESC, node_id LIMIT ?"
    params.append(int(limit))
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_node(r) for r in rows]


# ============================================================
# Revisions
# ============================================================

def list_revisions(conn: sqlite3.Connection, project_id: str, node_id: str,
                   since: Optional[int] = None, before: Optional[int] = None,
                   limit: int = 20) -> list[dict]:
    sql = ("SELECT revision_id, project_id, node_id, ts, change_type, "
           "prev_revision_id, change_summary, batch_id, source, actor, "
           "git_sha, note FROM revisions "
           "WHERE project_id = ? AND node_id = ?")
    params: list = [project_id, node_id]
    if since is not None:
        sql += " AND revision_id > ?"
        params.append(int(since))
    if before is not None:
        sql += " AND revision_id < ?"
        params.append(int(before))
    sql += " ORDER BY ts DESC, revision_id DESC LIMIT ?"
    params.append(int(limit))
    rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["change_summary"] = _parse_json_field(r, "change_summary")
        out.append(d)
    return out


def list_changes_since(conn: sqlite3.Connection,
                       project_id: Optional[str] = None,
                       since_ts: Optional[str] = None,
                       since_revision_id: Optional[int] = None,
                       limit: int = 100, cursor: Optional[str] = None) -> list[dict]:
    if since_ts is None and since_revision_id is None:
        raise ValueError("one of since_ts or since_revision_id must be given")
    sql = ("SELECT revision_id, project_id, node_id, ts, change_type, "
           "change_summary, source, actor, git_sha "
           "FROM revisions WHERE 1=1")
    params: list = []
    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)
    if since_ts:
        sql += " AND ts > ?"
        params.append(since_ts)
    if since_revision_id is not None:
        sql += " AND revision_id > ?"
        params.append(int(since_revision_id))
    if cursor:
        sql += " AND revision_id > ?"
        params.append(int(_cursor_value(cursor) or 0))
    sql += " ORDER BY revision_id ASC LIMIT ?"
    params.append(int(limit))
    rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["change_summary"] = _parse_json_field(r, "change_summary")
        out.append(d)
    return out


def diff_revisions(conn: sqlite3.Connection, project_id: str, node_id: str,
                   from_revision_id: int, to_revision_id: int) -> Optional[dict]:
    rows = conn.execute(
        "SELECT revision_id, snapshot FROM revisions "
        "WHERE project_id = ? AND node_id = ? AND revision_id IN (?, ?)",
        (project_id, node_id, int(from_revision_id), int(to_revision_id)),
    ).fetchall()
    by_id = {r["revision_id"]: json.loads(r["snapshot"]) for r in rows}
    if from_revision_id not in by_id or to_revision_id not in by_id:
        return None
    a, b = by_id[from_revision_id], by_id[to_revision_id]
    fields = []
    for key in sorted(set(a) | set(b)):
        if a.get(key) != b.get(key):
            fields.append({"field": key, "old": a.get(key), "new": b.get(key)})
    body_diff = list(difflib.unified_diff(
        (a.get("body", "") or "").splitlines(),
        (b.get("body", "") or "").splitlines(),
        lineterm="", n=3,
    ))
    return {"from": from_revision_id, "to": to_revision_id,
            "fields": fields, "body_diff": body_diff}


# ============================================================
# Verdicts (incl. unstable verdicts / flips)
# ============================================================

def list_unstable_verdicts(conn: sqlite3.Connection,
                           project_id: Optional[str] = None, k: int = 3,
                           mechanism: Optional[str] = None,
                           limit: int = 50,
                           cursor: Optional[str] = None) -> list[dict]:
    """Verdicts whose status varies across the last K runs.

    `mechanism` filters to one mechanism (defaults to 'llm_judge' for
    backward compatibility — that's the only one where flips are interesting).
    Pass mechanism='' to see flips across all mechanisms.
    Uses a window function (SQLite >= 3.25).
    """
    sql_parts = [
        "WITH last_k AS (",
        "  SELECT project_id, node_id, status,",
        "         ROW_NUMBER() OVER (PARTITION BY project_id, node_id "
        "                             ORDER BY validation_id DESC) AS rn",
        "  FROM verdicts",
        "  WHERE 1=1",
    ]
    params: list = []
    effective_mechanism = "llm_judge" if mechanism is None else mechanism
    if effective_mechanism:
        sql_parts.append("    AND mechanism = ?")
        params.append(effective_mechanism)
    if project_id:
        sql_parts.append("    AND project_id = ?")
        params.append(project_id)
    sql_parts.extend([
        ")",
        "SELECT project_id, node_id, GROUP_CONCAT(DISTINCT status) AS statuses",
        "FROM last_k WHERE rn <= ?",
        "GROUP BY project_id, node_id",
        "HAVING COUNT(DISTINCT status) > 1",
    ])
    params.append(int(k))
    if cursor:
        sql_parts.append(" AND node_id > ?")
        params.append(_cursor_value(cursor))
    sql_parts.append("ORDER BY project_id, node_id LIMIT ?")
    params.append(int(limit))
    sql = "\n".join(sql_parts)
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# Validations
# ============================================================

def get_validation(conn: sqlite3.Connection, validation_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM validations WHERE validation_id = ?",
        (int(validation_id),),
    ).fetchone()
    if row is None:
        return None
    return dict(row)


def list_validations(conn: sqlite3.Connection,
                     project_id: Optional[str] = None,
                     limit: int = 20) -> list[dict]:
    sql = "SELECT * FROM validations"
    params: list = []
    if project_id:
        sql += " WHERE project_id = ?"
        params.append(project_id)
    sql += " ORDER BY validation_id DESC LIMIT ?"
    params.append(int(limit))
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ============================================================
# Graph traversal — node_edges (the audit-mandated table)
# ============================================================

def list_blocking_chain(conn: sqlite3.Connection, project_id: str,
                        node_id: str, direct_only: bool = False) -> list[dict]:
    """Return nodes that block `node_id` (transitively by default).

    A node X "blocks" Y when there's an edge (src=X, dst=Y, kind='blocks').
    Transitively: returns everything in the upstream chain.
    """
    if direct_only:
        rows = conn.execute(
            "SELECT src_node_id FROM node_edges "
            "WHERE project_id = ? AND dst_node_id = ? AND edge_kind = 'blocks'",
            (project_id, node_id),
        ).fetchall()
        return [{"node_id": r["src_node_id"]} for r in rows]

    rows = conn.execute(
        """
        WITH RECURSIVE chain(node_id, depth) AS (
          SELECT ?, 0
          UNION
          SELECT e.src_node_id, c.depth + 1 FROM node_edges e
          JOIN chain c ON e.dst_node_id = c.node_id
          WHERE e.project_id = ? AND e.edge_kind = 'blocks'
        )
        SELECT node_id, depth FROM chain WHERE node_id != ? ORDER BY depth, node_id
        """,
        (node_id, project_id, node_id),
    ).fetchall()
    return [dict(r) for r in rows]


def list_uncovered(conn: sqlite3.Connection, project_id: str,
                   layer: str) -> list[dict]:
    """Parent-layer nodes that have no children at `layer`.

    Walks the project's spec_config to find the layer just above `layer`.
    Skips kind=constraint and realized_by_external nodes (they correctly
    have no children).
    """
    proj = get_project(conn, project_id)
    if proj is None:
        return []
    layers = [l.get("name") for l in (proj["spec_config"] or {}).get("layers") or []
              if isinstance(l, dict)]
    if layer not in layers:
        return []
    idx = layers.index(layer)
    if idx == 0:
        return []  # top layer has no parent layer
    parent_layer = layers[idx - 1]

    rows = conn.execute(
        f"""
        SELECT {NODE_COLUMNS} FROM nodes n
        WHERE n.project_id = ? AND n.layer = ? AND n.kind != 'constraint'
          AND (n.realized_by_external IS NULL OR n.realized_by_external = '')
          AND n.deleted_at IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM node_edges e
            JOIN nodes c ON c.project_id = e.project_id AND c.node_id = e.src_node_id
            WHERE e.project_id = n.project_id AND e.dst_node_id = n.node_id
              AND e.edge_kind = 'parent' AND c.layer = ?
              AND c.deleted_at IS NULL
          )
        ORDER BY n.node_id
        """,
        (project_id, parent_layer, layer),
    ).fetchall()
    return [_row_to_node(r) for r in rows]


# ============================================================
# Fuzzy node lookup
# ============================================================

def resolve_node(conn: sqlite3.Connection, project_id: str,
                 query: str) -> list[str]:
    """Fuzzy lookup by node_id prefix or title substring."""
    q = (query or "").strip()
    if not q:
        return []
    rows = conn.execute(
        """
        SELECT node_id FROM nodes
        WHERE project_id = ?
          AND (LOWER(node_id) LIKE LOWER(? || '%')
               OR LOWER(title) LIKE LOWER('%' || ? || '%'))
          AND deleted_at IS NULL
        ORDER BY CASE WHEN LOWER(node_id) = LOWER(?) THEN 0
                      WHEN LOWER(node_id) LIKE LOWER(? || '%') THEN 1
                      ELSE 2 END,
                 node_id
        LIMIT 20
        """,
        (project_id, q, q, q, q),
    ).fetchall()
    return [r["node_id"] for r in rows]


# ============================================================
# Composite: peek_node_full
# ============================================================

def peek_node_full(conn: sqlite3.Connection, project_id: str, node_id: str,
                   include: tuple = ("parents", "verdict")) -> Optional[dict]:
    """Composite read for plan-orchestrator-style consumers.

    `include` may contain any of: 'parents', 'children', 'depends_on',
    'blockers', 'verdict_history', 'revisions', 'verdict'.
    """
    node = get_node(conn, project_id, node_id)
    if node is None:
        return None
    out: dict = dict(node)
    if "parents" in include:
        rows = conn.execute(
            "SELECT n.node_id, n.title, n.layer, n.target_status "
            "FROM node_edges e "
            "JOIN nodes n ON n.project_id = e.project_id AND n.node_id = e.dst_node_id "
            "WHERE e.project_id = ? AND e.src_node_id = ? AND e.edge_kind = 'parent' "
            "AND n.deleted_at IS NULL",
            (project_id, node_id),
        ).fetchall()
        out["parents_detail"] = [dict(r) for r in rows]
    if "children" in include:
        rows = conn.execute(
            "SELECT n.node_id, n.title, n.layer, n.target_status "
            "FROM node_edges e "
            "JOIN nodes n ON n.project_id = e.project_id AND n.node_id = e.src_node_id "
            "WHERE e.project_id = ? AND e.dst_node_id = ? AND e.edge_kind = 'parent' "
            "AND n.deleted_at IS NULL",
            (project_id, node_id),
        ).fetchall()
        out["children"] = [dict(r) for r in rows]
    if "depends_on" in include:
        rows = conn.execute(
            "SELECT n.node_id, n.title FROM node_edges e "
            "JOIN nodes n ON n.project_id = e.project_id AND n.node_id = e.dst_node_id "
            "WHERE e.project_id = ? AND e.src_node_id = ? AND e.edge_kind = 'depends_on' "
            "AND n.deleted_at IS NULL",
            (project_id, node_id),
        ).fetchall()
        out["depends_on_detail"] = [dict(r) for r in rows]
    if "blockers" in include:
        rows = conn.execute(
            "SELECT dst_node_id FROM node_edges "
            "WHERE project_id = ? AND src_node_id = ? AND edge_kind = 'blocks'",
            (project_id, node_id),
        ).fetchall()
        out["blockers"] = [r["dst_node_id"] for r in rows]
    if "verdict_history" in include:
        rows = conn.execute(
            "SELECT validation_id, status, mechanism, source, evidence_ref "
            "FROM verdicts WHERE project_id = ? AND node_id = ? "
            "ORDER BY validation_id DESC LIMIT 5",
            (project_id, node_id),
        ).fetchall()
        out["verdict_history"] = [dict(r) for r in rows]
    if "revisions" in include:
        out["recent_revisions"] = list_revisions(conn, project_id, node_id, limit=5)
    if "verdict" in include:
        out["verdict"] = {
            "mechanism": node.get("verdict_mechanism") or None,
            "stored_status": node.get("verdict_status") or None,
            "check": node.get("verdict_check") or None,
            "assertion": node.get("verdict_assertion") or None,
            "judge_prompt": node.get("verdict_judge_prompt") or None,
            "last_checked": node.get("verdict_last_checked") or None,
            "evidence_ref": node.get("verdict_evidence_ref") or None,
        }
    return out


def list_deleted_nodes(conn: sqlite3.Connection, project_id: str,
                        limit: int = 100) -> list[dict]:
    """List soft-deleted nodes in a project, newest deletion first."""
    rows = conn.execute(
        f"SELECT {NODE_COLUMNS} FROM nodes "
        "WHERE project_id = ? AND deleted_at IS NOT NULL "
        "ORDER BY deleted_at DESC LIMIT ?",
        (project_id, int(limit)),
    ).fetchall()
    return [_row_to_node(r) for r in rows]


# ============================================================
# Spec-audit queries (M3 — revision discipline, not spec↔code drift)
# ============================================================

def spec_audit_flagged_revisions(conn: sqlite3.Connection, project_id: str,
                                 *, since: Optional[str] = None,
                                 include_other: bool = True) -> list[dict]:
    """Revisions needing review: pivot, unset change_reason, or other.

    Used by spec-audit (not intent drift report / spec↔code — Topic E).
    """
    where = ["project_id = ?"]
    params: list = [project_id]
    if since:
        where.append("ts >= ?")
        params.append(since)
    if include_other:
        where.append(
            "(change_type != 'created' AND ("
            "change_reason = 'pivot' OR change_reason = 'drift' OR change_reason = '' "
            "OR change_reason IS NULL OR change_reason = 'other'"
            " OR change_reason NOT IN ('correction','evolution','clarification',"
            "'refactor','pivot','other','drift')))"
        )
    else:
        where.append(
            "(change_type != 'created' AND ("
            "change_reason = 'pivot' OR change_reason = 'drift' OR change_reason = '' "
            "OR change_reason IS NULL"
            " OR change_reason NOT IN ('correction','evolution','clarification',"
            "'refactor','pivot','other','drift')))"
        )
    sql = (
        f"SELECT * FROM revisions WHERE {' AND '.join(where)} "
        "ORDER BY ts DESC"
    )
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def spec_audit_unclarified_rationale(
        conn: sqlite3.Connection, project_id: str,
        *, since: Optional[str] = None) -> list[dict]:
    """Rationale field changed without clarification or correction change_reason.

    Heuristic: change_summary LIKE '%rationale%' AND
               (change_reason NOT IN ('clarification', 'correction')
                OR change_reason IS NULL).

    Args:
        conn: SQLite connection.
        project_id: Project to filter by.
        since: Optional ISO timestamp string; only return revisions with ts >= since.

    Returns:
        List of revision dicts.
    """
    where = [
        "project_id = ?",
        "change_summary LIKE '%rationale%'",
        "(change_reason NOT IN ('clarification', 'correction') "
        "OR change_reason IS NULL)",
    ]
    params: list = [project_id]
    if since:
        where.append("ts >= ?")
        params.append(since)
    sql = f"SELECT * FROM revisions WHERE {' AND '.join(where)}"
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def project_dashboard_stats(conn: sqlite3.Connection, project_id: str) -> dict:
    """Six-bundle stats for the project dashboard. One small query per bundle."""
    layer_rows = conn.execute(
        "SELECT layer, COUNT(*) as count FROM nodes "
        "WHERE project_id = ? AND deleted_at IS NULL "
        "GROUP BY layer ORDER BY layer",
        (project_id,),
    ).fetchall()
    target_rows = conn.execute(
        "SELECT COALESCE(target_status, '') as ts, COUNT(*) as count FROM nodes "
        "WHERE project_id = ? AND deleted_at IS NULL GROUP BY ts",
        (project_id,),
    ).fetchall()
    verdict_rows = conn.execute(
        "SELECT COALESCE(verdict_status, '') as vs, COUNT(*) as count FROM nodes "
        "WHERE project_id = ? AND deleted_at IS NULL GROUP BY vs",
        (project_id,),
    ).fetchall()
    last_mod = conn.execute(
        "SELECT node_id, title, layer, last_modified_at FROM nodes "
        "WHERE project_id = ? AND deleted_at IS NULL "
        "ORDER BY last_modified_at DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    last_val = conn.execute(
        "SELECT validation_id, status, issues_total, verdicts_run, finished_at "
        "FROM validations WHERE project_id = ? "
        "ORDER BY validation_id DESC LIMIT 1",
        (project_id,),
    ).fetchone()
    seven_days = conn.execute(
        "SELECT COUNT(*) as count FROM revisions "
        "WHERE project_id = ? AND ts >= datetime('now', '-7 days')",
        (project_id,),
    ).fetchone()
    return {
        "nodes_per_layer": [dict(r) for r in layer_rows],
        "target_distribution": {(r["ts"] or "(none)"): r["count"] for r in target_rows},
        "verdict_distribution": {(r["vs"] or "(none)"): r["count"] for r in verdict_rows},
        "last_modified": dict(last_mod) if last_mod else None,
        "last_validation": dict(last_val) if last_val else None,
        "revisions_7d": (seven_days["count"] if seven_days else 0),
    }


def _next_leaf_candidates(conn: sqlite3.Connection, project_id: str,
                          layer: str | None = None) -> list[dict]:
    """Leaves matching target_status criteria, before cross-block filter."""
    params: list = [project_id]
    layer_clause = ""
    if layer is not None:
        layer_clause = "AND n.layer = ?"
        params.append(layer)

    rows = conn.execute(f"""
        SELECT n.* FROM nodes n
        WHERE n.project_id = ?
          AND n.deleted_at IS NULL
          AND (n.target_status IN ('planned', 'in_progress') OR n.target_status = ''
               OR n.target_status IS NULL)
          AND NOT EXISTS (
            SELECT 1 FROM node_edges e
            WHERE e.project_id = n.project_id
              AND e.dst_node_id = n.node_id
              AND e.edge_kind = 'parent'
          )
          {layer_clause}
        ORDER BY n.layer, n.node_id
    """, params).fetchall()
    return [_row_to_node(r) for r in rows]


def _attach_computed_verdicts(
    conn: sqlite3.Connection,
    project_id: str,
    leaves: list[dict],
    project_root: str,
) -> list[dict]:
    """Run ephemeral verdict checks and attach computed_verdict_status to each leaf."""
    from . import validate

    if not project_root or not leaves:
        return leaves

    project_row = conn.execute(
        "SELECT spec_config FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    spec_config: dict = {}
    if project_row:
        try:
            spec_config = json.loads(project_row["spec_config"] or "{}")
        except (json.JSONDecodeError, TypeError):
            spec_config = {}

    nbi = validate._build_nodes_by_id(conn, project_id)
    if not nbi:
        return leaves

    judge_cmd = validate._resolve_judge_command(spec_config)
    verdicts_map = validate.run_verdicts(
        conn, project_id, nbi, project_root, False, judge_cmd=judge_cmd,
    )
    enriched: list[dict] = []
    for leaf in leaves:
        row = dict(leaf)
        verdict = verdicts_map.get(leaf["node_id"], {})
        row["computed_verdict_status"] = verdict.get("status") or ""
        enriched.append(row)
    return enriched


def next_leaves(conn: sqlite3.Connection, project_id: str,
                layer: str | None = None, *,
                project_root: str | None = None) -> list[dict]:
    """Return leaves whose target_status is in {planned, in_progress, ""}.

    A leaf is a node that has no children pointing to it via 'parent' edges
    (i.e. no other node names it as a parent). Sorted by layer then node_id.
    Excludes nodes cross-blocked by an unachieved blocker in another project.

    When ``project_root`` is set, each leaf also includes ``computed_verdict_status``
    from an ephemeral ``run_verdicts`` pass (same engine as drift-report; not persisted).

    Args:
        conn: SQLite connection.
        project_id: Project to query.
        layer: Optional layer name filter; if given, only return nodes in that layer.
        project_root: Optional checkout path; when set, attach computed verdict status.

    Returns:
        List of node dicts matching the criteria.
    """
    leaves = [
        leaf for leaf in _next_leaf_candidates(conn, project_id, layer)
        if not is_cross_blocked(conn, project_id, leaf["node_id"])
    ]
    root = (project_root or "").strip()
    if root:
        leaves = _attach_computed_verdicts(conn, project_id, leaves, root)
    return leaves


def next_leaves_excluded(conn: sqlite3.Connection, project_id: str,
                         layer: str | None = None) -> list[dict]:
    """Leaves excluded from next_leaves, with cross-block reasons."""
    excluded: list[dict] = []
    for leaf in _next_leaf_candidates(conn, project_id, layer):
        node_id = leaf["node_id"]
        if not is_cross_blocked(conn, project_id, node_id):
            continue
        chain = list_cross_blocking_chain(conn, project_id, node_id)
        excluded.append({
            "node_id": node_id,
            "layer": leaf.get("layer") or "",
            "title": leaf.get("title") or "",
            "target_status": leaf.get("target_status") or "",
            "verdict_status": leaf.get("verdict_status") or "",
            "verdict_mechanism": leaf.get("verdict_mechanism") or "",
            "reason": "cross_blocked",
            "blocked_by": [c["node_ref"] for c in chain],
        })
    return excluded


# ============================================================
# Portfolio (Topic H) + cross-project (Topic I)
# ============================================================

def list_portfolio_links(conn: sqlite3.Connection, *,
                         theme_node_id: Optional[str] = None,
                         project_id: Optional[str] = None) -> list[dict]:
    sql = (
        "SELECT theme_node_id, project_id, node_id, created_at "
        "FROM portfolio_links WHERE 1=1"
    )
    params: list = []
    if theme_node_id:
        sql += " AND theme_node_id = ?"
        params.append(theme_node_id)
    if project_id:
        sql += " AND project_id = ?"
        params.append(project_id)
    sql += " ORDER BY theme_node_id, project_id, node_id"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def _portfolio_theme_nodes(conn: sqlite3.Connection,
                           theme_node_id: Optional[str] = None) -> list[dict]:
    from .constants import PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER

    if get_project(conn, PORTFOLIO_PROJECT_ID) is None:
        return []
    sql = (
        f"SELECT {NODE_COLUMNS} FROM nodes "
        "WHERE project_id = ? AND layer = ? AND deleted_at IS NULL"
    )
    params: list = [PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER]
    if theme_node_id:
        sql += " AND node_id = ?"
        params.append(theme_node_id)
    sql += " ORDER BY node_id"
    return [_row_to_node(r) for r in conn.execute(sql, params).fetchall()]


def _link_status_summary(links: list[dict]) -> dict:
    summary = {"planned": 0, "in_progress": 0, "achieved": 0, "blocked": 0}
    for link in links:
        if link.get("blocked_by"):
            summary["blocked"] += 1
            continue
        status = (link.get("target_status") or "").strip() or "planned"
        if status in summary:
            summary[status] += 1
        else:
            summary["planned"] += 1
    return summary


def portfolio_report(conn: sqlite3.Connection, *,
                     theme_node_id: Optional[str] = None) -> dict:
    """Roll up portfolio themes and linked team nodes (L20, L24)."""
    from .constants import PORTFOLIO_PROJECT_ID
    from .node_ref import format_node_ref

    themes_out = []
    for theme in _portfolio_theme_nodes(conn, theme_node_id=theme_node_id):
        tid = theme["node_id"]
        raw_links = list_portfolio_links(conn, theme_node_id=tid)
        links = []
        for row in raw_links:
            node = get_node(conn, row["project_id"], row["node_id"])
            if node is None:
                continue
            blocked_by = [
                b["node_ref"]
                for b in list_cross_blocking_chain(
                    conn, row["project_id"], row["node_id"])
            ]
            links.append({
                "node_ref": format_node_ref(row["project_id"], row["node_id"]),
                "project_id": row["project_id"],
                "node_id": row["node_id"],
                "title": node.get("title") or "",
                "target_status": node.get("target_status") or "",
                "verdict_status": node.get("verdict_status") or "",
                "blocked_by": blocked_by,
            })
        themes_out.append({
            "theme_node_id": tid,
            "title": theme.get("title") or "",
            "links": links,
            "summary": _link_status_summary(links),
        })

    return {
        "portfolio_project_id": PORTFOLIO_PROJECT_ID,
        "themes": themes_out,
    }


def list_cross_edges(conn: sqlite3.Connection, *,
                     project_id: Optional[str] = None,
                     node_ref: Optional[str] = None) -> list[dict]:
    from .node_ref import format_node_ref, parse_node_ref

    sql = (
        "SELECT src_project_id, src_node_id, dst_project_id, dst_node_id, "
        "edge_kind, created_at FROM cross_project_edges WHERE 1=1"
    )
    params: list = []
    if project_id:
        sql += (
            " AND (src_project_id = ? OR dst_project_id = ?)"
        )
        params.extend([project_id, project_id])
    if node_ref:
        pid, nid = parse_node_ref(node_ref)
        sql += (
            " AND ((src_project_id = ? AND src_node_id = ?) "
            "OR (dst_project_id = ? AND dst_node_id = ?))"
        )
        params.extend([pid, nid, pid, nid])
    sql += " ORDER BY src_project_id, src_node_id, dst_project_id, dst_node_id"
    rows = conn.execute(sql, params).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["src_ref"] = format_node_ref(d["src_project_id"], d["src_node_id"])
        d["dst_ref"] = format_node_ref(d["dst_project_id"], d["dst_node_id"])
        out.append(d)
    return out


def _node_is_achieved(conn: sqlite3.Connection, project_id: str,
                      node_id: str) -> bool:
    row = conn.execute(
        "SELECT target_status FROM nodes "
        "WHERE project_id = ? AND node_id = ? AND deleted_at IS NULL",
        (project_id, node_id),
    ).fetchone()
    return bool(row and row["target_status"] == "achieved")


def list_cross_blocking_chain(conn: sqlite3.Connection, project_id: str,
                              node_id: str) -> list[dict]:
    """Transitive cross-project blockers for a node (L25 — mirrors list_blocking_chain)."""
    from .node_ref import format_node_ref

    seen: set[tuple[str, str]] = set()
    chain: list[dict] = []

    def walk(proj: str, nid: str, depth: int) -> None:
        key = (proj, nid)
        if key in seen:
            return
        seen.add(key)
        rows = conn.execute(
            "SELECT dst_project_id, dst_node_id FROM cross_project_edges "
            "WHERE src_project_id = ? AND src_node_id = ? AND edge_kind = 'blocks'",
            (proj, nid),
        ).fetchall()
        for r in rows:
            dst_p, dst_n = r["dst_project_id"], r["dst_node_id"]
            if _node_is_achieved(conn, dst_p, dst_n):
                continue
            ref = format_node_ref(dst_p, dst_n)
            chain.append({
                "node_ref": ref,
                "project_id": dst_p,
                "node_id": dst_n,
                "depth": depth,
            })
            walk(dst_p, dst_n, depth + 1)

    walk(project_id, node_id, 1)
    chain.sort(key=lambda x: (x["depth"], x["node_ref"]))
    return chain


def is_cross_blocked(conn: sqlite3.Connection, project_id: str,
                     node_id: str) -> bool:
    """True when any cross-project blocks target is not achieved."""
    return len(list_cross_blocking_chain(conn, project_id, node_id)) > 0


# ============================================================
# Drift report (M4 — spec↔code, not revision discipline)
# ============================================================

def drift_report(conn: sqlite3.Connection, project_id: str, *,
                 project_root: Optional[str] = None,
                 layer: Optional[str] = None,
                 all_layers: bool = False,
                 force: bool = False) -> dict:
    """Spec↔code drift report for realization-layer nodes (default: bottom layer).

    Runs verdict checks via validate.run_verdicts without persisting a validation
    run. See docs/archive/topics/drift-report-design.md.
    """
    from . import validate
    from .drift_report import classify_finding

    empty = {
        "project_id": project_id,
        "layer_scope": layer or ("all" if all_layers else ""),
        "project_root": project_root or "",
        "summary": {
            "total": 0, "violated": 0, "errored": 0, "unverified": 0, "satisfied": 0,
            "deferred_external": 0, "other": 0,
        },
        "violated": [], "errored": [], "unverified": [], "satisfied": [],
        "deferred_external": [], "other": [],
        "warnings": [],
    }

    project_row = conn.execute(
        "SELECT spec_config FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if not project_row:
        return empty

    try:
        spec_config = json.loads(project_row["spec_config"] or "{}")
    except (json.JSONDecodeError, TypeError):
        spec_config = {}

    layer_names = [L.get("name", "") for L in (spec_config.get("layers") or [])]
    if all_layers:
        layer_scope = "all"
        target_layers = set(layer_names)
    elif layer:
        layer_scope = layer
        target_layers = {layer}
    else:
        layer_scope = layer_names[-1] if layer_names else ""
        target_layers = {layer_scope} if layer_scope else set()

    resolved_root = (project_root or spec_config.get("project_root") or "").strip()
    empty["layer_scope"] = layer_scope
    empty["project_root"] = resolved_root

    warnings: list[str] = []
    if not resolved_root:
        warnings.append(
            "project_root is unset; automated checks may not reflect the deployed codebase"
        )

    nbi = validate._build_nodes_by_id(conn, project_id)
    if not nbi:
        return empty

    judge_cmd = validate._resolve_judge_command(spec_config)
    verdicts_map = validate.run_verdicts(
        conn, project_id, nbi, resolved_root, force, judge_cmd=judge_cmd)

    buckets = {k: [] for k in (
        "violated", "errored", "unverified", "satisfied", "deferred_external", "other")}
    summary = dict(empty["summary"])

    for nid, node in nbi.items():
        if node.get("deleted_at"):
            continue
        if target_layers and node.get("layer") not in target_layers:
            continue

        v = verdicts_map.get(nid, {})
        status = v.get("status") or "unknown"
        source = v.get("source") or ""
        mechanism = node.get("verdict_mechanism") or ""
        bucket = classify_finding(status, source, mechanism)

        finding = {
            "node_id": nid,
            "layer": node.get("layer") or "",
            "title": node.get("title") or "",
            "rationale": (node.get("rationale") or "")[:500],
            "verdict_status": status,
            "verdict_source": source,
            "verdict_evidence": v.get("evidence_ref") or "",
            "verdict_mechanism": mechanism,
        }
        buckets[bucket].append(finding)
        summary[bucket] += 1
        summary["total"] += 1

    return {
        "project_id": project_id,
        "layer_scope": layer_scope,
        "project_root": resolved_root,
        "warnings": warnings,
        "summary": summary,
        **buckets,
    }
