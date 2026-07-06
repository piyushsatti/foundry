"""
Unit tests for the manifold web server handlers.

Calls handler functions directly (no socket binding). The smoke test
(test_smoke_http_server.py) runs the full server as a subprocess.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pathsetup  # noqa: F401, E402

from manifold import queries, writes, config as _config
from manifold_web import html, web
from pathsetup import fresh_db, seed_portfolio_fixture, seed_project

# Hermetic config: ensure load_config() never touches the real
# ~/.claude/manifold.json when _resolve_judge_command is called via run_validation.
_MANIFOLD_CONFIG_OVERRIDE = os.path.join(
    tempfile.gettempdir(), "manifold-test-web-nonexistent.json"
)


def setUpModule():
    os.environ["MANIFOLD_CONFIG"] = _MANIFOLD_CONFIG_OVERRIDE
    _config._reset_config_cache()


def tearDownModule():
    os.environ.pop("MANIFOLD_CONFIG", None)
    _config._reset_config_cache()


def _mock_handler(conn):
    """Build a fake request handler exposing only what the handlers need."""
    h = MagicMock()
    h.server.conn = conn
    h.server.verbose = False
    return h


class TestHTMLHandlers(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", label="P1")
        # start from "" so legacy "no targets" + "transition to planned" tests work
        writes.create_node(self.conn, "p1", "intent", "I.1", "root",
                            body="# I.1\n\nroot body.", target_status="", actor="h")

    def test_index_lists_project(self):
        html, status = web.html_index(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn("p1", html)
        self.assertIn("Projects", html)

    def test_project_page_shows_node(self):
        html, status = web.html_project(_mock_handler(self.conn),
                                          {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("I.1", html)
        self.assertIn("root", html)
        self.assertIn("/projects/p1/brief", html)
        self.assertIn("/projects/p1/mindmap", html)
        self.assertIn("viz-nav", html)
        self.assertIn("/projects/p1/views/decomposition", html)

    def test_project_404(self):
        html, status = web.html_project(_mock_handler(self.conn),
                                          {"project_id": "missing"}, {})
        self.assertEqual(status, 404)

    def test_node_page_renders_body(self):
        html, status = web.html_node(_mock_handler(self.conn),
                                       {"project_id": "p1", "node_id": "I.1"}, {})
        self.assertEqual(status, 200)
        # Body markdown rendered to HTML
        self.assertIn("<h1>I.1</h1>", html)
        self.assertIn("<p>root body.</p>", html)
        # Edit link
        self.assertIn("/projects/p1/nodes/I.1/edit", html)

    def test_node_edit_get_includes_codemirror(self):
        html, status = web.html_node_edit_get(_mock_handler(self.conn),
                                                {"project_id": "p1", "node_id": "I.1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("/static/codemirror/codemirror.min.js", html)
        self.assertIn("/static/codemirror/mode/markdown/markdown.min.js", html)
        self.assertIn("expected_revision_id", html)
        # Body content is in the textarea
        self.assertIn("root body.", html)

    def test_targets_empty(self):
        html, status = web.html_targets(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn("No targets", html)

    def test_targets_with_match(self):
        # Mark I.1 as planned
        node = self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id = 'I.1'"
        ).fetchone()
        writes.transition_target(self.conn, "p1", "I.1", "planned",
                                  expected_revision_id=node["current_revision_id"],
                                  actor="h")
        html, status = web.html_targets(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn("I.1", html)
        self.assertIn("planned", html)


class TestAPIHandlers(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "root",
                            body="body", actor="h")

    def test_api_list_projects(self):
        payload, status = web.api_list_projects(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["projects"]), 1)

    def test_api_get_node(self):
        payload, status = web.api_get_node(_mock_handler(self.conn),
                                             {"project_id": "p1", "node_id": "I.1"}, {})
        self.assertEqual(status, 200)
        self.assertEqual(payload["title"], "root")

    def test_api_get_node_404(self):
        payload, status = web.api_get_node(_mock_handler(self.conn),
                                             {"project_id": "p1", "node_id": "miss"}, {})
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "NODE_NOT_FOUND")

    def test_api_run_validation(self):
        h = _mock_handler(self.conn)
        h._json_body.return_value = {"actor": "human:tester"}
        payload, status = web.api_run_validation(
            h, {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "finished")
        self.assertIn("validation_id", payload)
        self.assertIn("issues", payload)

    def test_api_get_validation(self):
        h = _mock_handler(self.conn)
        h._json_body.return_value = {"actor": "human:tester"}
        ran, _ = web.api_run_validation(h, {"project_id": "p1"}, {})
        payload, status = web.api_get_validation(
            _mock_handler(self.conn),
            {"project_id": "p1", "validation_id": str(ran["validation_id"])},
            {},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["validation"]["status"], "finished")
        self.assertIn("verdicts", payload)

    def test_api_register_project(self):
        h = _mock_handler(self.conn)
        h._json_body.return_value = {
            "project_id": "new",
            "spec_config": {"layers": [{"name": "intent"}]},
            "label": "New",
        }
        payload, status = web.api_register_project(h, {}, {})
        self.assertEqual(status, 200)
        self.assertEqual(payload["project_id"], "new")
        self.assertTrue(payload["created"])

    def test_api_register_project_missing_id(self):
        h = _mock_handler(self.conn)
        h._json_body.return_value = {}
        payload, status = web.api_register_project(h, {}, {})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "INVALID_ARGUMENTS")


class TestContentTypes(unittest.TestCase):
    def test_static_content_types(self):
        self.assertEqual(web._guess_content_type("x.js"),
                          "application/javascript; charset=utf-8")
        self.assertEqual(web._guess_content_type("x.css"),
                          "text/css; charset=utf-8")
        self.assertEqual(web._guess_content_type("unknown.bin"),
                          "application/octet-stream")


# ============================================================
# dashboard + diff + validation + structural editor
# ============================================================

class TestProjectPageDashboard(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", label="P1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "root",
                            body="root body.", actor="h")

    def test_dashboard_cards_render(self):
        html, status = web.html_project(_mock_handler(self.conn),
                                          {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("Nodes per layer", html)
        self.assertIn("Target status", html)
        self.assertIn("Verdict status", html)
        self.assertIn("Last modified", html)
        self.assertIn("Last validation", html)
        self.assertIn("Revisions (7d)", html)

    def test_trigger_form_present(self):
        html, status = web.html_project(_mock_handler(self.conn),
                                          {"project_id": "p1"}, {})
        self.assertIn('action="/projects/p1/validations"', html)
        self.assertIn("Run validation", html)


class TestRevisionDetail(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "v1",
                            body="first body", actor="h")
        node = self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id='I.1'"
        ).fetchone()
        self.rev1 = node["current_revision_id"]
        writes.update_node(self.conn, "p1", "I.1",
                            {"title": "v2", "body": "second body"},
                            expected_revision_id=self.rev1, actor="h",
                            change_reason="evolution")
        self.rev2 = self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id='I.1'"
        ).fetchone()["current_revision_id"]

    def test_renders_diff_table(self):
        html, status = web.html_revision_detail(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1",
             "revision_id": str(self.rev2)}, {})
        self.assertEqual(status, 200)
        self.assertIn("title", html)
        self.assertIn("v1", html)
        self.assertIn("v2", html)
        self.assertIn("second body", html)

    def test_unchanged_body_says_so(self):
        # Update only title (not body) → no body diff section
        writes.update_node(self.conn, "p1", "I.1",
                            {"title": "v3"},
                            expected_revision_id=self.rev2, actor="h",
                            change_reason="evolution")
        rev3 = self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id='I.1'"
        ).fetchone()["current_revision_id"]
        html, status = web.html_revision_detail(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1",
             "revision_id": str(rev3)}, {})
        self.assertEqual(status, 200)
        self.assertIn("(unchanged)", html)

    def test_404_for_missing_revision(self):
        html, status = web.html_revision_detail(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1",
             "revision_id": "9999"}, {})
        self.assertEqual(status, 404)

    def test_404_when_revision_belongs_to_other_node(self):
        html, status = web.html_revision_detail(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.999",
             "revision_id": str(self.rev2)}, {})
        self.assertEqual(status, 404)


class TestRunValidationPost(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "T", actor="h")

    def test_triggers_and_redirects(self):
        h = _mock_handler(self.conn)
        h._form_data.return_value = {"with_verdicts": "on"}
        h.client_address = ("127.0.0.1", 0)
        web.html_run_validation_post(h, {"project_id": "p1"}, {})
        # _redirect was called with /projects/p1/validations/<id>
        h._redirect.assert_called_once()
        location = h._redirect.call_args[0][0]
        self.assertTrue(location.startswith("/projects/p1/validations/"))
        # Validation row landed
        row = self.conn.execute(
            "SELECT verdicts_run, status FROM validations"
        ).fetchone()
        self.assertEqual(row["status"], "finished")
        self.assertGreater(row["verdicts_run"], 0)

    def test_with_verdicts_off_runs_structural_only(self):
        h = _mock_handler(self.conn)
        h._form_data.return_value = {}
        h.client_address = ("127.0.0.1", 0)
        web.html_run_validation_post(h, {"project_id": "p1"}, {})
        row = self.conn.execute(
            "SELECT verdicts_run FROM validations"
        ).fetchone()
        self.assertEqual(row["verdicts_run"], 0)


class TestValidationDetail(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "T", actor="h")
        result = writes.run_validation(self.conn, "p1",
                                         with_verdicts=True, actor="h")
        self.val_id = result["validation_id"]

    def test_renders_summary(self):
        html, status = web.html_validation_detail(
            _mock_handler(self.conn),
            {"project_id": "p1", "validation_id": str(self.val_id)}, {})
        self.assertEqual(status, 200)
        self.assertIn(f"Validation #{self.val_id}", html)
        self.assertIn("finished", html)
        self.assertIn("I.1", html)

    def test_404_for_missing(self):
        html, status = web.html_validation_detail(
            _mock_handler(self.conn),
            {"project_id": "p1", "validation_id": "9999"}, {})
        self.assertEqual(status, 404)


class TestStructuralEditor(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[
            {"name": "intent"}, {"name": "realizations"}])
        # start from "" so transition-from-empty tests still exercise that path
        writes.create_node(self.conn, "p1", "intent", "I.1", "Top",
                            body="orig body", target_status="", actor="h")

    def test_edit_get_renders_structural_panel(self):
        html, status = web.html_node_edit_get(_mock_handler(self.conn),
                                                {"project_id": "p1",
                                                 "node_id": "I.1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("Structural fields", html)
        self.assertIn('name="title"', html)
        self.assertIn('name="target_status"', html)
        self.assertIn('name="parents"', html)
        self.assertIn('name="layer"', html)
        self.assertIn('name="verdict_mechanism"', html)
        self.assertIn('name="change_reason"', html)

    def _post(self, fields):
        h = _mock_handler(self.conn)
        payload = dict(fields)
        if "change_reason" not in payload and any(
            k in payload for k in ("title", "body", "kind", "layer", "parents",
                                   "peers_depends_on", "verdict_mechanism",
                                   "verdict_check", "verdict_assertion",
                                   "target_achieved_when", "realized_by_external")
        ):
            payload["change_reason"] = "evolution"
        h._form_data.return_value = payload
        h.client_address = ("127.0.0.1", 0)
        return web.html_node_edit_post(
            h, {"project_id": "p1", "node_id": "I.1"}, {})

    def _current_rev(self):
        return self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id='I.1'"
        ).fetchone()["current_revision_id"]

    def test_post_changes_title(self):
        rev = self._current_rev()
        self._post({"expected_revision_id": str(rev),
                    "title": "New Title", "body": "orig body"})
        node = queries.get_node(self.conn, "p1", "I.1")
        self.assertEqual(node["title"], "New Title")

    def test_post_transitions_target_and_updates_body(self):
        rev = self._current_rev()
        self._post({"expected_revision_id": str(rev),
                    "target_status": "planned",
                    "body": "new body"})
        node = queries.get_node(self.conn, "p1", "I.1")
        self.assertEqual(node["target_status"], "planned")
        self.assertEqual(node["body"], "new body")
        # Two revisions land: one for transition, one for body
        revs = queries.list_revisions(self.conn, "p1", "I.1")
        self.assertGreaterEqual(len(revs), 3)  # create + transition + update

    def test_post_with_stale_revision_returns_409(self):
        self._post({"expected_revision_id": "999",
                    "title": "Whatever", "body": "x"})
        # Verify nothing changed
        node = queries.get_node(self.conn, "p1", "I.1")
        self.assertEqual(node["title"], "Top")

    def test_post_with_nonexistent_parent_returns_400(self):
        rev = self._current_rev()
        html, status = self._post({"expected_revision_id": str(rev),
                                     "parents": "Z.999"})
        self.assertEqual(status, 400)
        self.assertIn("nonexistent", html)

    def test_post_with_illegal_transition_returns_400(self):
        # Move to planned, then achieved, then try to go back to planned
        rev = self._current_rev()
        writes.transition_target(self.conn, "p1", "I.1", "planned",
                                  expected_revision_id=rev, actor="h")
        rev = self._current_rev()
        writes.transition_target(self.conn, "p1", "I.1", "achieved",
                                  expected_revision_id=rev, actor="h")
        rev = self._current_rev()
        html, status = self._post({"expected_revision_id": str(rev),
                                     "target_status": "planned"})
        self.assertEqual(status, 400)


class TestSoftDeleteUI(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "T", actor="h")

    def _current_rev(self):
        return self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id='I.1'"
        ).fetchone()["current_revision_id"]

    def test_soft_delete_via_post(self):
        h = _mock_handler(self.conn)
        h._form_data.return_value = {
            "expected_revision_id": str(self._current_rev())}
        h.client_address = ("127.0.0.1", 0)
        web.html_soft_delete_node(
            h, {"project_id": "p1", "node_id": "I.1"}, {})
        # Node is now soft-deleted (deleted_at is set)
        row = self.conn.execute(
            "SELECT deleted_at FROM nodes WHERE node_id='I.1'"
        ).fetchone()
        self.assertIsNotNone(row["deleted_at"])

    def test_restore_via_post(self):
        # First delete it
        rev = self._current_rev()
        writes.soft_delete_node(self.conn, "p1", "I.1",
                                  expected_revision_id=rev, actor="h")
        # Then restore via web handler
        h = _mock_handler(self.conn)
        h.client_address = ("127.0.0.1", 0)
        web.html_restore_node(h, {"project_id": "p1", "node_id": "I.1"}, {})
        row = self.conn.execute(
            "SELECT deleted_at FROM nodes WHERE node_id='I.1'"
        ).fetchone()
        self.assertIsNone(row["deleted_at"])

    def test_deleted_nodes_page(self):
        rev = self._current_rev()
        writes.soft_delete_node(self.conn, "p1", "I.1",
                                  expected_revision_id=rev, actor="h")
        html, status = web.html_deleted_nodes(
            _mock_handler(self.conn), {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("I.1", html)
        self.assertIn("Restore", html)


class TestArchivedProjectsUI(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        seed_project(self.conn, "p2")

    def test_archive_via_post(self):
        h = _mock_handler(self.conn)
        h._form_data.return_value = {}
        web.html_archive_project(h, {"project_id": "p1"}, {})
        row = self.conn.execute(
            "SELECT archived_at FROM projects WHERE project_id='p1'"
        ).fetchone()
        self.assertIsNotNone(row["archived_at"])

    def test_unarchive_via_post(self):
        writes.archive_project(self.conn, "p1")
        h = _mock_handler(self.conn)
        web.html_unarchive_project(h, {"project_id": "p1"}, {})
        row = self.conn.execute(
            "SELECT archived_at FROM projects WHERE project_id='p1'"
        ).fetchone()
        self.assertIsNone(row["archived_at"])

    def test_archived_projects_list(self):
        writes.archive_project(self.conn, "p2")
        html, status = web.html_archived_projects(
            _mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn("p2", html)
        self.assertIn("Unarchive", html)

    def test_archived_route_pattern_matches_before_generic(self):
        """Route order regression: /projects/archived must match its own
        handler, not /projects/<project_id>=archived which would 404."""
        import re as _re
        archived_pat = None
        generic_pat = None
        for method, pat, name in web.ROUTES_HTML:
            if name == "html_archived_projects":
                archived_pat = pat
                archived_idx = web.ROUTES_HTML.index((method, pat, name))
            elif name == "html_project":
                generic_pat = pat
                generic_idx = web.ROUTES_HTML.index((method, pat, name))
        self.assertIsNotNone(archived_pat)
        self.assertIsNotNone(generic_pat)
        # archived route must come earlier in the table
        self.assertLess(archived_idx, generic_idx,
                         "archived route must precede the generic project route")


class TestFilteredReports(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[
            {"name": "intent"}, {"name": "realizations"}])
        # start from "" so we can exercise the "" → planned transition below
        writes.create_node(self.conn, "p1", "intent", "I.1", "T",
                            target_status="", actor="h")
        rev = self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id='I.1'"
        ).fetchone()["current_revision_id"]
        writes.transition_target(self.conn, "p1", "I.1", "planned",
                                   expected_revision_id=rev, actor="h")

    def test_targets_filter_form_present(self):
        html, status = web.html_targets(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn('action="/reports/targets"', html)
        self.assertIn('name="layer"', html)
        self.assertIn('name="status"', html)
        # Default filter shows planned target
        self.assertIn("I.1", html)

    def test_targets_filter_by_layer(self):
        html, status = web.html_targets(_mock_handler(self.conn), {},
                                          {"layer": ["realizations"]})
        self.assertEqual(status, 200)
        # I.1 is in intent layer, filtered out
        self.assertIn("No targets matching", html)

    def test_flips_filter_form_present(self):
        html, status = web.html_flips(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn('action="/reports/flips"', html)
        self.assertIn('name="mechanism"', html)


class TestPrimaryParentRenderConvention(unittest.TestCase):
    """Multi-parent nodes: first parent is primary, others are cross-refs."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[
            {"name": "L0"}, {"name": "L1"}
        ])
        writes.create_node(self.conn, "p1", "L0", "A", "Parent A", actor="h")
        writes.create_node(self.conn, "p1", "L0", "B", "Parent B", actor="h")
        # C has two parents: A is primary (first), B is secondary
        writes.create_node(self.conn, "p1", "L1", "C", "Child C",
                           parents=["A", "B"], actor="h")

    def test_node_detail_marks_first_parent_as_primary(self):
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "C"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn('class="primary-parent"', html_body)

    def test_node_detail_shows_primary_parent_link(self):
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "C"}, {}
        )
        self.assertEqual(status, 200)
        # Primary parent A should appear with its link
        self.assertIn(">A<", html_body)

    def test_node_detail_shows_other_parents_as_cross_refs(self):
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "C"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn('class="other-parents"', html_body)
        # Secondary parent B should also appear
        self.assertIn(">B<", html_body)

    def test_single_parent_node_shows_primary_only(self):
        # Node A has no parents; node B has no parents; create D with one parent
        writes.create_node(self.conn, "p1", "L1", "D", "Child D",
                           parents=["A"], actor="h")
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "D"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn('class="primary-parent"', html_body)
        # No "other-parents" section for single-parent node
        self.assertNotIn('class="other-parents"', html_body)

    def test_no_parent_node_shows_no_parents_panel(self):
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "A"}, {}
        )
        self.assertEqual(status, 200)
        # Root node has no parents panel at all
        self.assertNotIn('class="primary-parent"', html_body)
        self.assertNotIn('class="parents-panel"', html_body)

    def test_parents_panel_helper_directly(self):
        """Unit-test the html.parents_panel helper."""
        # Empty parents
        self.assertEqual(html.parents_panel([]), "")
        # Single parent
        out = html.parents_panel(["X"])
        self.assertIn('class="primary-parent"', out)
        self.assertNotIn('class="other-parents"', out)
        # Multi-parent
        out = html.parents_panel(["X", "Y", "Z"])
        self.assertIn('class="primary-parent"', out)
        self.assertIn('class="other-parents"', out)
        self.assertIn(">X<", out)
        self.assertIn(">Y<", out)
        self.assertIn(">Z<", out)
