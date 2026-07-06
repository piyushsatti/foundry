"""
Smoke test — exercises the four web-UI features end-to-end
through a live subprocess server.

Drives: dashboard render, validation trigger + detail, revision diff,
structural-field editor round-trip.
"""
import http.client
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pathsetup  # noqa: F401, E402

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = REPO_ROOT / "packages" / "manifold"
WEB_ROOT = REPO_ROOT / "apps" / "manifold-web"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServerProc:
    def __init__(self, db_path: str, port: int):
        self.port = port
        env = {
            **os.environ,
            "MANIFOLD_DB": db_path,
            "PYTHONPATH": f"{PKG_ROOT}:{WEB_ROOT}",
        }
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "manifold", "serve",
             "--host", "127.0.0.1", "--port", str(port)],
            cwd=str(PKG_ROOT), env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.time() + 5.0
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    return
            except OSError:
                time.sleep(0.05)
        out, err = self.proc.communicate(timeout=1)
        raise RuntimeError(
            f"server didn't bind on port {port}\nstdout: {out}\nstderr: {err}"
        )

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        if self.proc.stdout:
            self.proc.stdout.close()
        if self.proc.stderr:
            self.proc.stderr.close()


def _seed_db(db_path: str):
    """Seed a project with two nodes so the dashboard + edit flows have content."""
    code = (
        "from pathlib import Path; "
        "from manifold import db, schema, writes; "
        f"conn = db.connect(Path({db_path!r})); "
        "schema.bootstrap(conn); "
        "writes.register_project(conn, 'p', "
        "{'layers':[{'name':'intent'},{'name':'realizations'}]}); "
        "writes.create_node(conn, 'p', 'intent', 'I.1', 'Top', "
        "body='# Title\\n\\nbody.', actor='h'); "
        "writes.create_node(conn, 'p', 'realizations', 'R.1', 'Real', "
        "parents=['I.1'], actor='h'); "
        "conn.commit()"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=str(PKG_ROOT),
        env={**os.environ, "MANIFOLD_DB": db_path, "PYTHONPATH": str(PKG_ROOT)},
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"seed failed: {result.stderr}")


class TestV032Smoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db = str(Path(cls._tmp.name) / "smoke.db")
        _seed_db(cls.db)
        cls.port = _free_port()
        cls._server = ServerProc(cls.db, cls.port).__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._server.__exit__(None, None, None)
        cls._tmp.cleanup()

    def _get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("GET", path)
        r = c.getresponse()
        body = r.read().decode("utf-8")
        c.close()
        return r.status, body

    def _post_form(self, path, fields):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("POST", path, body=urllib.parse.urlencode(fields),
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
        r = c.getresponse()
        body = r.read().decode("utf-8")
        loc = r.getheader("Location") or ""
        c.close()
        return r.status, body, loc

    def test_1_project_page_renders_dashboard_and_trigger(self):
        status, body = self._get("/projects/p")
        self.assertEqual(status, 200)
        self.assertIn("Nodes per layer", body)
        self.assertIn("Run validation", body)
        self.assertIn("Revisions (7d)", body)

    def test_2_validation_trigger_redirects_to_detail(self):
        status, _, loc = self._post_form(
            "/projects/p/validations", {"with_verdicts": "on"})
        self.assertEqual(status, 303)
        self.assertTrue(loc.startswith("/projects/p/validations/"))
        status2, detail = self._get(loc)
        self.assertEqual(status2, 200)
        self.assertIn("finished", detail.lower())
        # Both seeded nodes appear in the verdicts table
        self.assertIn("I.1", detail)
        self.assertIn("R.1", detail)

    def test_3_revision_detail_renders_diff(self):
        status, body = self._get("/projects/p/nodes/I.1")
        self.assertEqual(status, 200)
        m = re.search(r"/projects/p/nodes/I\.1/revisions/(\d+)", body)
        self.assertIsNotNone(m, "no revision link on node page")
        status2, diff = self._get(m.group(0))
        self.assertEqual(status2, 200)
        # 'created' revision: no body diff, no field changes
        self.assertIn("Revision r", diff)

    def test_4_structural_edit_round_trip(self):
        # Get the edit page; verify structural panel + extract expected revision
        status, body = self._get("/projects/p/nodes/I.1/edit")
        self.assertEqual(status, 200)
        self.assertIn("Structural fields", body)
        m = re.search(r'name="expected_revision_id"\s+value="(\d+)"', body)
        self.assertIsNotNone(m)
        rev = m.group(1)
        # POST a title change with the structural-fields form
        status2, _, loc = self._post_form("/projects/p/nodes/I.1", {
            "expected_revision_id": rev,
            "title": "Renamed",
            "body": "# Title\n\nbody.",
            "layer": "intent",
            "kind": "spec",
            "target_status": "",
            "change_reason": "clarification",
        })
        self.assertEqual(status2, 303)
        # Confirm the change landed on the node page
        status3, node_page = self._get("/projects/p/nodes/I.1")
        self.assertEqual(status3, 200)
        self.assertIn("Renamed", node_page)

    def test_5_validation_then_dashboard_shows_last_validation(self):
        # Trigger a validation
        self._post_form("/projects/p/validations", {"with_verdicts": "on"})
        # Dashboard now shows "Last validation" with a link
        status, body = self._get("/projects/p")
        self.assertEqual(status, 200)
        self.assertIn("Last validation", body)
        self.assertIn("/projects/p/validations/", body)


if __name__ == "__main__":
    unittest.main()
