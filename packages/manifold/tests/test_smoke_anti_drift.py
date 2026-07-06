"""End-to-end smoke test for the KAOS substrate, compass, and anti-drift features.

Exercises every major feature in one coherent roundtrip:
  - Multi-parent node creation (DAG-across-layers; Wave 1 Task 1)
  - Default target_status="planned" on create (Wave 1 Task 2)
  - Schema v2 columns: rationale, alternatives_considered (Wave 1 Task 3 + Wave 2 Task 6)
  - queries.next_leaves returns expected leaves (Wave 1 Task 2 + Wave 2 Task 5)
  - update_node with change_reason (Wave 2 Task 6)
  - queries.spec_audit_flagged_revisions finds a deliberately-tagged drift revision (Wave 2 Task 7)
  - writes.run_validation runs cleanly (no errors; advisories allowed)
  - Multi-parent propagation: failing one child invalidates ALL its parents
"""
import unittest

from manifold import db, schema, writes, queries, validate
from tests.conftest import fresh_db


class TestAntiDriftEndToEnd(unittest.TestCase):
    """Comprehensive end-to-end test for all major features."""

    def setUp(self):
        # fresh_db uses tempfile, bootstraps schema, registers cleanup automatically.
        self.conn, self.db_path = fresh_db(self)

    # ------------------------------------------------------------------
    # Feature: Schema v2 — rationale, alternatives_considered, change_reason
    # ------------------------------------------------------------------

    def test_schema_v2_columns_exist(self):
        """Nodes table has rationale + alternatives_considered; revisions has change_reason."""
        node_cols = [
            r["name"] for r in self.conn.execute("PRAGMA table_info(nodes)")
        ]
        rev_cols = [
            r["name"] for r in self.conn.execute("PRAGMA table_info(revisions)")
        ]
        self.assertIn("rationale", node_cols,
                      "nodes.rationale column missing (schema v2 not applied)")
        self.assertIn("alternatives_considered", node_cols,
                      "nodes.alternatives_considered column missing")
        self.assertIn("change_reason", rev_cols,
                      "revisions.change_reason column missing")

    # ------------------------------------------------------------------
    # Main roundtrip test
    # ------------------------------------------------------------------

    def test_full_v04_roundtrip(self):
        """End-to-end roundtrip: register → create nodes → verify → update → drift."""
        conn = self.conn

        # ---- 1. Register project with three layers ----
        writes.register_project(conn, "smoke", spec_config={
            "layers": [{"name": "I"}, {"name": "C"}, {"name": "R"}]
        })

        # ---- 2. Create two top-layer intent nodes ----
        writes.create_node(conn, "smoke", "I", "I.1", "intent A",
                           rationale="why A exists",
                           alternatives_considered="option X rejected",
                           actor="human:test")
        writes.create_node(conn, "smoke", "I", "I.2", "intent B",
                           rationale="why B exists",
                           actor="human:test")

        # ---- 3. Multi-parent node: C.1 satisfies BOTH I.1 and I.2 (DAG) ----
        writes.create_node(conn, "smoke", "C", "C.1", "capability AB",
                           parents=["I.1", "I.2"],
                           rationale="serves both intents",
                           actor="human:test")

        # ---- 4. Leaf node at the bottom layer ----
        writes.create_node(conn, "smoke", "R", "R.1", "realization",
                           parents=["C.1"],
                           rationale="implements C.1",
                           actor="human:test")

        # ---- 5. Default target_status="planned" (Wave 1 Task 2) ----
        r1 = queries.get_node(conn, "smoke", "R.1")
        self.assertIsNotNone(r1, "R.1 not found")
        self.assertEqual(r1["target_status"], "planned",
                         "New node should default to target_status='planned'")

        # All created nodes should default to planned
        for nid in ("I.1", "I.2", "C.1", "R.1"):
            n = queries.get_node(conn, "smoke", nid)
            self.assertEqual(n["target_status"], "planned",
                             f"Node {nid} should have target_status='planned'")

        # ---- 6. rationale + alternatives_considered roundtrip (Wave 2 Task 6) ----
        i1 = queries.get_node(conn, "smoke", "I.1")
        self.assertEqual(i1["rationale"], "why A exists")
        self.assertEqual(i1["alternatives_considered"], "option X rejected")

        c1 = queries.get_node(conn, "smoke", "C.1")
        self.assertEqual(c1["rationale"], "serves both intents")

        # ---- 7. queries.next_leaves returns only R.1 (Wave 2 Task 5) ----
        # R.1 is the only leaf (no node has R.1 as its dst in a parent edge).
        # I.1, I.2, C.1 all have children pointing to them.
        leaves = queries.next_leaves(conn, "smoke")
        leaf_ids = [l["node_id"] for l in leaves]
        self.assertIn("R.1", leaf_ids,
                      "R.1 should appear in next_leaves (it is the only leaf)")
        self.assertNotIn("I.1", leaf_ids,
                         "I.1 has a child (C.1) so should NOT be in next_leaves")
        self.assertNotIn("I.2", leaf_ids,
                         "I.2 has a child (C.1) so should NOT be in next_leaves")
        self.assertNotIn("C.1", leaf_ids,
                         "C.1 has a child (R.1) so should NOT be in next_leaves")
        self.assertEqual(len(leaves), 1,
                         f"Expected exactly 1 leaf, got {len(leaves)}: {leaf_ids}")

        # ---- 8. next_leaves with layer filter ----
        leaves_r = queries.next_leaves(conn, "smoke", layer="R")
        self.assertEqual(len(leaves_r), 1)
        self.assertEqual(leaves_r[0]["node_id"], "R.1")

        leaves_i = queries.next_leaves(conn, "smoke", layer="I")
        self.assertEqual(len(leaves_i), 0,
                         "I layer nodes are NOT leaves (they have children)")

        # ---- 9. Validate cleanly — no structural errors (advisories allowed) ----
        result = writes.run_validation(conn, "smoke", actor="human:test")
        self.assertEqual(result["status"], "finished")
        non_advisory_issues = [
            iss for iss in result["issues"]
            if iss.get("severity") not in ("advisory", None)
        ]
        self.assertEqual(non_advisory_issues, [],
                         f"Unexpected non-advisory validation issues: {non_advisory_issues}")

        # ---- 10. Update with change_reason="pivot" (Wave 2 Task 6) ----
        r1_fresh = queries.get_node(conn, "smoke", "R.1")
        rev_id = r1_fresh["current_revision_id"]
        writes.update_node(conn, "smoke", "R.1",
                           {"title": "renamed realization"},
                           expected_revision_id=rev_id,
                           change_reason="pivot",
                           actor="human:test")

        # Verify the title changed
        r1_updated = queries.get_node(conn, "smoke", "R.1")
        self.assertEqual(r1_updated["title"], "renamed realization")

        # ---- 11. spec_audit_flagged_revisions finds the drift-tagged revision (Wave 2 Task 7) ----
        drift = queries.spec_audit_flagged_revisions(conn, "smoke")
        drift_reasons = [r["change_reason"] for r in drift]
        self.assertIn("pivot", drift_reasons,
                      "spec_audit_flagged_revisions should surface pivot revisions")

        # ---- 12. Multi-parent propagation: violated R.1 invalidates C.1, I.1, AND I.2 ----
        nbi = validate._build_nodes_by_id(conn, "smoke")
        verdicts = {
            "I.1": {"status": "satisfied", "source": "human"},
            "I.2": {"status": "satisfied", "source": "human"},
            "C.1": {"status": "satisfied", "source": "human"},
            "R.1": {"status": "violated", "source": "automated"},
        }
        validate.propagate_failures(verdicts, nbi)

        # C.1 is R.1's parent → must be invalidated
        self.assertEqual(verdicts["C.1"]["status"], "invalidated_by_descendant",
                         "C.1 (parent of violated R.1) must become invalidated_by_descendant")
        # I.1 and I.2 are C.1's parents → both must be invalidated (multi-parent DAG)
        self.assertEqual(verdicts["I.1"]["status"], "invalidated_by_descendant",
                         "I.1 (parent of invalidated C.1) must become invalidated_by_descendant")
        self.assertEqual(verdicts["I.2"]["status"], "invalidated_by_descendant",
                         "I.2 (parent of invalidated C.1) must become invalidated_by_descendant")

    # ------------------------------------------------------------------
    # Feature: spec_audit_flagged_revisions with 'since' filter
    # ------------------------------------------------------------------

    def test_spec_audit_flagged_revisions_since_filter(self):
        """spec_audit_flagged_revisions respects the 'since' timestamp filter."""
        conn = self.conn
        writes.register_project(conn, "drift-p", spec_config={
            "layers": [{"name": "L0"}]
        })
        writes.create_node(conn, "drift-p", "L0", "N1", "node one",
                           actor="human:test")

        n1 = queries.get_node(conn, "drift-p", "N1")
        writes.update_node(conn, "drift-p", "N1",
                           {"title": "node one revised"},
                           expected_revision_id=n1["current_revision_id"],
                           change_reason="pivot",
                           actor="human:test")

        # With no since filter: finds the drift revision
        all_drift = queries.spec_audit_flagged_revisions(conn, "drift-p")
        self.assertTrue(any(r["change_reason"] == "pivot" for r in all_drift),
                        "Should find pivot revision without since filter")

        # With a far-future since filter: returns nothing
        future_drift = queries.spec_audit_flagged_revisions(conn, "drift-p",
                                               since="2099-01-01T00:00:00+00:00")
        self.assertEqual(future_drift, [],
                         "No revisions should be after 2099-01-01")

    # ------------------------------------------------------------------
    # Feature: next_leaves excludes achieved / abandoned nodes
    # ------------------------------------------------------------------

    def test_next_leaves_excludes_achieved_nodes(self):
        """next_leaves only returns planned / in_progress / unset leaves."""
        conn = self.conn
        writes.register_project(conn, "leaves-p", spec_config={
            "layers": [{"name": "L0"}]
        })
        writes.create_node(conn, "leaves-p", "L0", "A", "node A",
                           actor="human:test")  # defaults to planned

        # A is a leaf with target_status=planned → appears in next_leaves
        leaves = queries.next_leaves(conn, "leaves-p")
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0]["node_id"], "A")

        # Transition A: planned → in_progress → achieved
        a = queries.get_node(conn, "leaves-p", "A")
        writes.transition_target(conn, "leaves-p", "A", "in_progress",
                                 expected_revision_id=a["current_revision_id"],
                                 actor="human:test")
        a2 = queries.get_node(conn, "leaves-p", "A")
        writes.transition_target(conn, "leaves-p", "A", "achieved",
                                 expected_revision_id=a2["current_revision_id"],
                                 actor="human:test")

        leaves_after = queries.next_leaves(conn, "leaves-p")
        self.assertEqual(leaves_after, [],
                         "Achieved node should not appear in next_leaves")


if __name__ == "__main__":
    unittest.main()
