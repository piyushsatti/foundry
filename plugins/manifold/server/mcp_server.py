"""
manifold MCP server — stdio JSON-RPC 2.0.

Exposes 46 tools (27 read + 19 write) wrapping the packages/manifold library.
Run directly: python3 plugins/manifold/server/mcp_server.py
"""
import importlib.util
import json
import os
import sys
import traceback
from pathlib import Path
from typing import Any, Callable

# Locate the `manifold` library: prefer an installed copy (`pip install packages/manifold`);
# otherwise walk up to find packages/manifold (running from the repo or via --plugin-dir).
if importlib.util.find_spec("manifold") is None:
    for _base in Path(__file__).resolve().parents:
        if (_base / "packages" / "manifold" / "manifold" / "__init__.py").exists():
            sys.path.insert(0, str(_base / "packages" / "manifold"))
            break

from manifold import config, db, errors, queries, schema, writes

_CHANGE_REASON_ENUM = list(writes.DOCUMENTED_CHANGE_REASONS)


# ============================================================
# Tool handlers (one per MCP tool)
# Each handler takes a sqlite3.Connection and the args dict.
# Each returns a dict (success result) or an error envelope dict.
# ============================================================


def _resolve_node_or_error(conn, project_id: str, node_id: str,
                           include_deleted: bool = False) -> dict:
    """Return node dict or NOT_FOUND envelope."""
    node = queries.get_node(conn, project_id, node_id, include_deleted=include_deleted)
    if node is None:
        return errors.not_found_envelope("node", project_id=project_id, node_id=node_id)
    return {"node": node}


# --- Read handlers ---

def h_list_projects(conn, args):
    return {"projects": queries.list_projects(
        conn,
        include_archived=bool(args.get("include_archived", False)),
        limit=int(args.get("limit", 50)),
        cursor=args.get("cursor"),
    )}


def h_peek_project(conn, args):
    pid = args.get("project_id", "")
    proj = queries.get_project(conn, pid)
    if proj is None:
        return errors.not_found_envelope("project", project_id=pid)
    # Add small rollup
    node_count = conn.execute(
        "SELECT COUNT(*) AS c FROM nodes WHERE project_id = ? AND deleted_at IS NULL",
        (pid,),
    ).fetchone()["c"]
    by_status = {row["target_status"] or "": row["c"] for row in conn.execute(
        "SELECT target_status, COUNT(*) AS c FROM nodes "
        "WHERE project_id = ? AND deleted_at IS NULL GROUP BY target_status",
        (pid,),
    ).fetchall()}
    return {"project": proj, "node_count": node_count, "by_target_status": by_status}


def h_peek_node(conn, args):
    return _resolve_node_or_error(conn, args.get("project_id", ""), args.get("node_id", ""))


def h_peek_node_full(conn, args):
    pid = args.get("project_id", "")
    nid = args.get("node_id", "")
    include = tuple(args.get("include") or ("parents", "verdict"))
    result = queries.peek_node_full(conn, pid, nid, include=include)
    if result is None:
        return errors.not_found_envelope("node", project_id=pid, node_id=nid)
    return {"node": result}


def h_peek_validation(conn, args):
    vid = int(args.get("validation_id", 0))
    v = queries.get_validation(conn, vid)
    if v is None:
        return errors.not_found_envelope("validation", validation_id=vid)
    return {"validation": v}


def h_list_nodes(conn, args):
    return {"nodes": queries.list_nodes(
        conn, args.get("project_id", ""),
        layer=args.get("layer"),
        limit=int(args.get("limit", 50)),
        cursor=args.get("cursor"),
        include_deleted=bool(args.get("include_deleted", False)),
    )}


def h_list_targets(conn, args):
    return {"targets": queries.list_targets(
        conn,
        project_id=args.get("project_id"),
        status=args.get("status"),
        older_than_days=args.get("older_than_days"),
        limit=int(args.get("limit", 50)),
        cursor=args.get("cursor"),
    )}


def h_list_unstable_verdicts(conn, args):
    return {"nodes": queries.list_unstable_verdicts(
        conn,
        project_id=args.get("project_id"),
        k=int(args.get("k", 3)),
        limit=int(args.get("limit", 50)),
        cursor=args.get("cursor"),
    )}


def h_list_blocking_chain(conn, args):
    return {"chain": queries.list_blocking_chain(
        conn, args.get("project_id", ""), args.get("node_id", ""),
        direct_only=bool(args.get("direct_only", False)),
    )}


def h_list_revisions(conn, args):
    return {"revisions": queries.list_revisions(
        conn, args.get("project_id", ""), args.get("node_id", ""),
        since=args.get("since"),
        before=args.get("before"),
        limit=int(args.get("limit", 20)),
    )}


def h_list_changes_since(conn, args):
    if args.get("since_ts") is None and args.get("since_revision_id") is None:
        return errors.envelope(
            errors.INVALID_ARGUMENTS,
            "list_changes_since requires either since_ts or since_revision_id",
            retry=errors.RETRY_WITH_NEW_ARGS,
        )
    return {"changes": queries.list_changes_since(
        conn,
        project_id=args.get("project_id"),
        since_ts=args.get("since_ts"),
        since_revision_id=args.get("since_revision_id"),
        limit=int(args.get("limit", 100)),
        cursor=args.get("cursor"),
    )}


