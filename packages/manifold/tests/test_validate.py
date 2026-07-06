"""
Tests for manifold validate module.

Covers: _build_nodes_by_id projection, structural checks (layer membership,
tree property, intra-layer DAG, external realization, coverage, targets),
verdict runners (automated_check, python_assertion, human_signoff, llm_judge),
and the orchestrator + caching + propagation logic.
"""
import json
import os
import pathlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from manifold import db, schema, writes, validate, config as _config
from tests.conftest import fresh_db, seed_project, now_iso

# Point MANIFOLD_CONFIG at a non-existent temp path for the whole module so
# that _resolve_judge_command's config-file fallback never reads the real
# ~/.claude/manifold.json during this test run.
_MANIFOLD_CONFIG_OVERRIDE = os.path.join(
    tempfile.gettempdir(), "manifold-test-validate-nonexistent.json"
)


def setUpModule():
    os.environ["MANIFOLD_CONFIG"] = _MANIFOLD_CONFIG_OVERRIDE
    _config._reset_config_cache()


def tearDownModule():
    os.environ.pop("MANIFOLD_CONFIG", None)
    _config._reset_config_cache()


def _seed_with_layers(conn, project_id, layer_names):
    """Insert a project row directly with custom layer list."""
    conn.execute(
        "INSERT INTO projects (project_id, label, spec_config, created_at) "
        "VALUES (?, ?, ?, ?)",
        (project_id, project_id,
         json.dumps({"layers": [{"name": L} for L in layer_names]}),
         now_iso()),
    )


def _insert_node(conn, project_id, node_id, layer, **fields):
    """Directly insert a nodes row, bypassing writes validation."""
    cols = ["project_id", "node_id", "layer", "last_modified_at"]
    vals = [project_id, node_id, layer, fields.pop("last_modified_at", now_iso())]
    for k, v in fields.items():
        cols.append(k)
        vals.append(v)
    placeholders = ", ".join("?" * len(cols))
    conn.execute(
        f"INSERT INTO nodes ({', '.join(cols)}) VALUES ({placeholders})",
        vals,
    )


def _insert_edge(conn, project_id, src, dst, kind):
    conn.execute(
        "INSERT INTO node_edges VALUES (?, ?, ?, ?, ?)",
        (project_id, src, dst, kind, now_iso()),
    )


# ============================================================
# _build_nodes_by_id
# ============================================================

