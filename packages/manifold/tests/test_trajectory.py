"""Tests for trajectory (Topic J)."""

import json
import tempfile
import unittest
from pathlib import Path

from manifold import db, schema, trajectory, writes


def _seed(conn, project_id="tr-proj"):
    writes.register_project(conn, project_id, spec_config={
        "layers": [
            {"name": "intent"},
            {"name": "realizations"},
        ],
    })
    writes.create_node(conn, project_id, "intent", "I.1", "Root intent",
                       actor="human:test")
    writes.create_node(
        conn, project_id, "realizations", "R.1", "Leaf work",
        parents=["I.1"], target_status="planned", actor="human:test",
    )


class TestTrajectory(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.conn = db.connect(self.tmp.name)
        schema.bootstrap(self.conn)
        _seed(self.conn)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        for suffix in ("", "-shm", "-wal"):
            p = Path(self.tmp.name + suffix)
            if p.exists():
                p.unlink()

    def test_propose_show_accept_transition(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "achieved"},
        }]
        prop = trajectory.propose_trajectory(
            self.conn, "tr-proj", "Achieve R.1", legs, proposed_by="human:test",
        )
        tid = prop["trajectory_id"]
        self.conn.commit()

        from manifold import queries
        self.assertEqual(len(queries.next_leaves(self.conn, "tr-proj")), 1)

        report = trajectory.peek_trajectory(self.conn, tid)
        self.assertIn("impact_preview", report)
        after_preview = report["impact_preview"]["next_leaves_after"]
        self.assertEqual(len(after_preview), 0)

        result = trajectory.accept_trajectory_legs(
            self.conn, tid, actor="human:test",
        )
        self.conn.commit()
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(len(queries.next_leaves(self.conn, "tr-proj")), 0)

    def test_propose_requires_change_reason_on_update(self):
        legs = [{
            "leg_kind": "update_node",
            "payload": {
                "node_id": "I.1",
                "fields": {"rationale": "evolved"},
            },
        }]
        with self.assertRaises(trajectory.TrajectoryError):
            trajectory.propose_trajectory(
                self.conn, "tr-proj", "brief", legs, proposed_by="human:test",
            )

    def test_propose_rejects_invalid_transition(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "deferred"},
        }]
        with self.assertRaises(trajectory.TrajectoryError) as ctx:
            trajectory.propose_trajectory(
                self.conn, "tr-proj", "brief", legs, proposed_by="human:test",
            )
        self.assertIn("deferred", str(ctx.exception))
        self.assertIn("allowed", str(ctx.exception))

    def test_propose_rejects_noop_transition(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "planned"},
        }]
        with self.assertRaises(trajectory.TrajectoryError) as ctx:
            trajectory.propose_trajectory(
                self.conn, "tr-proj", "brief", legs, proposed_by="human:test",
            )
        self.assertIn("planned", str(ctx.exception))

    def test_propose_rejects_missing_node(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.missing", "to_status": "achieved"},
        }]
        with self.assertRaises(trajectory.TrajectoryError) as ctx:
            trajectory.propose_trajectory(
                self.conn, "tr-proj", "brief", legs, proposed_by="human:test",
            )
        self.assertIn("node not found", str(ctx.exception))

    def test_reject_draft_trajectory(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "achieved"},
        }]
        prop = trajectory.propose_trajectory(
            self.conn, "tr-proj", "brief", legs, proposed_by="human:test",
        )
        result = trajectory.reject_trajectory(
            self.conn, prop["trajectory_id"], actor="human:test",
        )
        self.assertEqual(result["status"], "rejected")
        traj = trajectory.get_trajectory(self.conn, prop["trajectory_id"])
        self.assertEqual(traj["status"], "rejected")

    def test_reject_non_draft_raises(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "achieved"},
        }]
        prop = trajectory.propose_trajectory(
            self.conn, "tr-proj", "brief", legs, proposed_by="human:test",
        )
        trajectory.accept_trajectory_legs(
            self.conn, prop["trajectory_id"], actor="human:test",
        )
        with self.assertRaises(trajectory.TrajectoryError):
            trajectory.reject_trajectory(
                self.conn, prop["trajectory_id"], actor="human:test",
            )

    def test_update_node_leg(self):
        legs = [{
            "leg_kind": "update_node",
            "payload": {
                "node_id": "I.1",
                "fields": {"rationale": "because"},
                "change_reason": "evolution",
            },
        }]
        prop = trajectory.propose_trajectory(
            self.conn, "tr-proj", "Update intent", legs, proposed_by="human:test",
        )
        trajectory.accept_trajectory_legs(
            self.conn, prop["trajectory_id"], actor="human:test",
        )
        self.conn.commit()
        from manifold import queries
        node = queries.get_node(self.conn, "tr-proj", "I.1")
        self.assertEqual(node["rationale"], "because")

    def test_format_show_markdown(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "achieved"},
        }]
        prop = trajectory.propose_trajectory(
            self.conn, "tr-proj", "Target brief line", legs, proposed_by="human:test",
        )
        report = trajectory.peek_trajectory(self.conn, prop["trajectory_id"])
        md = trajectory.format_show_markdown(report)
        self.assertIn("Target brief line", md)
        self.assertIn("impact preview", md)


class TestTrajectoryCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.conn = db.connect(self.tmp.name)
        schema.bootstrap(self.conn)
        _seed(self.conn)
        self.conn.commit()
        self.conn.close()

    def tearDown(self):
        for suffix in ("", "-shm", "-wal"):
            p = Path(self.tmp.name + suffix)
            if p.exists():
                p.unlink()

    def test_cli_propose_show(self):
        import os
        from manifold.cli import main

        legs_path = Path(self.tmp.name + ".legs.json")
        brief_path = Path(self.tmp.name + ".brief.md")
        brief_path.write_text("To-be state", encoding="utf-8")
        legs_path.write_text(json.dumps([{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "achieved"},
        }]), encoding="utf-8")

        os.environ["MANIFOLD_DB"] = self.tmp.name
        rc = main([
            "trajectory", "propose", "tr-proj",
            "--target-brief-file", str(brief_path),
            "--legs-file", str(legs_path),
        ])
        self.assertEqual(rc, 0)

        conn = db.connect(self.tmp.name)
        rows = conn.execute(
            "SELECT trajectory_id FROM trajectories"
        ).fetchall()
        conn.close()
        self.assertEqual(len(rows), 1)
        tid = rows[0]["trajectory_id"]

        rc = main(["trajectory", "show", tid, "--format", "md"])
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