def h_list_uncovered(conn, args):
    return {"uncovered": queries.list_uncovered(
        conn, args.get("project_id", ""), args.get("layer", ""),
    )}


def h_list_validations(conn, args):
    return {"validations": queries.list_validations(
        conn,
        project_id=args.get("project_id"),
        limit=int(args.get("limit", 20)),
    )}


def h_diff_revisions(conn, args):
    pid = args.get("project_id", "")
    nid = args.get("node_id", "")
    diff = queries.diff_revisions(
        conn, pid, nid,
        int(args.get("from_revision_id", 0)),
        int(args.get("to_revision_id", 0)),
    )
    if diff is None:
        return errors.envelope(
            errors.INVALID_ARGUMENTS,
            "one or both revisions not found",
            retry=errors.RETRY_WITH_NEW_ARGS,
            context={"project_id": pid, "node_id": nid,
                     "from_revision_id": args.get("from_revision_id"),
                     "to_revision_id": args.get("to_revision_id")},
        )
    return {"diff": diff}


def h_resolve_node(conn, args):
    return {"node_ids": queries.resolve_node(
        conn, args.get("project_id", ""), args.get("query", ""),
    )}


def h_next_leaves(conn, args):
    project_id = args.get("project_id", "")
    layer = args.get("layer")
    project_root = (args.get("project_root") or "").strip() or None
    result = {
        "leaves": queries.next_leaves(
            conn, project_id, layer=layer, project_root=project_root,
        ),
    }
    if args.get("include_excluded"):
        result["excluded"] = queries.next_leaves_excluded(
            conn, project_id, layer=layer)
    return result


def h_spec_audit(conn, args):
    project_id = args.get("project_id", "")
    since = args.get("since")
    include_other = bool(args.get("include_other", True))
    flagged = queries.spec_audit_flagged_revisions(
        conn, project_id, since=since, include_other=include_other)
    rationale = queries.spec_audit_unclarified_rationale(
        conn, project_id, since=since)
    return {
        "flagged_revisions": flagged,
        "unclarified_rationale_changes": rationale,
    }


def h_drift_report(conn, args):
    project_id = args.get("project_id", "")
    return queries.drift_report(
        conn, project_id,
        project_root=args.get("project_root"),
        layer=args.get("layer"),
        all_layers=bool(args.get("all_layers", False)),
        force=bool(args.get("force", False)),
    )


def h_peek_diagram(conn, args):
    from manifold import presentation_views, view_registry
    if args.get("view_id"):
        return view_registry.build_registered_view(
            conn, args.get("project_id", ""), args["view_id"],
            focus_node_id=args.get("focus_node_id"),
            trajectory_id=args.get("trajectory_id"),
            max_nodes=int(args.get("max_nodes", 12)),
        )
    return presentation_views.build_diagram_view(
        conn, args.get("project_id", ""),
        diagram_type=args.get("diagram_type", "blockers"),
        focus_node_id=args.get("focus_node_id"),
        trajectory_id=args.get("trajectory_id"),
        max_nodes=int(args.get("max_nodes", 12)),
    )


def h_peek_mindmap(conn, args):
    from manifold import presentation_views, view_registry
    if args.get("view_id"):
        return view_registry.build_registered_view(
            conn, args.get("project_id", ""), args["view_id"],
            focus_node_id=args.get("focus_node_id"),
            max_depth=int(args.get("max_depth", 4)),
            max_nodes=int(args.get("max_nodes", 12)),
        )
    return presentation_views.build_mindmap_view(
        conn, args.get("project_id", ""),
        mindmap_type=args.get("mindmap_type", "flow"),
        focus_node_id=args.get("focus_node_id"),
        max_depth=int(args.get("max_depth", 4)),
        max_nodes=int(args.get("max_nodes", 12)),
    )


def h_list_presentation_views(conn, args):
    from manifold import view_registry
    return {"views": view_registry.list_views()}


def h_peek_status_brief(conn, args):
    from manifold import status_brief
    return status_brief.build_status_brief_view(
        conn, args.get("project_id", ""),
    )


def _trajectory_error(exc):
    return errors.envelope(
        errors.INVALID_ARGUMENTS, str(exc),
        retry=errors.RETRY_WITH_NEW_ARGS,
    )


def h_propose_trajectory(conn, args):
    from manifold import trajectory as traj
    try:
        return traj.propose_trajectory(
            conn,
            args.get("project_id", ""),
            args.get("target_brief", ""),
            args.get("legs") or [],
            proposed_by=args.get("proposed_by") or args.get("actor") or "",
            scope=args.get("scope"),
        )
    except traj.TrajectoryError as exc:
        return _trajectory_error(exc)
    except writes.ProjectNotFound as exc:
        return errors.envelope(errors.PROJECT_NOT_FOUND, str(exc))


