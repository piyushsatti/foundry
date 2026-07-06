import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from manifold import db, schema


class TestDb(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        for suffix in ("", "-shm", "-wal"):
            p = Path(str(self.path) + suffix)
            if p.exists():
                p.unlink()

    def test_connect_returns_connection(self):
        conn = db.connect(self.path)
        self.assertIsInstance(conn, sqlite3.Connection)
        conn.close()

    def test_connect_enables_wal(self):
        conn = db.connect(self.path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        self.assertEqual(mode.lower(), "wal")
        conn.close()

    def test_connect_enables_foreign_keys(self):
        conn = db.connect(self.path)
        fk = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(fk, 1)
        conn.close()

    def test_connect_row_factory_dict_like(self):
        conn = db.connect(self.path)
        conn.execute("CREATE TABLE t (x INTEGER)")
        conn.execute("INSERT INTO t VALUES (42)")
        row = conn.execute("SELECT x FROM t").fetchone()
        self.assertEqual(row["x"], 42)
        conn.close()


# Minimal v1 schema — mirrors the original schema.sql before the anti-drift columns.
_V1_SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    schema_version INTEGER NOT NULL,
    upgraded_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    project_id        TEXT PRIMARY KEY,
    label             TEXT,
    spec_config       TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    archived_at       TEXT,
    last_revision_id  INTEGER
);

CREATE TABLE IF NOT EXISTS nodes (
    project_id            TEXT NOT NULL,
    node_id               TEXT NOT NULL,
    layer                 TEXT NOT NULL,
    title                 TEXT,
    kind                  TEXT NOT NULL DEFAULT 'spec',
    realized_by_external  TEXT,
    body                  TEXT NOT NULL DEFAULT '',
    contract              TEXT,
    delegate_to           TEXT,
    applies_to            TEXT,
    target_status         TEXT,
    target_shape          TEXT,
    target_rationale_ref  TEXT,
    target_achieved_when  TEXT,
    target_achieved_at    TEXT,
    target_superseded_by  TEXT,
    verdict_mechanism     TEXT,
    verdict_check         TEXT,
    verdict_assertion     TEXT,
    verdict_judge_prompt  TEXT,
    verdict_status        TEXT,
    verdict_evidence_ref  TEXT,
    verdict_evidence_hash TEXT,
    verdict_last_checked  TEXT,
    current_revision_id   INTEGER,
    last_modified_at      TEXT NOT NULL,
    deleted_at            TEXT,
    PRIMARY KEY (project_id, node_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS revisions (
    revision_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       TEXT NOT NULL,
    node_id          TEXT NOT NULL,
    ts               TEXT NOT NULL,
    change_type      TEXT NOT NULL,
    prev_revision_id INTEGER,
    snapshot         TEXT NOT NULL,
    change_summary   TEXT,
    batch_id         TEXT,
    source           TEXT NOT NULL,
    actor            TEXT NOT NULL,
    git_sha          TEXT,
    note             TEXT
);
"""


class TestSchemaMigrationV1toV2(unittest.TestCase):
    """Verify that opening a v1 DB via schema.bootstrap migrates to v2 idempotently."""

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

    def tearDown(self):
        for suffix in ("", "-shm", "-wal"):
            p = self.path + suffix
            if os.path.exists(p):
                os.unlink(p)

    def _make_v1_db(self):
        """Create a raw v1 SQLite DB without the new columns."""
        conn = sqlite3.connect(self.path)
        conn.executescript(_V1_SCHEMA_SQL)
        conn.execute(
            "INSERT INTO schema_meta (schema_version, upgraded_at) VALUES (1, '2025-01-01T00:00:00+00:00')"
        )
        conn.commit()
        conn.close()

    def test_v1_db_upgrades_to_v2(self):
        self._make_v1_db()

        # Open via manifold.db.connect + schema.bootstrap; should upgrade
        conn = db.connect(self.path)
        schema.bootstrap(conn)

        # New columns should exist in nodes
        cols = [r[1] for r in conn.execute("PRAGMA table_info(nodes)")]
        self.assertIn("rationale", cols)
        self.assertIn("alternatives_considered", cols)

        # New column should exist in revisions
        rev_cols = [r[1] for r in conn.execute("PRAGMA table_info(revisions)")]
        self.assertIn("change_reason", rev_cols)

        # schema_version should now be 1
        version = conn.execute("SELECT schema_version FROM schema_meta").fetchone()[0]
        self.assertEqual(version, 1)

        conn.close()

    def test_v1_db_migration_is_idempotent(self):
        self._make_v1_db()

        # First open — migrates
        conn = db.connect(self.path)
        schema.bootstrap(conn)
        cols_first = [r[1] for r in conn.execute("PRAGMA table_info(nodes)")]
        conn.close()

        # Second open — should be safe (no duplicate column error)
        conn = db.connect(self.path)
        schema.bootstrap(conn)
        cols_second = [r[1] for r in conn.execute("PRAGMA table_info(nodes)")]
        conn.close()

        self.assertEqual(cols_first, cols_second)


if __name__ == "__main__":
    unittest.main()
