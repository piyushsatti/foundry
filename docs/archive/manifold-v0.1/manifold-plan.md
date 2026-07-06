# manifold v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship manifold v0.1 with KAOS substrate (DAG-across-layers), compass minimum (default `target_status="planned"`, `next-leaves` API), and anti-drift (rationale, alternatives_considered, change_reason, drift-report).

**Architecture:** Stays on KAOS AND-refinement. Relaxes strict tree-across-layers to AND/OR DAG. Adds `rationale` + `alternatives_considered` columns to `nodes` and `change_reason` to `revisions`. New CLI commands: `next-leaves`, `drift-report`. Backfill existing 3 self-spec projects.

**Tech Stack:** Python stdlib only. SQLite via existing `manifold/db.py`. CodeMirror 5 (already vendored). HTTP via stdlib `ThreadingHTTPServer` (already in place). MCP via stdio JSON-RPC 2.0 (already wired).

**Parallelization:** Tasks are grouped into 4 waves. Tasks within a wave have no dependencies on each other; tasks in later waves depend on earlier ones. Dispatch subagents in parallel within each wave.

**Working directory:** `plugins/manifold/skills/manifold/`

---

## Wave 1 — substrate (3 parallel tasks)

These three tasks have no shared files and can run fully in parallel.

### Task 1: DAG migration (Stream A)

**Files:**
- Modify: `manifold/validate.py` — rename `check_tree_property` → `check_dag_property`, drop single-parent check, keep cycle check.
- Modify: `manifold/writes.py` — drop any single-parent assertions in `create_node` / `update_node`.
- Test: `tests/test_validate.py` — add multi-parent test cases.

- [ ] **Step 1: Write failing test for multi-parent acceptance**

```python
# tests/test_validate.py
class TestDAGAcrossLayers(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        writes.register_project(self.conn, "p", spec_config={
            "layers": [
                {"name": "L0"}, {"name": "L1"}, {"name": "L2"}
            ]
        }, actor="human:test")
        writes.create_node(self.conn, "p", "L0", "I.1", "intent 1", actor="human:test")
        writes.create_node(self.conn, "p", "L0", "I.2", "intent 2", actor="human:test")
        writes.create_node(self.conn, "p", "L1", "C.1", "cap 1",
                            parents=["I.1", "I.2"], actor="human:test")  # multi-parent

    def test_multi_parent_validates_clean(self):
        validate.run_structural_checks(self.conn, "p")
        issues = list(self.conn.execute(
            "SELECT * FROM validations WHERE project_id='p' ORDER BY validation_id DESC LIMIT 1"
        ))
        self.assertEqual(issues[0]["error_count"], 0)
```

- [ ] **Step 2: Run test to verify it fails**

```
cd skills/manifold && python3 -m unittest tests.test_validate.TestDAGAcrossLayers.test_multi_parent_validates_clean -v
```

Expected: FAIL with "tree property violated: C.1 has 2 parents" or similar.

- [ ] **Step 3: Rename and relax `check_tree_property`**

In `manifold/validate.py`:

```python
def check_dag_property(nodes_by_id, edges, layer_order):
    """v0.4: relaxed from strict tree. Allows multi-parent across layers.
    Still enforces: acyclic across layers, layer ordering."""
    issues = []
    # acyclic check across layers — DFS from each node, fail on back-edge
    parents_of = defaultdict(list)
    for e in edges:
        if e["edge_kind"] == "parent":
            parents_of[e["src_node_id"]].append(e["dst_node_id"])

    def has_cycle(start):
        stack = [(start, set([start]))]
        while stack:
            node, path = stack.pop()
            for parent in parents_of.get(node, []):
                if parent in path:
                    return True
                stack.append((parent, path | {parent}))
        return False

    for node_id in nodes_by_id:
        if has_cycle(node_id):
            issues.append({"kind": "cycle_across_layers", "node_id": node_id,
                           "severity": "error"})
    # layer ordering check (existing logic)
    # ... preserve existing checks here ...
    return issues
```

Replace all callers of `check_tree_property` with `check_dag_property`.

- [ ] **Step 4: Verify propagation handles multi-parent**

In `manifold/validate.py:propagate_failures` — the existing code walks all parents in a loop. Verify with test:

```python
def test_multi_parent_propagation(self):
    # C.1 has parents [I.1, I.2]; mark C.1 violated; both parents should invalidate.
    writes.set_verdict_status(self.conn, "p", "C.1", "violated", actor="human:test")
    validate.propagate_failures(self.conn, "p")
    i1 = queries.get_node(self.conn, "p", "I.1")
    i2 = queries.get_node(self.conn, "p", "I.2")
    self.assertEqual(i1["verdict_status"], "invalidated_by_descendant")
    self.assertEqual(i2["verdict_status"], "invalidated_by_descendant")
```

