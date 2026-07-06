"""
Tests for manifold writes layer.

Covers create/update/transition/revert/soft-delete/with_batch/project lifecycle.
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from manifold import writes, queries, config as _config
from tests.conftest import fresh_db, seed_project, now_iso

# Hermetic config: ensure load_config() never touches the real
# ~/.claude/manifold.json when _resolve_judge_command is called via
# writes.run_validation(..., with_verdicts=True).
_MANIFOLD_CONFIG_OVERRIDE = os.path.join(
    tempfile.gettempdir(), "manifold-test-writes-nonexistent.json"
)


def setUpModule():
    os.environ["MANIFOLD_CONFIG"] = _MANIFOLD_CONFIG_OVERRIDE
    _config._reset_config_cache()


def tearDownModule():
    os.environ.pop("MANIFOLD_CONFIG", None)
    _config._reset_config_cache()


# ============================================================
# create_node
# ============================================================

class TestCreateNode(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")

    def test_writes_row_and_revision(self):
        result = writes.create_node(
            self.conn, "p1", "intent", "I.1", "First Thesis",
            body="The thing exists.", actor="human:test",
        )
        self.assertIn("revision_id", result)
        node = queries.get_node(self.conn, "p1", "I.1")
        self.assertEqual(node["title"], "First Thesis")
        revs = queries.list_revisions(self.conn, "p1", "I.1")
        self.assertEqual(len(revs), 1)
        self.assertEqual(revs[0]["change_type"], "created")

    def test_writes_parent_edges(self):
        writes.create_node(self.conn, "p1", "intent", "I.1", "root", actor="h")
        writes.create_node(
            self.conn, "p1", "realizations", "R.1", "child",
            parents=["I.1"], actor="h",
        )
        rows = self.conn.execute(
            "SELECT src_node_id, dst_node_id, edge_kind FROM node_edges "
            "WHERE project_id = ?", ("p1",)
        ).fetchall()
        kinds = {(r["src_node_id"], r["dst_node_id"], r["edge_kind"]) for r in rows}
        self.assertIn(("R.1", "I.1", "parent"), kinds)

    def test_rejects_duplicate(self):
        writes.create_node(self.conn, "p1", "intent", "I.1", "x", actor="h")
        with self.assertRaises(writes.NodeAlreadyExists):
            writes.create_node(self.conn, "p1", "intent", "I.1", "y", actor="h")

    def test_rejects_empty_actor(self):
        with self.assertRaises(writes.MissingActor):
            writes.create_node(self.conn, "p1", "intent", "I.1", "x", actor="")

    def test_rejects_unknown_project(self):
        with self.assertRaises(writes.ProjectNotFound):
            writes.create_node(self.conn, "missing", "intent", "I.1", "x", actor="h")


# ============================================================
# update_node + concurrency
# ============================================================

class TestUpdateNode(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        r = writes.create_node(self.conn, "p1", "intent", "I.1", "v1",
                                body="body v1", actor="h")
        self.revision = r["revision_id"]

    def test_title_change_creates_new_revision(self):
        r2 = writes.update_node(
            self.conn, "p1", "I.1", {"title": "v2"},
            expected_revision_id=self.revision, actor="h",
            change_reason="evolution",
        )
        self.assertNotEqual(r2["revision_id"], self.revision)
        node = queries.get_node(self.conn, "p1", "I.1")
        self.assertEqual(node["title"], "v2")
        revs = queries.list_revisions(self.conn, "p1", "I.1")
        self.assertEqual(len(revs), 2)
        # change_summary should record the title change
        summary = revs[0]["change_summary"]
        title_diffs = [d for d in summary if d["field"] == "title"]
        self.assertEqual(len(title_diffs), 1)
        self.assertEqual(title_diffs[0]["old"], "v1")
        self.assertEqual(title_diffs[0]["new"], "v2")

    def test_stale_revision_raises(self):
        with self.assertRaises(writes.StaleRevision):
            writes.update_node(
                self.conn, "p1", "I.1", {"title": "v2"},
                expected_revision_id=99999, actor="h",
                change_reason="evolution",
            )

    def test_invalid_change_reason_rejected(self):
        with self.assertRaises(writes.WritesError) as ctx:
            writes.update_node(
                self.conn, "p1", "I.1", {"title": "v2"},
                expected_revision_id=self.revision, actor="h",
                change_reason="banana",
            )
        self.assertIn("invalid change_reason", str(ctx.exception))

    def test_concurrency_disabled_via_env(self):
        with patch.dict(os.environ, {"MANIFOLD_STRICT_CONCURRENCY": "false"}):
            result = writes.update_node(
                self.conn, "p1", "I.1", {"title": "v2"},
                expected_revision_id=99999, actor="h",
                change_reason="evolution",
            )
        self.assertIn("revision_id", result)

    def test_updating_parents_changes_edges(self):
        writes.create_node(self.conn, "p1", "intent", "I.0", "root", actor="h")
        writes.create_node(self.conn, "p1", "realizations", "R.1", "child",
                            parents=["I.0"], actor="h")
        # Read R.1's current revision
        node = queries.get_node(self.conn, "p1", "R.1")
        rev = node["current_revision_id"]
        writes.update_node(
            self.conn, "p1", "R.1", {"parents": ["I.1"]},
            expected_revision_id=rev, actor="h",
            change_reason="refactor",
        )
        edges = self.conn.execute(
            "SELECT dst_node_id FROM node_edges WHERE project_id = ? "
            "AND src_node_id = ? AND edge_kind = 'parent'",
            ("p1", "R.1"),
        ).fetchall()
        self.assertEqual([e["dst_node_id"] for e in edges], ["I.1"])

    def test_no_change_returns_unchanged(self):
        result = writes.update_node(
            self.conn, "p1", "I.1", {"title": "v1"},  # same as current
            expected_revision_id=self.revision, actor="h",
        )
        self.assertTrue(result.get("unchanged"))


# ============================================================
# transition_target (state machine)
# ============================================================

class TestTransitionTarget(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        # explicitly start from "" so we can exercise the "" → planned transition
        r = writes.create_node(self.conn, "p1", "intent", "I.1", "x",
                               target_status="", actor="h")
        self.revision = r["revision_id"]

    def test_empty_to_planned(self):
        r2 = writes.transition_target(
            self.conn, "p1", "I.1", "planned",
            expected_revision_id=self.revision, actor="h",
        )
        self.assertEqual(r2["from"], "")
        self.assertEqual(r2["to"], "planned")
        node = queries.get_node(self.conn, "p1", "I.1")
        self.assertEqual(node["target_status"], "planned")

    def test_planned_to_achieved_sets_date(self):
        r2 = writes.transition_target(
            self.conn, "p1", "I.1", "planned",
            expected_revision_id=self.revision, actor="h",
        )
        writes.transition_target(
            self.conn, "p1", "I.1", "achieved",
            achieved_at="2026-05-23",
            expected_revision_id=r2["revision_id"], actor="h",
        )
        node = queries.get_node(self.conn, "p1", "I.1")
        self.assertEqual(node["target_status"], "achieved")
        self.assertEqual(node["target_achieved_at"], "2026-05-23")

    def test_invalid_transition_raises(self):
        writes.transition_target(
            self.conn, "p1", "I.1", "planned",
            expected_revision_id=self.revision, actor="h",
        )
        node = queries.get_node(self.conn, "p1", "I.1")
        # planned → in_progress is allowed; planned → superseded is not
        with self.assertRaises(writes.InvalidTransition):
            writes.transition_target(
                self.conn, "p1", "I.1", "superseded",
                superseded_by="I.2",
                expected_revision_id=node["current_revision_id"], actor="h",
            )

    def test_superseded_requires_superseded_by(self):
        # planned → achieved → superseded
        r2 = writes.transition_target(
            self.conn, "p1", "I.1", "planned",
            expected_revision_id=self.revision, actor="h",
        )
        r3 = writes.transition_target(
            self.conn, "p1", "I.1", "achieved",
            expected_revision_id=r2["revision_id"], actor="h",
        )
        with self.assertRaises(writes.InvalidTransition):
            writes.transition_target(
                self.conn, "p1", "I.1", "superseded",
                expected_revision_id=r3["revision_id"], actor="h",
            )


# ============================================================
# revert
# ============================================================

class TestRevert(unittest.TestCase):
    def test_revert_copies_past_snapshot_forward(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        r1 = writes.create_node(conn, "p1", "intent", "I.1", "v1",
                                 body="body v1", actor="h")
        rev1 = r1["revision_id"]
        r2 = writes.update_node(conn, "p1", "I.1", {"title": "v2", "body": "body v2"},
                                 expected_revision_id=rev1, actor="h",
                                 change_reason="evolution")
        # Revert to rev1
        r3 = writes.revert(conn, "p1", "I.1", rev1, actor="h")
        node = queries.get_node(conn, "p1", "I.1")
        self.assertEqual(node["title"], "v1")
        self.assertEqual(node["body"], "body v1")
        revs = queries.list_revisions(conn, "p1", "I.1")
        self.assertEqual(revs[0]["change_type"], "reverted")


# ============================================================
# soft_delete + restore
# ============================================================

class TestSoftDeleteRestore(unittest.TestCase):
    def test_soft_delete_hides_from_default_queries(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        r = writes.create_node(conn, "p1", "intent", "I.1", "x", actor="h")
        writes.soft_delete_node(conn, "p1", "I.1",
                                 expected_revision_id=r["revision_id"], actor="h")
        self.assertIsNone(queries.get_node(conn, "p1", "I.1"))
        # Still findable with include_deleted
        self.assertIsNotNone(queries.get_node(conn, "p1", "I.1", include_deleted=True))

    def test_restore_unhides(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        r = writes.create_node(conn, "p1", "intent", "I.1", "x", actor="h")
        writes.soft_delete_node(conn, "p1", "I.1",
                                 expected_revision_id=r["revision_id"], actor="h")
        writes.restore_node(conn, "p1", "I.1", actor="h")
        self.assertIsNotNone(queries.get_node(conn, "p1", "I.1"))


# ============================================================
# with_batch
# ============================================================

class TestWithBatch(unittest.TestCase):
    def test_three_ops_share_batch_id(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        result = writes.with_batch(
            conn, "create three nodes",
            [{"op": "create_node",
              "args": {"project_id": "p1", "layer": "intent",
                       "node_id": f"I.{i}", "title": f"node{i}"}}
             for i in (1, 2, 3)],
            actor="h",
        )
        self.assertEqual(len(result["revision_ids"]), 3)
        # All three revisions should share the batch_id
        rows = conn.execute(
            "SELECT batch_id FROM revisions WHERE project_id = ?", ("p1",)
        ).fetchall()
        batch_ids = {r["batch_id"] for r in rows}
        self.assertEqual(batch_ids, {result["batch_id"]})

    def test_batch_rolls_back_on_failure(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        writes.create_node(conn, "p1", "intent", "I.1", "x", actor="h")
        # The second op duplicates I.1 → should fail and roll back
        with self.assertRaises(writes.NodeAlreadyExists):
            writes.with_batch(
                conn, "should roll back",
                [{"op": "create_node",
                  "args": {"project_id": "p1", "layer": "intent",
                           "node_id": "I.2", "title": "ok"}},
                 {"op": "create_node",
                  "args": {"project_id": "p1", "layer": "intent",
                           "node_id": "I.1", "title": "dup"}}],
                actor="h",
            )
        # I.2 must not exist
        self.assertIsNone(queries.get_node(conn, "p1", "I.2"))


# ============================================================
# Project lifecycle
# ============================================================

class TestProjectLifecycle(unittest.TestCase):
    def test_register_then_archive_then_unarchive(self):
        conn, _ = fresh_db(self)
        writes.register_project(conn, "p1", {"layers": []}, label="P1")
        self.assertIsNotNone(queries.get_project(conn, "p1"))
        writes.archive_project(conn, "p1")
        proj = queries.get_project(conn, "p1")
        self.assertIsNotNone(proj["archived_at"])
        writes.unarchive_project(conn, "p1")
        proj = queries.get_project(conn, "p1")
        self.assertIsNone(proj["archived_at"])

    def test_register_emits_event(self):
        conn, _ = fresh_db(self)
        writes.register_project(conn, "p1", {"layers": []})
        row = conn.execute(
            "SELECT event_type, project_id FROM events"
        ).fetchone()
        self.assertEqual(row["event_type"], "project_registered")
        self.assertEqual(row["project_id"], "p1")


# ============================================================
# run_validation
# ============================================================

class TestRunValidation(unittest.TestCase):
    def test_creates_validations_row(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        result = writes.run_validation(conn, "p1", actor="h")
        self.assertIn("validation_id", result)
        self.assertEqual(result["status"], "finished")
        self.assertIn("issues", result)
        self.assertEqual(result["issues_total"], len(result["issues"]))

    def test_emits_event(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        writes.run_validation(conn, "p1", actor="h")
        row = conn.execute(
            "SELECT event_type FROM events WHERE event_type = 'validation_started'"
        ).fetchone()
        self.assertIsNotNone(row)
        finished = conn.execute(
            "SELECT event_type FROM events WHERE event_type = 'validation_finished'"
        ).fetchone()
        self.assertIsNotNone(finished)

    def test_writes_verdict_rows(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1", layers=[
            {"name": "intent"}, {"name": "realizations"}])
        writes.create_node(conn, "p1", "intent", "I.1", "Top",
                           actor="h")
        writes.create_node(conn, "p1", "realizations", "R.1", "Child",
                           parents=["I.1"], actor="h")
        # Update R.1 to have an automated check
        rev = queries.get_node(conn, "p1", "R.1")["current_revision_id"]
        writes.update_node(conn, "p1", "R.1",
                           {"verdict_mechanism": "automated_check",
                            "verdict_check": "true"},
                           expected_revision_id=rev, actor="h",
                           change_reason="evolution")
        result = writes.run_validation(conn, "p1", with_verdicts=True, actor="h")
        self.assertEqual(result["verdicts_run"], 2)
        # Verdicts row exists for R.1 with satisfied
        row = conn.execute(
            "SELECT status FROM verdicts WHERE project_id='p1' AND node_id='R.1'"
        ).fetchone()
        self.assertEqual(row["status"], "satisfied")


# ============================================================
# Default target_status
# ============================================================

class TestDefaultTargetStatus(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        writes.register_project(self.conn, "p", spec_config={
            "layers": [{"name": "L0"}]
        })

    def test_new_node_defaults_to_planned(self):
        writes.create_node(self.conn, "p", "L0", "A", "node A", actor="human:test")
        n = queries.get_node(self.conn, "p", "A")
        self.assertEqual(n["target_status"], "planned")

    def test_explicit_target_status_preserved(self):
        writes.create_node(self.conn, "p", "L0", "B", "node B",
                           target_status="in_progress", actor="human:test")
        n = queries.get_node(self.conn, "p", "B")
        self.assertEqual(n["target_status"], "in_progress")

    def test_explicit_empty_target_status_preserved(self):
        writes.create_node(self.conn, "p", "L0", "C", "node C",
                           target_status="", actor="human:test")
        n = queries.get_node(self.conn, "p", "C")
        self.assertEqual(n["target_status"], "")


# ============================================================
# rationale + alternatives_considered + change_reason
# ============================================================

class TestRationaleAndAlternatives(unittest.TestCase):
    """Task 6: create_node / update_node accept and persist rationale fields."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        writes.register_project(self.conn, "p", spec_config={
            "layers": [{"name": "L0"}]
        })

    def test_rationale_roundtrip_create(self):
        """create_node with rationale + alternatives_considered; get_node returns them."""
        writes.create_node(
            self.conn, "p", "L0", "A", "node A",
            rationale="exists because Q",
            alternatives_considered="X considered, rejected due to Y",
            actor="human:test",
        )
        n = queries.get_node(self.conn, "p", "A")
        self.assertEqual(n["rationale"], "exists because Q")
        self.assertEqual(n["alternatives_considered"], "X considered, rejected due to Y")

    def test_rationale_in_revision_snapshot(self):
        """rationale is captured in the revision snapshot at create time."""
        writes.create_node(
            self.conn, "p", "L0", "B", "node B",
            rationale="snapshot reason",
            actor="human:test",
        )
        rev = self.conn.execute(
            "SELECT snapshot FROM revisions WHERE project_id='p' AND node_id='B'"
        ).fetchone()
        snap = json.loads(rev["snapshot"])
        self.assertEqual(snap.get("rationale"), "snapshot reason")

    def test_rationale_none_by_default(self):
        """create_node without rationale stores NULL."""
        writes.create_node(self.conn, "p", "L0", "C", "node C", actor="human:test")
        n = queries.get_node(self.conn, "p", "C")
        self.assertIsNone(n["rationale"])
        self.assertIsNone(n["alternatives_considered"])

    def test_update_node_accepts_rationale_in_fields(self):
        """update_node can set rationale and alternatives_considered via the fields dict."""
        r = writes.create_node(self.conn, "p", "L0", "D", "node D", actor="human:test")
        rev_id = r["revision_id"]
        writes.update_node(
            self.conn, "p", "D",
            {"rationale": "updated rationale",
             "alternatives_considered": "alt updated"},
            expected_revision_id=rev_id,
            actor="human:test",
            change_reason="clarification",
        )
        n = queries.get_node(self.conn, "p", "D")
        self.assertEqual(n["rationale"], "updated rationale")
        self.assertEqual(n["alternatives_considered"], "alt updated")

    def test_update_node_rationale_captured_in_change_summary(self):
        """When rationale changes, the revision change_summary reflects it."""
        r = writes.create_node(self.conn, "p", "L0", "E", "node E",
                               rationale="old reason", actor="human:test")
        writes.update_node(
            self.conn, "p", "E",
            {"rationale": "new reason"},
            expected_revision_id=r["revision_id"],
            actor="human:test",
            change_reason="clarification",
        )
        revs = queries.list_revisions(self.conn, "p", "E")
        # Most recent revision is first; it should record rationale change
        latest = revs[0]
        rationale_diffs = [d for d in (latest["change_summary"] or [])
                           if d["field"] == "rationale"]
        self.assertEqual(len(rationale_diffs), 1)
        self.assertEqual(rationale_diffs[0]["old"], "old reason")
        self.assertEqual(rationale_diffs[0]["new"], "new reason")


