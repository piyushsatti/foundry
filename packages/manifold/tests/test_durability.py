"""
Tests for manifold durability layer:
- snapshot via VACUUM INTO
- dump to NDJSON
- restore from NDJSON
"""
import json
import tempfile
import unittest
from pathlib import Path
from manifold import db, durability
from tests.conftest import fresh_db, seed_project, now_iso


class TestSnapshot(unittest.TestCase):
    def test_snapshot_creates_sibling_file(self):
        conn, path = fresh_db(self)
        seed_project(conn, "p1")
        out = durability.snapshot(path)
        self.assertTrue(Path(out).exists())
        self.assertNotEqual(Path(out), path)
        # Snapshot file is a valid SQLite DB with the same data
        snap_conn = db.connect(Path(out))
        n = snap_conn.execute("SELECT COUNT(*) AS c FROM projects").fetchone()
        self.assertEqual(n["c"], 1)
        snap_conn.close()
        Path(out).unlink()


class TestDump(unittest.TestCase):
    def test_dump_writes_ndjson_with_header(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        out_path = Path(tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False).name)
        self.addCleanup(lambda: out_path.unlink() if out_path.exists() else None)
        durability.dump(conn, out_path)
        lines = out_path.read_text().strip().splitlines()
        header = json.loads(lines[0])
        self.assertEqual(header["manifold_dump_version"], 1)
        self.assertIn("projects", header["tables"])
        project_rows = [json.loads(l) for l in lines[1:]
                        if json.loads(l)["table"] == "projects"]
        self.assertEqual(len(project_rows), 1)
        self.assertEqual(project_rows[0]["row"]["project_id"], "p1")


class TestRestore(unittest.TestCase):
    def test_dump_then_restore_round_trips(self):
        conn1, _ = fresh_db(self)
        seed_project(conn1, "p1")
        conn1.execute(
            "INSERT INTO nodes (project_id, node_id, layer, body, last_modified_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("p1", "I.1", "intent", "body", now_iso()),
        )
        dump_path = Path(tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False).name)
        self.addCleanup(lambda: dump_path.unlink() if dump_path.exists() else None)
        durability.dump(conn1, dump_path)

        new_path = Path(tempfile.NamedTemporaryFile(suffix=".db", delete=False).name)
        new_path.unlink()  # restore expects path NOT to exist
        self.addCleanup(lambda: [Path(str(new_path) + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(str(new_path) + s).exists()])

        durability.restore(dump_path, new_path)
        conn2 = db.connect(new_path)
        row = conn2.execute(
            "SELECT node_id, body FROM nodes WHERE project_id = 'p1'"
        ).fetchone()
        self.assertEqual(row["node_id"], "I.1")
        self.assertEqual(row["body"], "body")
        n_projects = conn2.execute("SELECT COUNT(*) AS c FROM projects").fetchone()["c"]
        self.assertEqual(n_projects, 1)
        conn2.close()

    def test_restore_refuses_existing_target(self):
        conn, db_path = fresh_db(self)
        dump_path = Path(tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False).name)
        self.addCleanup(lambda: dump_path.unlink() if dump_path.exists() else None)
        durability.dump(conn, dump_path)
        with self.assertRaises(FileExistsError):
            durability.restore(dump_path, db_path)


if __name__ == "__main__":
    unittest.main()
