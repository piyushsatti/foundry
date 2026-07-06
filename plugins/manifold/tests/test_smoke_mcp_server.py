"""
End-to-end smoke test for manifold (MCP server).
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pathsetup  # noqa: F401, E402

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = REPO_ROOT / "packages" / "manifold"
MCP_SCRIPT = REPO_ROOT / "plugins" / "manifold" / "server" / "mcp_server.py"
V02_REPO = PKG_ROOT


class MCPClient:
    """Minimal stdio JSON-RPC client for testing."""

    def __init__(self, db_path: str):
        env = {
            **os.environ,
            "MANIFOLD_DB": db_path,
            "PYTHONPATH": str(PKG_ROOT),
        }
        self.proc = subprocess.Popen(
            [sys.executable, str(MCP_SCRIPT)],
            env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
        )
        self._req_id = 0

    def call(self, method: str, params: dict | None = None,
             notify: bool = False) -> dict | None:
        self._req_id += 1
        req = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notify:
            req["id"] = self._req_id
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        if notify:
            return None
        line = self.proc.stdout.readline()
        return json.loads(line)

    def tool(self, name: str, args: dict | None = None) -> dict:
        resp = self.call("tools/call", {"name": name, "arguments": args or {}})
        text = resp["result"]["content"][0]["text"]
        return {"isError": resp["result"]["isError"], "payload": json.loads(text)}

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.wait(timeout=5)


class TestPhaseBSmoke(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.addCleanup(self._cleanup)
        self.client = MCPClient(self.db)
        self.addCleanup(self.client.close)
        # Per protocol, send initialize first
        init = self.client.call("initialize")
        self.assertIn("result", init)
        self.assertEqual(init["result"]["serverInfo"]["name"], "manifold")

    def _cleanup(self):
        for s in ("", "-shm", "-wal"):
            p = Path(self.db + s)
            if p.exists():
                p.unlink()

    def test_tools_list_over_stdio(self):
        resp = self.client.call("tools/list")
        tools = resp["result"]["tools"]
        self.assertGreaterEqual(len(tools), 29)
        names = {t["name"] for t in tools}
        self.assertIn("list_projects", names)
        self.assertIn("import_project", names)

    def test_list_projects_empty(self):
        result = self.client.tool("list_projects")
        self.assertFalse(result["isError"])
        self.assertEqual(result["payload"]["projects"], [])

    def test_register_project_then_peek(self):
        result = self.client.tool("register_project", {
            "project_id": "p1",
            "spec_config": {"layers": [{"name": "intent"}, {"name": "realizations"}]},
            "label": "Test Project",
        })
        self.assertFalse(result["isError"], msg=result["payload"])

        result = self.client.tool("peek_project", {"project_id": "p1"})
        self.assertFalse(result["isError"])
        self.assertEqual(result["payload"]["project"]["project_id"], "p1")

    def test_create_then_peek_node(self):
        self.client.tool("register_project", {
            "project_id": "p1",
            "spec_config": {"layers": [{"name": "intent"}]},
        })
        r = self.client.tool("create_node", {
            "project_id": "p1", "layer": "intent",
            "node_id": "I.1", "title": "first",
            "actor": "agent:test",
        })
        self.assertFalse(r["isError"], msg=r["payload"])
        rev = r["payload"]["revision_id"]
        self.assertIsInstance(rev, int)

        r2 = self.client.tool("peek_node",
                                {"project_id": "p1", "node_id": "I.1"})
        self.assertFalse(r2["isError"])
        self.assertEqual(r2["payload"]["node"]["title"], "first")

    def test_unknown_tool_envelope_isError(self):
        r = self.client.tool("nope", {})
        self.assertTrue(r["isError"])
        self.assertEqual(r["payload"]["error"]["code"], "UNKNOWN_TOOL")


@unittest.skipUnless(V02_REPO.exists() and (V02_REPO / "specs" / "spec.yaml").is_file(),
                     f"requires v0.2 spec at {V02_REPO}")
class TestPhaseBSmokeRealData(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.db = self.tmp.name
        self.addCleanup(self._cleanup)
        self.client = MCPClient(self.db)
        self.addCleanup(self.client.close)
        self.client.call("initialize")

    def _cleanup(self):
        for s in ("", "-shm", "-wal"):
            p = Path(self.db + s)
            if p.exists():
                p.unlink()

    def test_import_v02_via_mcp(self):
        r = self.client.tool("import_project", {
            "repo_root": str(V02_REPO),
            "actor": "agent:smoke",
        })
        self.assertFalse(r["isError"], msg=r["payload"])
        self.assertGreaterEqual(r["payload"]["nodes_imported"], 30)

        r2 = self.client.tool("peek_node", {
            "project_id": "manifold", "node_id": "I.1",
        })
        self.assertFalse(r2["isError"])
        self.assertEqual(r2["payload"]["node"]["node_id"], "I.1")

        r3 = self.client.tool("list_nodes", {
            "project_id": "manifold", "layer": "intent",
        })
        self.assertFalse(r3["isError"])
        self.assertGreaterEqual(len(r3["payload"]["nodes"]), 3)


if __name__ == "__main__":
    unittest.main()