def h_peek_trajectory(conn, args):
    from manifold import trajectory as traj
    leg_seqs = args.get("leg_seqs")
    try:
        return traj.peek_trajectory(
            conn,
            args.get("trajectory_id", ""),
            leg_seqs=leg_seqs,
        )
    except traj.TrajectoryError as exc:
        return _trajectory_error(exc)


def h_accept_trajectory_leg(conn, args):
    from manifold import trajectory as traj
    try:
        return traj.accept_trajectory_legs(
            conn,
            args.get("trajectory_id", ""),
            leg_seqs=args.get("leg_seqs"),
            actor=args.get("actor") or "",
        )
    except traj.TrajectoryError as exc:
        return _trajectory_error(exc)
    except writes.WritesError as exc:
        return errors.envelope(errors.INVALID_ARGUMENTS, str(exc))


def h_reject_trajectory(conn, args):
    from manifold import trajectory as traj
    try:
        return traj.reject_trajectory(
            conn,
            args.get("trajectory_id", ""),
            actor=args.get("actor") or "",
        )
    except traj.TrajectoryError as exc:
        return _trajectory_error(exc)


def h_portfolio_report(conn, args):
    return queries.portfolio_report(
        conn, theme_node_id=args.get("theme_node_id"))


def h_list_portfolio_links(conn, args):
    return {"links": queries.list_portfolio_links(
        conn,
        theme_node_id=args.get("theme_node_id"),
        project_id=args.get("project_id"),
    )}


def h_list_cross_edges(conn, args):
    return {"edges": queries.list_cross_edges(
        conn,
        project_id=args.get("project_id"),
        node_ref=args.get("node_ref"),
    )}


def h_list_cross_blocking_chain(conn, args):
    return {"chain": queries.list_cross_blocking_chain(
        conn, args.get("project_id", ""), args.get("node_id", ""),
    )}


def _portfolio_write(conn, fn, args, **kwargs):
    try:
        result = fn(conn, **kwargs)
        return result
    except ValueError as exc:
        return errors.envelope(
            errors.INVALID_ARGUMENTS, str(exc),
            retry=errors.RETRY_WITH_NEW_ARGS,
        )


def h_link_portfolio(conn, args):
    return _portfolio_write(
        conn, writes.link_portfolio, args,
        theme_node_id=args.get("theme_node_id", ""),
        project_id=args.get("project_id", ""),
        node_id=args.get("node_id", ""),
        actor=args.get("actor") or "",
    )


def h_unlink_portfolio(conn, args):
    return _portfolio_write(
        conn, writes.unlink_portfolio, args,
        theme_node_id=args.get("theme_node_id", ""),
        project_id=args.get("project_id", ""),
        node_id=args.get("node_id", ""),
        actor=args.get("actor") or "",
    )


def h_create_cross_edge(conn, args):
    return _portfolio_write(
        conn, writes.create_cross_edge, args,
        src_project_id=args.get("src_project_id", ""),
        src_node_id=args.get("src_node_id", ""),
        dst_project_id=args.get("dst_project_id", ""),
        dst_node_id=args.get("dst_node_id", ""),
        edge_kind=args.get("edge_kind", "blocks"),
        actor=args.get("actor") or "",
    )


def h_delete_cross_edge(conn, args):
    return _portfolio_write(
        conn, writes.delete_cross_edge, args,
        src_project_id=args.get("src_project_id", ""),
        src_node_id=args.get("src_node_id", ""),
        dst_project_id=args.get("dst_project_id", ""),
        dst_node_id=args.get("dst_node_id", ""),
        edge_kind=args.get("edge_kind", "blocks"),
        actor=args.get("actor") or "",
    )


# --- Write handlers ---

def _write(conn, fn, args, **kwargs):
    """Common pattern: call writes.fn, catch exceptions → envelope."""
    try:
        return fn(conn, **kwargs)
    except writes.WritesError as exc:
        return errors.from_writes_exception(
            exc,
            project_id=kwargs.get("project_id"),
            node_id=kwargs.get("node_id"),
        )


def h_register_project(conn, args):
    return _write(conn, writes.register_project, args,
                   project_id=args.get("project_id", ""),
                   spec_config=args.get("spec_config") or {},
                   label=args.get("label"))


def h_import_project(conn, args):
    from manifold import importer
    from pathlib import Path
    repo = args.get("repo_root", "")
    if not repo:
        return errors.envelope(errors.INVALID_ARGUMENTS,
                                "import_project requires repo_root",
                                retry=errors.RETRY_WITH_NEW_ARGS)
    actor = args.get("actor") or f"agent:{os.environ.get('USER', 'unknown')}"
    try:
        return importer.import_project(
            conn, Path(repo).expanduser().resolve(),
            project_id=args.get("project_id") or None,
            actor=actor,
        )
    except FileNotFoundError as exc:
        return errors.envelope(errors.NOT_A_SPEC_REPO, str(exc),
                                retry=errors.RETRY_NO,
                                context={"repo_root": repo})
    except writes.WritesError as exc:
        return errors.from_writes_exception(exc)


