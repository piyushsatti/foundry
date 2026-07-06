"""
Tests for manifold exporter.

Covers: slug helper, scalar emission, frontmatter shape, spec.yaml shape,
file layout, refusal to overwrite, full round-trip (export → re-import
into a fresh DB → node set + body match).
"""
import json
import tempfile
import unittest
from pathlib import Path

from manifold import db, schema, writes, queries, exporter, importer
from tests.conftest import fresh_db, seed_project


class TestSlug(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(exporter._slug("Hello World"), "hello-world")

    def test_empty_falls_back(self):
        self.assertEqual(exporter._slug(""), "node")

    def test_truncated(self):
        s = exporter._slug("a" * 200, max_len=60)
        self.assertEqual(len(s), 60)

    def test_collapses_separators(self):
        self.assertEqual(exporter._slug("foo / bar __ baz"), "foo-bar-baz")


class TestScalarEmission(unittest.TestCase):
    def test_simple_string(self):
        self.assertEqual(exporter._scalar("hello"), "hello")

    def test_empty_double_quoted(self):
        self.assertEqual(exporter._scalar(""), '""')

    def test_with_colon_quoted(self):
        self.assertEqual(exporter._scalar("a: b"), '"a: b"')

    def test_int_passthrough(self):
        self.assertEqual(exporter._scalar(42), "42")

    def test_bool(self):
        self.assertEqual(exporter._scalar(True), "true")
        self.assertEqual(exporter._scalar(False), "false")


class TestNodeFrontmatter(unittest.TestCase):
    def test_basic_fields(self):
        node = {"node_id": "I.1", "title": "Hello", "layer": "intent",
                "kind": "spec"}
        fm = exporter._node_frontmatter(node, [], [], [])
        self.assertEqual(fm["id"], "I.1")
        self.assertEqual(fm["title"], "Hello")
        self.assertEqual(fm["layer"], "intent")
        self.assertNotIn("parents", fm)  # empty list omitted

    def test_target_nested(self):
        node = {"node_id": "I.1", "title": "T", "layer": "intent",
                "target_status": "planned",
                "target_achieved_when": "tests pass"}
        fm = exporter._node_frontmatter(node, [], [], [])
        self.assertIn("target", fm)
        self.assertEqual(fm["target"]["status"], "planned")
        self.assertEqual(fm["target"]["achieved_when"], "tests pass")

    def test_verdict_nested(self):
        node = {"node_id": "I.1", "title": "T", "layer": "intent",
                "verdict_mechanism": "automated_check",
                "verdict_check": "true"}
        fm = exporter._node_frontmatter(node, [], [], [])
        self.assertIn("verdict", fm)
        self.assertEqual(fm["verdict"]["mechanism"], "automated_check")
        self.assertEqual(fm["verdict"]["check"], "true")

    def test_parents_and_peers_included(self):
        node = {"node_id": "C.1", "title": "C", "layer": "capabilities"}
        fm = exporter._node_frontmatter(node, ["I.1"], ["C.2"], ["K.3"])
        self.assertEqual(fm["parents"], ["I.1"])
        self.assertEqual(fm["peers_depends_on"], ["C.2"])
        self.assertEqual(fm["target"]["blocks"], ["K.3"])


class TestEmitFrontmatter(unittest.TestCase):
    def test_round_trips_through_parser(self):
        fm_dict = {
            "id": "I.1", "title": "Hello", "layer": "intent", "kind": "spec",
            "parents": ["P.1"],
            "target": {"status": "planned", "achieved_when": "x: y"},
            "verdict": {"mechanism": "automated_check", "check": "true"},
        }
        text = exporter._emit_frontmatter(fm_dict)
        # Run it through manifold's own parser
        parsed = importer._parse_yaml(text)
        self.assertEqual(parsed["id"], "I.1")
        self.assertEqual(parsed["parents"], ["P.1"])
        self.assertEqual(parsed["target"]["status"], "planned")
        self.assertEqual(parsed["target"]["achieved_when"], "x: y")
        self.assertEqual(parsed["verdict"]["mechanism"], "automated_check")


class TestSpecYAML(unittest.TestCase):
    def test_includes_layers(self):
        text = exporter._emit_spec_yaml("p1", {
            "name": "p1",
            "layers": [{"name": "intent", "verdict_default": "human_signoff"},
                       {"name": "realizations"}],
        })
        parsed = importer._parse_yaml(text)
        self.assertEqual(parsed["name"], "p1")
        self.assertEqual([L["name"] for L in parsed["layers"]],
                          ["intent", "realizations"])
        self.assertEqual(parsed["layers"][0].get("verdict_default"),
                          "human_signoff")


class TestExportProject(unittest.TestCase):
    def setUp(self):
        self.conn, _ = fresh_db(self)
        seed_project(self.conn, "p1", layers=[
            {"name": "intent"}, {"name": "realizations"}])
        writes.create_node(self.conn, "p1", "intent", "I.1", "Top",
                            body="# Top\n\nIntent body.", actor="h")
        writes.create_node(self.conn, "p1", "realizations", "R.1", "Real one",
                            body="implementation.",
                            parents=["I.1"], actor="h")

    def test_writes_spec_yaml_and_node_files(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "exported"
            result = exporter.export_project(self.conn, "p1", out)
            self.assertEqual(result["nodes_exported"], 2)
            self.assertTrue((out / "specs" / "spec.yaml").is_file())
            intent_files = list((out / "specs" / "intent").iterdir())
            real_files = list((out / "specs" / "realizations").iterdir())
            self.assertEqual(len(intent_files), 1)
            self.assertEqual(len(real_files), 1)
            self.assertTrue(intent_files[0].name.startswith("I.1-"))
            self.assertTrue(real_files[0].name.startswith("R.1-"))

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "specs").mkdir()
            with self.assertRaises(FileExistsError):
                exporter.export_project(self.conn, "p1", Path(td))

    def test_missing_project_raises(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                exporter.export_project(self.conn, "nope", Path(td) / "x")

    def test_node_file_parses_back(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "exported"
            exporter.export_project(self.conn, "p1", out)
            intent_file = next((out / "specs" / "intent").iterdir())
            parsed = importer.parse_node_file(intent_file.read_text(encoding="utf-8"))
            fm = parsed["frontmatter"]
            self.assertEqual(fm["id"], "I.1")
            self.assertEqual(fm["title"], "Top")
            self.assertEqual(fm["layer"], "intent")
            self.assertIn("Intent body", parsed["body"])

    def test_round_trip_via_git_import(self):
        """Full round-trip: export → init git → import into a fresh DB → compare nodes."""
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "exported"
            exporter.export_project(self.conn, "p1", out)
            # Make it a git repo so the importer can replay it
            for cmd in (
                ["git", "init", "-q"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=T", "add", "."],
                ["git", "-c", "user.email=t@t", "-c", "user.name=T",
                 "commit", "-q", "-m", "exported"],
            ):
                subprocess.run(cmd, cwd=str(out), check=True,
                                capture_output=True)
            # Re-import into a fresh DB
            tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            tmp_db.close()
            tmp_db_path = Path(tmp_db.name)
            self.addCleanup(lambda: [Path(str(tmp_db_path) + s).unlink(missing_ok=True)
                                       for s in ("", "-shm", "-wal")])
            conn2 = db.connect(tmp_db_path)
            schema.bootstrap(conn2)
            try:
                importer.import_project(conn2, out, actor="test:roundtrip")
                imported_proj = queries.get_project(conn2, "p1")
                self.assertIsNotNone(imported_proj)
                n_imported = queries.list_nodes(conn2, "p1", limit=100)
                self.assertEqual(
                    {n["node_id"] for n in n_imported},
                    {"I.1", "R.1"},
                )
                # Bodies survive
                r1 = queries.get_node(conn2, "p1", "R.1")
                self.assertIn("implementation", r1["body"])
                # Parents survive
                parents = conn2.execute(
                    "SELECT dst_node_id FROM node_edges WHERE project_id = 'p1' "
                    "AND src_node_id = 'R.1' AND edge_kind = 'parent'"
                ).fetchall()
                self.assertEqual([r["dst_node_id"] for r in parents], ["I.1"])
            finally:
                conn2.close()


if __name__ == "__main__":
    unittest.main()