class TestBuildNodesByID(unittest.TestCase):
    def test_includes_edges(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "R.1", "realizations")
        _insert_edge(conn, "p1", "R.1", "I.1", "parent")
        _insert_edge(conn, "p1", "R.1", "I.1", "depends_on")
        _insert_edge(conn, "p1", "R.1", "I.1", "blocks")
        nbi = validate._build_nodes_by_id(conn, "p1")
        self.assertEqual(set(nbi), {"I.1", "R.1"})
        self.assertEqual(nbi["R.1"]["parents"], ["I.1"])
        self.assertEqual(nbi["R.1"]["peers_depends_on"], ["I.1"])
        self.assertEqual(nbi["R.1"]["target_blocks"], ["I.1"])
        self.assertEqual(nbi["I.1"]["parents"], [])

    def test_excludes_soft_deleted(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "I.2", "intent", deleted_at=now_iso())
        nbi = validate._build_nodes_by_id(conn, "p1")
        self.assertEqual(set(nbi), {"I.1"})

    def test_scopes_to_project(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _seed_with_layers(conn, "p2", ["intent"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p2", "I.1", "intent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        self.assertEqual(len(nbi), 1)


# ============================================================
# check_layer_membership
# ============================================================

class TestLayerMembership(unittest.TestCase):
    def test_legal_layers_no_issues(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_layer_membership(["intent", "realizations"], nbi)
        self.assertEqual(issues, [])

    def test_illegal_layer_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "X.1", "ghost")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_layer_membership(["intent"], nbi)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["kind"], "layer_membership")
        self.assertEqual(issues[0]["node"], "X.1")


# ============================================================
# check_tree_property
# ============================================================

class TestTreeProperty(unittest.TestCase):
    def test_top_layer_node_with_parent_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "I.2", "intent")
        _insert_edge(conn, "p1", "I.1", "I.2", "parent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_tree_property(["intent", "realizations"], nbi)
        self.assertTrue(any("top layer" in i["message"] for i in issues))

    def test_non_top_layer_node_without_parent_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "R.1", "realizations")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_tree_property(["intent", "realizations"], nbi)
        self.assertTrue(any("has no parent" in i["message"] for i in issues))

    def test_nonexistent_parent_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "R.1", "realizations")
        _insert_edge(conn, "p1", "R.1", "I.999", "parent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_tree_property(["intent", "realizations"], nbi)
        self.assertTrue(any("nonexistent parent" in i["message"] for i in issues))

    def test_parent_must_be_one_layer_up(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "capabilities", "contracts"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "K.1", "contracts")
        _insert_edge(conn, "p1", "K.1", "I.1", "parent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_tree_property(
            ["intent", "capabilities", "contracts"], nbi)
        self.assertTrue(any("expected layer 'capabilities'" in i["message"]
                            for i in issues))

    def test_multiple_parents_no_longer_flagged(self):
        """Multi-parent nodes are valid (AND/OR DAG). check_tree_property
        is now an alias for check_dag_property and does NOT reject multi-parent."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "I.2", "intent")
        _insert_node(conn, "p1", "R.1", "realizations")
        _insert_edge(conn, "p1", "R.1", "I.1", "parent")
        _insert_edge(conn, "p1", "R.1", "I.2", "parent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_tree_property(["intent", "realizations"], nbi)
        # Multi-parent is now allowed — no "at most 1" error expected
        errors = [i for i in issues if i.get("severity") != "advisory"
                  and "at most 1" in i.get("message", "")]
        self.assertEqual(errors, [], "Multi-parent should not be flagged as an error")


# ============================================================
# check_intra_layer_dag
# ============================================================

class TestIntraLayerDAG(unittest.TestCase):
    def test_cycle_detected(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        for nid in ["A", "B", "C"]:
            _insert_node(conn, "p1", nid, "intent")
        for src, dst in [("A", "B"), ("B", "C"), ("C", "A")]:
            _insert_edge(conn, "p1", src, dst, "depends_on")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_intra_layer_dag(nbi)
        cycle_issues = [i for i in issues if i["kind"] == "intra_layer_cycle"]
        self.assertEqual(len(cycle_issues), 1)

    def test_no_cycle_no_issues(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "A", "intent")
        _insert_node(conn, "p1", "B", "intent")
        _insert_edge(conn, "p1", "A", "B", "depends_on")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_intra_layer_dag(nbi)
        self.assertEqual(issues, [])

    def test_cross_layer_dependency_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "R.1", "realizations")
        _insert_edge(conn, "p1", "R.1", "I.1", "depends_on")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_intra_layer_dag(nbi)
        self.assertTrue(any("not in layer" in i["message"] for i in issues))


# ============================================================
# check_external_realization
# ============================================================

class TestExternalRealization(unittest.TestCase):
    def test_unresolved_target_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "I.1", "intent", realized_by_external="I.999")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues, _ = validate.check_external_realization(nbi)
        self.assertTrue(any("not found" in i["message"] for i in issues))

    def test_cycle_in_external_chain_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "A", "intent", realized_by_external="B")
        _insert_node(conn, "p1", "B", "intent", realized_by_external="A")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues, _ = validate.check_external_realization(nbi)
        self.assertTrue(any(i["kind"] == "external_realization_cycle"
                            for i in issues))

    def test_external_with_children_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "I.2", "intent", realized_by_external="I.1")
        _insert_node(conn, "p1", "R.1", "realizations")
        _insert_edge(conn, "p1", "R.1", "I.2", "parent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues, _ = validate.check_external_realization(nbi)
        self.assertTrue(any("must have no children" in i["message"]
                            for i in issues))


# ============================================================
# check_coverage
# ============================================================

class TestCoverage(unittest.TestCase):
    def test_non_leaf_without_children_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        _, children_of = validate.check_external_realization(nbi)
        issues = validate.check_coverage(["intent", "realizations"], nbi,
                                          children_of)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["kind"], "coverage")
        self.assertEqual(issues[0]["node"], "I.1")

    def test_constraint_waives_coverage(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent", kind="constraint")
        nbi = validate._build_nodes_by_id(conn, "p1")
        _, children_of = validate.check_external_realization(nbi)
        issues = validate.check_coverage(["intent", "realizations"], nbi,
                                          children_of)
        self.assertEqual(issues, [])

    def test_external_realized_waives_coverage(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "I.2", "intent", realized_by_external="I.1")
        nbi = validate._build_nodes_by_id(conn, "p1")
        _, children_of = validate.check_external_realization(nbi)
        issues = validate.check_coverage(["intent", "realizations"], nbi,
                                          children_of)
        # I.2 has external, so waived. I.1 still has no children → flagged.
        flagged = [i["node"] for i in issues]
        self.assertNotIn("I.2", flagged)

    def test_bottom_layer_doesnt_need_children(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "R.1", "realizations")
        _insert_edge(conn, "p1", "R.1", "I.1", "parent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        _, children_of = validate.check_external_realization(nbi)
        issues = validate.check_coverage(["intent", "realizations"], nbi,
                                          children_of)
        self.assertEqual(issues, [])


# ============================================================
# check_targets
# ============================================================

class TestTargets(unittest.TestCase):
    def test_blocks_cycle_detected(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        for nid in ["A", "B", "C"]:
            _insert_node(conn, "p1", nid, "intent")
        for src, dst in [("A", "B"), ("B", "C"), ("C", "A")]:
            _insert_edge(conn, "p1", src, dst, "blocks")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_targets(nbi)
        self.assertTrue(any(i["kind"] == "target_blocks_cycle"
                            for i in issues))

    def test_unresolved_block_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "A", "intent")
        _insert_edge(conn, "p1", "A", "Z", "blocks")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_targets(nbi)
        self.assertTrue(any("nonexistent node" in i["message"]
                            for i in issues))

    def test_stale_planned_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        old = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
        _insert_node(conn, "p1", "A", "intent",
                     target_status="planned",
                     target_achieved_when="api returns 2xx",
                     last_modified_at=old)
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_targets(nbi)
        stale = [i for i in issues if i["kind"] == "target_stale_planned"]
        self.assertEqual(len(stale), 1)
        self.assertGreater(stale[0]["age_days"], 180)

    def test_recent_planned_not_flagged(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "A", "intent", target_status="planned")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_targets(nbi)
        self.assertFalse(any(i["kind"] == "target_stale_planned"
                              for i in issues))

    def test_empty_target_status_emits_advisory(self):
        """Nodes with empty target_status get a missing_target_status advisory."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "A", "intent", target_status="")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_targets(nbi)
        advisories = [i for i in issues if i.get("severity") == "advisory"]
        self.assertTrue(any(i["kind"] == "missing_target_status" for i in advisories))

    def test_null_target_status_emits_advisory(self):
        """Nodes with NULL target_status also get a missing_target_status advisory."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "B", "intent")  # no target_status → NULL
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_targets(nbi)
        advisories = [i for i in issues if i.get("severity") == "advisory"]
        self.assertTrue(any(i["kind"] == "missing_target_status" for i in advisories))

    def test_set_target_status_no_advisory(self):
        """Nodes with a non-empty target_status do NOT get the advisory."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "A", "intent", target_status="planned")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_targets(nbi)
        self.assertFalse(any(i["kind"] == "missing_target_status" for i in issues))

    def test_constraint_nodes_skip_advisory(self):
        """Constraint-kind nodes are excluded from the advisory check."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent"])
        _insert_node(conn, "p1", "C", "intent", kind="constraint", target_status="")
        nbi = validate._build_nodes_by_id(conn, "p1")
        issues = validate.check_targets(nbi)
        self.assertFalse(any(i["kind"] == "missing_target_status" for i in issues))


# ============================================================
# Verdict runners
# ============================================================

class TestRunAutomatedCheck(unittest.TestCase):
    def test_pass(self):
        status, _ = validate.run_automated_check({"verdict_check": "true"}, "")
        self.assertEqual(status, "satisfied")

    def test_fail(self):
        status, _ = validate.run_automated_check({"verdict_check": "false"}, "")
        self.assertEqual(status, "violated")

    def test_missing_check(self):
        status, msg = validate.run_automated_check({}, "")
        self.assertEqual(status, "unknown")
        self.assertIn("no verdict_check", msg)


class TestRunPythonAssertion(unittest.TestCase):
    def test_file_exists_truthy(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "x.txt"
            p.write_text("hi")
            node = {"verdict_assertion": "file_exists('x.txt')"}
            status, _ = validate.run_python_assertion(node, td)
            self.assertEqual(status, "satisfied")

    def test_file_exists_falsy(self):
        with tempfile.TemporaryDirectory() as td:
            node = {"verdict_assertion": "file_exists('nope.txt')"}
            status, _ = validate.run_python_assertion(node, td)
            self.assertEqual(status, "violated")

    def test_ast_has_def(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "f.py"
            p.write_text("def foo(): pass\n")
            node = {"verdict_assertion": "ast_has_def('f.py', 'foo')"}
            status, _ = validate.run_python_assertion(node, td)
            self.assertEqual(status, "satisfied")

    def test_disallowed_construct_rejected(self):
        # Attribute access is disallowed
        node = {"verdict_assertion": "().__class__"}
        status, msg = validate.run_python_assertion(node, ".")
        self.assertEqual(status, "violated")

    def test_unknown_helper_rejected(self):
        node = {"verdict_assertion": "wipe_disk('foo')"}
        status, msg = validate.run_python_assertion(node, ".")
        self.assertEqual(status, "violated")
        self.assertIn("unknown helper", msg)

    def test_missing_assertion(self):
        status, _ = validate.run_python_assertion({}, "")
        self.assertEqual(status, "unknown")


class TestRunHumanSignoff(unittest.TestCase):
    def test_reads_column(self):
        node = {"verdict_status": "satisfied",
                "verdict_evidence_ref": "ali signed 2026-01-15"}
        status, evidence = validate.run_human_signoff(node)
        self.assertEqual(status, "satisfied")
        self.assertIn("ali", evidence)

    def test_missing_status(self):
        status, _ = validate.run_human_signoff({})
        self.assertEqual(status, "unknown")


class TestRunLLMJudge(unittest.TestCase):
    def test_no_command_returns_judge_required(self):
        status, msg = validate.run_llm_judge({}, None, judge_cmd="")
        self.assertEqual(status, "judge_required")
        self.assertIn("no judge command", msg)

    def test_satisfied_via_echo(self):
        node = {"node_id": "I.1", "title": "T", "body": "x", "layer": "intent"}
        # echo command emits "satisfied\nlooks good"; first line parsed as status
        status, evidence = validate.run_llm_judge(
            node, None, judge_cmd="printf 'satisfied\\nlooks good\\n'")
        self.assertEqual(status, "satisfied")
        self.assertIn("looks good", evidence)

    def test_violated_via_echo(self):
        node = {"node_id": "I.1", "title": "T", "body": "x", "layer": "intent"}
        status, _ = validate.run_llm_judge(
            node, None, judge_cmd="printf 'violated\\nbad\\n'")
        self.assertEqual(status, "violated")

    def test_unparseable_output_returns_judge_required(self):
        node = {"node_id": "I.1", "title": "T", "body": "x", "layer": "intent"}
        status, msg = validate.run_llm_judge(
            node, None, judge_cmd="echo 'maybe satisfied'")
        self.assertEqual(status, "judge_required")
        self.assertIn("satisfied/violated", msg)

    def test_nonzero_exit_returns_judge_required(self):
        node = {"node_id": "I.1", "title": "T", "body": "x", "layer": "intent"}
        status, msg = validate.run_llm_judge(
            node, None, judge_cmd="false")
        self.assertEqual(status, "judge_required")
        self.assertIn("exited", msg)

    def test_resolve_judge_command_env_wins(self):
        cmd = validate._resolve_judge_command(
            {"judge_command": "from-spec"},
            env={"MANIFOLD_JUDGE_CMD": "from-env"})
        self.assertEqual(cmd, "from-env")

    def test_resolve_judge_command_falls_back_to_spec(self):
        cmd = validate._resolve_judge_command(
            {"judge_command": "from-spec"}, env={})
        self.assertEqual(cmd, "from-spec")

    def test_resolve_judge_command_returns_empty_when_unset(self):
        cmd = validate._resolve_judge_command({}, env={})
        self.assertEqual(cmd, "")

    def test_build_judge_prompt_contains_both_nodes(self):
        child = {"title": "Child", "layer": "contracts", "body": "child body"}
        parent = {"title": "Parent", "body": "parent body"}
        prompt = validate._build_judge_prompt(child, parent)
        self.assertIn("Child", prompt)
        self.assertIn("Parent", prompt)
        self.assertIn("child body", prompt)
        self.assertIn("parent body", prompt)
        self.assertIn("satisfied", prompt)
        self.assertIn("violated", prompt)


# ============================================================
# Orchestrator + cache
# ============================================================

class TestRunVerdicts(unittest.TestCase):
    def _setup(self):
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p1", ["intent", "realizations"])
        return conn

    def test_no_mechanism_returns_unknown(self):
        conn = self._setup()
        _insert_node(conn, "p1", "I.1", "intent")
        nbi = validate._build_nodes_by_id(conn, "p1")
        verdicts = validate.run_verdicts(conn, "p1", nbi, "", force=False)
        self.assertEqual(verdicts["I.1"]["status"], "unknown")
        self.assertEqual(verdicts["I.1"]["source"], "no_mechanism")

    def test_automated_check_runs(self):
        conn = self._setup()
        _insert_node(conn, "p1", "I.1", "intent",
                     verdict_mechanism="automated_check",
                     verdict_check="true")
        nbi = validate._build_nodes_by_id(conn, "p1")
        verdicts = validate.run_verdicts(conn, "p1", nbi, "", force=False)
        self.assertEqual(verdicts["I.1"]["status"], "satisfied")
        self.assertEqual(verdicts["I.1"]["source"], "automated")

    def test_cache_hit_after_insert(self):
        conn = self._setup()
        _insert_node(conn, "p1", "I.1", "intent",
                     verdict_mechanism="automated_check",
                     verdict_check="true")
        nbi = validate._build_nodes_by_id(conn, "p1")
        v1 = validate.run_verdicts(conn, "p1", nbi, "", force=False)
        # Insert v1's result into the verdicts table to simulate a prior run
        conn.execute(
            "INSERT INTO validations (project_id, started_at, status) "
            "VALUES ('p1', ?, 'finished')", (now_iso(),))
        validation_id = conn.execute(
            "SELECT MAX(validation_id) FROM validations").fetchone()[0]
        conn.execute(
            "INSERT INTO verdicts (validation_id, project_id, node_id, "
            "mechanism, status, source, evidence_hash) "
            "VALUES (?, 'p1', 'I.1', 'automated_check', ?, ?, ?)",
            (validation_id, v1["I.1"]["status"], v1["I.1"]["source"],
             v1["I.1"]["evidence_hash"]),
        )
        # Now re-run; should hit cache
        v2 = validate.run_verdicts(conn, "p1", nbi, "", force=False)
        self.assertEqual(v2["I.1"]["source"], "cache")

    def test_force_bypasses_cache(self):
        conn = self._setup()
        _insert_node(conn, "p1", "I.1", "intent",
                     verdict_mechanism="automated_check",
                     verdict_check="true")
        nbi = validate._build_nodes_by_id(conn, "p1")
        v1 = validate.run_verdicts(conn, "p1", nbi, "", force=False)
        conn.execute(
            "INSERT INTO validations (project_id, started_at, status) "
            "VALUES ('p1', ?, 'finished')", (now_iso(),))
        validation_id = conn.execute(
            "SELECT MAX(validation_id) FROM validations").fetchone()[0]
        conn.execute(
            "INSERT INTO verdicts (validation_id, project_id, node_id, "
            "mechanism, status, source, evidence_hash) "
            "VALUES (?, 'p1', 'I.1', 'automated_check', 'satisfied', "
            "'automated', ?)",
            (validation_id, v1["I.1"]["evidence_hash"]),
        )
        v2 = validate.run_verdicts(conn, "p1", nbi, "", force=True)
        self.assertEqual(v2["I.1"]["source"], "automated")

    def test_external_short_circuits(self):
        conn = self._setup()
        _insert_node(conn, "p1", "I.1", "intent")
        _insert_node(conn, "p1", "I.2", "intent", realized_by_external="I.1")
        nbi = validate._build_nodes_by_id(conn, "p1")
        verdicts = validate.run_verdicts(conn, "p1", nbi, "", force=False)
        self.assertEqual(verdicts["I.2"]["status"], "deferred_external")
        self.assertTrue(verdicts["I.2"]["source"].startswith("external:"))


# ============================================================
# resolve_external + propagate_failures
# ============================================================

class TestResolveExternal(unittest.TestCase):
    def test_status_follows_target(self):
        nbi = {
            "A": {"node_id": "A", "realized_by_external": "B", "parents": []},
            "B": {"node_id": "B", "realized_by_external": None, "parents": []},
        }
        verdicts = {
            "A": {"status": "deferred_external", "source": "external:B"},
            "B": {"status": "violated", "source": "automated"},
        }
        validate.resolve_external(verdicts, nbi)
        self.assertEqual(verdicts["A"]["status"], "violated")


class TestPropagateFailures(unittest.TestCase):
    def test_failure_propagates_up(self):
        nbi = {
            "I.1": {"node_id": "I.1", "parents": []},
            "C.1": {"node_id": "C.1", "parents": ["I.1"]},
            "K.1": {"node_id": "K.1", "parents": ["C.1"]},
        }
        verdicts = {
            "I.1": {"status": "satisfied"},
            "C.1": {"status": "satisfied"},
            "K.1": {"status": "violated"},
        }
        validate.propagate_failures(verdicts, nbi)
        self.assertEqual(verdicts["C.1"]["status"], "invalidated_by_descendant")
        self.assertEqual(verdicts["I.1"]["status"], "invalidated_by_descendant")

    def test_no_propagation_when_all_satisfied(self):
        nbi = {
            "A": {"node_id": "A", "parents": []},
            "B": {"node_id": "B", "parents": ["A"]},
        }
        verdicts = {
            "A": {"status": "satisfied"},
            "B": {"status": "satisfied"},
        }
        validate.propagate_failures(verdicts, nbi)
        self.assertEqual(verdicts["A"]["status"], "satisfied")


# ============================================================
# compute_input_hash stability
# ============================================================

class TestComputeInputHash(unittest.TestCase):
    def test_stable(self):
        node = {"node_id": "I.1", "layer": "intent", "kind": "spec",
                "body": "foo", "realized_by_external": None,
                "target_status": "planned",
                "verdict_mechanism": "automated_check",
                "verdict_check": "true", "verdict_assertion": None}
        h1 = validate.compute_input_hash(node, {"P": "satisfied"})
        h2 = validate.compute_input_hash(node, {"P": "satisfied"})
        self.assertEqual(h1, h2)

    def test_changes_when_body_changes(self):
        node1 = {"node_id": "I.1", "body": "v1", "verdict_mechanism": "x"}
        node2 = {"node_id": "I.1", "body": "v2", "verdict_mechanism": "x"}
        h1 = validate.compute_input_hash(node1, {})
        h2 = validate.compute_input_hash(node2, {})
        self.assertNotEqual(h1, h2)

    def test_changes_when_parent_status_changes(self):
        node = {"node_id": "C.1", "body": "x"}
        h1 = validate.compute_input_hash(node, {"P": "satisfied"})
        h2 = validate.compute_input_hash(node, {"P": "violated"})
        self.assertNotEqual(h1, h2)


# ============================================================
# TestDAGAcrossLayers (multi-parent acceptance)
# ============================================================

class TestDAGAcrossLayers(unittest.TestCase):
    """Relax strict-tree to AND/OR DAG. Multi-parent nodes must validate cleanly."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        writes.register_project(self.conn, "p", spec_config={
            "layers": [
                {"name": "L0"}, {"name": "L1"}, {"name": "L2"}
            ]
        })
        writes.create_node(self.conn, "p", "L0", "I.1", "intent 1", actor="human:test")
        writes.create_node(self.conn, "p", "L0", "I.2", "intent 2", actor="human:test")
        writes.create_node(self.conn, "p", "L1", "C.1", "cap 1",
                            parents=["I.1", "I.2"], actor="human:test")  # multi-parent

    def test_multi_parent_validates_clean(self):
        """Multi-parent node with valid parents-above-layer must produce zero errors."""
        nbi = validate._build_nodes_by_id(self.conn, "p")
        issues = validate.check_dag_property(["L0", "L1", "L2"], nbi)
        errors = [i for i in issues if i.get("severity") != "advisory"]
        self.assertEqual(errors, [], f"Expected no errors, got: {errors}")

    def test_multi_parent_propagation(self):
        """C.1 has parents [I.1, I.2]; violated child must invalidate ALL parents."""
        # Add L2 child so C.1 is not a childless mid-layer node
        writes.create_node(self.conn, "p", "L2", "R.1", "realization 1",
                           parents=["C.1"], actor="human:test")

        nbi = validate._build_nodes_by_id(self.conn, "p")
        verdicts = {
            "I.1": {"status": "satisfied", "source": "human"},
            "I.2": {"status": "satisfied", "source": "human"},
            "C.1": {"status": "satisfied", "source": "human"},
            "R.1": {"status": "violated", "source": "automated"},
        }
        validate.propagate_failures(verdicts, nbi)
        # C.1 has violated descendant R.1 → invalidated
        self.assertEqual(verdicts["C.1"]["status"], "invalidated_by_descendant")
        # Both parents of C.1 should also be invalidated
        self.assertEqual(verdicts["I.1"]["status"], "invalidated_by_descendant")
        self.assertEqual(verdicts["I.2"]["status"], "invalidated_by_descendant")

    def test_cycle_across_layers_still_blocked(self):
        """Even with multi-parent allowed, cycles across layers must be caught."""
        conn, _ = fresh_db(self)
        writes.register_project(conn, "cyc", spec_config={
            "layers": [{"name": "L0"}, {"name": "L1"}]
        })
        nbi = {
            "A": {"node_id": "A", "layer": "L0", "parents": ["B"]},
            "B": {"node_id": "B", "layer": "L1", "parents": ["A"]},
        }
        issues = validate.check_dag_property(["L0", "L1"], nbi)
        cycle_issues = [i for i in issues if i.get("kind") == "cycle_across_layers"]
        self.assertGreater(len(cycle_issues), 0, "Cycle should have been detected")

    def test_realized_by_external_emits_advisory(self):
        """realized_by_external should emit an advisory (not error)."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "ext", ["intent"])
        _insert_node(conn, "ext", "I.1", "intent", realized_by_external="I.2")
        _insert_node(conn, "ext", "I.2", "intent")
        nbi = validate._build_nodes_by_id(conn, "ext")
        issues = validate.check_dag_property(["intent"], nbi)
        advisories = [i for i in issues if i.get("severity") == "advisory"
                      and i.get("kind") == "deprecated_field"]
        self.assertGreater(len(advisories), 0,
                           "realized_by_external should emit a deprecated_field advisory")


# ============================================================
# check_rationale (advisory warning for missing rationale)
# ============================================================

class TestCheckRationale(unittest.TestCase):
    """Task 6: check_rationale emits advisory issues for non-constraint nodes
    that have no rationale set."""

    def test_missing_rationale_emits_advisory(self):
        """Nodes without rationale get a missing_rationale advisory."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p", ["intent"])
        _insert_node(conn, "p", "A", "intent")  # no rationale
        nbi = validate._build_nodes_by_id(conn, "p")
        issues = validate.check_rationale(nbi)
        advisories = [i for i in issues if i.get("severity") == "advisory"]
        self.assertTrue(any(i["kind"] == "missing_rationale" for i in advisories),
                        f"Expected missing_rationale advisory, got: {issues}")

    def test_set_rationale_no_advisory(self):
        """Nodes with rationale do NOT get the advisory."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p", ["intent"])
        _insert_node(conn, "p", "A", "intent", rationale="exists because Q")
        nbi = validate._build_nodes_by_id(conn, "p")
        issues = validate.check_rationale(nbi)
        self.assertFalse(any(i["kind"] == "missing_rationale" for i in issues),
                         f"Should not emit advisory when rationale is set, got: {issues}")

    def test_constraint_nodes_skip_rationale_advisory(self):
        """constraint-kind nodes are excluded from the rationale advisory check."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p", ["intent"])
        _insert_node(conn, "p", "C", "intent", kind="constraint")
        nbi = validate._build_nodes_by_id(conn, "p")
        issues = validate.check_rationale(nbi)
        self.assertFalse(any(i["kind"] == "missing_rationale" for i in issues),
                         "constraint nodes should not get missing_rationale advisory")

    def test_check_rationale_wired_into_run_validation(self):
        """run_validation (structural pipeline) includes rationale advisories."""
        conn, _ = fresh_db(self)
        writes.register_project(conn, "p2", spec_config={
            "layers": [{"name": "L0"}]
        })
        writes.create_node(conn, "p2", "L0", "A", "A", actor="human:test")  # no rationale
        result = writes.run_validation(conn, "p2", actor="human:test")
        advisories = [i for i in result["issues"] if i.get("kind") == "missing_rationale"]
        self.assertGreater(len(advisories), 0,
                           "run_validation should surface missing_rationale advisories")

    def test_rationale_advisory_node_id_matches(self):
        """The advisory issue's node_id field matches the node that is missing rationale."""
        conn, _ = fresh_db(self)
        _seed_with_layers(conn, "p", ["intent"])
        _insert_node(conn, "p", "missing_node", "intent")
        _insert_node(conn, "p", "has_node", "intent", rationale="present")
        nbi = validate._build_nodes_by_id(conn, "p")
        issues = validate.check_rationale(nbi)
        flagged = [i["node_id"] for i in issues if i["kind"] == "missing_rationale"]
        self.assertIn("missing_node", flagged)
        self.assertNotIn("has_node", flagged)


if __name__ == "__main__":
    unittest.main()
