"""
Shared test fixtures for manifold tests.

`fresh_db()` returns a tuple (connection, path) for a freshly-bootstrapped
temp DB. Callers are responsible for closing the connection; the path is
cleaned up automatically when the file goes out of scope (we register via
unittest.addCleanup in test classes that use this).
"""
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from manifold import db, schema


def fresh_db(test_case: unittest.TestCase):
    """Open and bootstrap a new DB; return (conn, path).

    Registers cleanup via the test_case so the file is removed after the test.
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    path = Path(tmp.name)
    conn = db.connect(path)
    schema.bootstrap(conn)

    def _cleanup():
        try:
            conn.close()
        except sqlite3.Error:
            pass
        for suffix in ("", "-shm", "-wal"):
            p = Path(str(path) + suffix)
            if p.exists():
                p.unlink()

    test_case.addCleanup(_cleanup)
    return conn, path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def seed_project(conn: sqlite3.Connection, project_id: str = "test",
                 layers=None, label: str = "Test Project") -> None:
    """Insert a minimal projects row for tests that need one."""
    if layers is None:
        layers = [{"name": "intent", "verdict_default": "human_signoff"},
                  {"name": "realizations", "verdict_default": "automated_check"}]
    conn.execute(
        "INSERT INTO projects (project_id, label, spec_config, created_at) "
        "VALUES (?, ?, ?, ?)",
        (project_id, label, json.dumps({"layers": layers}), now_iso()),
    )


def seed_portfolio_fixture(conn: sqlite3.Connection, *,
                           cross_block: bool = False) -> None:
    """Portfolio theme + team links; optional cross-block on product-app R.12."""
    from manifold import writes
    from manifold.constants import PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER

    product_layers = [{"name": "intent"}]
    if cross_block:
        product_layers.append({"name": "realizations"})

    seed_project(conn, PORTFOLIO_PROJECT_ID,
                 layers=[{"name": PORTFOLIO_THEME_LAYER}])
    seed_project(conn, "product-app", layers=product_layers)
    seed_project(conn, "ai-platform", layers=[{"name": "capability"}])
    seed_project(conn, "pipeline", layers=[{"name": "intent"}])

    writes.create_node(
        conn, PORTFOLIO_PROJECT_ID, PORTFOLIO_THEME_LAYER, "T.1",
        "Q3 Reliability", actor="test",
    )
    writes.create_node(conn, "product-app", "intent", "I.1", "App intent",
                       actor="test")
    writes.create_node(conn, "ai-platform", "capability", "C.4", "AI cap",
                       actor="test")
    writes.create_node(conn, "pipeline", "intent", "I.2", "Pipe intent",
                       actor="test")

    writes.link_portfolio(conn, "T.1", "product-app", "I.1", actor="test")
    writes.link_portfolio(conn, "T.1", "ai-platform", "C.4", actor="test")
    writes.link_portfolio(conn, "T.1", "pipeline", "I.2", actor="test")

    if cross_block:
        writes.create_node(
            conn, "product-app", "realizations", "R.12", "Blocked leaf",
            actor="test",
        )
        writes.link_portfolio(
            conn, "T.1", "product-app", "R.12", actor="test")
        writes.create_cross_edge(
            conn, "product-app", "R.12", "ai-platform", "C.4",
            "blocks", actor="test",
        )