class TestSpecAuditReportView(unittest.TestCase):
    """GET /projects/<p>/spec-audit HTML view."""

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

    def test_html_spec_audit_returns_200(self):
        html_body, status = web.html_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)

    def test_html_spec_audit_shows_project(self):
        html_body, status = web.html_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("p1", html_body)

    def test_html_spec_audit_shows_pivot_revision(self):
        html_body, status = web.html_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("pivot", html_body)

    def test_html_spec_audit_has_two_sections(self):
        html_body, status = web.html_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("Flagged Revisions", html_body)
        self.assertIn("Unclarified Rationale Changes", html_body)

    def test_html_spec_audit_404_for_missing_project(self):
        html_body, status = web.html_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "missing"}, {})
        self.assertEqual(status, 404)

    def test_html_spec_audit_since_filter(self):
        html_body, status = web.html_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"},
            {"since": ["2099-01-01T00:00:00Z"]})
        self.assertEqual(status, 200)

    def test_route_registered_in_routes_html(self):
        route_names = [name for _, _, name in web.ROUTES_HTML]
        self.assertIn("html_spec_audit", route_names)


class TestSpecAuditReportAPI(unittest.TestCase):
    """GET /api/v1/projects/<id>/spec-audit JSON API."""

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

    def test_api_spec_audit_returns_200(self):
        payload, status = web.api_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)

    def test_api_spec_audit_has_both_keys(self):
        payload, status = web.api_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("flagged_revisions", payload)
        self.assertIn("unclarified_rationale_changes", payload)

    def test_api_spec_audit_flagged_revisions_is_list(self):
        payload, status = web.api_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertIsInstance(payload["flagged_revisions"], list)

    def test_api_spec_audit_finds_drift_revision(self):
        payload, status = web.api_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        reasons = [r.get("change_reason") for r in payload["flagged_revisions"]]
        self.assertIn("pivot", reasons)

    def test_api_spec_audit_since_filter(self):
        payload, status = web.api_spec_audit(
            _mock_handler(self.conn),
            {"project_id": "p1"},
            {"since": ["2099-01-01T00:00:00Z"]})
        self.assertEqual(status, 200)
        self.assertEqual(payload["flagged_revisions"], [])

    def test_route_registered_in_routes_api(self):
        route_names = [name for _, _, name in web.ROUTES_API]
        self.assertIn("api_spec_audit", route_names)


