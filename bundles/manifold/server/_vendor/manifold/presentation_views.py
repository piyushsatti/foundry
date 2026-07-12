"""Topic K view-model builders — graph → dict (diagrams, mindmaps).

Renderers live in presentation_format.py. Graph is authoritative; these are projections.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from .node_ref import format_node_ref
from . import queries

MAX_DIAGRAM_NODES = 12
MAX_MINDMAP_NODES = 64
MAX_PRESENTATION_NODES = MAX_DIAGRAM_NODES  # backward compat alias
DIAGRAM_TYPES = frozenset({"blockers", "decomposition", "trajectory"})
MINDMAP_TYPES = frozenset({"flow", "decomposition"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _node_entry(conn: sqlite3.Connection, project_id: str, node_id: str) -> Optional[dict]:
    node = queries.get_node(conn, project_id, node_id)
    if node is None:
        return None
    return {
        "node_ref": format_node_ref(project_id, node_id),
        "project_id": project_id,
        "node_id": node_id,
        "title": node.get("title") or "",
        "layer": node.get("layer") or "",
        "target_status": node.get("target_status") or "",
    }


def _add_node(nodes: dict, entry: Optional[dict], *, max_nodes: int) -> bool:
    """Add entry to nodes dict. Returns True if truncated."""
    if entry is None:
        return False
    ref = entry["node_ref"]
    if ref in nodes:
        return False
    if len(nodes) >= max_nodes:
        return True
    nodes[ref] = entry
    return False


def _resolve_focus(conn: sqlite3.Connection, project_id: str,
                   focus_node_id: Optional[str]) -> Optional[str]:
    if focus_node_id:
        if queries.get_node(conn, project_id, focus_node_id) is None:
            return None
        return focus_node_id
    excluded = queries.next_leaves_excluded(conn, project_id)
    if excluded:
        return excluded[0]["node_id"]
    leaves = queries.next_leaves(conn, project_id)
    if leaves:
        return leaves[0]["node_id"]
    rows = queries.list_nodes(conn, project_id, limit=1)
    return rows[0]["node_id"] if rows else None


def build_diagram_view(conn: sqlite3.Connection, project_id: str, *,
                       diagram_type: str = "blockers",
                       focus_node_id: Optional[str] = None,
                       trajectory_id: Optional[str] = None,
                       max_nodes: int = MAX_PRESENTATION_NODES) -> dict:
    """Build a bounded flowchart view-model (nodes + edges).

    diagram_type: blockers | decomposition | trajectory
    """
    diagram_type = (diagram_type or "blockers").strip()
    if diagram_type not in DIAGRAM_TYPES:
        diagram_type = "blockers"

    base = {
        "project_id": project_id,
        "view_kind": "diagram",
        "diagram_type": diagram_type,
        "generated_at": _now_iso(),
        "focus_node_id": focus_node_id,
        "trajectory_id": trajectory_id,
        "truncated": False,
        "warnings": [],
        "nodes": [],
        "edges": [],
    }

    if queries.get_project(conn, project_id) is None:
        base["warnings"].append("project_not_found")
        return base

    if diagram_type == "trajectory":
        return _diagram_trajectory(conn, base, trajectory_id, max_nodes)

    focus = _resolve_focus(conn, project_id, focus_node_id)
    if focus is None:
        base["warnings"].append("no_nodes")
        return base
    base["focus_node_id"] = focus

    if diagram_type == "blockers":
        return _diagram_blockers(conn, project_id, focus, base, max_nodes)
    return _diagram_decomposition(conn, project_id, focus, base, max_nodes)


def _diagram_blockers(conn: sqlite3.Connection, project_id: str, focus: str,
                      base: dict, max_nodes: int) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    truncated = False

    focus_ref = format_node_ref(project_id, focus)
    truncated = _add_node(nodes, _node_entry(conn, project_id, focus), max_nodes=max_nodes) or truncated

    for row in queries.list_cross_blocking_chain(conn, project_id, focus):
        if truncated:
            break
        bp, bn = row["project_id"], row["node_id"]
        truncated = _add_node(nodes, _node_entry(conn, bp, bn), max_nodes=max_nodes) or truncated
        edges.append({
            "from_ref": format_node_ref(bp, bn),
            "to_ref": focus_ref,
            "kind": "blocks",
            "scope": "cross_project",
        })

    for row in queries.list_blocking_chain(conn, project_id, focus, direct_only=True):
        if truncated:
            break
        bid = row["node_id"]
        truncated = _add_node(nodes, _node_entry(conn, project_id, bid), max_nodes=max_nodes) or truncated
        edges.append({
            "from_ref": format_node_ref(project_id, bid),
            "to_ref": focus_ref,
            "kind": "blocks",
            "scope": "project",
        })

    for row in queries.list_blocking_chain(conn, project_id, focus, direct_only=False):
        if truncated:
            break
        bid = row["node_id"]
        if bid == focus:
            continue
        truncated = _add_node(nodes, _node_entry(conn, project_id, bid), max_nodes=max_nodes) or truncated

    if truncated:
        base["warnings"].append("truncated")
    base["nodes"] = list(nodes.values())
    base["edges"] = edges
    base["truncated"] = truncated
    return base


def _diagram_decomposition(conn: sqlite3.Connection, project_id: str, focus: str,
                           base: dict, max_nodes: int) -> dict:
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    truncated = False
    queue = [focus]
    seen = set()

    while queue and not truncated:
        nid = queue.pop(0)
        if nid in seen:
            continue
        seen.add(nid)
        truncated = _add_node(nodes, _node_entry(conn, project_id, nid), max_nodes=max_nodes) or truncated
        if truncated:
            break
        full = queries.peek_node_full(conn, project_id, nid, include=("children",))
        if not full:
            continue
        parent_ref = format_node_ref(project_id, nid)
        for child in full.get("children") or []:
            cid = child["node_id"]
            truncated = _add_node(
                nodes,
                {
                    "node_ref": format_node_ref(project_id, cid),
                    "project_id": project_id,
                    "node_id": cid,
                    "title": child.get("title") or "",
                    "layer": child.get("layer") or "",
                    "target_status": child.get("target_status") or "",
                },
                max_nodes=max_nodes,
            ) or truncated
            edges.append({
                "from_ref": parent_ref,
                "to_ref": format_node_ref(project_id, cid),
                "kind": "parent",
                "scope": "project",
            })
            if cid not in seen:
                queue.append(cid)

    if truncated:
        base["warnings"].append("truncated")
    base["nodes"] = list(nodes.values())
    base["edges"] = edges
    base["truncated"] = truncated
    return base


def _diagram_trajectory(conn: sqlite3.Connection, base: dict,
                        trajectory_id: Optional[str], max_nodes: int) -> dict:
    from . import trajectory as traj_mod

    if not trajectory_id:
        base["warnings"].append("trajectory_id_required")
        return base
    report = traj_mod.peek_trajectory(conn, trajectory_id)
    if report.get("error"):
        base["warnings"].append(report["error"])
        return base

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    truncated = False
    prev_ref: Optional[str] = None
    pid = report.get("project_id") or base["project_id"]

    for leg in report.get("legs") or []:
        if truncated:
            break
        label = leg.get("summary") or leg.get("leg_kind") or f"leg-{leg.get('seq')}"
        ref = f"trajectory/{trajectory_id}/leg-{leg.get('seq')}"
        entry = {
            "node_ref": ref,
            "project_id": pid,
            "node_id": str(leg.get("seq")),
            "title": label,
            "layer": "trajectory",
            "target_status": leg.get("status") or "",
        }
        truncated = _add_node(nodes, entry, max_nodes=max_nodes) or truncated
        if prev_ref:
            edges.append({
                "from_ref": prev_ref,
                "to_ref": ref,
                "kind": "then",
                "scope": "trajectory",
            })
        prev_ref = ref

    base["project_id"] = pid
    base["focus_node_id"] = None
    base["nodes"] = list(nodes.values())
    base["edges"] = edges
    base["truncated"] = truncated
    if truncated:
        base["warnings"].append("truncated")
    return base


def build_mindmap_view(conn: sqlite3.Connection, project_id: str, *,
                       mindmap_type: str = "flow",
                       focus_node_id: Optional[str] = None,
                       max_depth: int = 4,
                       max_nodes: int = MAX_MINDMAP_NODES) -> dict:
    """Build a hierarchical mindmap view-model (tree + flat nodes list)."""
    mindmap_type = (mindmap_type or "flow").strip()
    if mindmap_type not in MINDMAP_TYPES:
        mindmap_type = "flow"

    base = {
        "project_id": project_id,
        "view_kind": "mindmap",
        "mindmap_type": mindmap_type,
        "generated_at": _now_iso(),
        "focus_node_id": focus_node_id,
        "truncated": False,
        "warnings": [],
        "nodes": [],
        "tree": None,
    }

    if queries.get_project(conn, project_id) is None:
        base["warnings"].append("project_not_found")
        return base

    focus = _resolve_focus(conn, project_id, focus_node_id)
    if focus is None:
        base["warnings"].append("no_nodes")
        return base
    base["focus_node_id"] = focus

    flat: dict[str, dict] = {}
    truncated = False

    def walk(nid: str, depth: int) -> Optional[dict]:
        nonlocal truncated
        if depth > max_depth or truncated:
            return None
        entry = _node_entry(conn, project_id, nid)
        if entry is None:
            return None
        truncated = _add_node(flat, entry, max_nodes=max_nodes) or truncated
        node = {
            "node_ref": entry["node_ref"],
            "label": entry["title"] or entry["node_id"],
            "status": entry["target_status"],
            "children": [],
        }
        if truncated and depth > 0:
            return node
        full = queries.peek_node_full(conn, project_id, nid, include=("children",))
        for child in (full or {}).get("children") or []:
            if truncated:
                break
            child_tree = walk(child["node_id"], depth + 1)
            if child_tree:
                node["children"].append(child_tree)
        return node

    tree = walk(focus, 0)
    if truncated:
        base["warnings"].append("truncated")
    base["tree"] = tree
    base["nodes"] = list(flat.values())
    base["truncated"] = truncated
    return base