def h_create_node(conn, args):
    return _write(conn, writes.create_node, args,
                   project_id=args.get("project_id", ""),
                   layer=args.get("layer", ""),
                   node_id=args.get("node_id", ""),
                   title=args.get("title", ""),
                   body=args.get("body", ""),
                   kind=args.get("kind", "spec"),
                   parents=args.get("parents"),
                   peers_depends_on=args.get("peers_depends_on"),
                   target_blocks=args.get("target_blocks"),
                   target_status=args.get("target_status"),  # pass-through
                   actor=args.get("actor") or "",
                   source=args.get("source", "mcp"),
                   batch_id=args.get("batch_id"))


def h_update_node(conn, args):
    return _write(conn, writes.update_node, args,
                   project_id=args.get("project_id", ""),
                   node_id=args.get("node_id", ""),
                   fields=args.get("fields") or {},
                   expected_revision_id=int(args.get("expected_revision_id", 0)),
                   actor=args.get("actor") or "",
                   source=args.get("source", "mcp"),
                   batch_id=args.get("batch_id"),
                   note=args.get("note"),
                   change_reason=args.get("change_reason"))


def h_transition_target(conn, args):
    return _write(conn, writes.transition_target, args,
                   project_id=args.get("project_id", ""),
                   node_id=args.get("node_id", ""),
                   to_status=args.get("to_status", ""),
                   achieved_at=args.get("achieved_at"),
                   superseded_by=args.get("superseded_by"),
                   note=args.get("note"),
                   expected_revision_id=int(args.get("expected_revision_id", 0)),
                   actor=args.get("actor") or "",
                   source=args.get("source", "mcp"))


def h_revert(conn, args):
    return _write(conn, writes.revert, args,
                   project_id=args.get("project_id", ""),
                   node_id=args.get("node_id", ""),
                   to_revision_id=int(args.get("to_revision_id", 0)),
                   actor=args.get("actor") or "",
                   source=args.get("source", "mcp"))


def h_soft_delete_node(conn, args):
    return _write(conn, writes.soft_delete_node, args,
                   project_id=args.get("project_id", ""),
                   node_id=args.get("node_id", ""),
                   expected_revision_id=int(args.get("expected_revision_id", 0)),
                   actor=args.get("actor") or "",
                   source=args.get("source", "mcp"))


def h_restore_node(conn, args):
    return _write(conn, writes.restore_node, args,
                   project_id=args.get("project_id", ""),
                   node_id=args.get("node_id", ""),
                   actor=args.get("actor") or "",
                   source=args.get("source", "mcp"))


def h_with_batch(conn, args):
    return _write(conn, writes.with_batch, args,
                   label=args.get("label", ""),
                   ops=args.get("ops") or [],
                   actor=args.get("actor") or "",
                   source=args.get("source", "mcp"))


def h_run_validation(conn, args):
    return _write(conn, writes.run_validation, args,
                   project_id=args.get("project_id", ""),
                   with_verdicts=bool(args.get("with_verdicts", False)),
                   with_targets=bool(args.get("with_targets", False)),
                   force=bool(args.get("force", False)),
                   actor=args.get("actor") or "")


def h_archive_project(conn, args):
    return _write(conn, writes.archive_project, args,
                   project_id=args.get("project_id", ""))


def h_unarchive_project(conn, args):
    return _write(conn, writes.unarchive_project, args,
                   project_id=args.get("project_id", ""))


# ============================================================
# Tool registry
# ============================================================

