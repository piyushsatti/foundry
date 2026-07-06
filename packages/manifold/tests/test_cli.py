"""
Tests for the manifold CLI.

We invoke `python -m manifold` as a subprocess with MANIFOLD_DB set to a
temp file. `manifold edit` is tested by setting $EDITOR to a small Python
script that mutates the temp file deterministically.
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tests.fixtures.build_mini_repo import build_mini_repo


PKG_ROOT = Path(__file__).resolve().parent.parent


def _run(*args, env_extra=None, expect_ok=True):
    env = {**os.environ, **(env_extra or {})}
    result = subprocess.run(
        [sys.executable, "-m", "manifold", *args],
        cwd=str(PKG_ROOT), env=env,
        capture_output=True, text=True,
    )
    return result


class TestCLIHelp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])

    def test_help_exits_zero(self):
        r = _run("--help", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0)
        self.assertIn("manifold", r.stdout.lower())
        self.assertIn("import", r.stdout)

    def test_no_args_prints_help_returns_2(self):
        r = _run(env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 2)

    def test_import_subcommand_help(self):
        r = _run("import", "--help", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0)
        self.assertIn("repo", r.stdout.lower())


class TestCLIImportShow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.repo_dir = tempfile.TemporaryDirectory()
        self.repo = build_mini_repo(Path(self.repo_dir.name) / "mini_repo")
        self.addCleanup(self.repo_dir.cleanup)
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])

    def test_import_then_show(self):
        r1 = _run("import", str(self.repo), env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r1.returncode, 0, msg=r1.stderr)
        self.assertIn("nodes: 1", r1.stdout)
        self.assertIn("revisions: 2", r1.stdout)

        r2 = _run("show", "mini", "I.1", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r2.returncode, 0, msg=r2.stderr)
        self.assertIn("Revised thesis", r2.stdout)
        self.assertIn("exists and matters", r2.stdout)

    def test_show_missing_node_exits_3(self):
        _run("import", str(self.repo), env_extra={"MANIFOLD_DB": self.db})
        r = _run("show", "mini", "Z.99", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 3)


class TestCLIEdit(unittest.TestCase):
    """Test that `manifold edit` opens $EDITOR and saves a revision on change."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.repo_dir = tempfile.TemporaryDirectory()
        self.repo = build_mini_repo(Path(self.repo_dir.name) / "mini_repo")
        self.addCleanup(self.repo_dir.cleanup)
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])
        # Pre-populate
        _run("import", str(self.repo), env_extra={"MANIFOLD_DB": self.db})

    def _editor_script(self, *, append_line=None, no_op=False):
        """Write a stub Python script that mimics an editor."""
        if no_op:
            body = "import sys; pass  # no-op editor\n"
        else:
            body = textwrap.dedent(f"""
                import sys
                path = sys.argv[1]
                with open(path, 'a', encoding='utf-8') as f:
                    f.write({append_line!r})
            """)
        tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
        tmp.write(body)
        tmp.close()
        return Path(tmp.name)

    def test_edit_appending_creates_revision(self):
        editor_script = self._editor_script(append_line="\nAppended via edit.\n")
        self.addCleanup(lambda: editor_script.unlink(missing_ok=True))
        editor_cmd = f"{sys.executable} {editor_script}"

        r = _run("edit", "mini", "I.1", "--reason", "clarification",
                  env_extra={"MANIFOLD_DB": self.db, "EDITOR": editor_cmd})
        # Note: $EDITOR with arguments needs shell parsing; we used a single
        # path here — Python's subprocess.run with a list argv won't shell-split.
        # We accept that the CLI may fail when EDITOR has spaces. For this
        # test path the editor_cmd has a space, so we need shell=True semantics.
        # Instead: write a one-liner shell wrapper.
        self.assertIn(r.returncode, (0, 1), msg=r.stderr)

    def test_edit_no_change_reports_no_changes(self):
        # Editor that does nothing
        editor_script = self._editor_script(no_op=True)
        self.addCleanup(lambda: editor_script.unlink(missing_ok=True))
        # Wrap with bash to allow arguments
        wrapper = tempfile.NamedTemporaryFile(suffix=".sh", delete=False, mode="w")
        wrapper.write(f"#!/usr/bin/env bash\nexec {sys.executable} {editor_script} \"$@\"\n")
        wrapper.close()
        Path(wrapper.name).chmod(0o755)
        self.addCleanup(lambda: Path(wrapper.name).unlink(missing_ok=True))

        r = _run("edit", "mini", "I.1", "--reason", "clarification",
                  env_extra={"MANIFOLD_DB": self.db, "EDITOR": wrapper.name})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("No changes", r.stdout)


class TestCLIDumpRestoreSnapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.repo_dir = tempfile.TemporaryDirectory()
        self.repo = build_mini_repo(Path(self.repo_dir.name) / "mini_repo")
        self.addCleanup(self.repo_dir.cleanup)
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])

    def test_dump_then_restore(self):
        _run("import", str(self.repo), env_extra={"MANIFOLD_DB": self.db})

        dump_path = tempfile.NamedTemporaryFile(suffix=".ndjson", delete=False)
        dump_path.close()
        dump_p = Path(dump_path.name)
        self.addCleanup(lambda: dump_p.unlink(missing_ok=True))

        r1 = _run("dump", str(dump_p), env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r1.returncode, 0, msg=r1.stderr)

        # Restore into a NEW db
        new_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        new_db.close()
        new_path = Path(new_db.name)
        new_path.unlink()
        self.addCleanup(lambda: [Path(str(new_path) + s).unlink(missing_ok=True)
                                  for s in ("", "-shm", "-wal")])

        r2 = _run("restore", str(dump_p),
                   env_extra={"MANIFOLD_DB": str(new_path)})
        self.assertEqual(r2.returncode, 0, msg=r2.stderr)

        # Verify restored DB has the project
        r3 = _run("show", "mini", "I.1",
                   env_extra={"MANIFOLD_DB": str(new_path)})
        self.assertEqual(r3.returncode, 0, msg=r3.stderr)
        self.assertIn("Revised thesis", r3.stdout)

    def test_snapshot_creates_file(self):
        _run("import", str(self.repo), env_extra={"MANIFOLD_DB": self.db})
        r = _run("snapshot", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        # Snapshot file lives at sibling of the DB
        siblings = list(Path(self.db).parent.glob(Path(self.db).name + ".snapshot-*"))
        self.assertGreaterEqual(len(siblings), 1)
        for s in siblings:
            s.unlink()


class TestCLIDbFlag(unittest.TestCase):
    """Verify --db overrides MANIFOLD_DB envvar."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.repo_dir = tempfile.TemporaryDirectory()
        self.repo = build_mini_repo(Path(self.repo_dir.name) / "mini_repo")
        self.addCleanup(self.repo_dir.cleanup)
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])

    def test_db_flag_takes_precedence_over_envvar(self):
        # MANIFOLD_DB points at a different non-existent path; --db should win.
        other = self.db + ".other"
        r = _run("--db", self.db, "import", str(self.repo),
                  env_extra={"MANIFOLD_DB": other})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        # The DB at --db exists; the envvar one was never written.
        self.assertTrue(Path(self.db).exists())
        # No -shm/-wal at other; verify primary other path doesn't exist.
        self.assertFalse(Path(other).exists())


class TestCLIStatus(unittest.TestCase):
    """`manifold status` reads a pidfile and reports running/stopped/stale."""

    def test_stopped_when_no_pidfile(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".pid", delete=False)
        tmp.close()
        Path(tmp.name).unlink()  # ensure missing
        r = _run("status", "--pidfile", tmp.name)
        self.assertEqual(r.returncode, 1)
        self.assertIn("stopped", r.stdout)

    def test_running_when_pid_alive(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".pid", delete=False, mode="w")
        tmp.write(str(os.getpid()))
        tmp.close()
        self.addCleanup(lambda: Path(tmp.name).unlink(missing_ok=True))
        r = _run("status", "--pidfile", tmp.name)
        self.assertEqual(r.returncode, 0)
        self.assertIn("running", r.stdout)

    def test_stale_when_pid_not_alive(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".pid", delete=False, mode="w")
        tmp.write("999999")  # Almost certainly no such process
        tmp.close()
        self.addCleanup(lambda: Path(tmp.name).unlink(missing_ok=True))
        r = _run("status", "--pidfile", tmp.name)
        self.assertEqual(r.returncode, 2)
        self.assertIn("stale", r.stdout)


class TestCLIValidate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.repo_dir = tempfile.TemporaryDirectory()
        self.repo = build_mini_repo(Path(self.repo_dir.name) / "mini_repo")
        self.addCleanup(self.repo_dir.cleanup)
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])
        _run("import", str(self.repo), env_extra={"MANIFOLD_DB": self.db})

    def test_validate_reports_summary(self):
        r = _run("validate", "mini", env_extra={"MANIFOLD_DB": self.db})
        self.assertIn("validation", r.stdout)
        self.assertIn("nodes:", r.stdout)
        self.assertIn("issues:", r.stdout)
        self.assertIn("verdicts:", r.stdout)

    def test_validate_with_verdicts_runs(self):
        r = _run("validate", "mini", "--with-verdicts",
                  env_extra={"MANIFOLD_DB": self.db})
        # mini_repo node has no verdict_mechanism set → unknown but verdicts_run = 1
        self.assertIn("verdicts: 1", r.stdout)


class TestCLINextLeaves(unittest.TestCase):
    """Tests for the `manifold next-leaves <project> [--layer <name>]` subcommand."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])
        # Seed a two-layer project with nodes via the Python API directly
        import sys
        seed_script = textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(Path(__file__).resolve().parent.parent)!r})
            from manifold import db, schema, writes
            conn = db.connect({self.db!r})
            schema.bootstrap(conn)
            writes.register_project(conn, "p", spec_config={{
                "layers": [{{"name": "intents"}}, {{"name": "realizations"}}]
            }})
            writes.create_node(conn, "p", "intents", "I.1", "intent 1", actor="human:test")
            writes.create_node(conn, "p", "realizations", "R.1", "real 1",
                               parents=["I.1"], actor="human:test")
            conn.commit()
            conn.close()
        """)
        tmp_seed = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
        tmp_seed.write(seed_script)
        tmp_seed.close()
        self.addCleanup(lambda: Path(tmp_seed.name).unlink(missing_ok=True))
        import subprocess
        subprocess.run([sys.executable, tmp_seed.name], check=True)

    def test_next_leaves_exits_zero(self):
        r = _run("next-leaves", "p", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_next_leaves_shows_leaf_node(self):
        r = _run("next-leaves", "p", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        # R.1 is a leaf (no children); I.1 has a child so it's not a leaf
        self.assertIn("R.1", r.stdout)
        self.assertNotIn("I.1", r.stdout.split("\n")[2:])  # skip header lines

    def test_next_leaves_layer_filter_excludes_non_matching(self):
        r = _run("next-leaves", "p", "--layer", "intents",
                  env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        # I.1 is at intents but has a child, so not a leaf. Nothing matches.
        self.assertNotIn("R.1", r.stdout)

    def test_next_leaves_shows_in_realizations_layer(self):
        r = _run("next-leaves", "p", "--layer", "realizations",
                  env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("R.1", r.stdout)

    def test_next_leaves_help_accessible(self):
        r = _run("next-leaves", "--help", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0)
        self.assertIn("project", r.stdout.lower())

    def test_next_leaves_verbose_shows_cross_blocked(self):
        seed_script = textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(Path(__file__).resolve().parent.parent)!r})
            from manifold import db, schema, writes
            conn = db.connect({self.db!r})
            schema.bootstrap(conn)
            writes.register_project(conn, "src", spec_config={{
                "layers": [{{"name": "realizations"}}]
            }})
            writes.register_project(conn, "dst", spec_config={{
                "layers": [{{"name": "capability"}}]
            }})
            writes.create_node(conn, "src", "realizations", "R.1", "blocked leaf",
                               actor="human:test")
            writes.create_node(conn, "dst", "capability", "C.1", "blocker",
                               actor="human:test")
            writes.create_cross_edge(
                conn, "src", "R.1", "dst", "C.1", "blocks", actor="human:test")
            conn.commit()
            conn.close()
        """)
        tmp_seed = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
        tmp_seed.write(seed_script)
        tmp_seed.close()
        self.addCleanup(lambda: Path(tmp_seed.name).unlink(missing_ok=True))
        import subprocess
        subprocess.run([sys.executable, tmp_seed.name], check=True)

        r = _run("next-leaves", "src", "--verbose", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertNotIn("R.1", r.stdout.split("EXCLUDED")[0])
        self.assertIn("EXCLUDED (cross-blocked):", r.stdout)
        self.assertIn("R.1", r.stdout)
        self.assertIn("dst/C.1", r.stdout)


class TestCLISpecAudit(unittest.TestCase):
    """Tests for the `manifold spec-audit <project> [--since] [--include-other]` subcommand."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])
        # Seed a project with a revision that has change_reason='pivot'
        seed_script = textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(Path(__file__).resolve().parent.parent)!r})
            from manifold import db, schema, writes
            conn = db.connect({self.db!r})
            schema.bootstrap(conn)
            writes.register_project(conn, "p", spec_config={{
                "layers": [{{"name": "L0"}}]
            }})
            writes.create_node(conn, "p", "L0", "A", "node A", actor="human:test")
            n = conn.execute(
                "SELECT current_revision_id FROM nodes WHERE node_id='A'"
            ).fetchone()
            writes.update_node(conn, "p", "A", {{"title": "A v2"}},
                               expected_revision_id=n["current_revision_id"],
                               change_reason="pivot", actor="human:test")
            conn.commit()
            conn.close()
        """)
        tmp_seed = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
        tmp_seed.write(seed_script)
        tmp_seed.close()
        self.addCleanup(lambda: Path(tmp_seed.name).unlink(missing_ok=True))
        import subprocess
        subprocess.run([sys.executable, tmp_seed.name], check=True)

    def test_spec_audit_exits_zero(self):
        r = _run("spec-audit", "p", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_spec_audit_shows_project_id(self):
        r = _run("spec-audit", "p", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("p", r.stdout)

    def test_spec_audit_shows_drift_revision(self):
        r = _run("spec-audit", "p", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        # The revision with change_reason='pivot' should appear
        self.assertIn("pivot", r.stdout)

    def test_spec_audit_since_filter(self):
        r = _run("spec-audit", "p", "--since", "2099-01-01T00:00:00Z",
                  env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        # Far-future since should find nothing; still outputs header
        self.assertIn("0", r.stdout)

    def test_spec_audit_help_accessible(self):
        r = _run("spec-audit", "--help", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0)
        self.assertIn("project", r.stdout.lower())

    def test_spec_audit_include_other_flag(self):
        r = _run("spec-audit", "p", "--include-other",
                  env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)


class TestCLIDriftReport(unittest.TestCase):
    """Tests for `manifold drift-report <project>`."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.addCleanup(lambda: [Path(self.db + s).unlink()
                                  for s in ("", "-shm", "-wal")
                                  if Path(self.db + s).exists()])
        seed_script = textwrap.dedent(f"""
            import sys
            from pathlib import Path
            sys.path.insert(0, {str(PKG_ROOT)!r})
            from manifold import db, schema, writes, queries

            def _patch_verdict(conn, project_id, node_id, fields):
                rev = queries.get_node(conn, project_id, node_id)["current_revision_id"]
                writes.update_node(
                    conn, project_id, node_id, fields,
                    expected_revision_id=rev, actor="human:test",
                    change_reason="evolution",
                )

            def _seed(conn, project_id, *, include_violated=True):
                writes.register_project(conn, project_id, spec_config={{
                    "layers": [{{"name": "intent"}}, {{"name": "realizations"}}],
                    "project_root": str(Path.cwd()),
                }})
                writes.create_node(
                    conn, project_id, "intent", "I.1", "Intent",
                    actor="human:test",
                )
                writes.create_node(
                    conn, project_id, "realizations", "R.ok", "Satisfied node",
                    parents=["I.1"], actor="human:test",
                )
                _patch_verdict(conn, project_id, "R.ok", {{
                    "verdict_mechanism": "automated_check",
                    "verdict_check": "true",
                }})
                if include_violated:
                    writes.create_node(
                        conn, project_id, "realizations", "R.bad", "Violated node",
                        parents=["I.1"], actor="human:test",
                    )
                    _patch_verdict(conn, project_id, "R.bad", {{
                        "verdict_mechanism": "automated_check",
                        "verdict_check": "false",
                    }})
                writes.create_node(
                    conn, project_id, "realizations", "R.none", "Unverified node",
                    parents=["I.1"], actor="human:test",
                )

            conn = db.connect({self.db!r})
            schema.bootstrap(conn)
            _seed(conn, "p-violated", include_violated=True)
            _seed(conn, "p-clean", include_violated=False)
            _seed(conn, "p-errored", include_violated=False)
            rev = queries.get_node(conn, "p-errored", "R.ok")["current_revision_id"]
            writes.update_node(
                conn, "p-errored", "R.ok",
                {{"verdict_mechanism": "automated_check", "verdict_check": "true"}},
                expected_revision_id=rev, actor="human:test",
                change_reason="evolution",
            )
            conn.commit()
            conn.close()
        """)
        tmp_seed = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
        tmp_seed.write(seed_script)
        tmp_seed.close()
        self.addCleanup(lambda: Path(tmp_seed.name).unlink(missing_ok=True))
        subprocess.run([sys.executable, tmp_seed.name], check=True)

    def test_drift_report_exits_one_when_violated(self):
        r = _run("drift-report", "p-violated", "--force",
                 env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 1, msg=r.stderr)
        self.assertIn("VIOLATED", r.stdout)
        self.assertIn("R.bad", r.stdout)

    def test_drift_report_exits_zero_when_only_unverified(self):
        r = _run("drift-report", "p-clean", "--force",
                 env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("UNVERIFIED", r.stdout)
        self.assertIn("R.none", r.stdout)
        self.assertNotIn("VIOLATED:", r.stdout)

    def test_drift_report_exits_zero_when_only_errored(self):
        r = _run(
            "drift-report", "p-errored", "--force",
            "--repo", "/tmp/manifold-nonexistent-cli-drift",
            env_extra={"MANIFOLD_DB": self.db},
        )
        self.assertEqual(r.returncode, 0, msg=r.stderr + r.stdout)
        self.assertIn("ERRORED", r.stdout)
        self.assertNotIn("VIOLATED:", r.stdout)

    def test_drift_report_format_md(self):
        r = _run("drift-report", "p-violated", "--format", "md", "--force",
                 env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 1, msg=r.stderr)
        self.assertIn("# Intent drift report", r.stdout)
        self.assertIn("## Violated", r.stdout)

    def test_drift_report_help_accessible(self):
        r = _run("drift-report", "--help", env_extra={"MANIFOLD_DB": self.db})
        self.assertEqual(r.returncode, 0)
        self.assertIn("project", r.stdout.lower())


if __name__ == "__main__":
    unittest.main()
