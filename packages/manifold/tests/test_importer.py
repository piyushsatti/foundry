"""
Tests for manifold importer.

Builds a mini v0.2 git repo in a tempdir and verifies:
- parse_node_file extracts frontmatter + body
- The vendored YAML parser handles block scalars and nested mappings
- import_project walks git log + replays revisions with git_sha
- change_summary is computed against the prior snapshot
- Idempotent: re-running advances only from the last imported sha
"""
import json
import tempfile
import unittest
from pathlib import Path
from manifold import importer
from tests.conftest import fresh_db
from tests.fixtures.build_mini_repo import build_mini_repo


SAMPLE = """---
id: I.1
title: Authenticate users
layer: intent
kind: spec
parents: []
peers_depends_on: []
verdict:
  mechanism: human_signoff
  status: satisfied
---

# I.1 — Authenticate users

## why

Consumer apps need authentication.
"""


# ============================================================
# parse_node_file
# ============================================================

class TestParseNode(unittest.TestCase):
    def test_parse_frontmatter_and_body(self):
        result = importer.parse_node_file(SAMPLE)
        self.assertEqual(result["frontmatter"]["id"], "I.1")
        self.assertEqual(result["frontmatter"]["title"], "Authenticate users")
        self.assertEqual(result["frontmatter"]["layer"], "intent")
        self.assertEqual(result["frontmatter"]["kind"], "spec")
        self.assertEqual(result["frontmatter"]["parents"], [])
        self.assertIn("Consumer apps need authentication.", result["body"])

    def test_parse_no_frontmatter_returns_body_only(self):
        result = importer.parse_node_file("just body\n")
        self.assertEqual(result["frontmatter"], {})
        self.assertEqual(result["body"].strip(), "just body")


# ============================================================
# Vendored YAML parser — edge cases
# ============================================================

class TestYAMLEdgeCases(unittest.TestCase):
    def test_block_scalar_folded(self):
        s = "key: >\n  multi\n  line\n  text\n"
        result = importer._parse_yaml(s)
        self.assertEqual(result["key"], "multi line text")

    def test_nested_mapping(self):
        s = "contract:\n  version: 0.1.0\n  locked: false\n"
        result = importer._parse_yaml(s)
        self.assertEqual(result["contract"]["version"], "0.1.0")
        self.assertEqual(result["contract"]["locked"], False)

    def test_block_list_of_mappings(self):
        s = ("layers:\n"
             "  - name: intent\n"
             "    purpose: \"why\"\n"
             "  - name: realizations\n")
        result = importer._parse_yaml(s)
        self.assertEqual(len(result["layers"]), 2)
        self.assertEqual(result["layers"][0]["name"], "intent")
        self.assertEqual(result["layers"][0]["purpose"], "why")
        self.assertEqual(result["layers"][1]["name"], "realizations")

    def test_flow_list_of_strings(self):
        s = 'parents: ["I.1", "I.2"]\n'
        result = importer._parse_yaml(s)
        self.assertEqual(result["parents"], ["I.1", "I.2"])

    def test_double_quoted_escapes(self):
        s = 'key: "with \\"quote\\""\n'
        result = importer._parse_yaml(s)
        self.assertEqual(result["key"], 'with "quote"')


# ============================================================
# change_summary
# ============================================================

class TestChangeSummary(unittest.TestCase):
    def test_returns_field_diff(self):
        prev = {"title": "A", "body": "x", "parents": []}
        curr = {"title": "B", "body": "x", "parents": ["I.1"]}
        diff = importer._compute_change_summary(prev, curr)
        fields = {d["field"]: d for d in diff}
        self.assertEqual(fields["title"]["old"], "A")
        self.assertEqual(fields["title"]["new"], "B")
        self.assertIn("parents", fields)
        self.assertNotIn("body", fields)

    def test_returns_none_for_first(self):
        self.assertIsNone(importer._compute_change_summary(None, {"title": "X"}))


# ============================================================
# import_project — end-to-end git replay
# ============================================================

class TestImportReplay(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = build_mini_repo(Path(self.tmp.name) / "mini_repo")

    def test_two_commits_become_two_revisions(self):
        conn, _ = fresh_db(self)
        result = importer.import_project(conn, self.repo, project_id="mini",
                                          actor="human:test")
        self.assertEqual(result["project_id"], "mini")
        self.assertEqual(result["nodes_imported"], 1)
        self.assertEqual(result["revisions_imported"], 2)

        revs = conn.execute(
            "SELECT snapshot, change_type, git_sha FROM revisions "
            "WHERE project_id = ? AND node_id = ? ORDER BY ts ASC",
            ("mini", "I.1"),
        ).fetchall()
        self.assertEqual(len(revs), 2)
        self.assertEqual(revs[0]["change_type"], "created")
        self.assertEqual(revs[1]["change_type"], "updated")
        # Title progression
        titles = [json.loads(r["snapshot"])["title"] for r in revs]
        self.assertEqual(titles, ["Initial thesis", "Revised thesis"])
        # Each revision has a git_sha set
        self.assertIsNotNone(revs[0]["git_sha"])
        self.assertIsNotNone(revs[1]["git_sha"])

    def test_nodes_table_synced_to_head(self):
        conn, _ = fresh_db(self)
        importer.import_project(conn, self.repo, project_id="mini",
                                 actor="human:test")
        node = conn.execute(
            "SELECT title, body FROM nodes WHERE project_id = ? AND node_id = ?",
            ("mini", "I.1"),
        ).fetchone()
        self.assertEqual(node["title"], "Revised thesis")
        self.assertIn("exists and matters", node["body"])


class TestImporterIdempotency(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = build_mini_repo(Path(self.tmp.name) / "mini_repo")

    def test_second_import_is_no_op(self):
        conn, _ = fresh_db(self)
        r1 = importer.import_project(conn, self.repo, project_id="mini",
                                      actor="human:test")
        r2 = importer.import_project(conn, self.repo, project_id="mini",
                                      actor="human:test")
        self.assertEqual(r1["revisions_imported"], 2)
        self.assertEqual(r2["revisions_imported"], 0)


if __name__ == "__main__":
    unittest.main()