def _patch_verdict(conn, project_id, node_id, fields, *, actor="h"):
    rev = queries.get_node(conn, project_id, node_id)["current_revision_id"]
    writes.update_node(
        conn, project_id, node_id, fields,
        expected_revision_id=rev, actor=actor, change_reason="evolution",
    )


class TestWebDriftReport(unittest.TestCase):
    """GET /projects/<p>/drift-report HTML view."""

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

    def test_html_drift_report_returns_200(self):
        html_body, status = web.html_drift_report(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)

    def test_html_drift_report_shows_project(self):
        html_body, status = web.html_drift_report(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)
        self.assertIn("p1", html_body)

    def test_html_drift_report_shows_violated_node(self):
        html_body, status = web.html_drift_report(
            _mock_handler(self.conn),
            {"project_id": "p1"},
            {"force": ["1"]})
        self.assertEqual(status, 200)
        self.assertIn("R.bad", html_body)
        self.assertIn("Violated", html_body)

    def test_html_drift_report_404_for_missing_project(self):
        html_body, status = web.html_drift_report(
            _mock_handler(self.conn),
            {"project_id": "missing"}, {})
        self.assertEqual(status, 404)

    def test_route_registered_in_routes_html(self):
        route_names = [name for _, _, name in web.ROUTES_HTML]
        self.assertIn("html_drift_report", route_names)