- [ ] **Step 5: Deprecate `realized_by_external` (advisory only)**

In `manifold/validate.py`, in the per-node walk:

```python
if node.get("realized_by_external"):
    issues.append({
        "kind": "deprecated_field",
        "node_id": node_id,
        "field": "realized_by_external",
        "severity": "advisory",
        "message": "realized_by_external is deprecated as of v0.4; multi-parent edges replace it.",
    })
```

- [ ] **Step 6: Run tests; all pass**

```
cd skills/manifold && python3 -m unittest discover -v
```

Expected: 0 failures. ~300 tests pass plus the new multi-parent tests.

- [ ] **Step 7: Commit**

```
git add manifold/validate.py manifold/writes.py tests/test_validate.py
git commit -F /tmp/v04-task1-commit-msg.txt
```

Commit message: `feat(manifold-v04): relax tree-across-layers to AND/OR DAG (KAOS substrate)`

---

### Task 2: Compass minimum (Stream B)

**Files:**
- Modify: `manifold/writes.py` — default `target_status="planned"` in `create_node`.
- Modify: `manifold/validate.py` — advisory warning when `target_status=""`.
- Modify: `manifold/queries.py` — add `next_leaves(conn, project_id, layer=None)` function.
- Test: `tests/test_writes.py`, `tests/test_validate.py`, `tests/test_queries.py`.

- [ ] **Step 1: Write failing test for default target_status**

```python
# tests/test_writes.py
class TestDefaultTargetStatus(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        writes.register_project(self.conn, "p", spec_config={
            "layers": [{"name": "L0"}]
        }, actor="human:test")

    def test_new_node_defaults_to_planned(self):
        writes.create_node(self.conn, "p", "L0", "A", "node A", actor="human:test")
        n = queries.get_node(self.conn, "p", "A")
        self.assertEqual(n["target_status"], "planned")
```

- [ ] **Step 2: Run test, expect failure**

- [ ] **Step 3: Update `writes.create_node`**

```python
# manifold/writes.py
def create_node(conn, project_id, layer, node_id, title, *,
                kind="spec", body="", parents=None, peers_depends_on=None,
                realized_by_external="", target_status=None,  # was ""
                verdict_mechanism="human_signoff", actor, ...):
    # ...
    if target_status is None:
        target_status = "planned"  # v0.4 default
    # ... rest unchanged
```

- [ ] **Step 4: Write failing test for advisory warning**

```python
def test_empty_target_status_emits_advisory(self):
    # Create a node with explicit target_status="" (backwards-compat)
    writes.create_node(self.conn, "p", "L0", "A", "A",
                       target_status="", actor="human:test")
    validate.run_structural_checks(self.conn, "p")
    issues = list(self.conn.execute(
        "SELECT * FROM issues WHERE project_id='p' AND node_id='A'"
    ))
    advisories = [i for i in issues if i["severity"] == "advisory"]
    self.assertTrue(any(i["kind"] == "missing_target_status" for i in advisories))
```

- [ ] **Step 5: Add advisory in `validate.check_targets`**

```python
# manifold/validate.py
def check_targets(nodes_by_id):
    issues = []
    for node_id, node in nodes_by_id.items():
        if node.get("kind") == "constraint":
            continue
        if not node.get("target_status"):
            issues.append({
                "kind": "missing_target_status",
                "node_id": node_id,
                "severity": "advisory",
                "message": "target_status is unset. Default to 'planned' on next edit.",
            })
        # ... existing state machine checks ...
    return issues
```

- [ ] **Step 6: Write failing test for `next_leaves`**

```python
# tests/test_queries.py
class TestNextLeaves(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect(":memory:")
        writes.register_project(self.conn, "p", spec_config={
            "layers": [{"name": "L0"}, {"name": "L1"}]
        }, actor="human:test")
        writes.create_node(self.conn, "p", "L0", "I", "intent", actor="human:test")
        writes.create_node(self.conn, "p", "L1", "C", "cap", parents=["I"], actor="human:test")
        # I has child C, so I is not a leaf. C is a leaf.

    def test_returns_leaf_only(self):
        result = queries.next_leaves(self.conn, "p")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["node_id"], "C")

    def test_filters_by_layer(self):
        result = queries.next_leaves(self.conn, "p", layer="L0")
        self.assertEqual(len(result), 0)  # I is at L0 but not a leaf
```

- [ ] **Step 7: Implement `queries.next_leaves`**

