#!/usr/bin/env python3
"""Wire automated_check verdicts on the manifold project for drift-report dogfood."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_PKG_ROOT = Path(__file__).resolve().parents[1]
if str(_PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(_PKG_ROOT))

from manifold import db, queries, writes  # noqa: E402
from manifold import schema  # noqa: E402

PROJECT_ID = "ai-foundry"
ACTOR = "script:bootstrap_dogfood_verdicts"
CHANGE_REASON = "evolution"
SOURCE = "script:bootstrap_dogfood_verdicts"

NODE_WIRES: dict[str, dict[str, str]] = {
    nid: {"verdict_mechanism": "automated_check", "verdict_check": check}
    for nid, check in {
        "R.core": "test -f packages/manifold/manifold/queries.py",
        "R.mcp": "test -f plugins/manifold/server/mcp_server.py",
        "R.web": "test -d apps/manifold-web/manifold_web",
        "R.K1": "test -f packages/manifold/manifold/status_brief.py",
        "R.K2": "test -f packages/manifold/manifold/presentation_svg.py",
        "R.traj": "test -f packages/manifold/manifold/trajectory.py",
    }.items()
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def default_db_path() -> Path:
    override = os.environ.get("MANIFOLD_DB", "").strip()
    if override:
        return Path(os.path.expanduser(override))
    return Path.home() / ".claude" / "manifold.db"


def _desired_fields(spec: dict[str, str]) -> dict[str, str]:
    fields = dict(spec)
    if "verdict_check" in fields and "verdict_mechanism" not in fields:
        fields["verdict_mechanism"] = "automated_check"
    return fields


def merge_spec_config_project_root(
    conn, root: Path, *, dry_run: bool
) -> tuple[bool, str | None]:
    """Merge project_root into projects.spec_config. Returns (changed, previous)."""
    project = queries.get_project(conn, PROJECT_ID)
    if project is None:
        raise SystemExit(f"project {PROJECT_ID!r} not found in database")

    spec = dict(project.get("spec_config") or {})
    root_str = str(root)
    previous = spec.get("project_root")
    if spec.get("project_root") == root_str:
        return False, previous

    spec["project_root"] = root_str
    if dry_run:
        return True, previous

    conn.execute(
        "UPDATE projects SET spec_config = ? WHERE project_id = ?",
        (json.dumps(spec), PROJECT_ID),
    )
    return True, previous


def wire_node(
    conn, node_id: str, fields: dict[str, str], *, dry_run: bool
) -> str:
    """Update node if needed. Returns action label: updated | unchanged | missing."""
    node = queries.get_node(conn, PROJECT_ID, node_id)
    if node is None:
        return "missing"

    desired = _desired_fields(fields)
    current = {
        k: (node.get(k) or "")
        for k in desired
    }
    normalized_desired = {k: desired[k] for k in desired}
    if current == normalized_desired:
        return "unchanged"

    if dry_run:
        return "would_update"

    rev = node["current_revision_id"]
    result = writes.update_node(
        conn,
        PROJECT_ID,
        node_id,
        desired,
        expected_revision_id=rev,
        actor=ACTOR,
        source=SOURCE,
        change_reason=CHANGE_REASON,
    )
    return "unchanged" if result.get("unchanged") else "updated"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing to the database",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite DB path (default: $MANIFOLD_DB or ~/.claude/manifold.db)",
    )
    args = parser.parse_args(argv)

    root = repo_root()
    db_path = args.db if args.db is not None else default_db_path()

    conn = db.connect(db_path)
    schema.bootstrap(conn)
    try:
        spec_changed, prev_root = merge_spec_config_project_root(
            conn, root, dry_run=args.dry_run
        )

        node_results: dict[str, str] = {}
        for node_id, spec in NODE_WIRES.items():
            node_results[node_id] = wire_node(
                conn, node_id, spec, dry_run=args.dry_run
            )

        if not args.dry_run:
            conn.commit()
    finally:
        conn.close()

    print("bootstrap_dogfood_verdicts summary")
    print(f"  db:           {db_path}")
    print(f"  project_id:   {PROJECT_ID}")
    print(f"  repo root:    {root}")
    print(f"  dry_run:      {args.dry_run}")
    if spec_changed:
        label = "would_set" if args.dry_run else "set"
        print(f"  spec_config:  {label} project_root (was {prev_root!r})")
    else:
        print(f"  spec_config:  project_root unchanged ({prev_root!r})")

    for node_id in NODE_WIRES:
        action = node_results[node_id]
        check = _desired_fields(NODE_WIRES[node_id]).get("verdict_check", "")
        print(f"  {node_id}: {action} — {check!r}")

    counts = {}
    for v in node_results.values():
        counts[v] = counts.get(v, 0) + 1
    print(f"  nodes:        {counts}")

    if any(v == "missing" for v in node_results.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
