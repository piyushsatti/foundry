import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from manifold import config


class TestConfig(unittest.TestCase):
    """Tests for config resolution: env var > file > default."""

    def setUp(self):
        # Each test gets a fresh temp dir; MANIFOLD_CONFIG points at a path that
        # does NOT yet exist (simulates absent-file for most tests unless the
        # test explicitly writes it). This ensures we never touch the real
        # ~/.claude/manifold.json during tests.
        self._tmpdir = tempfile.TemporaryDirectory()
        self._cfg_path = os.path.join(self._tmpdir.name, "manifold.json")
        # Reset the module-level cache so each test starts clean.
        config._reset_config_cache()

    def tearDown(self):
        config._reset_config_cache()
        self._tmpdir.cleanup()

    # --- helpers ---

    def _write_config(self, data: dict):
        with open(self._cfg_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        config._reset_config_cache()

    def _env(self, extra: dict | None = None) -> dict:
        """Base env: MANIFOLD_CONFIG points at our temp path; no other manifold vars."""
        base = {"MANIFOLD_CONFIG": self._cfg_path}
        if extra:
            base.update(extra)
        return base

    # -----------------------------------------------------------------------
    # Existing tests — adapted so they don't accidentally read the real file
    # -----------------------------------------------------------------------

    def test_db_path_default(self):
        with patch.dict(os.environ, self._env(), clear=True):
            self.assertEqual(config.db_path(), Path.home() / ".claude" / "manifold.db")

    def test_db_path_override(self):
        with patch.dict(os.environ, self._env({"MANIFOLD_DB": "/tmp/x.db"}), clear=True):
            self.assertEqual(config.db_path(), Path("/tmp/x.db"))

    def test_snapshot_interval_default(self):
        with patch.dict(os.environ, self._env(), clear=True):
            self.assertEqual(config.snapshot_interval_seconds(), 3600)

    def test_snapshot_interval_override(self):
        with patch.dict(os.environ, self._env({"MANIFOLD_SNAPSHOT_INTERVAL": "300"}), clear=True):
            self.assertEqual(config.snapshot_interval_seconds(), 300)

    def test_schema_version_constant(self):
        self.assertEqual(config.SCHEMA_VERSION, 1)

    # -----------------------------------------------------------------------
    # Test 1: Absent file → db_path() returns default; load_config() returns {}
    # -----------------------------------------------------------------------

    def test_1_absent_file_returns_defaults(self):
        # self._cfg_path does not exist
        with patch.dict(os.environ, self._env(), clear=True):
            self.assertFalse(Path(self._cfg_path).exists())
            self.assertEqual(config.load_config(), {})
            self.assertEqual(config.db_path(), Path.home() / ".claude" / "manifold.db")

    # -----------------------------------------------------------------------
    # Test 2: File sets db_path → db_path() returns it (with ~ expanded)
    # -----------------------------------------------------------------------

    def test_2_file_sets_db_path_with_tilde_expansion(self):
        self._write_config({"db_path": "~/.claude/custom.db"})
        with patch.dict(os.environ, self._env(), clear=True):
            result = config.db_path()
            expected = Path.home() / ".claude" / "custom.db"
            self.assertEqual(result, expected)

    # -----------------------------------------------------------------------
    # Test 3: Env beats file → when both MANIFOLD_DB and file db_path, env wins
    # -----------------------------------------------------------------------

    def test_3_env_beats_file_for_db_path(self):
        self._write_config({"db_path": "/from/file.db"})
        with patch.dict(os.environ, self._env({"MANIFOLD_DB": "/from/env.db"}), clear=True):
            self.assertEqual(config.db_path(), Path("/from/env.db"))

    # -----------------------------------------------------------------------
    # Test 4: File beats default → file snapshot_interval used when env unset
    # -----------------------------------------------------------------------

    def test_4_file_snapshot_interval_beats_default(self):
        self._write_config({"snapshot_interval": 7200})
        with patch.dict(os.environ, self._env(), clear=True):
            self.assertEqual(config.snapshot_interval_seconds(), 7200)

    # -----------------------------------------------------------------------
    # Test 5: Malformed JSON → no exception; defaults returned; one stderr warning
    # -----------------------------------------------------------------------

    def test_5_malformed_json_falls_back_to_defaults_with_warning(self):
        # Write invalid JSON
        with open(self._cfg_path, "w", encoding="utf-8") as f:
            f.write("{not valid json}")
        config._reset_config_cache()

        stderr_buf = io.StringIO()
        with patch.dict(os.environ, self._env(), clear=True):
            with patch.object(sys, "stderr", stderr_buf):
                result = config.load_config()
                db = config.db_path()

        self.assertEqual(result, {})
        self.assertEqual(db, Path.home() / ".claude" / "manifold.db")
        warning = stderr_buf.getvalue()
        self.assertIn("manifold: ignoring malformed config", warning)
        self.assertIn(self._cfg_path, warning)

    # -----------------------------------------------------------------------
    # Test 6: Unknown keys → ignored by resolvers; surfaced by config show
    # -----------------------------------------------------------------------

    def test_6_unknown_keys_ignored_by_resolvers_surfaced_by_show(self):
        self._write_config({"db_path": "/from/file.db", "typo_key": "oops"})
        with patch.dict(os.environ, self._env(), clear=True):
            loaded = config.load_config()
            # Unknown key is returned in the raw dict
            self.assertIn("typo_key", loaded)
            # But resolvers work fine (db_path resolved normally)
            self.assertEqual(config.db_path(), Path("/from/file.db"))
            # effective_settings surfaces the unknown key
            settings = config.effective_settings()
            self.assertIn("typo_key", settings.get("unrecognized", {}))

    # -----------------------------------------------------------------------
    # Test 7: Judge precedence: env > spec_config.judge_command > file > unset
    # -----------------------------------------------------------------------

    def test_7_judge_precedence_env_wins(self):
        from manifold.validate import _resolve_judge_command
        self._write_config({"judge_command": "file-judge"})
        spec_cfg = {"judge_command": "project-judge"}
        with patch.dict(os.environ, self._env({"MANIFOLD_JUDGE_CMD": "env-judge"}), clear=True):
            result = _resolve_judge_command(spec_cfg)
        self.assertEqual(result, "env-judge")

    def test_7_judge_precedence_spec_config_beats_file(self):
        from manifold.validate import _resolve_judge_command
        self._write_config({"judge_command": "file-judge"})
        spec_cfg = {"judge_command": "project-judge"}
        with patch.dict(os.environ, self._env(), clear=True):
            result = _resolve_judge_command(spec_cfg)
        self.assertEqual(result, "project-judge")

    def test_7_judge_precedence_file_beats_unset(self):
        from manifold.validate import _resolve_judge_command
        self._write_config({"judge_command": "file-judge"})
        spec_cfg = {}  # no per-project setting
        with patch.dict(os.environ, self._env(), clear=True):
            result = _resolve_judge_command(spec_cfg)
        self.assertEqual(result, "file-judge")

    def test_7_judge_precedence_unset_returns_empty(self):
        from manifold.validate import _resolve_judge_command
        # No env, no spec_config, no file judge_command
        spec_cfg = {}
        with patch.dict(os.environ, self._env(), clear=True):
            result = _resolve_judge_command(spec_cfg)
        self.assertEqual(result, "")

    # -----------------------------------------------------------------------
    # Test 8: config init writes file seeded from effective values; round-trips
    # -----------------------------------------------------------------------

    def test_8_config_init_writes_and_round_trips(self):
        # No file yet; env sets db path
        with patch.dict(os.environ, self._env({"MANIFOLD_DB": "/env/db.db"}), clear=True):
            result = config.config_init(self._cfg_path, force=False)
        self.assertTrue(result["ok"])
        self.assertTrue(Path(self._cfg_path).exists())
        # Reset cache so load_config picks up the newly written file
        config._reset_config_cache()
        with patch.dict(os.environ, self._env({"MANIFOLD_DB": "/env/db.db"}), clear=True):
            loaded = config.load_config()
        # The file should contain a db_path (from env at time of init)
        self.assertIn("db_path", loaded)

    # -----------------------------------------------------------------------
    # Test 9: config init clobber-refusal / --force overwrites
    # -----------------------------------------------------------------------

    def test_9_init_refuses_clobber_without_force(self):
        # Write initial file
        self._write_config({"db_path": "/original.db"})
        with patch.dict(os.environ, self._env(), clear=True):
            result = config.config_init(self._cfg_path, force=False)
        self.assertFalse(result["ok"])
        self.assertIn("already exists", result["message"])
        # Original file should be unchanged
        config._reset_config_cache()
        with patch.dict(os.environ, self._env(), clear=True):
            loaded = config.load_config()
        self.assertEqual(loaded.get("db_path"), "/original.db")

    def test_9_init_force_overwrites(self):
        self._write_config({"db_path": "/original.db"})
        with patch.dict(os.environ, self._env({"MANIFOLD_DB": "/new/db.db"}), clear=True):
            result = config.config_init(self._cfg_path, force=True)
        self.assertTrue(result["ok"])
        config._reset_config_cache()
        with patch.dict(os.environ, self._env(), clear=True):
            loaded = config.load_config()
        # After force overwrite, old value is gone; new db_path from env seed
        self.assertNotEqual(loaded.get("db_path"), "/original.db")

    # -----------------------------------------------------------------------
    # Test 10: config show source attribution
    # -----------------------------------------------------------------------

    def test_10_show_source_attribution(self):
        # File sets judge_command; env sets MANIFOLD_DB; snapshot_interval is default
        self._write_config({"judge_command": "file-judge"})
        with patch.dict(os.environ, self._env({"MANIFOLD_DB": "/env/db.db"}), clear=True):
            settings = config.effective_settings()

        self.assertEqual(settings["db_path"]["value"], Path("/env/db.db"))
        self.assertEqual(settings["db_path"]["source"], "env")

        self.assertEqual(settings["judge_command"]["value"], "file-judge")
        self.assertEqual(settings["judge_command"]["source"], "file")

        self.assertEqual(settings["snapshot_interval"]["value"], 3600)
        self.assertEqual(settings["snapshot_interval"]["source"], "default")


if __name__ == "__main__":
    unittest.main()