```python
# manifold/queries.py
def next_leaves(conn, project_id, layer=None):
    """Return leaves whose target_status is in {planned, in_progress, ""}.
    Sorted by layer (top-to-bottom per spec_config), then node_id."""
    params = [project_id]
    layer_clause = ""
    if layer is not None:
        layer_clause = "AND n.layer = ?"
        params.append(layer)

    rows = conn.execute(f"""
        SELECT n.* FROM nodes n
        WHERE n.project_id = ?
          AND n.deleted_at IS NULL
          AND (n.target_status IN ('planned', 'in_progress') OR n.target_status = '')
          AND NOT EXISTS (
            SELECT 1 FROM node_edges e
            WHERE e.project_id = n.project_id
              AND e.dst_node_id = n.node_id
              AND e.edge_kind = 'parent'
          )
          {layer_clause}
        ORDER BY n.layer, n.node_id
    """, params).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 8: Run all tests; all pass**

- [ ] **Step 9: Commit**

```
git commit -F /tmp/v04-task2-commit-msg.txt
```

Message: `feat(manifold-v04): default target_status=planned, advisory warning on unset, queries.next_leaves`

---

### Task 3: Schema migration v1→v2 (Stream C)

**Files:**
- Modify: `manifold/schema.sql` — add columns to nodes and revisions.
- Modify: `manifold/db.py` — `bootstrap` detects schema_version and applies migration.
- Modify: `manifold/config.py` — `SCHEMA_VERSION = 2`.
- Test: `tests/test_db.py` — migration is idempotent; existing DBs upgrade cleanly.

- [ ] **Step 1: Update schema.sql (fresh schema for new DBs)**

```sql
-- manifold/schema.sql
CREATE TABLE IF NOT EXISTS nodes (
    -- ... existing columns ...
    rationale TEXT,                       -- v0.4
    alternatives_considered TEXT,         -- v0.4
    -- ...
);

CREATE TABLE IF NOT EXISTS revisions (
    -- ... existing columns ...
    change_reason TEXT,                   -- v0.4
    -- ...
);
```

- [ ] **Step 2: Bump `SCHEMA_VERSION` in config.py**

```python
# manifold/config.py
SCHEMA_VERSION = 2  # was 1
```

- [ ] **Step 3: Write failing test for migration**

```python
# tests/test_db.py
class TestSchemaMigrationV1toV2(unittest.TestCase):
    def test_v1_db_upgrades_idempotently(self):
        # Create a v1 DB (no rationale column)
        path = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(path)
        conn.executescript(self.v1_schema_sql)  # minimal v1 schema
        conn.execute("INSERT INTO schema_meta (key, value) VALUES ('schema_version', '1')")
        conn.commit()
        conn.close()

        # Open via manifold.db.connect, which should upgrade
        conn = db.connect(path)
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(nodes)")]
        self.assertIn("rationale", cols)
        self.assertIn("alternatives_considered", cols)
        rev_cols = [r["name"] for r in conn.execute("PRAGMA table_info(revisions)")]
        self.assertIn("change_reason", rev_cols)

        # Re-open; idempotent
        conn.close()
        conn = db.connect(path)
        cols2 = [r["name"] for r in conn.execute("PRAGMA table_info(nodes)")]
        self.assertEqual(cols, cols2)
```

- [ ] **Step 4: Implement migration in `db.bootstrap`**

```python
# manifold/db.py
def _apply_migrations(conn):
    """Idempotent schema upgrades."""
    current = _get_schema_version(conn)
    if current is None:
        # fresh DB; full bootstrap already happened
        return
    if current < 2:
        # v1 → v2
        for stmt in [
            "ALTER TABLE nodes ADD COLUMN rationale TEXT",
            "ALTER TABLE nodes ADD COLUMN alternatives_considered TEXT",
            "ALTER TABLE revisions ADD COLUMN change_reason TEXT",
        ]:
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    raise
        conn.execute("UPDATE schema_meta SET value = ? WHERE key = 'schema_version'",
                     (str(config.SCHEMA_VERSION),))
```

Call `_apply_migrations(conn)` in `bootstrap` after schema is loaded.

- [ ] **Step 5: Run all tests; all pass**

- [ ] **Step 6: Commit**

Message: `feat(manifold-v04): schema v2 — add rationale, alternatives_considered, change_reason`

---

## Wave 2 — surfaces and APIs (4 parallel tasks)

Begin after Wave 1 commits land.

### Task 4: Primary-parent render convention (Stream A)

**Files:**
- Modify: `manifold/html.py` — node detail page shows all parents; primary distinguished.
- Modify: `manifold/web.py` — render mode uses primary parent for narrative tree.
- Test: `tests/test_web.py`, `tests/test_html.py`.

- [ ] **Step 1: Write test that the first parent is displayed as primary**

```python
def test_multi_parent_html_marks_first_as_primary(self):
    # ... create node C with parents=["A", "B"] ...
    body = html.node_detail(self.conn, "p", "C")
    self.assertIn('class="primary-parent"', body)  # A is primary
    self.assertIn('A', body)
    self.assertIn('B', body)  # other parents shown as cross-refs
