"""
Tests for manifold queries layer.

Covers the 13 read functions from queries.py. Each test class focuses on
one function (or pair).
"""
import json
import unittest
from manifold import queries
from tests.conftest import fresh_db, seed_project, now_iso


def _insert_node(conn, project_id, node_id, layer, *, title="", kind="spec",
                 body="", deleted=False, target_status=None,
                 verdict_status=None, contract=None, last_modified=None):
    last_modified = last_modified or now_iso()
    conn.execute(
        "INSERT INTO nodes (project_id, node_id, layer, title, kind, body, "
        "target_status, verdict_status, contract, last_modified_at, deleted_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (project_id, node_id, layer, title, kind, body,
         target_status, verdict_status,
         json.dumps(contract) if contract else None,
         last_modified, now_iso() if deleted else None),
    )


def _insert_edge(conn, project_id, src, dst, kind):
    conn.execute(
        "INSERT INTO node_edges (project_id, src_node_id, dst_node_id, "
        "edge_kind, created_at) VALUES (?, ?, ?, ?, ?)",
        (project_id, src, dst, kind, now_iso()),
    )


# ============================================================
# Projects
# ============================================================

class TestProjectQueries(unittest.TestCase):
    def test_get_project_returns_row(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1", label="My Project")
        p = queries.get_project(conn, "p1")
        self.assertEqual(p["project_id"], "p1")
        self.assertEqual(p["label"], "My Project")
        self.assertIn("layers", p["spec_config"])

    def test_get_project_returns_none_when_missing(self):
        conn, _ = fresh_db(self)
        self.assertIsNone(queries.get_project(conn, "missing"))

    def test_list_projects_excludes_archived_by_default(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        seed_project(conn, "p2")
        conn.execute("UPDATE projects SET archived_at = '2026-01-01' WHERE project_id = 'p2'")
        ids = [p["project_id"] for p in queries.list_projects(conn)]
        self.assertEqual(ids, ["p1"])

    def test_list_projects_includes_archived_when_asked(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        seed_project(conn, "p2")
        conn.execute("UPDATE projects SET archived_at = '2026-01-01' WHERE project_id = 'p2'")
        ids = sorted([p["project_id"] for p in queries.list_projects(conn, include_archived=True)])
        self.assertEqual(ids, ["p1", "p2"])


# ============================================================
# Nodes
# ============================================================

class TestGetNode(unittest.TestCase):
    def test_get_node_returns_row_with_parsed_json(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        _insert_node(conn, "p1", "K.7", "contracts", title="TokenIssuer",
                     body="## interface\n…",
                     contract={"version": "0.1.0", "locked": False,
                               "field_anchors": ["interface"]})
        node = queries.get_node(conn, "p1", "K.7")
        self.assertEqual(node["node_id"], "K.7")
        self.assertEqual(node["title"], "TokenIssuer")
        self.assertEqual(node["contract"]["version"], "0.1.0")
        self.assertEqual(node["contract"]["field_anchors"], ["interface"])

    def test_get_node_returns_none_when_missing(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        self.assertIsNone(queries.get_node(conn, "p1", "nope"))

    def test_get_node_excludes_soft_deleted_by_default(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        _insert_node(conn, "p1", "I.1", "intent", deleted=True)
        self.assertIsNone(queries.get_node(conn, "p1", "I.1"))
        n = queries.get_node(conn, "p1", "I.1", include_deleted=True)
        self.assertEqual(n["node_id"], "I.1")


class TestListNodes(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        for i, layer in enumerate(["intent", "intent", "realizations"]):
            _insert_node(self.conn, "p1", f"X.{i}", layer)

    def test_list_nodes_all_layers(self):
        rows = queries.list_nodes(self.conn, "p1")
        self.assertEqual(len(rows), 3)

    def test_list_nodes_filtered_by_layer(self):
        rows = queries.list_nodes(self.conn, "p1", layer="intent")
        self.assertEqual(len(rows), 2)
        for r in rows:
            self.assertEqual(r["layer"], "intent")

    def test_list_nodes_pagination(self):
        page1 = queries.list_nodes(self.conn, "p1", limit=2)
        self.assertEqual(len(page1), 2)
        page2 = queries.list_nodes(self.conn, "p1", limit=2,
                                    cursor=f"id:{page1[-1]['node_id']}")
        self.assertEqual(len(page2), 1)


# ============================================================
# Targets
# ============================================================

class TestListTargets(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        _insert_node(self.conn, "p1", "K.1", "contracts", target_status="planned",
                     last_modified="2025-01-01T00:00:00+00:00")
        _insert_node(self.conn, "p1", "K.2", "contracts", target_status="in_progress")
        _insert_node(self.conn, "p1", "K.3", "contracts")    # no target

    def test_list_targets_returns_targeted_nodes(self):
        rows = queries.list_targets(self.conn, project_id="p1")
        ids = sorted([r["node_id"] for r in rows])
        self.assertEqual(ids, ["K.1", "K.2"])

    def test_list_targets_filter_by_status(self):
        rows = queries.list_targets(self.conn, project_id="p1", status="planned")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["node_id"], "K.1")

    def test_list_targets_older_than_days(self):
        rows = queries.list_targets(self.conn, project_id="p1", older_than_days=180)
        # K.1 is dated 2025-01-01, definitely > 180 days from 2026-05-23
        ids = [r["node_id"] for r in rows]
        self.assertIn("K.1", ids)


# ============================================================
# Revisions
# ============================================================

class TestListRevisions(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        _insert_node(self.conn, "p1", "I.1", "intent")
        for i, ts in enumerate(["2025-01-01T00:00:00+00:00",
                                 "2025-02-01T00:00:00+00:00",
                                 "2025-03-01T00:00:00+00:00"]):
            self.conn.execute(
                "INSERT INTO revisions (project_id, node_id, ts, change_type, "
                "snapshot, source, actor) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("p1", "I.1", ts, "updated", json.dumps({"v": i}), "test", "h"),
            )

    def test_returns_newest_first(self):
        rows = queries.list_revisions(self.conn, "p1", "I.1")
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["ts"], "2025-03-01T00:00:00+00:00")

    def test_limit_caps_result(self):
        rows = queries.list_revisions(self.conn, "p1", "I.1", limit=2)
        self.assertEqual(len(rows), 2)


class TestListChangesSince(unittest.TestCase):
    def test_filters_by_revision_id(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        _insert_node(conn, "p1", "I.1", "intent")
        for ts in ["2025-01-01T00:00:00+00:00", "2025-02-01T00:00:00+00:00"]:
            conn.execute(
                "INSERT INTO revisions (project_id, node_id, ts, change_type, "
                "snapshot, source, actor) VALUES (?, ?, ?, 'updated', ?, 'test', 'h')",
                ("p1", "I.1", ts, "{}"),
            )
        rows = queries.list_changes_since(conn, project_id="p1", since_revision_id=1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["revision_id"], 2)

    def test_raises_without_either_filter(self):
        conn, _ = fresh_db(self)
        with self.assertRaises(ValueError):
            queries.list_changes_since(conn, project_id="p1")


class TestDiffRevisions(unittest.TestCase):
    def test_returns_field_and_body_diff(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        _insert_node(conn, "p1", "I.1", "intent")
        a = {"title": "A", "body": "line one\nline two"}
        b = {"title": "B", "body": "line one\nline two changed"}
        conn.execute(
            "INSERT INTO revisions (project_id, node_id, ts, change_type, "
            "snapshot, source, actor) VALUES (?, ?, ?, 'created', ?, 'test', 'h')",
            ("p1", "I.1", "2025-01-01T00:00:00+00:00", json.dumps(a)),
        )
        conn.execute(
            "INSERT INTO revisions (project_id, node_id, ts, change_type, "
            "snapshot, source, actor) VALUES (?, ?, ?, 'updated', ?, 'test', 'h')",
            ("p1", "I.1", "2025-02-01T00:00:00+00:00", json.dumps(b)),
        )
        diff = queries.diff_revisions(conn, "p1", "I.1", 1, 2)
        self.assertIsNotNone(diff)
        field_names = {d["field"] for d in diff["fields"]}
        self.assertIn("title", field_names)
        self.assertIn("body", field_names)
        self.assertTrue(any("changed" in line for line in diff["body_diff"]))

    def test_returns_none_when_revision_missing(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        self.assertIsNone(queries.diff_revisions(conn, "p1", "I.1", 999, 998))


# ============================================================
# Unstable verdicts (flip detection)
# ============================================================

class TestListUnstableVerdicts(unittest.TestCase):
    def test_detects_flipping_judge(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        _insert_node(conn, "p1", "K.1", "contracts")
        # Three validations with alternating verdict status
        for i, status in enumerate(["satisfied", "violated", "satisfied"]):
            conn.execute(
                "INSERT INTO validations (project_id, started_at, status) "
                "VALUES (?, ?, 'completed')", ("p1", f"2025-0{i+1}-01T00:00:00+00:00"),
            )
            conn.execute(
                "INSERT INTO verdicts (validation_id, project_id, node_id, "
                "mechanism, status, source) VALUES (?, ?, ?, 'llm_judge', ?, 'llm_judge')",
                (i + 1, "p1", "K.1", status),
            )
        rows = queries.list_unstable_verdicts(conn, project_id="p1", k=3)
        ids = [r["node_id"] for r in rows]
        self.assertIn("K.1", ids)


# ============================================================
# Validations
# ============================================================

class TestValidations(unittest.TestCase):
    def test_get_and_list(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        conn.execute(
            "INSERT INTO validations (project_id, started_at, status, "
            "nodes_total, issues_total) VALUES (?, ?, 'completed', 39, 0)",
            ("p1", "2025-01-01T00:00:00+00:00"),
        )
        v = queries.get_validation(conn, 1)
        self.assertEqual(v["nodes_total"], 39)
        rows = queries.list_validations(conn, project_id="p1")
        self.assertEqual(len(rows), 1)


# ============================================================
# Graph: list_blocking_chain (recursive CTE)
# ============================================================

class TestListBlockingChain(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        # K.1 blocked by K.2 blocked by K.3
        for nid in ("K.1", "K.2", "K.3"):
            _insert_node(self.conn, "p1", nid, "contracts")
        _insert_edge(self.conn, "p1", "K.2", "K.1", "blocks")
        _insert_edge(self.conn, "p1", "K.3", "K.2", "blocks")

    def test_direct_only(self):
        rows = queries.list_blocking_chain(self.conn, "p1", "K.1", direct_only=True)
        ids = [r["node_id"] for r in rows]
        self.assertEqual(ids, ["K.2"])

    def test_transitive(self):
        rows = queries.list_blocking_chain(self.conn, "p1", "K.1")
        ids = sorted([r["node_id"] for r in rows])
        self.assertEqual(ids, ["K.2", "K.3"])


# ============================================================
# list_uncovered (parent-no-child detection)
# ============================================================

class TestListUncovered(unittest.TestCase):
    def test_finds_intent_with_no_capability_child(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1", layers=[
            {"name": "intent", "verdict_default": "human_signoff"},
            {"name": "capabilities", "verdict_default": "llm_judge"},
            {"name": "realizations", "verdict_default": "automated_check"},
        ])
        _insert_node(conn, "p1", "I.1", "intent", title="covered")
        _insert_node(conn, "p1", "I.2", "intent", title="uncovered")
        _insert_node(conn, "p1", "C.1", "capabilities")
        _insert_edge(conn, "p1", "C.1", "I.1", "parent")

        rows = queries.list_uncovered(conn, "p1", "capabilities")
        ids = [r["node_id"] for r in rows]
        self.assertEqual(ids, ["I.2"])

    def test_skips_constraints(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1", layers=[
            {"name": "intent"}, {"name": "capabilities"}, {"name": "realizations"},
        ])
        _insert_node(conn, "p1", "I.1", "intent", kind="constraint")
        rows = queries.list_uncovered(conn, "p1", "capabilities")
        self.assertEqual(rows, [])


# ============================================================
# resolve_node (fuzzy lookup)
# ============================================================

class TestResolveNode(unittest.TestCase):
    def test_exact_id_match_first(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        _insert_node(conn, "p1", "K.1", "contracts", title="auth contract")
        _insert_node(conn, "p1", "K.10", "contracts", title="logging")
        ids = queries.resolve_node(conn, "p1", "K.1")
        self.assertEqual(ids[0], "K.1")

    def test_title_substring(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        _insert_node(conn, "p1", "K.1", "contracts", title="TokenIssuer")
        _insert_node(conn, "p1", "K.2", "contracts", title="PasswordVerifier")
        ids = queries.resolve_node(conn, "p1", "token")
        self.assertIn("K.1", ids)

    def test_empty_query_returns_empty(self):
        conn, _ = fresh_db(self)
        seed_project(conn, "p1")
        self.assertEqual(queries.resolve_node(conn, "p1", ""), [])


# ============================================================
# peek_node_full (composite)
# ============================================================

class TestPeekNodeFull(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        _insert_node(self.conn, "p1", "I.1", "intent", title="root")
        _insert_node(self.conn, "p1", "C.1", "capabilities", title="cap")
        _insert_edge(self.conn, "p1", "C.1", "I.1", "parent")

    def test_default_include_returns_parents(self):
        result = queries.peek_node_full(self.conn, "p1", "C.1")
        self.assertEqual(result["node_id"], "C.1")
        self.assertIn("parents_detail", result)
        self.assertEqual(len(result["parents_detail"]), 1)
        self.assertEqual(result["parents_detail"][0]["node_id"], "I.1")

    def test_default_include_returns_verdict_block(self):
        result = queries.peek_node_full(self.conn, "p1", "C.1")
        self.assertIn("verdict", result)
        self.assertIn("mechanism", result["verdict"])
        self.assertIn("stored_status", result["verdict"])

    def test_verdict_include_on_wired_node(self):
        from manifold import writes
        writes.update_node(
            self.conn, "p1", "C.1",
            {"verdict_mechanism": "human_signoff", "verdict_status": "satisfied"},
            expected_revision_id=queries.get_node(self.conn, "p1", "C.1")["current_revision_id"],
            actor="h", change_reason="evolution",
        )
        result = queries.peek_node_full(self.conn, "p1", "C.1", include=("verdict",))
        self.assertEqual(result["verdict"]["mechanism"], "human_signoff")
        self.assertEqual(result["verdict"]["stored_status"], "satisfied")

    def test_include_children(self):
        result = queries.peek_node_full(self.conn, "p1", "I.1", include=("children",))
        self.assertEqual(len(result["children"]), 1)
        self.assertEqual(result["children"][0]["node_id"], "C.1")

    def test_returns_none_when_missing(self):
        result = queries.peek_node_full(self.conn, "p1", "nope")
        self.assertIsNone(result)


class TestNextLeavesComputedVerdict(unittest.TestCase):
    def test_project_root_attaches_computed_status(self):
        import tempfile
        from pathlib import Path
        from manifold import writes

        conn, _ = fresh_db(self)
        seed_project(conn, "p1", layers=[
            {"name": "intent"}, {"name": "realizations"},
        ])
        writes.create_node(conn, "p1", "intent", "I.1", "root", actor="h")
        writes.create_node(
            conn, "p1", "realizations", "R.1", "leaf",
            parents=["I.1"], target_status="planned", actor="h",
        )
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "exists.txt").write_text("ok", encoding="utf-8")
            rev = queries.get_node(conn, "p1", "R.1")["current_revision_id"]
            writes.update_node(
                conn, "p1", "R.1",
                {
                    "verdict_mechanism": "python_assertion",
                    "verdict_assertion": "file_exists('exists.txt')",
                },
                expected_revision_id=rev,
                actor="h",
                change_reason="evolution",
            )
            leaves = queries.next_leaves(conn, "p1", project_root=tmp)
            self.assertEqual(len(leaves), 1)
            self.assertEqual(leaves[0]["computed_verdict_status"], "satisfied")

        bare = queries.next_leaves(conn, "p1")
        self.assertNotIn("computed_verdict_status", bare[0])


class TestProjectDashboardStats(unittest.TestCase):
    def setUp(self):
        from manifold import writes
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[
            {"name": "intent"}, {"name": "realizations"}])
        writes.create_node(self.conn, "p1", "intent", "I.1", "Top",
                            actor="h")
        writes.create_node(self.conn, "p1", "realizations", "R.1", "Real",
                            parents=["I.1"], actor="h")

    def test_returns_six_keys(self):
        s = queries.project_dashboard_stats(self.conn, "p1")
        for k in ("nodes_per_layer", "target_distribution",
                   "verdict_distribution", "last_modified",
                   "last_validation", "revisions_7d"):
            self.assertIn(k, s)

    def test_nodes_per_layer_counts(self):
        s = queries.project_dashboard_stats(self.conn, "p1")
        per = {r["layer"]: r["count"] for r in s["nodes_per_layer"]}
        self.assertEqual(per["intent"], 1)
        self.assertEqual(per["realizations"], 1)

    def test_revisions_7d_counts(self):
        s = queries.project_dashboard_stats(self.conn, "p1")
        self.assertEqual(s["revisions_7d"], 2)

    def test_last_modified_returns_node(self):
        s = queries.project_dashboard_stats(self.conn, "p1")
        self.assertIsNotNone(s["last_modified"])
        self.assertIn(s["last_modified"]["node_id"], {"I.1", "R.1"})

    def test_empty_project(self):
        seed_project(self.conn, "empty")
        s = queries.project_dashboard_stats(self.conn, "empty")
        self.assertEqual(s["nodes_per_layer"], [])
        self.assertEqual(s["revisions_7d"], 0)
        self.assertIsNone(s["last_modified"])
        self.assertIsNone(s["last_validation"])

    def test_last_validation_after_run(self):
        from manifold import writes
        writes.run_validation(self.conn, "p1", actor="h")
        s = queries.project_dashboard_stats(self.conn, "p1")
        self.assertIsNotNone(s["last_validation"])
        self.assertEqual(s["last_validation"]["status"], "finished")


# ============================================================
# spec_audit_flagged_revisions
# ============================================================

def _insert_revision(conn, project_id, node_id, ts, change_reason=None,
                     change_summary=None):
    """Insert a minimal revision row directly via SQL."""
    conn.execute(
        "INSERT INTO revisions (project_id, node_id, ts, change_type, "
        "snapshot, source, actor, change_summary, change_reason) "
        "VALUES (?, ?, ?, 'updated', '{}', 'test', 'human:test', ?, ?)",
        (project_id, node_id, ts, change_summary, change_reason),
    )


class TestSpecAuditFlagged(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p")
        _insert_node(self.conn, "p", "I.1", "intent")
        # Seed revisions with various change_reason values
        _insert_revision(self.conn, "p", "I.1", "2026-01-02T00:00:00Z",
                         change_reason="pivot", change_summary="scope crept")
        _insert_revision(self.conn, "p", "I.1", "2026-01-03T00:00:00Z",
                         change_reason="clarification", change_summary="clarified wording")
        _insert_revision(self.conn, "p", "I.1", "2026-01-04T00:00:00Z",
                         change_reason=None, change_summary="no reason given")
        _insert_revision(self.conn, "p", "I.1", "2026-01-05T00:00:00Z",
                         change_reason="", change_summary="empty reason")
        _insert_revision(self.conn, "p", "I.1", "2026-01-06T00:00:00Z",
                         change_reason="other", change_summary="miscellaneous")
        _insert_revision(self.conn, "p", "I.1", "2026-01-07T00:00:00Z",
                         change_reason="evolution", change_summary="planned change")

    def test_spec_audit_flagged_revisions_excludes_clarification_and_evolution(self):
        rows = queries.spec_audit_flagged_revisions(self.conn, "p")
        reasons = [r["change_reason"] for r in rows]
        self.assertNotIn("clarification", reasons)
        self.assertNotIn("evolution", reasons)

    def test_spec_audit_flagged_revisions_includes_pivot_null_and_empty(self):
        rows = queries.spec_audit_flagged_revisions(self.conn, "p")
        reasons = [r["change_reason"] for r in rows]
        self.assertTrue(any(r == "pivot" for r in reasons))
        self.assertTrue(any(r is None for r in reasons))
        self.assertTrue(any(r == "" for r in reasons))

    def test_spec_audit_flagged_revisions_includes_other_by_default(self):
        rows = queries.spec_audit_flagged_revisions(self.conn, "p")
        reasons = [r["change_reason"] for r in rows]
        self.assertIn("other", reasons)

    def test_spec_audit_flagged_revisions_excludes_other_when_flag_false(self):
        rows = queries.spec_audit_flagged_revisions(self.conn, "p", include_other=False)
        reasons = [r["change_reason"] for r in rows]
        self.assertNotIn("other", reasons)

    def test_spec_audit_flagged_revisions_since_filter(self):
        rows = queries.spec_audit_flagged_revisions(self.conn, "p", since="2026-01-05T00:00:00Z")
        # Only revisions at or after 2026-01-05 should be returned
        # drift (Jan 2), null (Jan 4) should be excluded; empty (Jan 5), other (Jan 6) in range
        for r in rows:
            self.assertGreaterEqual(r["ts"], "2026-01-05T00:00:00Z")

    def test_spec_audit_flagged_revisions_ordered_newest_first(self):
        rows = queries.spec_audit_flagged_revisions(self.conn, "p")
        timestamps = [r["ts"] for r in rows]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))

    def test_spec_audit_flagged_revisions_returns_dicts(self):
        rows = queries.spec_audit_flagged_revisions(self.conn, "p")
        for r in rows:
            self.assertIsInstance(r, dict)
            self.assertIn("change_reason", r)

    def test_spec_audit_flagged_revisions_all_reasons_valid(self):
        """All returned rows must have change_reason in {pivot, other, '', None}."""
        rows = queries.spec_audit_flagged_revisions(self.conn, "p")
        for r in rows:
            self.assertIn(r["change_reason"], ("pivot", "drift", "other", "", None))

    def test_spec_audit_flagged_revisions_wrong_project_returns_empty(self):
        rows = queries.spec_audit_flagged_revisions(self.conn, "nonexistent")
        self.assertEqual(rows, [])


# ============================================================
# spec_audit_unclarified_rationale
# ============================================================

class TestRationaleChangesWithoutClarification(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p")
        _insert_node(self.conn, "p", "I.1", "intent")
        # rationale changed, reason is drift — should be returned
        _insert_revision(self.conn, "p", "I.1", "2026-01-02T00:00:00Z",
                         change_reason="pivot",
                         change_summary="updated rationale for intent")
        # rationale mentioned, but reason is clarification — should NOT be returned
        _insert_revision(self.conn, "p", "I.1", "2026-01-03T00:00:00Z",
                         change_reason="clarification",
                         change_summary="clarified rationale wording")
        # rationale mentioned, but reason is correction — should NOT be returned
        _insert_revision(self.conn, "p", "I.1", "2026-01-04T00:00:00Z",
                         change_reason="correction",
                         change_summary="fixed rationale typo")
        # no rationale in change_summary — should NOT be returned
        _insert_revision(self.conn, "p", "I.1", "2026-01-05T00:00:00Z",
                         change_reason="evolution",
                         change_summary="changed title only")
        # rationale changed, no reason set — should be returned
        _insert_revision(self.conn, "p", "I.1", "2026-01-06T00:00:00Z",
                         change_reason=None,
                         change_summary="rationale was overhauled")

    def test_includes_rationale_change_with_drift_reason(self):
        rows = queries.spec_audit_unclarified_rationale(self.conn, "p")
        summaries = [r["change_summary"] for r in rows]
        self.assertIn("updated rationale for intent", summaries)

    def test_excludes_clarification_reason(self):
        rows = queries.spec_audit_unclarified_rationale(self.conn, "p")
        for r in rows:
            self.assertNotEqual(r["change_reason"], "clarification")

    def test_excludes_correction_reason(self):
        rows = queries.spec_audit_unclarified_rationale(self.conn, "p")
        for r in rows:
            self.assertNotEqual(r["change_reason"], "correction")

    def test_excludes_non_rationale_changes(self):
        rows = queries.spec_audit_unclarified_rationale(self.conn, "p")
        summaries = [r["change_summary"] for r in rows]
        self.assertNotIn("changed title only", summaries)

    def test_includes_null_reason_with_rationale_change(self):
        rows = queries.spec_audit_unclarified_rationale(self.conn, "p")
        summaries = [r["change_summary"] for r in rows]
        self.assertIn("rationale was overhauled", summaries)

    def test_since_filter_applied(self):
        rows = queries.spec_audit_unclarified_rationale(
            self.conn, "p", since="2026-01-05T00:00:00Z")
        for r in rows:
            self.assertGreaterEqual(r["ts"], "2026-01-05T00:00:00Z")

    def test_returns_dicts(self):
        rows = queries.spec_audit_unclarified_rationale(self.conn, "p")
        for r in rows:
            self.assertIsInstance(r, dict)
            self.assertIn("change_reason", r)

    def test_wrong_project_returns_empty(self):
        rows = queries.spec_audit_unclarified_rationale(self.conn, "nonexistent")
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
