import tempfile
import unittest
from pathlib import Path

from manifold import db, schema, queries, writes
from manifold.drift_report import classify_finding, format_terminal, format_markdown


class TestClassifyFinding(unittest.TestCase):
    def test_no_mechanism_is_unverified(self):
        self.assertEqual(
            classify_finding("unknown", "no_mechanism", ""),
            "unverified",
        )

    def test_violated_is_violated(self):
        self.assertEqual(
            classify_finding("violated", "automated", "automated_check"),
            "violated",
        )

    def test_judge_required_is_violated(self):
        self.assertEqual(
            classify_finding("judge_required", "judge_required", "llm_judge"),
            "violated",
        )

    def test_satisfied_is_satisfied(self):
        self.assertEqual(
            classify_finding("satisfied", "automated", "automated_check"),
            "satisfied",
        )

    def test_deferred_external_bucket(self):
        self.assertEqual(
            classify_finding("deferred_external", "external:R.9", "automated_check"),
            "deferred_external",
        )

    def test_errored_bucket(self):
        self.assertEqual(
            classify_finding("errored", "automated", "automated_check"),
            "errored",
        )

    def test_human_unknown_with_mechanism_is_other(self):
        self.assertEqual(
            classify_finding("unknown", "human", "human_signoff"),
            "other",
        )


def _patch_verdict(conn, project_id, node_id, fields, *, actor="human:test"):
    rev = queries.get_node(conn, project_id, node_id)["current_revision_id"]
    writes.update_node(
        conn, project_id, node_id, fields,
        expected_revision_id=rev, actor=actor, change_reason="evolution",
    )


def _seed_project(conn, project_id="p", layers=None):
    layers = layers or [
        {"name": "intent"},
        {"name": "realizations"},
    ]
    writes.register_project(conn, project_id, spec_config={
        "layers": layers,
        "project_root": str(Path.cwd()),
    })
    writes.create_node(conn, project_id, "intent", "I.1", "Intent",
                       actor="human:test")
    writes.create_node(
        conn, project_id, "realizations", "R.ok", "Satisfied node",
        parents=["I.1"], actor="human:test",
    )
    _patch_verdict(conn, project_id, "R.ok", {
        "verdict_mechanism": "automated_check",
        "verdict_check": "true",
    })
    writes.create_node(
        conn, project_id, "realizations", "R.bad", "Violated node",
        parents=["I.1"], actor="human:test",
    )
    _patch_verdict(conn, project_id, "R.bad", {
        "verdict_mechanism": "automated_check",
        "verdict_check": "false",
    })
    writes.create_node(
        conn, project_id, "realizations", "R.none", "Unverified node",
        parents=["I.1"], actor="human:test",
    )


