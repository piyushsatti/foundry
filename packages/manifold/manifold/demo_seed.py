"""Idempotent demo portfolio for Topic K human surfaces (brief, diagrams, mindmaps).

Seeds acme-checkout + ai-platform under portfolio theme T.checkout — mirrors the
.gitignored/demos/human-layer-demo narrative with a real graph in $MANIFOLD_DB.
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from . import queries, writes
from .constants import PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER

DEMO_MAIN_PROJECT = "acme-checkout"
DEMO_PLATFORM_PROJECT = "ai-platform"
DEMO_THEME_ID = "T.checkout"

# Projects left visible when --archive-legacy is passed.
DEMO_KEEP_PROJECTS = frozenset({
    PORTFOLIO_PROJECT_ID,
    DEMO_MAIN_PROJECT,
    DEMO_PLATFORM_PROJECT,
    "obs-fastapi",  # real drift dogfood testbed
})

LEGACY_ARCHIVE_CANDIDATES = frozenset({
    "chronicler",
    "manifold",
    "manifold-v03",
    "obs-express",
    "obs-gin",
    "orchestrator",
    "plan-orchestrator",
})


def seed_acme_checkout_demo(conn: sqlite3.Connection, *,
                            actor: str = "demo:seed",
                            force: bool = False) -> dict:
    """Create or refresh the Acme Checkout showcase graph. Returns summary dict."""
    if queries.get_project(conn, DEMO_MAIN_PROJECT) and not force:
        return _summary(conn, status="already_seeded")

    _ensure_portfolio_project(conn)
    _register_team_projects(conn)

    # Theme
    if queries.get_node(conn, PORTFOLIO_PROJECT_ID, DEMO_THEME_ID) is None:
        writes.create_node(
            conn, PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER, DEMO_THEME_ID,
            "Q3 Checkout Resilience",
            body=(
                "# Q3 Checkout Resilience\n\n"
                "Company bet: reduce checkout friction and fraud false-positives "
                "before peak season."
            ),
            target_status="in_progress",
            actor=actor,
        )

    pid = DEMO_MAIN_PROJECT
    plat = DEMO_PLATFORM_PROJECT

    # Intent
    if queries.get_node(conn, pid, "I.1") is None:
        writes.create_node(
            conn, pid, "intent", "I.1", "Checkout revamp",
            body=(
                "# Checkout revamp\n\n"
                "Replace legacy multi-step checkout with one-click flow on web and mobile."
            ),
            target_status="in_progress",
            actor=actor,
        )

    # Capabilities
    if queries.get_node(conn, pid, "C.3") is None:
        writes.create_node(
            conn, pid, "capabilities", "C.3", "Mobile wallet",
            body="Apple Pay and Google Pay live on mobile web.",
            parents=["I.1"],
            target_status="achieved",
            actor=actor,
        )
    if queries.get_node(conn, pid, "C.1") is None:
        writes.create_node(
            conn, pid, "capabilities", "C.1", "One-click checkout",
            body="Saved payment + address; target Q3 ship.",
            parents=["I.1"],
            target_status="in_progress",
            actor=actor,
        )

    # Realizations
    if queries.get_node(conn, pid, "R.3") is None:
        writes.create_node(
            conn, pid, "realizations", "R.3", "One-click API",
            body="POST /checkout/one-click — in progress.",
            parents=["C.1"],
            target_status="planned",
            actor=actor,
        )
    if queries.get_node(conn, pid, "R.12") is None:
        writes.create_node(
            conn, pid, "realizations", "R.12", "Fraud scoring integration",
            body="Wire checkout to platform fraud model before launch.",
            parents=["C.1"],
            target_status="planned",
            actor=actor,
        )

    # Platform capability (blocker)
    if queries.get_node(conn, plat, "C.4") is None:
        writes.create_node(
            conn, plat, "capability", "C.4", "Fraud ML model",
            body="Production fraud scoring API — not yet achieved.",
            target_status="planned",
            actor=actor,
        )

    # Portfolio links
    for project_id, node_id in (
        (pid, "I.1"),
        (pid, "R.12"),
        (plat, "C.4"),
    ):
        writes.link_portfolio(conn, DEMO_THEME_ID, project_id, node_id, actor=actor)

    # Cross-project block
    existing = queries.list_cross_edges(conn, project_id=pid)
    has_block = any(
        e.get("src_project_id") == pid and e.get("src_node_id") == "R.12"
        and e.get("dst_project_id") == plat and e.get("dst_node_id") == "C.4"
        for e in existing
    )
    if not has_block:
        writes.create_cross_edge(
            conn, pid, "R.12", plat, "C.4", "blocks", actor=actor,
        )

    return _summary(conn, status="seeded")


def archive_legacy_projects(conn: sqlite3.Connection) -> list[str]:
    """Archive experimental projects so the demo portfolio is easy to find."""
    archived = []
    for project_id in sorted(LEGACY_ARCHIVE_CANDIDATES):
        if project_id in DEMO_KEEP_PROJECTS:
            continue
        if queries.get_project(conn, project_id) is None:
            continue
        row = conn.execute(
            "SELECT archived_at FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if row and row["archived_at"]:
            continue
        writes.archive_project(conn, project_id)
        archived.append(project_id)
    return archived


def demo_urls(*, host: str = "127.0.0.1", port: int = 7779) -> dict[str, str]:
    base = f"http://{host}:{port}"
    pid = DEMO_MAIN_PROJECT
    return {
        "home": f"{base}/",
        "project": f"{base}/projects/{pid}",
        "brief": f"{base}/projects/{pid}/brief",
        "diagram_blockers": f"{base}/projects/{pid}/views/blockers?focus=R.12",
        "mindmap": f"{base}/projects/{pid}/mindmap?focus=I.1",
        "portfolio": f"{base}/reports/portfolio",
        "drift": f"{base}/projects/{pid}/drift-report",
        "obs_fastapi": f"{base}/projects/obs-fastapi/brief",
    }


def _summary(conn: sqlite3.Connection, *, status: str) -> dict:
    return {
        "status": status,
        "theme_id": DEMO_THEME_ID,
        "main_project": DEMO_MAIN_PROJECT,
        "platform_project": DEMO_PLATFORM_PROJECT,
        "urls": demo_urls(),
        "nodes": {
            "acme-checkout": _node_count(conn, DEMO_MAIN_PROJECT),
            "ai-platform": _node_count(conn, DEMO_PLATFORM_PROJECT),
        },
    }


def _node_count(conn: sqlite3.Connection, project_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM nodes WHERE project_id = ? AND deleted_at IS NULL",
        (project_id,),
    ).fetchone()
    return int(row["n"]) if row else 0


def _ensure_portfolio_project(conn: sqlite3.Connection) -> None:
    if queries.get_project(conn, PORTFOLIO_PROJECT_ID):
        return
    writes.register_project(
        conn, PORTFOLIO_PROJECT_ID,
        spec_config={"layers": [{"name": PORTFOLIO_THEME_LAYER}]},
        label="Company portfolio",
    )


def _register_team_projects(conn: sqlite3.Connection) -> None:
    layers_checkout = [
        {"name": "intent", "verdict_default": "human_signoff"},
        {"name": "capabilities", "verdict_default": "human_signoff"},
        {"name": "realizations", "verdict_default": "automated_check"},
    ]
    layers_platform = [
        {"name": "capability", "verdict_default": "human_signoff"},
    ]
    for project_id, label, layers in (
        (DEMO_MAIN_PROJECT, "Acme Checkout", layers_checkout),
        (DEMO_PLATFORM_PROJECT, "AI Platform", layers_platform),
    ):
        if queries.get_project(conn, project_id):
            continue
        writes.register_project(
            conn, project_id,
            spec_config={"layers": layers},
            label=label,
        )
