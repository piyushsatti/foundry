"""Purge legacy DB projects and seed ai-foundry — foundry dogfood graph."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import queries, writes
from .constants import PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER

PROJECT_ID = "ai-foundry"
PROJECT_LABEL = "AI Foundry"
THEME_ID = "T.foundry"
THEME_TITLE = "Foundry platform"

LAYERS = [
    {"name": "intent", "verdict_default": "human_signoff"},
    {"name": "capabilities", "verdict_default": "human_signoff"},
    {"name": "realizations", "verdict_default": "automated_check"},
]

# realization node_id → verdict_check (repo-relative paths)
VERDICT_WIRES: dict[str, str] = {
    "R.core": "test -f packages/manifold/manifold/queries.py",
    "R.mcp": "test -f plugins/manifold/server/mcp_server.py",
    "R.web": "test -d apps/manifold-web/manifold_web",
    "R.K1": "test -f packages/manifold/manifold/status_brief.py",
    "R.K2": "test -f packages/manifold/manifold/presentation_svg.py",
    "R.traj": "test -f packages/manifold/manifold/trajectory.py",
}


def purge_all_projects(conn: sqlite3.Connection) -> list[str]:
    """Delete every project and dependent rows. Returns removed project ids."""
    ids = [r["project_id"] for r in conn.execute("SELECT project_id FROM projects")]
    if not ids:
        return []

    for pid in ids:
        conn.execute("DELETE FROM revisions WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM verdicts WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM validations WHERE project_id = ?", (pid,))
    conn.execute("DELETE FROM trajectory_legs")
    conn.execute("DELETE FROM trajectories")
    conn.execute("DELETE FROM cross_project_edges")
    conn.execute("DELETE FROM portfolio_links")
    for pid in ids:
        conn.execute("DELETE FROM projects WHERE project_id = ?", (pid,))
    return ids


def seed_ai_foundry(
    conn: sqlite3.Connection,
    *,
    repo_root: Path,
    actor: str = "foundry:init",
    include_portfolio: bool = False,
) -> dict:
    """Create ai-foundry graph aligned to current foundry work.

    When ``include_portfolio`` is True, also seeds portfolio/T.foundry theme link.
    Solo-idea DBs should leave this False.
    """
    root_str = str(repo_root.resolve())
    spec_config = {"layers": LAYERS, "project_root": root_str}

    if include_portfolio:
        writes.register_project(
            conn, PORTFOLIO_PROJECT_ID,
            spec_config={"layers": [{"name": PORTFOLIO_THEME_LAYER}]},
            label="Company portfolio",
        )

    writes.register_project(
        conn, PROJECT_ID,
        spec_config=spec_config,
        label=PROJECT_LABEL,
    )

    if include_portfolio:
        writes.create_node(
            conn, PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER, THEME_ID,
            THEME_TITLE,
            body=(
                "# Foundry platform\n\n"
                "Private monorepo: manifold compass, skills, MCP servers, web UI."
            ),
            target_status="in_progress",
            actor=actor,
        )

    _node(conn, PROJECT_ID, "intent", "I.1", "Foundry compass monorepo",
          body=(
              "# Foundry\n\n"
              "Agent skills + MCP + SQLite spec graph for long-horizon software work. "
              "Repo: ai-foundry."
          ),
          target_status="in_progress", actor=actor)

    caps = [
        ("C.1", "Core compass", "Graph, spec-audit, drift-report, next-leaves", "achieved"),
        ("C.2", "Portfolio & cross-project", "Themes, portfolio-report, cross blocks", "achieved"),
        ("C.3", "Trajectory", "propose → show → accept spec evolution", "achieved"),
        ("C.4", "Human output (Topic K)", "status-brief, diagrams, present skill", "achieved"),
        ("C.5", "Orchestrator", "Dispatch boundary + progress-tracker interop", "planned"),
    ]
    for nid, title, body, status in caps:
        _node(conn, PROJECT_ID, "capabilities", nid, title,
              body=f"# {title}\n\n{body}.", parents=["I.1"],
              target_status=status, actor=actor)

    reals = [
        ("R.core", "Core library", "packages/manifold", "C.1", "achieved"),
        ("R.mcp", "Manifold MCP server", "plugins/manifold (42 tools)", "C.1", "achieved"),
        ("R.web", "Manifold web UI", "apps/manifold-web", "C.1", "achieved"),
        ("R.traj", "Trajectory v1", "schema + CLI + MCP + HTTP peek", "C.3", "achieved"),
        ("R.j3", "Trajectory web inbox", "J3 — plan/apply UX on web", "C.3", "planned"),
        ("R.K1", "Status brief", "build_status_brief_view + /brief + peek_status_brief", "C.4", "achieved"),
        ("R.K2", "Diagrams & mindmaps", "SVG views, registry, content negotiation", "C.4", "achieved"),
        ("R.orch", "Orchestrator skill", "Separate track — skills/orchestrator", "C.5", "planned"),
    ]
    for nid, title, body, parent, status in reals:
        _node(conn, PROJECT_ID, "realizations", nid, title,
              body=f"# {title}\n\n{body}.", parents=[parent],
              target_status=status, actor=actor)
        check = VERDICT_WIRES.get(nid)
        if check and queries.get_node(conn, PROJECT_ID, nid):
            node = queries.get_node(conn, PROJECT_ID, nid)
            writes.update_node(
                conn, PROJECT_ID, nid,
                {"verdict_mechanism": "automated_check", "verdict_check": check},
                expected_revision_id=node["current_revision_id"],
                actor=actor, source="foundry:init", change_reason="evolution",
            )

    if include_portfolio:
        writes.link_portfolio(conn, THEME_ID, PROJECT_ID, "I.1", actor=actor)

    return summary(conn, repo_root=root_str, include_portfolio=include_portfolio)


def _node(conn, project_id, layer, node_id, title, *, body, actor,
          parents=None, target_status="planned"):
    if queries.get_node(conn, project_id, node_id) is not None:
        return
    writes.create_node(
        conn, project_id, layer, node_id, title,
        body=body, parents=parents or [], target_status=target_status, actor=actor,
    )


def summary(conn: sqlite3.Connection, *, repo_root: str,
            host: str = "127.0.0.1", port: int = 7779,
            include_portfolio: bool = False) -> dict:
    base = f"http://{host}:{port}"
    pid = PROJECT_ID
    urls = {
        "home": f"{base}/",
        "project": f"{base}/projects/{pid}",
        "brief": f"{base}/projects/{pid}/brief",
        "mindmap": f"{base}/projects/{pid}/mindmap?focus=I.1",
        "next_leaves": f"{base}/projects/{pid}",
        "drift": f"{base}/projects/{pid}/drift-report",
    }
    if include_portfolio:
        urls["portfolio"] = f"{base}/reports/portfolio"
    out = {
        "project_id": pid,
        "project_label": PROJECT_LABEL,
        "repo_root": repo_root,
        "node_count": conn.execute(
            "SELECT COUNT(*) AS n FROM nodes WHERE project_id = ? AND deleted_at IS NULL",
            (pid,),
        ).fetchone()["n"],
        "urls": urls,
    }
    if include_portfolio:
        out["theme_id"] = THEME_ID
    return out


def init_foundry_db(conn: sqlite3.Connection, *, repo_root: Path,
                    actor: str = "foundry:init") -> dict:
    """Purge all projects, seed ai-foundry. One-shot clean slate."""
    removed = purge_all_projects(conn)
    result = seed_ai_foundry(conn, repo_root=repo_root, actor=actor)
    result["removed_projects"] = removed
    return result
