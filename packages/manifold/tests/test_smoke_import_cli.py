"""
End-to-end smoke test for manifold (substrate + importer + CLI).

Imports the live manifold v0.2 self-spec from the sibling skill. Verifies:
- All ~35+ nodes load
- Revision history is populated (multiple git commits replay)
- Every query function works on real data
- Round-trip dump/restore preserves the data
"""
import tempfile
import unittest
from pathlib import Path
from manifold import db, importer, queries, durability
from tests.conftest import fresh_db


# Imports a sibling v0.2 file-based spec (specs/spec.yaml) if one is present; skips otherwise.
V02_REPO = Path(__file__).resolve().parents[1]


@unittest.skipUnless(V02_REPO.exists() and (V02_REPO / "specs" / "spec.yaml").is_file(),
                     f"requires v0.2 spec at {V02_REPO}/specs/spec.yaml")
class TestPhaseASmoke(unittest.TestCase):
    def test_import_manifold_self_spec(self):
        conn, _ = fresh_db(self)
        result = importer.import_project(
            conn, V02_REPO, project_id="manifold", actor="human:smoke",
        )
        # v0.2 self-spec ships with 35-39 nodes depending on point in history
        self.assertGreaterEqual(result["nodes_imported"], 30,
                                msg=f"expected ≥30 nodes; got {result['nodes_imported']}")
        # Multi-commit history should produce many revisions
        self.assertGreaterEqual(result["revisions_imported"], 35,
                                msg=f"expected ≥35 revisions; got {result['revisions_imported']}")

        # Project exists in DB
        proj = queries.get_project(conn, "manifold")
        self.assertEqual(proj["project_id"], "manifold")
        self.assertIn("layers", proj["spec_config"])

        # All intent nodes from v0.2 self-spec are loaded
        intent_nodes = queries.list_nodes(conn, "manifold", layer="intent")
        self.assertGreaterEqual(len(intent_nodes), 3,
                                 msg=f"expected ≥3 intent nodes; got {len(intent_nodes)}")

        # I.1 must be present (multi-resolution-spec)
        i1 = queries.get_node(conn, "manifold", "I.1")
        self.assertIsNotNone(i1, "I.1 missing from imported manifold spec")

    def test_revision_history_for_known_node(self):
        """C.3 (author capability) had a target-state demo with multiple
        revisions in v0.2's history. Verify the history made it across.
        """
        conn, _ = fresh_db(self)
        importer.import_project(conn, V02_REPO, project_id="manifold",
                                 actor="human:smoke")
        # C.3 exists
        c3 = queries.get_node(conn, "manifold", "C.3")
        if c3 is None:
            self.skipTest("C.3 not present in this v0.2 snapshot")
        revs = queries.list_revisions(conn, "manifold", "C.3", limit=50)
        self.assertGreater(len(revs), 0,
                           msg="C.3 should have at least one revision")
        # Every revision should have a git_sha (because it was imported)
        for r in revs:
            self.assertIsNotNone(r["git_sha"],
                                  msg=f"revision {r['revision_id']} missing git_sha")

    def test_node_edges_populated(self):
        """After import, node_edges should hold parent relationships from frontmatter."""
        conn, _ = fresh_db(self)
        importer.import_project(conn, V02_REPO, project_id="manifold",
                                 actor="human:smoke")
        # At least some 'parent' edges should exist
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM node_edges WHERE project_id = ? "
            "AND edge_kind = 'parent'", ("manifold",)
        ).fetchone()["c"]
        self.assertGreater(count, 0, msg="expected parent edges from imported nodes")

    def test_dump_restore_round_trip(self):
        """Dump after import, restore into a new DB, verify counts match."""
        conn, _ = fresh_db(self)
        importer.import_project(conn, V02_REPO, project_id="manifold",
                                 actor="human:smoke")
        before = conn.execute(
            "SELECT COUNT(*) AS c FROM revisions WHERE project_id = ?",
            ("manifold",)
        ).fetchone()["c"]

        dump_path = Path(tempfile.NamedTemporaryFile(suffix=".ndjson",
                                                       delete=False).name)
        self.addCleanup(lambda: dump_path.unlink(missing_ok=True))
        durability.dump(conn, dump_path)

        new_db = Path(tempfile.NamedTemporaryFile(suffix=".db", delete=False).name)
        new_db.unlink()
        self.addCleanup(lambda: [Path(str(new_db) + s).unlink(missing_ok=True)
                                  for s in ("", "-shm", "-wal")])

        durability.restore(dump_path, new_db)
        conn2 = db.connect(new_db)
        after = conn2.execute(
            "SELECT COUNT(*) AS c FROM revisions WHERE project_id = ?",
            ("manifold",)
        ).fetchone()["c"]
        conn2.close()
        self.assertEqual(before, after,
                          msg=f"revision count drift after restore: {before} → {after}")


if __name__ == "__main__":
    unittest.main()