```

- [ ] **Step 2: Update node detail rendering**

```python
# manifold/html.py
def parents_panel(parents):
    if not parents:
        return ""
    primary = parents[0]
    others = parents[1:]
    out = f'<div class="parents-panel">'
    out += f'<div class="primary-parent"><strong>Primary:</strong> <a href="{primary}">{primary}</a></div>'
    if others:
        out += '<div class="other-parents">Also satisfies: '
        out += ', '.join(f'<a href="{p}">{p}</a>' for p in others)
        out += '</div>'
    out += '</div>'
    return out
```

- [ ] **Step 3: Update CSS for primary-parent**

Add CSS rule:
```css
.primary-parent { font-weight: 600; }
.other-parents { color: var(--muted); font-size: 0.9em; }
```

- [ ] **Step 4: Tests pass; commit**

Message: `feat(manifold-v04): primary-parent render convention for multi-parent nodes`

---

### Task 5: `next-leaves` surfaces (CLI + HTTP + MCP) (Stream B)

**Files:**
- Modify: `manifold/cli.py` — add `next-leaves` subcommand.
- Modify: `manifold/web.py` — add HTTP route + JSON API.
- Modify: `manifold/mcp_server.py` — add `next_leaves` tool.
- Test: `tests/test_cli.py`, `tests/test_web.py`, `tests/test_mcp_server.py`.

- [ ] **Step 1: Failing test for CLI**

```python
def test_cli_next_leaves(self):
    # ... seed DB with a multi-layer spec ...
    result = subprocess.run(
        ["python3", "-m", "manifold.cli", "--db", str(self.db_path),
         "next-leaves", "p"],
        capture_output=True, text=True
    )
    self.assertEqual(result.returncode, 0)
    self.assertIn("realizations", result.stdout)  # leaf layer present
```

- [ ] **Step 2: Add `next-leaves` CLI subcommand**

```python
# manifold/cli.py
def _cmd_next_leaves(args):
    conn = db.connect()
    rows = queries.next_leaves(conn, args.project_id, layer=args.layer)
    print(f"{'NODE':<14} {'LAYER':<16} {'TARGET':<14} {'VERDICT':<14} {'MECH':<20} TITLE")
    print("-" * 100)
    for r in rows:
        print(f"{r['node_id']:<14} {r['layer']:<16} {r['target_status']:<14} "
              f"{r['verdict_status'] or '(unset)':<14} "
              f"{r['verdict_mechanism'] or '(unset)':<20} {r['title']}")
    return 0
```

Wire into the subparser:
```python
sp = subparsers.add_parser("next-leaves")
sp.add_argument("project_id")
sp.add_argument("--layer", default=None)
sp.set_defaults(func=_cmd_next_leaves)
```

- [ ] **Step 3: Failing test for HTTP route**

```python
def test_http_next_leaves(self):
    response = self.client.get("/api/v1/projects/p/next-leaves")
    self.assertEqual(response.status, 200)
    data = json.loads(response.body)
    self.assertIsInstance(data, list)
```

- [ ] **Step 4: Implement HTTP route**

```python
# manifold/web.py
def api_next_leaves(handler, project_id, query_params):
    conn = handler.conn
    layer = query_params.get("layer", [None])[0]
    rows = queries.next_leaves(conn, project_id, layer=layer)
    return _json_response(handler, 200, rows)
```

Register in `HANDLERS_API`:
```python
HANDLERS_API[("GET", re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/next-leaves$"))] = api_next_leaves
```

- [ ] **Step 5: Add MCP tool**

```python
# manifold/mcp_server.py
TOOLS["manifold__next_leaves"] = {
    "description": "Return leaf nodes ready to be worked on (target_status in planned/in_progress/unset).",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_id": {"type": "string"},
            "layer": {"type": "string"},
        },
        "required": ["project_id"],
    },
    "handler": lambda args: queries.next_leaves(get_conn(), args["project_id"], layer=args.get("layer")),
}
```

- [ ] **Step 6: All tests pass; commit**

Message: `feat(manifold-v04): next-leaves CLI + HTTP + MCP surfaces`

---

### Task 6: writes API for rationale + alternatives + change_reason (Stream C)

**Files:**
- Modify: `manifold/writes.py` — `create_node` and `update_node` accept new kwargs; revision capture includes them.
- Modify: `manifold/validate.py` — advisory warnings for missing rationale and missing change_reason.
- Test: `tests/test_writes.py`, `tests/test_validate.py`.

- [ ] **Step 1: Failing test for rationale roundtrip**

```python
def test_rationale_roundtrip(self):
    writes.create_node(self.conn, "p", "L0", "A", "node A",
                       rationale="exists because Q",
                       alternatives_considered="X considered, rejected due to Y",
                       actor="human:test")
    n = queries.get_node(self.conn, "p", "A")
    self.assertEqual(n["rationale"], "exists because Q")
    self.assertEqual(n["alternatives_considered"], "X considered, rejected due to Y")
