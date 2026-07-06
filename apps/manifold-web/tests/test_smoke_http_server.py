"""
End-to-end smoke test for manifold (HTTP/HTML/JSON API).

Runs the web server as a subprocess. Hits it with http.client. Verifies:
- /static/codemirror/codemirror.min.js is served
- /api/v1/projects round-trips
- /projects/<p>/nodes/<n>/edit returns the form with CodeMirror tags
- POST /projects/<p>/nodes/<n> writes a revision via the optimistic-concurrency form path
- PATCH /api/v1/projects/<p>/nodes/<n> requires If-Match and 409s on mismatch
"""
import http.client
import json
import os
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
V02_REPO = PKG_ROOT


def _free_port() -> int:
    """Pick an unused TCP port to avoid colliding with concurrent test runs."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServerProc:
    """Context manager that starts/stops the manifold web server subprocess."""

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
        # Wait for the server to bind. Poll the port for up to 5s.
        deadline = time.time() + 5.0
        while time.time() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    return
            except OSError:
                time.sleep(0.05)
        # Didn't come up
        out, err = self.proc.communicate(timeout=1)
        raise RuntimeError(
            f"server didn't bind on port {port}\nstdout: {out}\nstderr: {err}"
        )

    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        # Drain pipes to avoid ResourceWarning
        try:
            if self.proc.stdout:
                self.proc.stdout.close()
            if self.proc.stderr:
                self.proc.stderr.close()
        except Exception:
            pass


def _request(port: int, method: str, path: str, *,
             headers=None, body=None) -> tuple[int, dict, bytes]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        return resp.status, dict(resp.getheaders()), resp.read()
    finally:
        conn.close()


def _import_v02_into(db_path: str):
    """Use the CLI to import the v0.2 self-spec so the smoke server has data."""
    env = {**os.environ, "MANIFOLD_DB": db_path}
    subprocess.run(
        [sys.executable, "-m", "manifold", "import", str(V02_REPO)],
        cwd=str(PKG_ROOT), env=env,
        check=True, capture_output=True,
    )


class TestPhaseCSmoke(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.addCleanup(self._cleanup_db)
        if V02_REPO.exists() and (V02_REPO / "specs" / "spec.yaml").is_file():
            _import_v02_into(self.db)
        self.port = _free_port()
        self.server = ServerProc(self.db, self.port)
        self.addCleanup(self.server.close)

    def _cleanup_db(self):
        for s in ("", "-shm", "-wal"):
            p = Path(self.db + s)
            if p.exists():
                p.unlink()

    def test_index_responds_200(self):
        status, _, body = _request(self.port, "GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Projects", body)

    def test_static_codemirror_is_served(self):
        status, headers, body = _request(
            self.port, "GET", "/static/codemirror/codemirror.min.js")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"],
                          "application/javascript; charset=utf-8")
        # Sanity: actual JS, not an HTML 404 page
        self.assertGreater(len(body), 1000)
        self.assertIn(b"CodeMirror", body)

    def test_path_traversal_blocked(self):
        status, _, _ = _request(
            self.port, "GET", "/static/../../manifold_web/web.py")
        self.assertEqual(status, 404)

    def test_api_list_projects_json(self):
        status, headers, body = _request(self.port, "GET", "/api/v1/projects")
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/json")
        payload = json.loads(body)
        self.assertIn("projects", payload)


@unittest.skipUnless(V02_REPO.exists() and (V02_REPO / "specs" / "spec.yaml").is_file(),
                     f"requires v0.2 spec at {V02_REPO}")
class TestPhaseCSmokeRealData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.addCleanup(self._cleanup_db)
        _import_v02_into(self.db)
        self.port = _free_port()
        self.server = ServerProc(self.db, self.port)
        self.addCleanup(self.server.close)

    def _cleanup_db(self):
        for s in ("", "-shm", "-wal"):
            p = Path(self.db + s)
            if p.exists():
                p.unlink()

    def test_project_page_shows_imported_nodes(self):
        status, _, body = _request(self.port, "GET", "/projects/manifold")
        self.assertEqual(status, 200)
        # Imported nodes should appear
        self.assertIn(b"I.1", body)
        self.assertIn(b"intent", body)

    def test_node_page_renders_imported_body(self):
        status, _, body = _request(
            self.port, "GET", "/projects/manifold/nodes/I.1")
        self.assertEqual(status, 200)
        self.assertIn(b"I.1", body)
        # Body should be present (markdown-rendered)
        self.assertIn(b"<p>", body)

    def test_edit_form_includes_codemirror(self):
        status, _, body = _request(
            self.port, "GET", "/projects/manifold/nodes/I.1/edit")
        self.assertEqual(status, 200)
        self.assertIn(b"/static/codemirror/codemirror.min.js", body)
        self.assertIn(b"expected_revision_id", body)

    def test_post_edit_creates_revision(self):
        # Get current revision
        status, _, body = _request(
            self.port, "GET", "/api/v1/projects/manifold/nodes/I.1")
        self.assertEqual(status, 200)
        node = json.loads(body)
        rev = node["current_revision_id"]

        # Submit form-encoded update
        form_body = urllib.parse.urlencode({
            "expected_revision_id": str(rev),
            "body": "# Edited via web\n\nNew body.",
            "actor": "human:smoke-test",
        })
        status, headers, _ = _request(
            self.port, "POST", "/projects/manifold/nodes/I.1",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            body=form_body,
        )
        # Should redirect to node page
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/projects/manifold/nodes/I.1")

        # Verify new revision in the DB via API
        status, _, body = _request(
            self.port, "GET", "/api/v1/projects/manifold/nodes/I.1")
        new_node = json.loads(body)
        self.assertGreater(new_node["current_revision_id"], rev)
        self.assertIn("Edited via web", new_node["body"])

    def test_api_patch_requires_if_match(self):
        # No If-Match
        status, _, body = _request(
            self.port, "PATCH", "/api/v1/projects/manifold/nodes/I.1",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"fields": {"title": "x"}, "actor": "h"}),
        )
        self.assertEqual(status, 400)
        payload = json.loads(body)
        self.assertEqual(payload["error"]["code"], "INVALID_ARGUMENTS")

    def test_api_patch_409_on_stale(self):
        status, _, body = _request(
            self.port, "PATCH", "/api/v1/projects/manifold/nodes/I.1",
            headers={"Content-Type": "application/json",
                      "If-Match": "999999"},
            body=json.dumps({"fields": {"title": "x"}, "actor": "h"}),
        )
        self.assertEqual(status, 409)
        payload = json.loads(body)
        self.assertEqual(payload["error"]["code"], "STALE_REVISION")


if __name__ == "__main__":
    unittest.main()
