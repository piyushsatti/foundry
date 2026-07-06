import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from manifold import db, schema, config
from tests.conftest import fresh_db, seed_project, now_iso


class TestSchema(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.path = Path(self.tmp.name)

    def tearDown(self):
        for suffix in ("", "-shm", "-wal"):
            p = Path(str(self.path) + suffix)
            if p.exists():
                p.unlink()

    def test_bootstrap_creates_all_tables(self):
        conn = db.connect(self.path)
        schema.bootstrap(conn)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = {r["name"] for r in rows}
        expected = {"schema_meta", "projects", "nodes", "node_edges",
                    "revisions", "validations", "verdicts", "events"}
        for t in expected:
            self.assertIn(t, table_names, f"missing table: {t}")
        conn.close()

    def test_bootstrap_seeds_schema_version(self):
        conn = db.connect(self.path)
        schema.bootstrap(conn)
        row = conn.execute("SELECT schema_version FROM schema_meta").fetchone()
        self.assertEqual(row["schema_version"], config.SCHEMA_VERSION)
        conn.close()

    def test_bootstrap_idempotent(self):
        conn = db.connect(self.path)
        schema.bootstrap(conn)
        schema.bootstrap(conn)
        rows = conn.execute("SELECT COUNT(*) AS c FROM schema_meta").fetchone()
        self.assertEqual(rows["c"], 1, "schema_meta row duplicated on second bootstrap")
        conn.close()

    def test_bootstrap_creates_indexes(self):
        conn = db.connect(self.path)
        schema.bootstrap(conn)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        index_names = {r["name"] for r in rows}
        self.assertIn("nodes_layer", index_names)
        self.assertIn("edges_dst", index_names)
        self.assertIn("revisions_node_ts", index_names)
        conn.close()


class TestSchemaIntegrity(unittest.TestCase):
    def test_full_lifecycle_minimal_row_inserts(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        conn.execute(
            "INSERT INTO nodes (project_id, node_id, layer, title, kind, body, last_modified_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("p1", "I.1", "intent", "test node", "spec", "body text", now_iso()),
        )
        conn.execute(
            "INSERT INTO revisions (project_id, node_id, ts, change_type, snapshot, source, actor) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("p1", "I.1", now_iso(), "created", json.dumps({"title": "test node"}),
             "test", "human:test"),
        )
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM nodes WHERE project_id='p1'"
        ).fetchone()["c"]
        self.assertEqual(count, 1)
        rev_count = conn.execute(
            "SELECT COUNT(*) AS c FROM revisions WHERE project_id='p1'"
        ).fetchone()["c"]
        self.assertEqual(rev_count, 1)


if __name__ == "__main__":
    unittest.main()
