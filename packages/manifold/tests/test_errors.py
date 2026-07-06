"""
Tests for the error envelope module.

Verifies the envelope shape stays stable (audit requirement).
"""
import unittest
from manifold import errors, writes


class TestEnvelope(unittest.TestCase):
    def test_shape(self):
        e = errors.envelope("X", "msg", suggest=["a"], context={"k": "v"})
        self.assertEqual(set(e), {"error"})
        inner = e["error"]
        self.assertEqual(set(inner), {"code", "message", "retry", "suggest", "context"})
        self.assertEqual(inner["code"], "X")
        self.assertEqual(inner["retry"], "no")  # default
        self.assertEqual(inner["suggest"], ["a"])
        self.assertEqual(inner["context"], {"k": "v"})

    def test_retry_values(self):
        e = errors.envelope("X", "msg", retry=errors.RETRY_WITH_NEW_ARGS)
        self.assertEqual(e["error"]["retry"], "with_new_args")


class TestFromWritesException(unittest.TestCase):
    def test_node_already_exists(self):
        exc = writes.NodeAlreadyExists("p:n")
        e = errors.from_writes_exception(exc, project_id="p", node_id="n")
        self.assertEqual(e["error"]["code"], errors.NODE_ALREADY_EXISTS)
        self.assertEqual(e["error"]["context"]["project_id"], "p")
        self.assertEqual(e["error"]["context"]["node_id"], "n")

    def test_project_not_found_suggests_list_projects(self):
        exc = writes.ProjectNotFound("missing")
        e = errors.from_writes_exception(exc, project_id="missing")
        self.assertEqual(e["error"]["code"], errors.PROJECT_NOT_FOUND)
        self.assertIn("list_projects()", e["error"]["suggest"])

    def test_stale_revision_carries_current_revision_id(self):
        exc = writes.StaleRevision("stale", current_revision_id=42)
        e = errors.from_writes_exception(exc, project_id="p", node_id="n")
        self.assertEqual(e["error"]["code"], errors.STALE_REVISION)
        self.assertEqual(e["error"]["retry"], "with_new_args")
        self.assertEqual(e["error"]["context"]["current_revision_id"], 42)

    def test_invalid_transition(self):
        exc = writes.InvalidTransition("bad")
        e = errors.from_writes_exception(exc)
        self.assertEqual(e["error"]["code"], errors.INVALID_TRANSITION)
        self.assertEqual(e["error"]["retry"], "with_new_args")

    def test_missing_actor(self):
        exc = writes.MissingActor("empty")
        e = errors.from_writes_exception(exc)
        self.assertEqual(e["error"]["code"], errors.MISSING_ACTOR)
        self.assertEqual(e["error"]["retry"], "with_new_args")

    def test_unknown_exception_falls_through(self):
        exc = ValueError("random")
        e = errors.from_writes_exception(exc)
        self.assertEqual(e["error"]["code"], errors.INTERNAL_ERROR)
        self.assertIn("ValueError", e["error"]["message"])


class TestNotFoundEnvelopes(unittest.TestCase):
    def test_node(self):
        e = errors.not_found_envelope("node", project_id="p", node_id="X")
        self.assertEqual(e["error"]["code"], errors.NODE_NOT_FOUND)
        self.assertTrue(any("list_nodes" in s for s in e["error"]["suggest"]))

    def test_project(self):
        e = errors.not_found_envelope("project", project_id="missing")
        self.assertEqual(e["error"]["code"], errors.PROJECT_NOT_FOUND)

    def test_validation(self):
        e = errors.not_found_envelope("validation", validation_id=99)
        self.assertEqual(e["error"]["code"], errors.VALIDATION_NOT_FOUND)
        self.assertEqual(e["error"]["context"]["validation_id"], 99)


if __name__ == "__main__":
    unittest.main()
