"""Named presentation view catalog (Structurizr-style views over the graph model)."""
from __future__ import annotations

import json
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from . import presentation_views

_REGISTRY_PATH = Path(__file__).resolve().parent / "data" / "presentation_views.json"


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    with _REGISTRY_PATH.open(encoding="utf-8") as fh:
        data = json.load(fh)
    views = data.get("views") or {}
    if not isinstance(views, dict):
        raise ValueError("presentation_views.json: views must be an object")
    return views


def list_views() -> list[dict[str, Any]]:
    """Catalog entries for UI / MCP list."""
    out = []
    for view_id, spec in sorted(load_registry().items()):
        out.append({
            "view_id": view_id,
            "kind": spec.get("kind"),
            "description": spec.get("description", ""),
            "diagram_type": spec.get("diagram_type"),
            "mindmap_type": spec.get("mindmap_type"),
        })
    return out


def get_view_spec(view_id: str) -> Optional[dict[str, Any]]:
    return load_registry().get(view_id)


def build_registered_view(conn: sqlite3.Connection, project_id: str, view_id: str, *,
                          focus_node_id: Optional[str] = None,
                          trajectory_id: Optional[str] = None,
                          max_nodes: Optional[int] = None,
                          max_depth: Optional[int] = None) -> dict:
    """Resolve a catalog view id to a view-model dict."""
    spec = get_view_spec(view_id)
    if spec is None:
        return {
            "project_id": project_id,
            "view_kind": "unknown",
            "view_id": view_id,
            "generated_at": presentation_views._now_iso(),
            "warnings": ["unknown_view_id"],
            "nodes": [],
            "edges": [],
            "tree": None,
        }

    cap = max_nodes if max_nodes is not None else int(spec.get("max_nodes", 12))
    kind = spec.get("kind")

    if kind == "diagram":
        view = presentation_views.build_diagram_view(
            conn, project_id,
            diagram_type=spec.get("diagram_type", "blockers"),
            focus_node_id=focus_node_id,
            trajectory_id=trajectory_id,
            max_nodes=cap,
        )
    elif kind == "mindmap":
        depth = max_depth if max_depth is not None else int(spec.get("max_depth", 4))
        view = presentation_views.build_mindmap_view(
            conn, project_id,
            mindmap_type=spec.get("mindmap_type", "flow"),
            focus_node_id=focus_node_id,
            max_depth=depth,
            max_nodes=cap,
        )
    else:
        view = {
            "project_id": project_id,
            "view_kind": "unknown",
            "warnings": ["invalid_view_kind"],
            "nodes": [],
        }

    view["view_id"] = view_id
    view["view_description"] = spec.get("description", "")
    return view