class TestDriftReportQuery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.conn = db.connect(self.tmp.name)
        schema.bootstrap(self.conn)
        _seed_project(self.conn)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        for suffix in ("", "-shm", "-wal"):
            p = Path(self.tmp.name + suffix)
            if p.exists():
                p.unlink()

    def test_drift_report_default_layer_is_bottom(self):
        report = queries.drift_report(self.conn, "p")
        self.assertEqual(report["layer_scope"], "realizations")
        ids = {f["node_id"] for f in report["violated"] + report["unverified"]}
        self.assertIn("R.bad", ids)
        self.assertIn("R.none", ids)
        self.assertNotIn("I.1", ids)

    def test_drift_report_summary_counts(self):
        report = queries.drift_report(self.conn, "p", force=True)
        self.assertEqual(report["summary"]["violated"], 1)
        self.assertEqual(report["summary"]["unverified"], 1)
        self.assertEqual(report["summary"]["satisfied"], 1)

    def test_drift_report_all_layers(self):
        report = queries.drift_report(self.conn, "p", all_layers=True, force=True)
        self.assertEqual(report["layer_scope"], "all")
        self.assertEqual(report["summary"]["total"], 4)

    def test_drift_report_repo_override(self):
        report = queries.drift_report(
            self.conn, "p", project_root="/tmp/custom-repo", force=True)
        self.assertEqual(report["project_root"], "/tmp/custom-repo")

    def test_drift_report_missing_project_returns_empty(self):
        report = queries.drift_report(self.conn, "missing")
        self.assertEqual(report["summary"]["total"], 0)
        self.assertEqual(report["violated"], [])

    def test_drift_report_bad_project_root_is_errored_not_violated(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        conn = db.connect(tmp.name)
        schema.bootstrap(conn)
        writes.register_project(conn, "bad-root", spec_config={
            "layers": [{"name": "intent"}, {"name": "realizations"}],
            "project_root": str(Path.cwd()),
        })
        writes.create_node(conn, "bad-root", "intent", "I.1", "Intent",
                           actor="human:test")
        writes.create_node(
            conn, "bad-root", "realizations", "R.exec", "Check node",
            parents=["I.1"], actor="human:test",
        )
        rev = queries.get_node(conn, "bad-root", "R.exec")["current_revision_id"]
        writes.update_node(
            conn, "bad-root", "R.exec",
            {"verdict_mechanism": "automated_check", "verdict_check": "true"},
            expected_revision_id=rev, actor="human:test",
            change_reason="evolution",
        )
        conn.commit()
        report = queries.drift_report(
            conn, "bad-root",
            project_root="/tmp/manifold-nonexistent-repo-for-drift-test",
            force=True,
        )
        errored_ids = {f["node_id"] for f in report["errored"]}
        violated_ids = {f["node_id"] for f in report["violated"]}
        self.assertIn("R.exec", errored_ids)
        self.assertNotIn("R.exec", violated_ids)
        self.assertEqual(report["summary"]["errored"], 1)
        conn.close()
        for suffix in ("", "-shm", "-wal"):
            p = Path(tmp.name + suffix)
            if p.exists():
                p.unlink()

    def test_drift_report_warns_when_project_root_unset(self):
        conn = db.connect(self.tmp.name)
        schema.bootstrap(conn)
        writes.register_project(conn, "no-root", spec_config={
            "layers": [{"name": "intent"}, {"name": "realizations"}],
        })
        writes.create_node(conn, "no-root", "intent", "I.1", "Intent",
                           actor="human:test")
        writes.create_node(
            conn, "no-root", "realizations", "R.1", "Real",
            parents=["I.1"], actor="human:test",
        )
        conn.commit()
        report = queries.drift_report(conn, "no-root", force=True)
        self.assertTrue(report.get("warnings"))
        self.assertIn("project_root is unset", report["warnings"][0])
        conn.close()


SAMPLE_REPORT = {
    "project_id": "p",
    "layer_scope": "realizations",
    "project_root": "/repo",
    "summary": {
        "total": 2, "violated": 1, "unverified": 1, "satisfied": 0,
        "deferred_external": 0, "other": 0,
    },
    "violated": [{
        "node_id": "R.bad", "layer": "realizations", "title": "Bad",
        "rationale": "Because", "verdict_status": "violated",
        "verdict_source": "automated", "verdict_evidence": "fail",
        "verdict_mechanism": "automated_check",
    }],
    "unverified": [{
        "node_id": "R.none", "layer": "realizations", "title": "None",
        "rationale": "", "verdict_status": "unknown",
        "verdict_source": "no_mechanism", "verdict_evidence": "",
        "verdict_mechanism": "",
    }],
    "satisfied": [], "deferred_external": [], "other": [],
}


class TestDriftReportFormatters(unittest.TestCase):
    def test_terminal_shows_violated_and_unverified(self):
        out = format_terminal(SAMPLE_REPORT)
        self.assertIn("VIOLATED", out)
        self.assertIn("UNVERIFIED", out)
        self.assertIn("R.bad", out)
        self.assertIn("R.none", out)

    def test_terminal_shows_errored_section(self):
        report = dict(SAMPLE_REPORT)
        report["errored"] = [{
            "node_id": "R.err", "layer": "realizations", "title": "Bad env",
            "rationale": "", "verdict_status": "errored",
            "verdict_source": "automated", "verdict_evidence": "check failed",
            "verdict_mechanism": "automated_check",
        }]
        report["summary"] = dict(report["summary"], errored=1, total=3)
        out = format_terminal(report)
        self.assertIn("ERRORED", out)
        self.assertIn("R.err", out)

    def test_markdown_has_headings(self):
        md = format_markdown(SAMPLE_REPORT)
        self.assertIn("# Intent drift report", md)
        self.assertIn("## Violated", md)
        self.assertIn("## Unverified", md)
        self.assertIn("R.bad", md)