class TestAPIDriftReport(unittest.TestCase):
    """GET /api/v1/projects/<id>/drift-report JSON API."""

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

    def test_api_drift_report_returns_200(self):
        payload, status = web.api_drift_report(
            _mock_handler(self.conn),
            {"project_id": "p1"}, {})
        self.assertEqual(status, 200)

    def test_api_drift_report_has_expected_keys(self):
        payload, status = web.api_drift_report(
            _mock_handler(self.conn),
            {"project_id": "p1"},
            {"force": ["1"]})
        self.assertEqual(status, 200)
        self.assertIn("summary", payload)
        self.assertIn("violated", payload)
        self.assertIn("unverified", payload)
        self.assertEqual(payload["project_id"], "p1")

    def test_api_drift_report_finds_violated_node(self):
        payload, status = web.api_drift_report(
            _mock_handler(self.conn),
            {"project_id": "p1"},
            {"force": ["1"]})
        self.assertEqual(status, 200)
        violated_ids = [f["node_id"] for f in payload["violated"]]
        self.assertIn("R.bad", violated_ids)

    def test_route_registered_in_routes_api(self):
        route_names = [name for _, _, name in web.ROUTES_API]
        self.assertIn("api_drift_report", route_names)


class TestAPITrajectory(unittest.TestCase):
    """Trajectory JSON API + HTML show page."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1")
        writes.create_node(self.conn, "p1", "intent", "I.1", "Intent", actor="h")
        writes.create_node(
            self.conn, "p1", "realizations", "R.1", "Leaf",
            parents=["I.1"], target_status="planned", actor="h",
        )
        from manifold import trajectory as traj
        prop = traj.propose_trajectory(
            self.conn, "p1", "Target brief", [{
                "leg_kind": "transition_target",
                "payload": {"node_id": "R.1", "to_status": "achieved"},
            }],
            proposed_by="human:test",
        )
        self.tid = prop["trajectory_id"]
        self.conn.commit()

    def test_api_peek_trajectory(self):
        payload, status = web.api_peek_trajectory(
            _mock_handler(self.conn),
            {"trajectory_id": self.tid}, {})
        self.assertEqual(status, 200)
        self.assertIn("impact_preview", payload)

    def test_api_propose_trajectory(self):
        h = _mock_handler(self.conn)
        h._json_body.return_value = {
            "project_id": "p1",
            "target_brief": "Another target",
            "legs": [{
                "leg_kind": "transition_target",
                "payload": {"node_id": "R.1", "to_status": "in_progress"},
            }],
            "proposed_by": "human:test",
        }
        payload, status = web.api_propose_trajectory(h, {}, {})
        self.assertEqual(status, 201)
        self.assertIn("trajectory_id", payload)

    def test_html_trajectory(self):
        html_body, status = web.html_trajectory(
            _mock_handler(self.conn),
            {"trajectory_id": self.tid}, {})
        self.assertEqual(status, 200)
        self.assertIn("Target brief", html_body)

    def test_routes_registered(self):
        api_names = [name for _, _, name in web.ROUTES_API]
        html_names = [name for _, _, name in web.ROUTES_HTML]
        self.assertIn("api_peek_trajectory", api_names)
        self.assertIn("api_propose_trajectory", api_names)
        self.assertIn("api_accept_trajectory", api_names)
        self.assertIn("html_trajectory", html_names)


class TestPortfolioWeb(unittest.TestCase):
    """GET /reports/portfolio HTML + JSON API."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)
        self.conn.commit()

    def test_html_portfolio_returns_200(self):
        html_body, status = web.html_portfolio(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn("Q3 Reliability", html_body)

    def test_html_portfolio_shows_blocked_link(self):
        html_body, status = web.html_portfolio(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn("product-app/R.12", html_body)
        self.assertIn("ai-platform/C.4", html_body)

    def test_api_portfolio_report_json(self):
        payload, status = web.api_portfolio_report(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        self.assertIn("themes", payload)
        self.assertEqual(payload["themes"][0]["theme_node_id"], "T.1")

    def test_api_portfolio_report_blocked_by(self):
        payload, status = web.api_portfolio_report(_mock_handler(self.conn), {}, {})
        self.assertEqual(status, 200)
        link = next(
            l for l in payload["themes"][0]["links"]
            if l["node_id"] == "R.12"
        )
        self.assertEqual(link["blocked_by"], ["ai-platform/C.4"])


class TestNextLeavesAPI(unittest.TestCase):
    """Tests for GET /api/v1/projects/<id>/next-leaves[?layer=<name>]"""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p", layers=[
            {"name": "intents"}, {"name": "realizations"}])
        writes.create_node(self.conn, "p", "intents", "I.1", "intent 1",
                            actor="h")
        writes.create_node(self.conn, "p", "realizations", "R.1", "real 1",
                            parents=["I.1"], actor="h")

    def test_api_next_leaves_returns_list(self):
        payload, status = web.api_next_leaves(
            _mock_handler(self.conn),
            {"project_id": "p"}, {})
        self.assertEqual(status, 200)
        self.assertIsInstance(payload, list)

    def test_api_next_leaves_returns_only_leaves(self):
        payload, status = web.api_next_leaves(
            _mock_handler(self.conn),
            {"project_id": "p"}, {})
        self.assertEqual(status, 200)
        node_ids = [n["node_id"] for n in payload]
        # R.1 is a leaf; I.1 has a child so it is not
        self.assertIn("R.1", node_ids)
        self.assertNotIn("I.1", node_ids)

    def test_api_next_leaves_layer_filter(self):
        payload, status = web.api_next_leaves(
            _mock_handler(self.conn),
            {"project_id": "p"}, {"layer": ["intents"]})
        self.assertEqual(status, 200)
        # I.1 is at intents but not a leaf; R.1 not at intents
        self.assertEqual(payload, [])

    def test_api_next_leaves_layer_realizations(self):
        payload, status = web.api_next_leaves(
            _mock_handler(self.conn),
            {"project_id": "p"}, {"layer": ["realizations"]})
        self.assertEqual(status, 200)
        node_ids = [n["node_id"] for n in payload]
        self.assertIn("R.1", node_ids)

    def test_route_registered_in_routes_api(self):
        """Verify the route is in ROUTES_API so it's reachable via HTTP."""
        route_names = [name for _, _, name in web.ROUTES_API]
        self.assertIn("api_next_leaves", route_names)


# ============================================================
# rationale section + change_reason badges
# ============================================================

class TestNodeDetailRationale(unittest.TestCase):
    """Node detail page displays node.rationale and node.alternatives_considered."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[{"name": "intent"}])

    def test_rationale_shown_in_node_detail(self):
        writes.create_node(
            self.conn, "p1", "intent", "I.1", "Root",
            body="body text",
            rationale="We chose this approach because it scales.",
            actor="h",
        )
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn("We chose this approach because it scales.", html_body)

    def test_alternatives_shown_in_node_detail(self):
        writes.create_node(
            self.conn, "p1", "intent", "I.1", "Root",
            body="body",
            alternatives_considered="We also considered Option B and Option C.",
            actor="h",
        )
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn("We also considered Option B and Option C.", html_body)

    def test_rationale_section_absent_when_not_set(self):
        writes.create_node(
            self.conn, "p1", "intent", "I.1", "Root",
            body="body",
            rationale=None,
            alternatives_considered=None,
            actor="h",
        )
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1"}, {}
        )
        self.assertEqual(status, 200)
        # No <details> element injected when both are empty
        # (We check that the rationale-section details block is absent)
        self.assertNotIn("Rationale &amp; Alternatives", html_body)
        self.assertNotIn("Rationale &amp;amp; Alternatives", html_body)

    def test_rationale_section_is_collapsible_details_open(self):
        writes.create_node(
            self.conn, "p1", "intent", "I.1", "Root",
            body="body",
            rationale="some rationale",
            actor="h",
        )
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn("<details", html_body)
        # Must be open by default
        self.assertIn(" open", html_body)


class TestRevisionTimelineChangeReasonBadges(unittest.TestCase):
    """Revision timeline in node detail shows change_reason as a colored badge."""

    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[{"name": "intent"}])
        writes.create_node(
            self.conn, "p1", "intent", "I.1", "Root", body="v1", actor="h"
        )
        self.rev1 = self.conn.execute(
            "SELECT current_revision_id FROM nodes WHERE node_id='I.1'"
        ).fetchone()["current_revision_id"]

    def test_spec_audit_badge_shown_in_revision_timeline(self):
        writes.update_node(
            self.conn, "p1", "I.1",
            {"body": "v2 — drift fix"},
            expected_revision_id=self.rev1,
            actor="h",
            change_reason="pivot",
        )
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn("reason-pivot", html_body)
        self.assertIn("pivot", html_body)

    def test_clarification_badge_shown_in_revision_timeline(self):
        writes.update_node(
            self.conn, "p1", "I.1",
            {"body": "v2 clarified"},
            expected_revision_id=self.rev1,
            actor="h",
            change_reason="clarification",
        )
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn("reason-clarification", html_body)

    def test_no_badge_when_change_reason_is_null_in_db(self):
        # create_node stores change_reason=NULL (no default); html_node should
        # render no reason-badge span for such revisions.
        # The created revision (rev1) has no change_reason in the DB.
        # Add a second revision so both appear in the timeline.
        writes.update_node(
            self.conn, "p1", "I.1",
            {"body": "v2 update"},
            expected_revision_id=self.rev1,
            actor="h",
            change_reason="evolution",   # explicit, to ensure rev1 stays NULL
        )
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1"}, {}
        )
        self.assertEqual(status, 200)
        # The timeline shows rev2 (evolution badge) and rev1 (no badge).
        # There must be exactly ONE reason-badge span (for rev2).
        import re
        badge_spans = re.findall(r'<span class="reason-badge[^"]*"', html_body)
        self.assertEqual(len(badge_spans), 1,
                         f"Expected exactly 1 reason-badge span, got: {badge_spans}")

    def test_evolution_badge_shown_in_revision_timeline(self):
        writes.update_node(
            self.conn, "p1", "I.1",
            {"body": "v2 evolved"},
            expected_revision_id=self.rev1,
            actor="h",
            change_reason="evolution",
        )
        html_body, status = web.html_node(
            _mock_handler(self.conn),
            {"project_id": "p1", "node_id": "I.1"}, {}
        )
        self.assertEqual(status, 200)
        self.assertIn("reason-evolution", html_body)


class TestPresentationHandlers(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)

    def _handler(self, accept: str = "text/html"):
        h = _mock_handler(self.conn)
        h.headers = {"Accept": accept}
        return h

    def test_diagram_html_has_server_svg(self):
        html_body, status = web.html_diagram(
            self._handler(),
            {"project_id": "product-app"},
            {"focus": ["R.12"]},
        )
        self.assertEqual(status, 200)
        self.assertIn("presentation-svg", html_body)
        self.assertIn("<svg", html_body)
        self.assertNotIn("jsdelivr", html_body.lower())

    def test_diagram_negotiates_json(self):
        result = web.html_diagram(
            self._handler("application/json"),
            {"project_id": "product-app"},
            {"focus": ["R.12"]},
        )
        self.assertEqual(result[0], "json")
        view = result[1]
        self.assertEqual(view["diagram_type"], "blockers")

    def test_diagram_format_json_query(self):
        result = web.html_diagram(
            self._handler(),
            {"project_id": "product-app"},
            {"format": ["json"], "focus": ["R.12"]},
        )
        self.assertEqual(result[0], "json")

    def test_view_route_by_registry_id(self):
        html_body, status = web.html_view(
            self._handler(),
            {"project_id": "product-app", "view_id": "blockers"},
            {"focus": ["R.12"]},
        )
        self.assertEqual(status, 200)
        self.assertIn("View id", html_body)
        self.assertIn("blockers", html_body)

    def test_api_list_presentation_views(self):
        payload, status = web.api_list_presentation_views(self._handler(), {}, {})
        self.assertEqual(status, 200)
        self.assertIn("blockers", {v["view_id"] for v in payload["views"]})


class TestStatusBriefHandlers(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_portfolio_fixture(self.conn, cross_block=True)

    def _handler(self, accept: str = "text/html"):
        h = _mock_handler(self.conn)
        h.headers = {"Accept": accept}
        return h

    def test_brief_html_renders_pill(self):
        html_body, status = web.html_brief(
            self._handler(),
            {"project_id": "product-app"},
            {},
        )
        self.assertEqual(status, 200)
        self.assertIn("pill--blocked", html_body)
        self.assertIn("Blocked leaf", html_body)

    def test_brief_negotiates_json(self):
        result = web.html_brief(
            self._handler("application/json"),
            {"project_id": "product-app"},
            {},
        )
        self.assertEqual(result[0], "json")
        self.assertEqual(result[1]["overall"]["status"], "blocked")

    def test_api_brief(self):
        payload, status = web.api_brief(
            self._handler(), {"project_id": "product-app"}, {},
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["view_kind"], "status_brief")


if __name__ == "__main__":
    unittest.main()