# Schema convention:
# - All string args use {"type": "string"}.
# - Optional fields are omitted from `required`.
# - `additionalProperties` not enforced so callers can pass forward-compatible extras.
TOOLS: list[dict[str, Any]] = [
    # Read tools
    {"name": "list_projects",
     "description": "List registered projects. Default excludes archived.",
     "handler": h_list_projects,
     "inputSchema": {"type": "object", "properties": {
         "include_archived": {"type": "boolean"},
         "limit": {"type": "integer"},
         "cursor": {"type": "string"},
     }}},
    {"name": "peek_project",
     "description": "Summary of one project: row + node_count + by_target_status rollup.",
     "handler": h_peek_project,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
     }}},
    {"name": "peek_node",
     "description": "Full node row (current state) for (project_id, node_id). Returns NODE_NOT_FOUND if missing or soft-deleted.",
     "handler": h_peek_node,
     "inputSchema": {"type": "object", "required": ["project_id", "node_id"], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
     }}},
    {"name": "peek_node_full",
     "description": "Composite node read: includes parents/children/blockers/verdict_history/revisions per `include` list. Default include: ['parents','verdict'].",
     "handler": h_peek_node_full,
     "inputSchema": {"type": "object", "required": ["project_id", "node_id"], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "include": {"type": "array", "items": {"type": "string"}},
     }}},
    {"name": "peek_validation",
     "description": "Validation row by validation_id.",
     "handler": h_peek_validation,
     "inputSchema": {"type": "object", "required": ["validation_id"], "properties": {
         "validation_id": {"type": "integer"},
     }}},
    {"name": "list_nodes",
     "description": "List nodes for a project, optionally filtered by layer. Paginates via limit + cursor.",
     "handler": h_list_nodes,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
         "layer": {"type": "string"},
         "limit": {"type": "integer"},
         "cursor": {"type": "string"},
         "include_deleted": {"type": "boolean"},
     }}},
    {"name": "list_targets",
     "description": "Targeted nodes (target_status != '') across one project (or all if project_id omitted). Filter by status; filter by older_than_days for staleness.",
     "handler": h_list_targets,
     "inputSchema": {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "status": {"type": "string"},
         "older_than_days": {"type": "integer"},
         "limit": {"type": "integer"},
         "cursor": {"type": "string"},
     }}},
    {"name": "list_unstable_verdicts",
     "description": "llm_judge verdicts whose status differs across the last K validations (flip detection).",
     "handler": h_list_unstable_verdicts,
     "inputSchema": {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "k": {"type": "integer"},
         "limit": {"type": "integer"},
         "cursor": {"type": "string"},
     }}},
    {"name": "list_blocking_chain",
     "description": "Transitive blockers of a node (everything that blocks it directly or via the chain). Set direct_only=true for just direct blockers.",
     "handler": h_list_blocking_chain,
     "inputSchema": {"type": "object", "required": ["project_id", "node_id"], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "direct_only": {"type": "boolean"},
     }}},
    {"name": "list_revisions",
     "description": "Revisions for a node, newest first.",
     "handler": h_list_revisions,
     "inputSchema": {"type": "object", "required": ["project_id", "node_id"], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "since": {"type": "integer"},
         "before": {"type": "integer"},
         "limit": {"type": "integer"},
     }}},
    {"name": "list_changes_since",
     "description": "Revisions across nodes since a given timestamp or revision_id. One of since_ts/since_revision_id is required.",
     "handler": h_list_changes_since,
     "inputSchema": {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "since_ts": {"type": "string"},
         "since_revision_id": {"type": "integer"},
         "limit": {"type": "integer"},
         "cursor": {"type": "string"},
     }}},
    {"name": "list_uncovered",
     "description": "Parent-layer nodes that have no children at the given layer. Skips constraints and external-realized nodes.",
     "handler": h_list_uncovered,
     "inputSchema": {"type": "object", "required": ["project_id", "layer"], "properties": {
         "project_id": {"type": "string"},
         "layer": {"type": "string"},
     }}},
    {"name": "list_validations",
     "description": "Validations for a project (newest first).",
     "handler": h_list_validations,
     "inputSchema": {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "limit": {"type": "integer"},
     }}},
    {"name": "diff_revisions",
     "description": "Per-field diff + body unified diff between two revisions of the same node.",
     "handler": h_diff_revisions,
     "inputSchema": {"type": "object", "required": [
         "project_id", "node_id", "from_revision_id", "to_revision_id"
     ], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "from_revision_id": {"type": "integer"},
         "to_revision_id": {"type": "integer"},
     }}},
    {"name": "resolve_node",
     "description": "Fuzzy lookup: id-prefix or title-substring match. Returns up to 20 node_ids.",
     "handler": h_resolve_node,
     "inputSchema": {"type": "object", "required": ["project_id", "query"], "properties": {
         "project_id": {"type": "string"},
         "query": {"type": "string"},
     }}},
    {"name": "next_leaves",
     "description": "Return leaf nodes ready to be worked on (target_status in planned/in_progress/unset). "
                    "A leaf has no children pointing to it via parent edges.",
     "handler": h_next_leaves,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
         "layer": {"type": "string"},
         "include_excluded": {
             "type": "boolean",
             "description": "When true, also return cross-blocked leaves with blocked_by reasons.",
         },
         "project_root": {
             "type": "string",
             "description": "When set, attach computed_verdict_status per leaf (ephemeral checks).",
         },
     }}},
    {"name": "spec_audit",
     "description": "Audit spec revision discipline (M3). Returns flagged_revisions "
                    "(change_reason pivot/unset/other) and unclarified_rationale_changes. "
                    "Not spec↔code intent drift — see docs/manifold/glossary.md.",
     "handler": h_spec_audit,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
         "since": {"type": "string", "description": "ISO timestamp; only revisions on or after this date."},
         "include_other": {"type": "boolean",
                           "description": "Include change_reason='other' revisions (default true)."},
     }}},
    {"name": "drift_report",
     "description": "Spec↔code drift report (M4). Returns summary counts and findings "
                    "(violated, unverified, satisfied, etc.) for realization-layer nodes. "
                    "Not revision discipline — see spec_audit for M3.",
     "handler": h_drift_report,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
         "project_root": {"type": "string",
                          "description": "Override repo root for verdict checks."},
         "layer": {"type": "string",
                   "description": "Layer to scan (default: bottom layer)."},
         "all_layers": {"type": "boolean",
                        "description": "Scan all layers (default false)."},
         "force": {"type": "boolean",
                   "description": "Re-run verdict checks even if cached (default false)."},
     }}},
    {"name": "peek_diagram",
     "description": "Bounded flowchart view-model (blockers, decomposition, trajectory). "
                    "Returns nodes + edges JSON for Mermaid/HTML renderers — graph is authoritative.",
     "handler": h_peek_diagram,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
         "view_id": {"type": "string",
                     "description": "Catalog view id (blockers, decomposition, trajectory). "
                                    "Overrides diagram_type when set."},
         "diagram_type": {"type": "string",
                          "enum": ["blockers", "decomposition", "trajectory"],
                          "description": "Diagram slice (default blockers)."},
         "focus_node_id": {"type": "string",
                           "description": "Center node; defaults to first cross-blocked leaf."},
         "trajectory_id": {"type": "string",
                           "description": "Required when diagram_type=trajectory."},
         "max_nodes": {"type": "integer", "description": "Node cap (default 12)."},
     }}},
    {"name": "peek_mindmap",
     "description": "Hierarchical mindmap view-model from graph decomposition. "
                    "Returns tree + flat nodes for Mermaid/HTML renderers.",
     "handler": h_peek_mindmap,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
         "view_id": {"type": "string",
                     "description": "Catalog view id (mindmap-flow, mindmap-decomposition). "
                                    "Overrides mindmap_type when set."},
         "mindmap_type": {"type": "string",
                          "enum": ["flow", "decomposition"],
                          "description": "Mindmap walk mode (default flow)."},
         "focus_node_id": {"type": "string"},
         "max_depth": {"type": "integer", "description": "Tree depth cap (default 4)."},
         "max_nodes": {"type": "integer", "description": "Node cap (default 12)."},
     }}},
    {"name": "list_presentation_views",
     "description": "Catalog of named presentation views (diagram + mindmap slices). "
                    "Use view_id with peek_diagram/peek_mindmap or GET /projects/<id>/views/<view_id>.",
     "handler": h_list_presentation_views,
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "peek_status_brief",
     "description": "Human status-brief view-model — shipped / in-flight / blocked / at-risk "
                    "leaves, recent changes, drift summary, theme link. Graph is authoritative.",
     "handler": h_peek_status_brief,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
     }}},
    {"name": "peek_trajectory",
     "description": "Show trajectory legs + impact preview (plan before accept). "
                    "Propose never mutates the graph; only accept applies legs.",
     "handler": h_peek_trajectory,
     "inputSchema": {"type": "object", "required": ["trajectory_id"], "properties": {
         "trajectory_id": {"type": "string"},
         "leg_seqs": {
             "type": "array",
             "items": {"type": "integer"},
             "description": "Leg seq numbers to simulate (default: all pending).",
         },
     }}},
    {"name": "portfolio_report",
     "description": "Company theme roll-up: linked team nodes with target_status, "
                    "verdict_status, and blocked_by node_refs. See portfolio-report.",
     "handler": h_portfolio_report,
     "inputSchema": {"type": "object", "properties": {
         "theme_node_id": {"type": "string",
                           "description": "Filter to one theme in project portfolio."},
     }}},
    {"name": "list_portfolio_links",
     "description": "List portfolio_links rows (theme tracks team node).",
     "handler": h_list_portfolio_links,
     "inputSchema": {"type": "object", "properties": {
         "theme_node_id": {"type": "string"},
         "project_id": {"type": "string"},
     }}},
    {"name": "list_cross_edges",
     "description": "List cross_project_edges (blocks/depends_on across projects).",
     "handler": h_list_cross_edges,
     "inputSchema": {"type": "object", "properties": {
         "project_id": {"type": "string"},
         "node_ref": {"type": "string", "description": "Filter edges touching project_id/node_id."},
     }}},
    {"name": "list_cross_blocking_chain",
     "description": "Transitive cross-project blockers for a node (mirrors list_blocking_chain).",
     "handler": h_list_cross_blocking_chain,
     "inputSchema": {"type": "object", "required": ["project_id", "node_id"], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
     }}},
    # Write tools
    {"name": "register_project",
     "description": "Register a new project with a spec_config (layers list). Returns the project row.",
     "handler": h_register_project,
     "inputSchema": {"type": "object", "required": ["project_id", "spec_config"], "properties": {
         "project_id": {"type": "string"},
         "spec_config": {"type": "object"},
         "label": {"type": "string"},
     }}},
    {"name": "import_project",
     "description": "Import a v0.2 spec dir into the DB; replays git log of specs/. Idempotent on re-run.",
     "handler": h_import_project,
     "inputSchema": {"type": "object", "required": ["repo_root"], "properties": {
         "repo_root": {"type": "string"},
         "project_id": {"type": "string"},
         "actor": {"type": "string"},
     }}},
    {"name": "create_node",
     "description": "Create a new node with optional parents/peers/blocks edges. Creates the initial revision. Requires actor.",
     "handler": h_create_node,
     "inputSchema": {"type": "object", "required": [
         "project_id", "layer", "node_id", "title", "actor"
     ], "properties": {
         "project_id": {"type": "string"},
         "layer": {"type": "string"},
         "node_id": {"type": "string"},
         "title": {"type": "string"},
         "body": {"type": "string"},
         "kind": {"type": "string"},
         "parents": {"type": "array"},
         "peers_depends_on": {"type": "array"},
         "target_blocks": {"type": "array"},
         "target_status": {"type": "string"},
         "actor": {"type": "string"},
         "source": {"type": "string"},
         "batch_id": {"type": "string"},
     }}},
    {"name": "update_node",
     "description": "Update a node's columnar/edge fields. expected_revision_id and change_reason are REQUIRED.",
     "handler": h_update_node,
     "inputSchema": {"type": "object", "required": [
         "project_id", "node_id", "fields", "expected_revision_id", "actor",
         "change_reason",
     ], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "fields": {"type": "object"},
         "expected_revision_id": {"type": "integer"},
         "change_reason": {
             "type": "string",
             "enum": _CHANGE_REASON_ENUM,
             "description": "Why this revision happened",
         },
         "actor": {"type": "string"},
         "source": {"type": "string"},
         "batch_id": {"type": "string"},
         "note": {"type": "string"},
     }}},
    {"name": "transition_target",
     "description": "Move a node's target_status through the state machine. Validates the transition.",
     "handler": h_transition_target,
     "inputSchema": {"type": "object", "required": [
         "project_id", "node_id", "to_status", "expected_revision_id", "actor"
     ], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "to_status": {"type": "string"},
         "achieved_at": {"type": "string"},
         "superseded_by": {"type": "string"},
         "note": {"type": "string"},
         "expected_revision_id": {"type": "integer"},
         "actor": {"type": "string"},
         "source": {"type": "string"},
     }}},
    {"name": "revert",
     "description": "Copy a past revision's snapshot forward as a new revision. The node's current_revision_id becomes the new one.",
     "handler": h_revert,
     "inputSchema": {"type": "object", "required": [
         "project_id", "node_id", "to_revision_id", "actor"
     ], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "to_revision_id": {"type": "integer"},
         "actor": {"type": "string"},
         "source": {"type": "string"},
     }}},
    {"name": "soft_delete_node",
     "description": "Mark a node deleted_at and create a 'deleted' revision. The node row stays for history; restore_node un-deletes.",
     "handler": h_soft_delete_node,
     "inputSchema": {"type": "object", "required": [
         "project_id", "node_id", "expected_revision_id", "actor"
     ], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "expected_revision_id": {"type": "integer"},
         "actor": {"type": "string"},
         "source": {"type": "string"},
     }}},
    {"name": "restore_node",
     "description": "Un-delete a soft-deleted node. Creates a 'restored' revision.",
     "handler": h_restore_node,
     "inputSchema": {"type": "object", "required": ["project_id", "node_id", "actor"], "properties": {
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "actor": {"type": "string"},
         "source": {"type": "string"},
     }}},
    {"name": "with_batch",
     "description": "Run a list of ops atomically under one batch_id. Returns {batch_id, revision_ids[], label}. Failure rolls back all.",
     "handler": h_with_batch,
     "inputSchema": {"type": "object", "required": ["label", "ops", "actor"], "properties": {
         "label": {"type": "string"},
         "ops": {"type": "array"},
         "actor": {"type": "string"},
         "source": {"type": "string"},
     }}},
    {"name": "run_validation",
     "description": "Run validation: structural checks always, plus verdict computation and target checks when requested. Writes a validations row and returns the validation_id. Synchronous.",
     "handler": h_run_validation,
     "inputSchema": {"type": "object", "required": ["project_id", "actor"], "properties": {
         "project_id": {"type": "string"},
         "with_verdicts": {"type": "boolean"},
         "with_targets": {"type": "boolean"},
         "force": {"type": "boolean"},
         "actor": {"type": "string"},
     }}},
    {"name": "archive_project",
     "description": "Soft-archive a project: sets archived_at; default queries hide it. Pair with unarchive_project.",
     "handler": h_archive_project,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
     }}},
    {"name": "unarchive_project",
     "description": "Clear a project's archived_at.",
     "handler": h_unarchive_project,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
     }}},
    {"name": "link_portfolio",
     "description": "A theme in project portfolio tracks a team node (portfolio link, not graph edge).",
     "handler": h_link_portfolio,
     "inputSchema": {"type": "object", "required": [
         "theme_node_id", "project_id", "node_id", "actor",
     ], "properties": {
         "theme_node_id": {"type": "string"},
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "actor": {"type": "string"},
     }}},
    {"name": "unlink_portfolio",
     "description": "Remove a portfolio link (theme stops tracking team node).",
     "handler": h_unlink_portfolio,
     "inputSchema": {"type": "object", "required": [
         "theme_node_id", "project_id", "node_id", "actor",
     ], "properties": {
         "theme_node_id": {"type": "string"},
         "project_id": {"type": "string"},
         "node_id": {"type": "string"},
         "actor": {"type": "string"},
     }}},
    {"name": "create_cross_edge",
     "description": "Create a cross-project edge (blocks or depends_on). src blocked until dst achieved.",
     "handler": h_create_cross_edge,
     "inputSchema": {"type": "object", "required": [
         "src_project_id", "src_node_id", "dst_project_id", "dst_node_id",
         "edge_kind", "actor",
     ], "properties": {
         "src_project_id": {"type": "string"},
         "src_node_id": {"type": "string"},
         "dst_project_id": {"type": "string"},
         "dst_node_id": {"type": "string"},
         "edge_kind": {"type": "string", "enum": ["blocks", "depends_on"]},
         "actor": {"type": "string"},
     }}},
    {"name": "delete_cross_edge",
     "description": "Delete a cross-project edge.",
     "handler": h_delete_cross_edge,
     "inputSchema": {"type": "object", "required": [
         "src_project_id", "src_node_id", "dst_project_id", "dst_node_id",
         "edge_kind", "actor",
     ], "properties": {
         "src_project_id": {"type": "string"},
         "src_node_id": {"type": "string"},
         "dst_project_id": {"type": "string"},
         "dst_node_id": {"type": "string"},
         "edge_kind": {"type": "string", "enum": ["blocks", "depends_on"]},
         "actor": {"type": "string"},
     }}},
    {"name": "propose_trajectory",
     "description": "Create a draft trajectory from target brief + legs. No graph writes.",
     "handler": h_propose_trajectory,
     "inputSchema": {"type": "object", "required": [
         "project_id", "target_brief", "legs", "proposed_by",
     ], "properties": {
         "project_id": {"type": "string"},
         "target_brief": {"type": "string"},
         "legs": {
             "type": "array",
             "items": {"type": "object"},
             "description": "Ordered legs: leg_kind, payload, optional node_ref.",
         },
         "proposed_by": {"type": "string"},
         "scope": {"type": "object"},
     }}},
    {"name": "accept_trajectory_leg",
     "description": "Apply pending trajectory legs to the graph (accept = apply).",
     "handler": h_accept_trajectory_leg,
     "inputSchema": {"type": "object", "required": [
         "trajectory_id", "actor",
     ], "properties": {
         "trajectory_id": {"type": "string"},
         "leg_seqs": {
             "type": "array",
             "items": {"type": "integer"},
             "description": "Leg seq numbers to accept (default: all pending).",
         },
         "actor": {"type": "string"},
     }}},
    {"name": "reject_trajectory",
     "description": "Mark a draft trajectory rejected without applying legs.",
     "handler": h_reject_trajectory,
     "inputSchema": {"type": "object", "required": [
         "trajectory_id", "actor",
     ], "properties": {
         "trajectory_id": {"type": "string"},
         "actor": {"type": "string"},
     }}},
]