class TestChangeReason(unittest.TestCase):
    """Task 6: update_node accepts change_reason kwarg; stored on revision row."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        writes.register_project(self.conn, "p", spec_config={
            "layers": [{"name": "L0"}]
        })
        r = writes.create_node(self.conn, "p", "L0", "A", "node A", actor="human:test")
        self.rev_id = r["revision_id"]

    def test_change_reason_stored_on_revision(self):
        """update_node with change_reason='clarification' stores it on the revision row."""
        writes.update_node(
            self.conn, "p", "A", {"title": "node A updated"},
            expected_revision_id=self.rev_id,
            change_reason="clarification",
            actor="human:test",
        )
        rev = self.conn.execute(
            "SELECT change_reason FROM revisions WHERE project_id='p' AND node_id='A' "
            "ORDER BY revision_id DESC LIMIT 1"
        ).fetchone()
        self.assertEqual(rev["change_reason"], "clarification")

    def test_change_reason_required(self):
        """update_node without change_reason raises WritesError."""
        with self.assertRaises(writes.WritesError):
            writes.update_node(
                self.conn, "p", "A", {"title": "v2"},
                expected_revision_id=self.rev_id,
                actor="human:test",
            )

    def test_all_valid_change_reasons_accepted(self):
        """All enum values from the design doc are accepted."""
        valid_reasons = ["correction", "evolution", "clarification",
                         "refactor", "pivot", "other"]
        # We have one node; update in sequence
        current_rev = self.rev_id
        for i, reason in enumerate(valid_reasons):
            result = writes.update_node(
                self.conn, "p", "A",
                {"title": f"update {i}"},
                expected_revision_id=current_rev,
                change_reason=reason,
                actor="human:test",
            )
            current_rev = result["revision_id"]
        # All updates succeeded; final title is the last one
        n = queries.get_node(self.conn, "p", "A")
        self.assertEqual(n["title"], f"update {len(valid_reasons) - 1}")

    def test_change_reason_on_create_revision_is_none(self):
        """create_node does not set change_reason (it is NULL / not applicable)."""
        rev = self.conn.execute(
            "SELECT change_reason FROM revisions WHERE project_id='p' AND node_id='A' "
            "ORDER BY revision_id ASC LIMIT 1"
        ).fetchone()
        # Create revision has no change_reason (it wasn't a change, it was a creation)
        self.assertIsNone(rev["change_reason"])


if __name__ == "__main__":
    unittest.main()