```

- [ ] **Step 2: Update `writes.create_node` and `writes.update_node`**

```python
def create_node(conn, project_id, layer, node_id, title, *,
                # ... existing kwargs ...
                rationale=None, alternatives_considered=None,
                actor, ...):
    # ...
    conn.execute("""
        INSERT INTO nodes (..., rationale, alternatives_considered, ...)
        VALUES (..., ?, ?, ...)
    """, (..., rationale, alternatives_considered, ...))
    # capture in revision snapshot too
```

```python
def update_node(conn, project_id, node_id, fields, *,
                expected_revision_id, change_reason=None, actor):
    # ...
    if change_reason is None:
        change_reason = "evolution"  # default; advisory will flag if not set explicitly
    # ... apply field updates ...
    conn.execute("""
        INSERT INTO revisions (..., change_reason, ...)
        VALUES (..., ?, ...)
    """, (..., change_reason, ...))
```

- [ ] **Step 3: Failing test for change_reason advisory**

```python
def test_missing_change_reason_emits_advisory(self):
    # create node, then update without change_reason
    writes.create_node(self.conn, "p", "L0", "A", "A", actor="human:test")
    n = queries.get_node(self.conn, "p", "A")
    writes.update_node(self.conn, "p", "A", {"title": "new title"},
                       expected_revision_id=n["current_revision_id"], actor="human:test")
    # default of evolution was set; advisory should fire if author didn't choose explicitly
    # (this is captured via a write-time advisory, optional implementation)
```

- [ ] **Step 4: Failing test for rationale advisory**

```python
def test_missing_rationale_emits_advisory(self):
    writes.create_node(self.conn, "p", "L0", "A", "A", actor="human:test")  # no rationale
    validate.run_structural_checks(self.conn, "p")
    issues = list(self.conn.execute("SELECT * FROM issues WHERE node_id='A' AND severity='advisory'"))
    self.assertTrue(any(i["kind"] == "missing_rationale" for i in issues))
```

- [ ] **Step 5: Add advisory in `validate.check_rationale` (new check)**

```python
# manifold/validate.py
def check_rationale(nodes_by_id):
    issues = []
    for node_id, node in nodes_by_id.items():
        if node.get("kind") == "constraint":
            continue
        if not node.get("rationale"):
            issues.append({
                "kind": "missing_rationale",
                "node_id": node_id,
                "severity": "advisory",
                "message": "rationale is unset. Add WHY this node exists.",
            })
    return issues
```

Wire `check_rationale` into the structural-check pipeline.

- [ ] **Step 6: All tests pass; commit**

Message: `feat(manifold-v04): writes accept rationale/alternatives/change_reason; advisories on missing`

---

### Task 7: drift-report queries (Stream C)

**Files:**
- Modify: `manifold/queries.py` — add `drift_revisions`, `rationale_changes_without_clarification`.
- Test: `tests/test_queries.py`.

- [ ] **Step 1: Failing test for `drift_revisions`**

```python
def test_drift_revisions(self):
    # ... seed some revisions with various change_reasons ...
    drift = queries.drift_revisions(self.conn, "p", since="2026-01-01T00:00:00Z")
    self.assertTrue(all(r["change_reason"] in ("drift", "other") or not r["change_reason"]
                        for r in drift))
```

- [ ] **Step 2: Implement queries**

```python
def drift_revisions(conn, project_id, *, since=None, include_other=True):
    """Revisions flagged as drift, or with no change_reason set, or 'other'."""
    where = ["project_id = ?"]
    params = [project_id]
    if since:
        where.append("created_at >= ?")
        params.append(since)
    reasons = ["drift", "", None]
    if include_other:
        reasons.append("other")
    placeholders = ",".join("?" for _ in reasons)
    where.append(f"(change_reason IN ({placeholders}) OR change_reason IS NULL)")
    params.extend(reasons)
    sql = f"SELECT * FROM revisions WHERE {' AND '.join(where)} ORDER BY created_at DESC"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]

def rationale_changes_without_clarification(conn, project_id, *, since=None):
    """Find revisions where the rationale field changed but change_reason is NOT 'clarification' or 'correction'."""
    where = ["project_id = ?"]
    params = [project_id]
    if since:
        where.append("created_at >= ?")
        params.append(since)
    sql = f"""
        SELECT r.* FROM revisions r
        WHERE {' AND '.join(where)}
          AND change_reason NOT IN ('clarification', 'correction')
          AND change_summary LIKE '%rationale%'
    """
    return [dict(row) for row in conn.execute(sql, params).fetchall()]