TOOLS_BY_NAME: dict[str, dict] = {t["name"]: t for t in TOOLS}


# ============================================================
# JSON-RPC dispatch
# ============================================================

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "manifold"
SERVER_VERSION = config.MANIFOLD_VERSION


def _ok(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _rpc_error(req_id, code, message, data=None):
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


def _tool_descriptor(t):
    return {"name": t["name"], "description": t["description"],
            "inputSchema": t["inputSchema"]}


def _content_text(payload):
    """MCP tools/call returns {content: [{type, text}, ...]}.

    We serialize the structured payload as a single text block of JSON. Callers
    parse it client-side. Some payloads are error envelopes; in that case we
    also set isError=true on the response so MCP clients can route correctly.
    """
    return [{"type": "text", "text": json.dumps(payload, default=str)}]


def handle(req, conn) -> dict | None:
    """Dispatch one JSON-RPC request. Returns response dict or None (for notifications)."""
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params") or {}

    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return _ok(req_id, {"tools": [_tool_descriptor(t) for t in TOOLS]})

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        tool = TOOLS_BY_NAME.get(name) if isinstance(name, str) else None
        if tool is None:
            return _ok(req_id, {
                "isError": True,
                "content": _content_text(errors.envelope(
                    errors.UNKNOWN_TOOL, f"unknown tool: {name!r}",
                    retry=errors.RETRY_NO,
                    suggest=[f"call tools/list to see available tools"],
                )),
            })
        try:
            result = tool["handler"](conn, arguments)
        except Exception as exc:
            tb = traceback.format_exc()
            return _ok(req_id, {
                "isError": True,
                "content": _content_text(errors.envelope(
                    errors.INTERNAL_ERROR,
                    f"{type(exc).__name__}: {exc}",
                    retry=errors.RETRY_NO,
                    context={"traceback": tb[-500:]},
                )),
            })
        is_error = isinstance(result, dict) and "error" in result and isinstance(result["error"], dict)
        return _ok(req_id, {
            "isError": is_error,
            "content": _content_text(result),
        })

    return _rpc_error(req_id, -32601, f"method not found: {method}")


def main() -> int:
    """Run the stdio JSON-RPC loop."""
    conn = db.connect()
    schema.bootstrap(conn)
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
            except json.JSONDecodeError as exc:
                sys.stdout.write(json.dumps(
                    _rpc_error(None, -32700, f"parse error: {exc}")
                ) + "\n")
                sys.stdout.flush()
                continue
            resp = handle(req, conn)
            if resp is not None:
                sys.stdout.write(json.dumps(resp, default=str) + "\n")
                sys.stdout.flush()
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
