"""
Smoke test — validate the imported v0.2 self-spec end-to-end.

Imports v0.2's self-spec (at skills/manifold/specs/) into a fresh DB,
runs structural validation, and confirms the spec is internally consistent.

Skipped if the v0.2 spec is not present (e.g. in CI on a clone that
doesn't include v0.2).
"""
import os
import tempfile
import unittest
from pathlib import Path
from manifold import db, schema, writes, importer, config as _config

# Hermetic config: ensure load_config() never touches the real
# ~/.claude/manifold.json when _resolve_judge_command is called via run_validation.
_MANIFOLD_CONFIG_OVERRIDE = os.path.join(
    tempfile.gettempdir(), "manifold-test-phase-d-nonexistent.json"
)


def setUpModule():
    os.environ["MANIFOLD_CONFIG"] = _MANIFOLD_CONFIG_OVERRIDE
    _config._reset_config_cache()


def tearDownModule():
    os.environ.pop("MANIFOLD_CONFIG", None)
    _config._reset_config_cache()

V02_SPEC_REPO = Path(__file__).resolve().parents[3] / "skills" / "manifold"


@unittest.skipUnless((V02_SPEC_REPO / "specs" / "spec.yaml").is_file(),
                     f"v0.2 self-spec not present at {V02_SPEC_REPO}")
class TestPhaseDSmoke(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        tmp.close()
        self.db_path = Path(tmp.name)
        self.addCleanup(lambda: [Path(str(self.db_path) + s).unlink(missing_ok=True)
                                  for s in ("", "-shm", "-wal")])
        self.conn = db.connect(self.db_path)
        schema.bootstrap(self.conn)
        importer.import_project(
            self.conn, str(V02_SPEC_REPO),
            actor="smoke:phase_d",
        )

    def test_structural_validation_passes_on_v02_self_spec(self):
        result = writes.run_validation(
            self.conn, "manifold", with_verdicts=False, actor="human:smoke",
        )
        self.assertEqual(result["status"], "finished")
        structural = [
            i for i in result["issues"]
            if i["kind"] not in (
                "target_stale_planned",  # advisory only
                "target_unresolved_block",  # may surface if blocks refs cross specs
                "missing_rationale",  # advisory: existing specs lack rationale
                "missing_target_status",  # advisory: existing specs may lack this
                "deprecated_field",  # advisory: realized_by_external deprecated
            )
            and i.get("severity") != "advisory"  # exclude all advisories
        ]
        # The v0.2 spec is meant to be internally consistent.
        self.assertEqual(structural, [],
                          f"unexpected structural issues:\n" +
                          "\n".join(f"  - [{i['kind']}] {i.get('message','')}"
                                     for i in structural))
        # And we should have seen all 39 nodes.
        self.assertEqual(result["nodes_total"], 39)

    def test_verdicts_pass_runs_on_v02_self_spec(self):
        result = writes.run_validation(
            self.conn, "manifold",
            with_verdicts=True, with_targets=False,
            actor="human:smoke",
        )
        # All non-deleted nodes get a verdict row.
        self.assertEqual(result["verdicts_run"], 39)
        # The validation row records the count.
        v_row = self.conn.execute(
            "SELECT verdicts_run FROM validations WHERE validation_id = ?",
            (result["validation_id"],),
        ).fetchone()
        self.assertEqual(v_row["verdicts_run"], 39)


if __name__ == "__main__":
    unittest.main()
