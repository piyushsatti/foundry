"""
Tests for the manifold MCP server.
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pathsetup  # noqa: F401, E402

from manifold import queries, writes
from pathsetup import fresh_db, seed_portfolio_fixture, seed_project
from server import mcp_server


def _call(conn, method, params=None):
    req = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    return mcp_server.handle(req, conn)


def _tool_call(conn, name, args=None):
    return _call(conn, "tools/call", {"name": name, "arguments": args or {}})


def _result_payload(resp):
    """Extract the structured payload from a tools/call response.

    The MCP shape is: result.content[0].text is JSON-encoded.
    """
    self_text = resp["result"]["content"][0]["text"]
    return json.loads(self_text)


# ============================================================
# Protocol surface
# ============================================================

class TestProtocol(unittest.TestCase):
    def test_initialize(self):
        conn, _ = fresh_db(self)
        r = _call(conn, "initialize")
        self.assertIn("result", r)
        self.assertEqual(r["result"]["serverInfo"]["name"], "manifold")
        self.assertIn("tools", r["result"]["capabilities"])

    def test_notifications_initialized_returns_none(self):
        conn, _ = fresh_db(self)
        r = _call(conn, "notifications/initialized")
        self.assertIsNone(r)

    def test_method_not_found(self):
        conn, _ = fresh_db(self)
        r = _call(conn, "bogus/method")
        self.assertIn("error", r)
        self.assertEqual(r["error"]["code"], -32601)

    def test_tools_list_returns_all(self):
        conn, _ = fresh_db(self)
        r = _call(conn, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        self.assertEqual(len(names), 46,
                         msg=f"expected 46 tools; got {len(names)}: {names}")
        # Read sample
        for expected in ["list_projects", "peek_node", "peek_node_full",
                          "list_blocking_chain", "list_cross_blocking_chain",
                          "list_changes_since", "diff_revisions", "resolve_node",
                          "portfolio_report", "list_cross_edges", "peek_trajectory"]:
            self.assertIn(expected, names)
        # Write sample
        for expected in ["create_node", "update_node", "transition_target",
                          "revert", "with_batch", "soft_delete_node",
                          "restore_node", "archive_project", "unarchive_project",
                          "register_project", "import_project", "run_validation",
                          "link_portfolio", "create_cross_edge",
                          "propose_trajectory", "accept_trajectory_leg",
                          "reject_trajectory"]:
            self.assertIn(expected, names)

    def test_all_tools_have_well_formed_schemas(self):
        conn, _ = fresh_db(self)
        r = _call(conn, "tools/list")
        for t in r["result"]["tools"]:
            self.assertIn("name", t)
            self.assertIn("description", t)
            self.assertIn("inputSchema", t)
            schema = t["inputSchema"]
            self.assertEqual(schema.get("type"), "object",
                              msg=f"tool {t['name']} schema not object-typed")
            self.assertIsInstance(schema.get("properties", {}), dict)


# ============================================================
# Tool dispatch — read
# ============================================================

class TestReadToolsDispatch(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "root",
                            body="root body", actor="h")
        writes.create_node(self.conn, "p1", "realizations", "R.1", "child",
                            parents=["I.1"], actor="h")

    def test_list_projects(self):
        r = _tool_call(self.conn, "list_projects")
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(len(payload["projects"]), 1)

    def test_peek_node(self):
        r = _tool_call(self.conn, "peek_node",
                        {"project_id": "p1", "node_id": "I.1"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["node"]["title"], "root")

    def test_peek_node_not_found_returns_envelope(self):
        r = _tool_call(self.conn, "peek_node",
                        {"project_id": "p1", "node_id": "MISSING"})
        self.assertTrue(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["error"]["code"], "NODE_NOT_FOUND")

    def test_peek_node_full_includes_children(self):
        r = _tool_call(self.conn, "peek_node_full",
                        {"project_id": "p1", "node_id": "I.1",
                         "include": ["children", "parents"]})
        payload = _result_payload(r)
        self.assertIn("children", payload["node"])
        self.assertEqual(len(payload["node"]["children"]), 1)

    def test_peek_node_full_default_includes_verdict(self):
        r = _tool_call(self.conn, "peek_node_full",
                        {"project_id": "p1", "node_id": "I.1"})
        payload = _result_payload(r)
        self.assertIn("verdict", payload["node"])

    def test_list_blocking_chain(self):
        r = _tool_call(self.conn, "list_blocking_chain",
                        {"project_id": "p1", "node_id": "I.1"})
        payload = _result_payload(r)
        self.assertEqual(payload["chain"], [])

    def test_list_changes_since_requires_filter(self):
        r = _tool_call(self.conn, "list_changes_since",
                        {"project_id": "p1"})
        self.assertTrue(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["error"]["code"], "INVALID_ARGUMENTS")

    def test_resolve_node(self):
        r = _tool_call(self.conn, "resolve_node",
                        {"project_id": "p1", "query": "I"})
        payload = _result_payload(r)
        self.assertIn("I.1", payload["node_ids"])


# ============================================================
# Tool dispatch — write + error envelope
# ============================================================

class TestWriteToolsDispatch(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")

    def test_create_node_returns_revision_id(self):
        r = _tool_call(self.conn, "create_node",
                        {"project_id": "p1", "layer": "intent",
                         "node_id": "I.1", "title": "x", "actor": "h"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertIn("revision_id", payload)

    def test_create_node_duplicate_returns_envelope(self):
        _tool_call(self.conn, "create_node",
                    {"project_id": "p1", "layer": "intent",
                     "node_id": "I.1", "title": "x", "actor": "h"})
        r = _tool_call(self.conn, "create_node",
                        {"project_id": "p1", "layer": "intent",
                         "node_id": "I.1", "title": "x", "actor": "h"})
        self.assertTrue(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["error"]["code"], "NODE_ALREADY_EXISTS")

    def test_create_node_missing_actor_envelope(self):
        r = _tool_call(self.conn, "create_node",
                        {"project_id": "p1", "layer": "intent",
                         "node_id": "I.1", "title": "x", "actor": ""})
        self.assertTrue(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["error"]["code"], "MISSING_ACTOR")

    def test_update_node_stale_revision_envelope(self):
        r1 = _tool_call(self.conn, "create_node",
                         {"project_id": "p1", "layer": "intent",
                          "node_id": "I.1", "title": "x", "actor": "h"})
        rev = _result_payload(r1)["revision_id"]
        r = _tool_call(self.conn, "update_node",
                        {"project_id": "p1", "node_id": "I.1",
                         "fields": {"title": "y"},
                         "expected_revision_id": rev + 999,
                         "change_reason": "evolution",
                         "actor": "h"})
        self.assertTrue(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["error"]["code"], "STALE_REVISION")
        self.assertEqual(payload["error"]["retry"], "with_new_args")
        self.assertEqual(payload["error"]["context"]["current_revision_id"], rev)

    def test_transition_target_invalid_returns_envelope(self):
        # explicitly create with target_status="" so the "" → achieved
        # path can be exercised (which is invalid by the state machine)
        r1 = _tool_call(self.conn, "create_node",
                         {"project_id": "p1", "layer": "intent",
                          "node_id": "I.1", "title": "x",
                          "target_status": "", "actor": "h"})
        rev = _result_payload(r1)["revision_id"]
        # Try to jump straight to 'achieved' from '' (invalid)
        r = _tool_call(self.conn, "transition_target",
                        {"project_id": "p1", "node_id": "I.1",
                         "to_status": "achieved",
                         "expected_revision_id": rev, "actor": "h"})
        self.assertTrue(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["error"]["code"], "INVALID_TRANSITION")

    def test_with_batch_three_ops(self):
        ops = [{"op": "create_node",
                 "args": {"project_id": "p1", "layer": "intent",
                          "node_id": f"I.{i}", "title": f"n{i}"}}
                for i in (1, 2, 3)]
        r = _tool_call(self.conn, "with_batch",
                        {"label": "three", "ops": ops, "actor": "h"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(len(payload["revision_ids"]), 3)

    def test_unknown_tool_returns_envelope(self):
        r = _tool_call(self.conn, "no_such_tool", {})
        self.assertTrue(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["error"]["code"], "UNKNOWN_TOOL")


class TestNextLeavesTool(unittest.TestCase):
    """Tests for the next_leaves MCP tool."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[
            {"name": "intents"}, {"name": "realizations"}])
        writes.create_node(self.conn, "p1", "intents", "I.1", "intent 1",
                            actor="h")
        writes.create_node(self.conn, "p1", "realizations", "R.1", "real 1",
                            parents=["I.1"], actor="h")

    def test_next_leaves_tool_registered(self):
        r = _call(self.conn, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        self.assertIn("next_leaves", names)

    def test_next_leaves_returns_leaves(self):
        r = _tool_call(self.conn, "next_leaves",
                        {"project_id": "p1"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertIn("leaves", payload)
        node_ids = [n["node_id"] for n in payload["leaves"]]
        self.assertIn("R.1", node_ids)
        self.assertNotIn("I.1", node_ids)

    def test_next_leaves_layer_filter(self):
        r = _tool_call(self.conn, "next_leaves",
                        {"project_id": "p1", "layer": "intents"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["leaves"], [])

    def test_next_leaves_well_formed_schema(self):
        r = _call(self.conn, "tools/list")
        tool = next((t for t in r["result"]["tools"] if t["name"] == "next_leaves"), None)
        self.assertIsNotNone(tool)
        self.assertIn("project_id", tool["inputSchema"]["required"])
        self.assertIn("project_id", tool["inputSchema"]["properties"])
        self.assertIn("layer", tool["inputSchema"]["properties"])


class TestSpecAuditReportTool(unittest.TestCase):
    """Tests for the spec_audit MCP tool."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[{"name": "L0"}])
        writes.create_node(self.conn, "p1", "L0", "A", "node A", actor="h")
        n = self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id='A'"
        ).fetchone()
        writes.update_node(self.conn, "p1", "A", {"title": "A v2"},
                            expected_revision_id=n["current_revision_id"],
                            change_reason="pivot", actor="h")

    def test_spec_audit_tool_registered(self):
        r = _call(self.conn, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        self.assertIn("spec_audit", names)

    def test_spec_audit_returns_both_keys(self):
        r = _tool_call(self.conn, "spec_audit",
                        {"project_id": "p1"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertIn("flagged_revisions", payload)
        self.assertIn("unclarified_rationale_changes", payload)

    def test_spec_audit_finds_drift_revision(self):
        r = _tool_call(self.conn, "spec_audit",
                        {"project_id": "p1"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        reasons = [rev.get("change_reason") for rev in payload["flagged_revisions"]]
        self.assertIn("pivot", reasons)

    def test_spec_audit_since_filter(self):
        r = _tool_call(self.conn, "spec_audit",
                        {"project_id": "p1", "since": "2099-01-01T00:00:00Z"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertEqual(payload["flagged_revisions"], [])

    def test_spec_audit_unclarified_rationale_changes_is_list(self):
        r = _tool_call(self.conn, "spec_audit",
                        {"project_id": "p1"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertIsInstance(payload["unclarified_rationale_changes"], list)

    def test_spec_audit_well_formed_schema(self):
        r = _call(self.conn, "tools/list")
        tool = next((t for t in r["result"]["tools"] if t["name"] == "spec_audit"), None)
        self.assertIsNotNone(tool)
        self.assertIn("project_id", tool["inputSchema"]["required"])
        self.assertIn("project_id", tool["inputSchema"]["properties"])
        self.assertIn("since", tool["inputSchema"]["properties"])


def _patch_verdict(conn, project_id, node_id, fields, *, actor="h"):
    rev = queries.get_node(conn, project_id, node_id)["current_revision_id"]
    writes.update_node(
        conn, project_id, node_id, fields,
        expected_revision_id=rev, actor=actor, change_reason="evolution",
    )


class TestMCPDriftReport(unittest.TestCase):
    """Tests for the drift_report MCP tool."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "Intent", actor="h")
        writes.create_node(
            self.conn, "p1", "realizations", "R.bad", "Violated node",
            parents=["I.1"], actor="h",
        )
        _patch_verdict(self.conn, "p1", "R.bad", {
            "verdict_mechanism": "automated_check",
            "verdict_check": "false",
        })

    def test_drift_report_tool_registered(self):
        r = _call(self.conn, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        self.assertIn("drift_report", names)

    def test_drift_report_returns_expected_keys(self):
        r = _tool_call(self.conn, "drift_report", {"project_id": "p1", "force": True})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertIn("summary", payload)
        self.assertIn("violated", payload)
        self.assertIn("unverified", payload)
        self.assertIn("project_id", payload)
        self.assertEqual(payload["project_id"], "p1")

    def test_drift_report_finds_violated_node(self):
        r = _tool_call(self.conn, "drift_report", {"project_id": "p1", "force": True})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        violated_ids = [f["node_id"] for f in payload["violated"]]
        self.assertIn("R.bad", violated_ids)

    def test_drift_report_well_formed_schema(self):
        r = _call(self.conn, "tools/list")
        tool = next((t for t in r["result"]["tools"] if t["name"] == "drift_report"), None)
        self.assertIsNotNone(tool)
        self.assertIn("project_id", tool["inputSchema"]["required"])
        self.assertIn("project_id", tool["inputSchema"]["properties"])
        self.assertIn("project_root", tool["inputSchema"]["properties"])
        self.assertIn("layer", tool["inputSchema"]["properties"])
        self.assertIn("all_layers", tool["inputSchema"]["properties"])
        self.assertIn("force", tool["inputSchema"]["properties"])


class TestPortfolioCrossToolsDispatch(unittest.TestCase):
    """MCP handler tests for portfolio + cross-project tools (Topic H+I)."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)
        self.conn.commit()

    def test_link_and_list_portfolio_links(self):
        r = _tool_call(self.conn, "list_portfolio_links", {"theme_node_id": "T.1"})
        self.assertFalse(r["result"]["isError"])
        payload = _result_payload(r)
        self.assertGreaterEqual(len(payload["links"]), 4)

    def test_unlink_portfolio(self):
        r = _tool_call(self.conn, "unlink_portfolio", {
            "theme_node_id": "T.1",
            "project_id": "pipeline",
            "node_id": "I.2",
            "actor": "h",
        })
        self.assertFalse(r["result"]["isError"])
        listed = _result_payload(_tool_call(
            self.conn, "list_portfolio_links", {"theme_node_id": "T.1"}))
        refs = {(l["project_id"], l["node_id"]) for l in listed["links"]}
        self.assertNotIn(("pipeline", "I.2"), refs)

    def test_create_cross_edge_and_list(self):
        r = _tool_call(self.conn, "create_cross_edge", {
            "src_project_id": "pipeline",
            "src_node_id": "I.2",
            "dst_project_id": "ai-platform",
            "dst_node_id": "C.4",
            "edge_kind": "depends_on",
            "actor": "h",
        })
        self.assertFalse(r["result"]["isError"])
        listed = _result_payload(_tool_call(
            self.conn, "list_cross_edges", {"project_id": "pipeline"}))
        kinds = {e["edge_kind"] for e in listed["edges"]}
        self.assertIn("depends_on", kinds)

    def test_create_cross_edge_rejects_self_edge(self):
        r = _tool_call(self.conn, "create_cross_edge", {
            "src_project_id": "product-app",
            "src_node_id": "R.12",
            "dst_project_id": "product-app",
            "dst_node_id": "R.12",
            "edge_kind": "blocks",
            "actor": "h",
        })
        self.assertTrue(r["result"]["isError"])

    def test_list_cross_blocking_chain(self):
        r = _tool_call(self.conn, "list_cross_blocking_chain", {
            "project_id": "product-app",
            "node_id": "R.12",
        })
        payload = _result_payload(r)
        self.assertEqual(payload["chain"][0]["node_ref"], "ai-platform/C.4")

    def test_delete_cross_edge(self):
        _tool_call(self.conn, "delete_cross_edge", {
            "src_project_id": "product-app",
            "src_node_id": "R.12",
            "dst_project_id": "ai-platform",
            "dst_node_id": "C.4",
            "edge_kind": "blocks",
            "actor": "h",
        })
        chain = _result_payload(_tool_call(
            self.conn, "list_cross_blocking_chain", {
                "project_id": "product-app", "node_id": "R.12"}))
        self.assertEqual(chain["chain"], [])

    def test_portfolio_report_blocked_by(self):
        r = _tool_call(self.conn, "portfolio_report", {})
        payload = _result_payload(r)
        link = next(
            l for l in payload["themes"][0]["links"]
            if l["node_id"] == "R.12"
        )
        self.assertEqual(link["blocked_by"], ["ai-platform/C.4"])

    def test_next_leaves_include_excluded(self):
        r = _tool_call(self.conn, "next_leaves", {
            "project_id": "product-app",
            "include_excluded": True,
        })
        payload = _result_payload(r)
        excluded_ids = [row["node_id"] for row in payload["excluded"]]
        self.assertIn("R.12", excluded_ids)
        self.assertEqual(payload["excluded"][0]["blocked_by"], ["ai-platform/C.4"])


class TestMCPTrajectory(unittest.TestCase):
    """Tests for propose_trajectory, peek_trajectory, accept_trajectory_leg."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "Intent", actor="h")
        writes.create_node(
            self.conn, "p1", "realizations", "R.1", "Leaf",
            parents=["I.1"], target_status="planned", actor="h",
        )
        self.conn.commit()

    def test_trajectory_tools_registered(self):
        r = _call(self.conn, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        for name in ("propose_trajectory", "peek_trajectory", "accept_trajectory_leg",
                     "reject_trajectory"):
            self.assertIn(name, names)

    def test_reject_draft_trajectory(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "achieved"},
        }]
        r = _tool_call(self.conn, "propose_trajectory", {
            "project_id": "p1",
            "target_brief": "brief",
            "legs": legs,
            "proposed_by": "agent:test",
        })
        tid = _result_payload(r)["trajectory_id"]
        self.conn.commit()

        r = _tool_call(self.conn, "reject_trajectory", {
            "trajectory_id": tid,
            "actor": "agent:test",
        })
        self.assertFalse(r["result"]["isError"])
        self.assertEqual(_result_payload(r)["status"], "rejected")

    def test_propose_peek_accept_flow(self):
        legs = [{
            "leg_kind": "transition_target",
            "payload": {"node_id": "R.1", "to_status": "achieved"},
        }]
        r = _tool_call(self.conn, "propose_trajectory", {
            "project_id": "p1",
            "target_brief": "Achieve R.1",
            "legs": legs,
            "proposed_by": "agent:test",
        })
        self.assertFalse(r["result"]["isError"])
        prop = _result_payload(r)
        tid = prop["trajectory_id"]
        self.conn.commit()

        r = _tool_call(self.conn, "peek_trajectory", {"trajectory_id": tid})
        self.assertFalse(r["result"]["isError"])
        peek = _result_payload(r)
        self.assertIn("impact_preview", peek)
        self.assertEqual(len(peek["impact_preview"]["next_leaves_after"]), 0)

        r = _tool_call(self.conn, "accept_trajectory_leg", {
            "trajectory_id": tid,
            "actor": "agent:test",
        })
        self.assertFalse(r["result"]["isError"])
        self.conn.commit()

        leaves = queries.next_leaves(self.conn, "p1")
        self.assertEqual(len(leaves), 0)


class TestMCPPresentation(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)
        self.conn.commit()

    def test_peek_diagram_and_mindmap_registered(self):
        r = _call(self.conn, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        self.assertIn("peek_diagram", names)
        self.assertIn("peek_mindmap", names)

    def test_peek_diagram_blockers(self):
        r = _tool_call(self.conn, "peek_diagram", {
            "project_id": "product-app",
            "diagram_type": "blockers",
            "focus_node_id": "R.12",
        })
        self.assertFalse(r["result"]["isError"])
        view = _result_payload(r)
        self.assertEqual(view["diagram_type"], "blockers")
        refs = {n["node_ref"] for n in view["nodes"]}
        self.assertIn("ai-platform/C.4", refs)

    def test_peek_mindmap_tree(self):
        r = _tool_call(self.conn, "peek_mindmap", {
            "project_id": "product-app",
            "focus_node_id": "I.1",
        })
        self.assertFalse(r["result"]["isError"])
        view = _result_payload(r)
        self.assertIsNotNone(view.get("tree"))

    def test_list_presentation_views(self):
        r = _tool_call(self.conn, "list_presentation_views", {})
        self.assertFalse(r["result"]["isError"])
        views = _result_payload(r)["views"]
        ids = {v["view_id"] for v in views}
        self.assertIn("blockers", ids)

    def test_peek_diagram_by_view_id(self):
        r = _tool_call(self.conn, "peek_diagram", {
            "project_id": "product-app",
            "view_id": "blockers",
            "focus_node_id": "R.12",
        })
        view = _result_payload(r)
        self.assertEqual(view["view_id"], "blockers")


class TestMCPStatusBrief(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)
        self.conn.commit()

    def test_peek_status_brief_registered(self):
        r = _call(self.conn, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        self.assertIn("peek_status_brief", names)

    def test_peek_status_brief_blocked(self):
        r = _tool_call(self.conn, "peek_status_brief", {"project_id": "product-app"})
        self.assertFalse(r["result"]["isError"])
        view = _result_payload(r)
        self.assertEqual(view["overall"]["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