```

- [ ] **Step 3: Tests pass; commit**

Message: `feat(manifold-v04): drift_revisions and rationale_changes_without_clarification queries`

---

## Wave 3 — UX and surfaces for anti-drift (3 parallel tasks)

Begin after Wave 2 commits land.

### Task 8: drift-report CLI + HTTP + MCP

**Files:**
- Modify: `manifold/cli.py` — `drift-report` subcommand.
- Modify: `manifold/web.py` — `/projects/<p>/drift-report` HTML view + API endpoint.
- Modify: `manifold/html.py` — drift report HTML rendering.
- Modify: `manifold/mcp_server.py` — `drift_report` tool.
- Test: existing test files extended.

- [ ] **Step 1: CLI implementation**

```python
def _cmd_drift_report(args):
    conn = db.connect()
    drift = queries.drift_revisions(conn, args.project_id, since=args.since,
                                     include_other=args.include_other)
    print(f"Drift Report — {args.project_id}")
    print(f"  since: {args.since or 'beginning'}")
    print(f"  {len(drift)} potentially-drift revisions found")
    for r in drift:
        print(f"  [{r['created_at']}] {r['node_id']}: reason={r['change_reason'] or '(unset)'}")
        print(f"    {r['change_summary']}")
    return 0
```

- [ ] **Step 2: HTTP route + HTML**

```python
# manifold/web.py
def view_drift_report(handler, project_id, query_params):
    since = query_params.get("since", [None])[0]
    drift = queries.drift_revisions(handler.conn, project_id, since=since)
    rat = queries.rationale_changes_without_clarification(handler.conn, project_id, since=since)
    body = html.drift_report_body(project_id, drift, rat, since)
    return _html_response(handler, 200, body)
```

```python
# manifold/html.py
def drift_report_body(project_id, drift, rationale_changes, since):
    # ... render two sections; table for drift revisions; table for rationale changes ...
```

- [ ] **Step 3: MCP tool**

```python
TOOLS["manifold__drift_report"] = {
    "description": "Report potentially-drift revisions in a project.",
    "input_schema": {
        "type": "object",
        "properties": {
            "project_id": {"type": "string"},
            "since": {"type": "string", "format": "date-time"},
        },
        "required": ["project_id"],
    },
    "handler": lambda args: {
        "drift_revisions": queries.drift_revisions(get_conn(), args["project_id"],
                                                    since=args.get("since")),
        "rationale_changes": queries.rationale_changes_without_clarification(
            get_conn(), args["project_id"], since=args.get("since")),
    },
}
```

- [ ] **Step 4: Tests pass; commit**

Message: `feat(manifold-v04): drift-report CLI + HTTP + MCP surfaces`

---

### Task 9: Node detail UX (rationale + alternatives + revision change_reason)

**Files:**
- Modify: `manifold/html.py` — rationale section on node detail; change_reason in revision timeline.
- Modify: `manifold/web.py` — wire the new sections.
- Test: `tests/test_web.py`, `tests/test_html.py`.

- [ ] **Step 1: Failing test for rationale display**

```python
def test_node_detail_shows_rationale(self):
    writes.create_node(self.conn, "p", "L0", "A", "A",
                       rationale="exists because Q",
                       alternatives_considered="X rejected because Y",
                       actor="human:test")
    body = html.node_detail(self.conn, "p", "A")
    self.assertIn("exists because Q", body)
    self.assertIn("X rejected because Y", body)
```

- [ ] **Step 2: Implement rationale section in node detail HTML**

```python
def rationale_section(node):
    if not node.get("rationale") and not node.get("alternatives_considered"):
        return ""
    out = '<details class="rationale-section" open>'
    out += '<summary>Rationale</summary>'
    if node.get("rationale"):
        out += f'<div class="rationale-body"><strong>Why:</strong> {html_escape(node["rationale"])}</div>'
    if node.get("alternatives_considered"):
        out += f'<div class="alternatives-body"><strong>Alternatives considered:</strong> {html_escape(node["alternatives_considered"])}</div>'
    out += '</details>'
    return out
```

- [ ] **Step 3: Add `change_reason` to revision timeline**

```python
def revision_timeline_row(rev):
    reason = rev.get("change_reason") or "(unset)"
    badge_class = f"reason-badge reason-{reason}"
    return f'<span class="{badge_class}">{reason}</span> ...'
```

CSS:
```css
.reason-badge { padding: 2px 8px; border-radius: 100px; font-size: 11px; }
.reason-drift { background: #fde0e0; color: #b8221a; }
.reason-clarification, .reason-correction { background: #e6f3ea; color: #2e6b3d; }
.reason-evolution, .reason-refactor { background: #eef0f5; color: #1f3a5f; }
```

- [ ] **Step 4: Tests pass; commit**

Message: `feat(manifold-v04): rationale section + change_reason badges in HTML views`

---

### Task 10: Docs update (KAOS citation + compass framing + migration guide)

**Files:**
- Modify: `skills/manifold/README.md`
- Modify: `skills/manifold/ARCHITECTURE.md`
- Modify: `skills/manifold/USER.md`
- Create: `skills/manifold/MIGRATION.md`

- [ ] **Step 1: Update README — lead with compass framing**

Open the README with the compass framing:
> "manifold is a project compass. It answers four questions: what is this project (root), where are we now (current state), where do we go next (next leaves), and have we drifted from prior intent (drift detection). Built on the KAOS goal-oriented requirements engineering formalism (Darimont & van Lamsweerde 1996; van Lamsweerde 2009)."

Move the previous opening (about layered specifications) to §2.

- [ ] **Step 2: Update ARCHITECTURE.md — add KAOS citation section**

New section "Theoretical foundations" near the top:
- Primary citation: KAOS AND/OR DAG (Darimont & van Lamsweerde 1996)
- Algorithmic lineage: Additive AND/OR graphs (Martelli & Montanari 1973)
- Textbook reference: van Lamsweerde (2009)
- What manifold inherits vs. leaves behind (cite the v0.1 design doc)

Document the v0.4 structural change (DAG-across-layers replacing strict tree).

- [ ] **Step 3: Update USER.md — new CLI examples**

Add sections:
- "Working with `next-leaves`": example output, --layer filter
- "Tracking rationale": example of authoring with rationale + alternatives
- "Detecting drift": example `manifold drift-report` invocation; what to look for

- [ ] **Step 4: Create MIGRATION.md**

```markdown
# Migrating from development to v0.4

## What changes

1. Strict tree-across-layers is relaxed to AND/OR DAG. Multi-parent nodes are now valid.
2. `realized_by_external` is deprecated (advisory warning). Multi-parent replaces it.
3. Default `target_status` for new nodes is now `"planned"` (was `""`).
4. New columns: `nodes.rationale`, `nodes.alternatives_considered`, `revisions.change_reason`.
5. New CLI commands: `manifold next-leaves`, `manifold drift-report`.
6. New HTTP routes and MCP tools for the above.

## What you need to do

### On first `manifold serve` / `manifold validate` after upgrading:

The schema migration runs automatically and idempotently. Your existing data is untouched.

### To backfill existing projects:

Run `python3 scripts/v04-backfill.py [--dry-run]`. This will:
- For every node with `target_status=""`: set to `"achieved"` if verdict is satisfied, else `"planned"`
- For every revision with `change_reason=""`: set to `"evolution"` and annotate `change_summary`
- Print a summary of changes before applying

Always run with `--dry-run` first to review.

### Citation update

If you cite manifold in any doc, update the lineage citation to reflect KAOS (Darimont & van Lamsweerde 1996) as the primary formal home.
```

- [ ] **Step 5: Commit**

Message: `docs(manifold-v04): README compass framing, ARCHITECTURE KAOS citation, USER examples, MIGRATION guide`

---

## Wave 4 — backfill and smoke test (sequential)

### Task 11: Backfill script for existing 3 projects

**Files:**
- Create: `skills/manifold/scripts/v04-backfill.py`

- [ ] **Step 1: Implement script with --dry-run flag**

```python
#!/usr/bin/env python3
"""v0.4 backfill for existing projects in the manifold DB.

For each node with target_status="":
  - If verdict_status="satisfied": set target_status="achieved"
  - Else: set target_status="planned"

For each revision with change_reason="":
  - Set change_reason="evolution"
  - Append "(backfilled in v0.4 migration)" to change_summary
"""
import argparse, sys
sys.path.insert(0, "..")  # adjust as needed
from manifold import db, queries, writes

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--db", default=None)
    args = ap.parse_args()

    conn = db.connect(args.db)
    projects = [r["project_id"] for r in conn.execute(
        "SELECT project_id FROM projects WHERE archived_at IS NULL"
    )]

    node_updates = 0
    rev_updates = 0
    for pid in projects:
        # nodes
        rows = list(conn.execute(
            "SELECT node_id, verdict_status FROM nodes WHERE project_id=? AND target_status=''",
            (pid,)
        ))
        for r in rows:
            new_status = "achieved" if r["verdict_status"] == "satisfied" else "planned"
            print(f"  [node] {pid}/{r['node_id']}: '' → '{new_status}'")
            if not args.dry_run:
                conn.execute(
                    "UPDATE nodes SET target_status=? WHERE project_id=? AND node_id=?",
                    (new_status, pid, r["node_id"])
                )
            node_updates += 1

        # revisions
        rev_rows = list(conn.execute(
            "SELECT revision_id FROM revisions WHERE project_id=? AND (change_reason='' OR change_reason IS NULL)",
            (pid,)
        ))
        for r in rev_rows:
            if not args.dry_run:
                conn.execute(
                    "UPDATE revisions SET change_reason='evolution', "
                    "change_summary = COALESCE(change_summary, '') || ' (backfilled in v0.4 migration)' "
                    "WHERE revision_id=?",
                    (r["revision_id"],)
                )
            rev_updates += 1

    if not args.dry_run:
        conn.commit()
    print(f"\nTotal: {node_updates} nodes, {rev_updates} revisions {'would be updated' if args.dry_run else 'updated'}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run dry-run against live DB; review output**

```
python3 skills/manifold/scripts/v04-backfill.py --dry-run
```

Spot-check the proposed changes for all 81 nodes across 3 projects.

- [ ] **Step 3: Apply for real**

```
python3 skills/manifold/scripts/v04-backfill.py
```

- [ ] **Step 4: Verify with `manifold next-leaves`**

```
manifold next-leaves manifold-v03
manifold next-leaves plan-orchestrator
manifold next-leaves manifold
```

Expected: non-empty lists for projects with actually-unfinished work.

- [ ] **Step 5: Commit the script** (DB itself is not in git)

Message: `chore(manifold-v04): v0.4 backfill script for existing projects`

---

### Task 12: End-to-end smoke test

**Files:**
- Create: `tests/test_v04_smoke.py`

- [ ] **Step 1: Write smoke test**

```python
"""End-to-end smoke test for v0.1 features."""
import unittest, tempfile, json, subprocess
from manifold import db, writes, queries, validate

class TestV04EndToEnd(unittest.TestCase):
    def test_full_v04_roundtrip(self):
        path = tempfile.mktemp(suffix=".db")
        conn = db.connect(path)

        # 1. Register project, multi-layer
        writes.register_project(conn, "smoke", spec_config={
            "layers": [{"name": "I"}, {"name": "C"}, {"name": "R"}]
        }, actor="human:test")

        # 2. Create nodes including multi-parent (DAG)
        writes.create_node(conn, "smoke", "I", "I.1", "intent A",
                           rationale="why A exists", actor="human:test")
        writes.create_node(conn, "smoke", "I", "I.2", "intent B",
                           rationale="why B exists", actor="human:test")
        writes.create_node(conn, "smoke", "C", "C.1", "capability AB",
                           parents=["I.1", "I.2"],  # multi-parent!
                           rationale="serves both intents",
                           actor="human:test")
        writes.create_node(conn, "smoke", "R", "R.1", "realization",
                           parents=["C.1"],
                           rationale="implements C.1",
                           actor="human:test")

        # 3. Default target_status
        n = queries.get_node(conn, "smoke", "R.1")
        self.assertEqual(n["target_status"], "planned")

        # 4. next_leaves returns R.1 (only leaf with planned status)
        leaves = queries.next_leaves(conn, "smoke")
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0]["node_id"], "R.1")

        # 5. Validate cleanly
        validate.run_structural_checks(conn, "smoke")
        # (no errors expected; advisories allowed)

        # 6. Update with change_reason=drift
        rev = n["current_revision_id"]
        writes.update_node(conn, "smoke", "R.1", {"title": "renamed"},
                            expected_revision_id=rev,
                            change_reason="drift",
                            actor="human:test")

        # 7. drift_revisions finds it
        drift = queries.drift_revisions(conn, "smoke")
        self.assertTrue(any(r["change_reason"] == "drift" for r in drift))

        conn.close()

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run smoke test; all passes**

- [ ] **Step 3: Tag the release**

```
git tag manifold-v0.1.0
```

- [ ] **Step 4: Commit smoke test**

Message: `test(manifold-v04): end-to-end smoke test for v0.1 features`

---

## Wave 4 acceptance gate

- [ ] All 300+ existing tests pass.
- [ ] 12 new tasks' tests pass.
- [ ] Backfill applied; `manifold next-leaves` returns meaningful output on all 3 self-spec projects.
- [ ] README opens with compass framing.
- [ ] ARCHITECTURE cites KAOS within the first 3 paragraphs.
- [ ] One end-to-end smoke test covering DAG + compass + rationale + drift.
- [ ] Tag `manifold-v0.1.0` exists.

Once all gates pass, v0.4 is shipped. Move on to v0.5 (qualitative aggregation + multi-actor) when there's appetite.

---

## Notes for the subagent dispatcher

- **Don't dispatch implementation subagents in parallel WITHIN a wave UNLESS you have a worktree per task.** Tasks within a wave share files (e.g. Tasks 6 and 7 both touch `validate.py` and `queries.py`). Either:
  - Use a worktree per task (cleanest; no merge issues), OR
  - Dispatch sequentially within a wave but parallelly across waves' independent streams
- **Two-stage review** (spec compliance + code quality) after each task.
- **Use sonnet** for the mechanical tasks (1, 2, 3, 5, 6, 9, 11, 12). **Use opus** for the synthesis tasks (4 — render convention design, 8 — drift-report UX, 10 — docs that need narrative flow).
- **Commit per task** with the suggested messages.
