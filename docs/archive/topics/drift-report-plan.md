# `drift-report` (Topic E / M4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship `manifold drift-report` — a project-wide spec↔code report that surfaces **violated** verdicts and **unverified** realization nodes (no check wired), reusing the existing verdict engine.

**Architecture:** Add a read-only query layer (`queries.drift_report`) that loads the graph, selects target-layer nodes, runs `validate.run_verdicts` (no validation row persisted), classifies findings, and returns structured JSON. CLI/MCP/HTTP surfaces mirror `spec-audit`. Terminal and `--format md` formatters live in a small `drift_report.py` module to keep `cli.py` thin.

**Tech stack:** Python 3 stdlib, SQLite, existing `packages/manifold/manifold/validate.py` verdict runners. No new dependencies.

**Design spec:** [`drift-report-design.md`](drift-report-design.md) (L16 v1, L17 v2 deferred).

**Working directory:** repo root (`foundry/`)

**Test command (full suite):**

```bash
cd packages/manifold && python3 -m unittest discover
cd mcps/manifold && python3 -m unittest discover
cd apps/manifold-web && python3 -m unittest discover
```

---

## File map

| File | Action | Responsibility |
|---|---|---|
| `packages/manifold/manifold/queries.py` | Modify | `drift_report()` query + `_drift_bucket()` classifier |
| `packages/manifold/manifold/drift_report.py` | **Create** | Terminal + markdown formatters |
| `packages/manifold/manifold/cli.py` | Modify | `drift-report` subcommand |
| `packages/manifold/tests/test_drift_report.py` | **Create** | Query + classifier unit tests |
| `packages/manifold/tests/test_cli.py` | Modify | CLI smoke tests |
| `mcps/manifold/server/mcp_server.py` | Modify | `drift_report` tool (30 tools total) |
| `mcps/manifold/tests/test_mcp_server.py` | Modify | MCP tool tests |
| `apps/manifold-web/manifold_web/web.py` | Modify | Routes + `html_drift_report` + `api_drift_report` |
| `apps/manifold-web/manifold_web/html.py` | Modify | `drift_report_body()` HTML renderer |
| `apps/manifold-web/tests/test_web.py` | Modify | HTTP/HTML/API tests |
| `docs/manifold/glossary.md` | Modify | Mark surfaces shipped; MCP count 30 |
| `skills/manifold/references/*.md` | Modify | Remove "not shipped" hedging where factual |
| `docs/manifold/todo.md` | Modify | Check off T4.6 tasks as implemented |

**Out of v1 (do not build):** `--since`, `--with-llm`, Spec Kit scan, finding→`change_reason` workflow, web-only fancy UI.

---

## Wave 1 — Core query + tests (blocking)

No CLI/MCP until this wave is green.

### Task 1: Classifier + `drift_report` query

**Files:**
- Create: `packages/manifold/manifold/drift_report.py` (classifier only first)
- Modify: `packages/manifold/manifold/queries.py` (append `drift_report`)
- Test: `packages/manifold/tests/test_drift_report.py`

**Return shape (lock this for all surfaces):**

```python
{
    "project_id": "my-project",
    "layer_scope": "realizations",   # or "all" or explicit layer name
    "project_root": "/abs/path/to/repo",
    "summary": {
        "total": 4,
        "violated": 1,
        "unverified": 1,
        "satisfied": 1,
        "deferred_external": 0,
        "other": 1,                  # unknown / inconclusive with mechanism set
    },
    "violated": [finding, ...],
    "unverified": [finding, ...],
    "satisfied": [finding, ...],     # omit from CLI unless --verbose
    "deferred_external": [finding, ...],
    "other": [finding, ...],
}
```

Each **finding** dict:

```python
{
    "node_id": "R.3",
    "layer": "realizations",
    "title": "Delete requires confirmation",
    "rationale": "Prevent accidental data loss",
    "verdict_status": "violated",
    "verdict_source": "automated",
    "verdict_evidence": "AssertionError: ...",
    "verdict_mechanism": "automated_check",
}
```

- [ ] **Step 1: Write failing classifier tests**

Create `packages/manifold/tests/test_drift_report.py`:

```python
import unittest
from manifold.drift_report import classify_finding


class TestClassifyFinding(unittest.TestCase):
    def test_no_mechanism_is_unverified(self):
        self.assertEqual(
            classify_finding("unknown", "no_mechanism", ""),
            "unverified",
        )

    def test_violated_is_violated(self):
        self.assertEqual(
            classify_finding("violated", "automated", "automated_check"),
            "violated",
        )

    def test_judge_required_is_violated(self):
        self.assertEqual(
            classify_finding("judge_required", "judge_required", "llm_judge"),
            "violated",
        )

    def test_satisfied_is_satisfied(self):
        self.assertEqual(
            classify_finding("satisfied", "automated", "automated_check"),
            "satisfied",
        )

    def test_deferred_external_bucket(self):
        self.assertEqual(
            classify_finding("deferred_external", "external:R.9", "automated_check"),
            "deferred_external",
        )

    def test_human_unknown_with_mechanism_is_other(self):
        self.assertEqual(
            classify_finding("unknown", "human", "human_signoff"),
            "other",
        )
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
cd packages/manifold && python3 -m unittest tests.test_drift_report.TestClassifyFinding -v
```

Expected: `ModuleNotFoundError` or `ImportError: classify_finding`

- [ ] **Step 3: Implement classifier**

Create `packages/manifold/manifold/drift_report.py`:

```python
"""Formatters and helpers for drift-report (M4 spec↔code)."""

from typing import Optional


def classify_finding(status: str, source: str, mechanism: str) -> str:
    """Map a verdict run result to a drift-report bucket."""
    mechanism = (mechanism or "").strip()
    status = (status or "").strip()
    source = (source or "").strip()

    if source == "no_mechanism" or not mechanism:
        return "unverified"
    if status == "deferred_external" or source.startswith("external:"):
        return "deferred_external"
    if status in ("violated", "judge_required"):
        return "violated"
    if status == "satisfied":
        return "satisfied"
    return "other"
```

- [ ] **Step 4: Run classifier tests — expect PASS**

```bash
cd packages/manifold && python3 -m unittest tests.test_drift_report.TestClassifyFinding -v
```

- [ ] **Step 5: Write failing `drift_report` integration tests**

Append to `tests/test_drift_report.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path

from manifold import db, schema, queries, writes, validate


def _seed_project(conn, project_id="p", layers=None):
    layers = layers or [
        {"name": "intent"},
        {"name": "realizations"},
    ]
    writes.register_project(conn, project_id, spec_config={
        "layers": layers,
        "project_root": str(Path.cwd()),
    }, actor="human:test")
    writes.create_node(conn, project_id, "intent", "I.1", "Intent",
                       actor="human:test")
    writes.create_node(
        conn, project_id, "realizations", "R.ok", "Satisfied node",
        parents=["I.1"], actor="human:test",
        patch={"verdict_mechanism": "automated_check",
               "verdict_check": "true"},
    )
    writes.create_node(
        conn, project_id, "realizations", "R.bad", "Violated node",
        parents=["I.1"], actor="human:test",
        patch={"verdict_mechanism": "automated_check",
               "verdict_check": "false"},
    )
    writes.create_node(
        conn, project_id, "realizations", "R.none", "Unverified node",
        parents=["I.1"], actor="human:test",
    )


class TestDriftReportQuery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()
        self.conn = db.connect(self.tmp.name)
        schema.bootstrap(self.conn)
        _seed_project(self.conn)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        for suffix in ("", "-shm", "-wal"):
            p = Path(self.tmp.name + suffix)
            if p.exists():
                p.unlink()

    def test_drift_report_default_layer_is_bottom(self):
        report = queries.drift_report(self.conn, "p")
        self.assertEqual(report["layer_scope"], "realizations")
        ids = {f["node_id"] for f in report["violated"] + report["unverified"]}
        self.assertIn("R.bad", ids)
        self.assertIn("R.none", ids)
        self.assertNotIn("I.1", ids)

    def test_drift_report_summary_counts(self):
        report = queries.drift_report(self.conn, "p", force=True)
        self.assertEqual(report["summary"]["violated"], 1)
        self.assertEqual(report["summary"]["unverified"], 1)
        self.assertEqual(report["summary"]["satisfied"], 1)

    def test_drift_report_all_layers(self):
        report = queries.drift_report(self.conn, "p", all_layers=True, force=True)
        self.assertEqual(report["layer_scope"], "all")
        self.assertEqual(report["summary"]["total"], 3)

    def test_drift_report_repo_override(self):
        report = queries.drift_report(
            self.conn, "p", project_root="/tmp/custom-repo", force=True)
        self.assertEqual(report["project_root"], "/tmp/custom-repo")

    def test_drift_report_missing_project_returns_empty(self):
        report = queries.drift_report(self.conn, "missing")
        self.assertEqual(report["summary"]["total"], 0)
        self.assertEqual(report["violated"], [])
```

- [ ] **Step 6: Run query tests — expect FAIL**

```bash
cd packages/manifold && python3 -m unittest tests.test_drift_report.TestDriftReportQuery -v
```

Expected: `AttributeError: module 'manifold.queries' has no attribute 'drift_report'`

- [ ] **Step 7: Implement `queries.drift_report`**

Append to `packages/manifold/manifold/queries.py`:

```python
# ============================================================
# Drift report (M4 — spec↔code, not revision discipline)
# ============================================================

def drift_report(conn: sqlite3.Connection, project_id: str, *,
                 project_root: Optional[str] = None,
                 layer: Optional[str] = None,
                 all_layers: bool = False,
                 force: bool = False) -> dict:
    """Spec↔code drift report for realization-layer nodes (default: bottom layer).

    Runs verdict checks via validate.run_verdicts without persisting a validation
    run. See docs/archive/topics/drift-report-design.md.
    """
    from . import validate
    from .drift_report import classify_finding

    empty = {
        "project_id": project_id,
        "layer_scope": layer or ("all" if all_layers else ""),
        "project_root": project_root or "",
        "summary": {
            "total": 0, "violated": 0, "unverified": 0, "satisfied": 0,
            "deferred_external": 0, "other": 0,
        },
        "violated": [], "unverified": [], "satisfied": [],
        "deferred_external": [], "other": [],
    }

    project_row = conn.execute(
        "SELECT spec_config FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if not project_row:
        return empty

    try:
        spec_config = json.loads(project_row["spec_config"] or "{}")
    except (json.JSONDecodeError, TypeError):
        spec_config = {}

    layer_names = [L.get("name", "") for L in (spec_config.get("layers") or [])]
    if all_layers:
        layer_scope = "all"
        target_layers = set(layer_names)
    elif layer:
        layer_scope = layer
        target_layers = {layer}
    else:
        layer_scope = layer_names[-1] if layer_names else ""
        target_layers = {layer_scope} if layer_scope else set()

    resolved_root = (project_root or spec_config.get("project_root") or "").strip()
    empty["layer_scope"] = layer_scope
    empty["project_root"] = resolved_root

    nbi = validate._build_nodes_by_id(conn, project_id)
    if not nbi:
        return empty

    judge_cmd = validate._resolve_judge_command(spec_config)
    verdicts_map = validate.run_verdicts(
        conn, project_id, nbi, resolved_root, force, judge_cmd=judge_cmd)

    buckets = {k: [] for k in (
        "violated", "unverified", "satisfied", "deferred_external", "other")}
    summary = dict(empty["summary"])

    for nid, node in nbi.items():
        if node.get("deleted_at"):
            continue
        if target_layers and node.get("layer") not in target_layers:
            continue

        v = verdicts_map.get(nid, {})
        status = v.get("status") or "unknown"
        source = v.get("source") or ""
        mechanism = node.get("verdict_mechanism") or ""
        bucket = classify_finding(status, source, mechanism)

        finding = {
            "node_id": nid,
            "layer": node.get("layer") or "",
            "title": node.get("title") or "",
            "rationale": (node.get("rationale") or "")[:500],
            "verdict_status": status,
            "verdict_source": source,
            "verdict_evidence": v.get("evidence_ref") or "",
            "verdict_mechanism": mechanism,
        }
        buckets[bucket].append(finding)
        summary[bucket] += 1
        summary["total"] += 1

    return {
        "project_id": project_id,
        "layer_scope": layer_scope,
        "project_root": resolved_root,
        "summary": summary,
        **buckets,
    }
```

- [ ] **Step 8: Run all drift_report tests — expect PASS**

```bash
cd packages/manifold && python3 -m unittest tests.test_drift_report -v
```

- [ ] **Step 9: Commit Wave 1**

```bash
git add packages/manifold/manifold/drift_report.py \
        packages/manifold/manifold/queries.py \
        packages/manifold/tests/test_drift_report.py
git commit -m "$(cat <<'EOF'
Add drift_report query and finding classifier for Topic E v1.

Reuses run_verdicts read-only; classifies violated vs unverified realizations.
EOF
)"
```

---

## Wave 2 — Formatters + CLI

Depends on Wave 1.

### Task 2: Terminal + markdown formatters

**Files:**
- Modify: `packages/manifold/manifold/drift_report.py`
- Test: `packages/manifold/tests/test_drift_report.py`

- [ ] **Step 1: Write failing formatter tests**

Append to `tests/test_drift_report.py`:

```python
from manifold.drift_report import format_terminal, format_markdown


SAMPLE_REPORT = {
    "project_id": "p",
    "layer_scope": "realizations",
    "project_root": "/repo",
    "summary": {
        "total": 2, "violated": 1, "unverified": 1, "satisfied": 0,
        "deferred_external": 0, "other": 0,
    },
    "violated": [{
        "node_id": "R.bad", "layer": "realizations", "title": "Bad",
        "rationale": "Because", "verdict_status": "violated",
        "verdict_source": "automated", "verdict_evidence": "fail",
        "verdict_mechanism": "automated_check",
    }],
    "unverified": [{
        "node_id": "R.none", "layer": "realizations", "title": "None",
        "rationale": "", "verdict_status": "unknown",
        "verdict_source": "no_mechanism", "verdict_evidence": "",
        "verdict_mechanism": "",
    }],
    "satisfied": [], "deferred_external": [], "other": [],
}


class TestDriftReportFormatters(unittest.TestCase):
    def test_terminal_shows_violated_and_unverified(self):
        out = format_terminal(SAMPLE_REPORT)
        self.assertIn("VIOLATED", out)
        self.assertIn("UNVERIFIED", out)
        self.assertIn("R.bad", out)
        self.assertIn("R.none", out)

    def test_markdown_has_headings(self):
        md = format_markdown(SAMPLE_REPORT)
        self.assertIn("# Intent drift report", md)
        self.assertIn("## Violated", md)
        self.assertIn("## Unverified", md)
        self.assertIn("R.bad", md)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd packages/manifold && python3 -m unittest tests.test_drift_report.TestDriftReportFormatters -v
```

- [ ] **Step 3: Implement formatters**

Append to `packages/manifold/manifold/drift_report.py`:

```python
def format_terminal(report: dict, *, verbose: bool = False) -> str:
    lines = [
        f"Intent Drift Report — {report.get('project_id', '')}",
        f"  layer scope:  {report.get('layer_scope', '')}",
        f"  project root: {report.get('project_root') or '(unset)'}",
    ]
    s = report.get("summary") or {}
    lines.append(
        f"  summary:      {s.get('total', 0)} nodes — "
        f"{s.get('violated', 0)} violated, "
        f"{s.get('unverified', 0)} unverified, "
        f"{s.get('satisfied', 0)} satisfied"
    )

    def _section(title, findings):
        if not findings:
            return
        lines.append("")
        lines.append(title + ":")
        for f in findings:
            ev = (f.get("verdict_evidence") or "")[:80]
            lines.append(
                f"  {f.get('node_id', ''):<14} "
                f"{(f.get('title') or '')[:40]}"
            )
            if f.get("rationale"):
                lines.append(f"    rationale: {(f['rationale'])[:120]}")
            if ev:
                lines.append(f"    evidence:  {ev}")

    _section("VIOLATED", report.get("violated") or [])
    _section("UNVERIFIED", report.get("unverified") or [])
    if verbose:
        _section("SATISFIED", report.get("satisfied") or [])
    return "\n".join(lines) + "\n"


def format_markdown(report: dict) -> str:
    pid = report.get("project_id", "")
    lines = [
        f"# Intent drift report — `{pid}`",
        "",
        f"- **Layer scope:** {report.get('layer_scope', '')}",
        f"- **Project root:** `{report.get('project_root') or '(unset)'}`",
        "",
    ]
    s = report.get("summary") or {}
    lines += [
        "## Summary",
        "",
        f"| Status | Count |",
        f"|--------|------:|",
        f"| Violated | {s.get('violated', 0)} |",
        f"| Unverified | {s.get('unverified', 0)} |",
        f"| Satisfied | {s.get('satisfied', 0)} |",
        f"| Total | {s.get('total', 0)} |",
        "",
    ]

    def _md_section(title, findings):
        if not findings:
            lines.append(f"## {title}")
            lines.append("")
            lines.append("_None._")
            lines.append("")
            return
        lines.append(f"## {title}")
        lines.append("")
        for f in findings:
            lines.append(f"### `{f.get('node_id', '')}` — {f.get('title') or ''}")
            if f.get("rationale"):
                lines.append(f"> {f['rationale'][:300]}")
            lines.append("")
            lines.append(f"- **Status:** `{f.get('verdict_status', '')}`")
            lines.append(f"- **Mechanism:** `{f.get('verdict_mechanism') or '(none)'}`")
            if f.get("verdict_evidence"):
                lines.append(f"- **Evidence:** {f['verdict_evidence'][:400]}")
            lines.append(f"- **Peek:** `manifold show {pid} {f.get('node_id', '')}`")
            lines.append("")

    _md_section("Violated", report.get("violated") or [])
    _md_section("Unverified", report.get("unverified") or [])
    return "\n".join(lines)
```

- [ ] **Step 4: Run formatter tests — expect PASS**

```bash
cd packages/manifold && python3 -m unittest tests.test_drift_report.TestDriftReportFormatters -v
```

### Task 3: CLI subcommand

**Files:**
- Modify: `packages/manifold/manifold/cli.py`
- Modify: `packages/manifold/tests/test_cli.py`

- [ ] **Step 1: Add parser + dispatch entries**

In `cli.py` module docstring, add `drift-report` to subcommand list.

After `p_audit` block (~line 97), add:

```python
    p_drift = sub.add_parser(
        "drift-report",
        help="Report spec↔code drift (verdict failures + unverified realizations).",
    )
    p_drift.add_argument("project_id", help="Project ID to report on.")
    p_drift.add_argument("--repo", default=None,
                         help="Override spec_config.project_root for checks.")
    p_drift.add_argument("--layer", default=None,
                         help="Layer to scan (default: bottom layer in spec_config).")
    p_drift.add_argument("--all-layers", action="store_true",
                         help="Scan all layers instead of bottom layer only.")
    p_drift.add_argument("--force", action="store_true",
                         help="Bypass verdict cache; recompute every node.")
    p_drift.add_argument("--format", choices=["text", "md"], default="text",
                         help="Output format (default: text).")
    p_drift.add_argument("--verbose", action="store_true",
                         help="Include satisfied nodes in text output.")
```

Add to dispatch dict: `"drift-report": _cmd_drift_report,`

- [ ] **Step 2: Implement `_cmd_drift_report`**

```python
def _cmd_drift_report(args) -> int:
    from manifold import db, schema, queries
    from manifold.drift_report import format_terminal, format_markdown

    conn = db.connect()
    schema.bootstrap(conn)
    try:
        report = queries.drift_report(
            conn, args.project_id,
            project_root=args.repo,
            layer=args.layer,
            all_layers=args.all_layers,
            force=args.force,
        )
    finally:
        conn.close()

    if args.format == "md":
        print(format_markdown(report), end="")
    else:
        print(format_terminal(report, verbose=args.verbose), end="")

    violated = (report.get("summary") or {}).get("violated", 0)
    return 1 if violated else 0
```

- [ ] **Step 3: Write CLI smoke tests**

Add `TestCLIDriftReport` class to `tests/test_cli.py` — mirror `TestCLISpecAudit` seed pattern but with three realization nodes (pass/fail/none mechanism). Assert:
- exit 1 when violated present
- exit 0 when only unverified
- `--format md` contains `# Intent drift report`
- `--help` works

- [ ] **Step 4: Run CLI tests**

```bash
cd packages/manifold && python3 -m unittest tests.test_cli.TestCLIDriftReport -v
```

- [ ] **Step 5: Commit Wave 2**

```bash
git add packages/manifold/manifold/drift_report.py \
        packages/manifold/manifold/cli.py \
        packages/manifold/tests/test_drift_report.py \
        packages/manifold/tests/test_cli.py
git commit -m "$(cat <<'EOF'
Add drift-report CLI with terminal and markdown output.

Exit 1 when violated findings exist; unverified alone exits 0.
EOF
)"
```

---

## Wave 3 — MCP + HTTP (parallel)

Both depend on Wave 1 only (Wave 2 CLI optional for manual smoke).

### Task 4: MCP `drift_report` tool

**Files:**
- Modify: `mcps/manifold/server/mcp_server.py`
- Modify: `mcps/manifold/tests/test_mcp_server.py`

- [ ] **Step 1: Add handler**

```python
def h_drift_report(conn, args):
    project_id = args.get("project_id", "")
    return queries.drift_report(
        conn, project_id,
        project_root=args.get("project_root"),
        layer=args.get("layer"),
        all_layers=bool(args.get("all_layers", False)),
        force=bool(args.get("force", False)),
    )
```

- [ ] **Step 2: Register tool** (after `spec_audit` entry)

```python
    {"name": "drift_report",
     "description": "Spec↔code intent drift report (M4). Returns violated verdicts "
                    "and unverified realization nodes. Not spec revision audit — "
                    "use spec_audit for M3. See docs/manifold/glossary.md.",
     "handler": h_drift_report,
     "inputSchema": {"type": "object", "required": ["project_id"], "properties": {
         "project_id": {"type": "string"},
         "project_root": {"type": "string",
                           "description": "Override spec_config.project_root."},
         "layer": {"type": "string",
                   "description": "Layer to scan (default: bottom layer)."},
         "all_layers": {"type": "boolean"},
         "force": {"type": "boolean"},
     }}},
```

- [ ] **Step 3: Add tests** (mirror `TestMCPSpecAudit`):
- tool registered in list
- returns keys: `summary`, `violated`, `unverified`, `project_id`
- finds seeded violated node

- [ ] **Step 4: Run MCP tests**

```bash
cd mcps/manifold && python3 -m unittest tests.test_mcp_server -v
```

- [ ] **Step 5: Commit**

```bash
git add mcps/manifold/server/mcp_server.py mcps/manifold/tests/test_mcp_server.py
git commit -m "Add drift_report MCP tool for Topic E spec↔code report."
```

### Task 5: HTTP + HTML surfaces

**Files:**
- Modify: `apps/manifold-web/manifold_web/web.py`
- Modify: `apps/manifold-web/manifold_web/html.py`
- Modify: `apps/manifold-web/tests/test_web.py`

- [ ] **Step 1: Register routes** in `web.py` `ROUTES` (before generic node routes, next to spec-audit):

```python
    ("GET", re.compile(r"^/projects/(?P<project_id>[^/]+)/drift-report$"), "html_drift_report"),
    ("GET", re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/drift-report$"), "api_drift_report"),
```

Query params: `repo`, `layer`, `all_layers` (bool), `force` (bool).

- [ ] **Step 2: Implement handlers**

```python
def html_drift_report(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    if queries.get_project(conn, pid) is None:
        return html.render_page("Not Found",
                                f"<h1>Project not found: {escape(pid)}</h1>"), 404
    report = queries.drift_report(
        conn, pid,
        project_root=_first(query.get("repo")),
        layer=_first(query.get("layer")),
        all_layers=_bool(query.get("all_layers")),
        force=_bool(query.get("force")),
    )
    body = html.drift_report_body(pid, report)
    return html.render_page(f"manifold · drift-report · {pid}", body), 200


def api_drift_report(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    return queries.drift_report(
        conn, pid,
        project_root=_first(query.get("repo")),
        layer=_first(query.get("layer")),
        all_layers=_bool(query.get("all_layers")),
        force=_bool(query.get("force")),
    ), 200
```

Register in handler map.

- [ ] **Step 3: Add `html.drift_report_body`**

Mirror `spec_audit_body` structure: summary counts, violated table, unverified table. Link node IDs to `/projects/<p>/nodes/<id>`.

- [ ] **Step 4: Web tests** — copy `TestWebSpecAudit` / `TestAPISpecAudit` patterns:
- 200 + project name in HTML
- violated node visible
- API returns `violated` list
- 404 for missing project
- routes registered

- [ ] **Step 5: Run web tests**

```bash
cd apps/manifold-web && python3 -m unittest discover -v
```

- [ ] **Step 6: Commit**

```bash
git add apps/manifold-web/manifold_web/web.py \
        apps/manifold-web/manifold_web/html.py \
        apps/manifold-web/tests/test_web.py
git commit -m "Add drift-report HTTP and HTML surfaces."
```

---

## Wave 4 — Documentation + todo closure

Depends on Waves 1–3.

### Task 6: Docs + glossary

**Files:**
- Modify: `docs/manifold/glossary.md`
- Modify: `skills/manifold/SKILL.md`
- Modify: `skills/manifold/references/user-guide.md`
- Modify: `skills/manifold/references/architecture.md`
- Modify: `skills/manifold/references/why-manifold.md`
- Modify: `skills/manifold/references/changelog.md`
- Modify: `packages/manifold/README.md`
- Modify: `docs/manifold/todo.md`

- [ ] **Step 1: Glossary updates**
- HTTP routes table: add `/drift-report` rows
- MCP tools: **30** tools; add `drift_report` under Compass/audit group
- Coverage audit: `drift-report` CLI/MCP → **Present**
- Positioning footnote: remove "not yet implemented" for drift-report clause

- [ ] **Step 2: Skill docs**
- Replace "reserved / not shipped" with usage examples:

```bash
manifold drift-report my-project
manifold drift-report my-project --format md --force
```

- Compass table: fourth question answered by `drift-report`
- `why-manifold.md`: positioning no longer "aspirational until Topic E"

- [ ] **Step 3: Changelog** — add v1.0 Topic E entry under 2026-06-06 section

- [ ] **Step 4: landscape todo** — mark T4.6/T4.7 complete; add plan link

- [ ] **Step 5: Commit docs**

```bash
git add docs/ skills/ packages/manifold/README.md
git commit -m "$(cat <<'EOF'
Document shipped drift-report (Topic E v1) across glossary and skill refs.

Positioning sentence on spec↔code drift is now factual for wired projects.
EOF
)"
```

---

## Verification checklist (before calling Topic E done)

- [ ] `cd packages/manifold && python3 -m unittest discover` — all green
- [ ] `cd mcps/manifold && python3 -m unittest discover` — all green
- [ ] `cd apps/manifold-web && python3 -m unittest discover` — all green
- [ ] Manual smoke:

```bash
packages/manifold/scripts/manifold drift-report <known-project>
packages/manifold/scripts/manifold drift-report <known-project> --format md
```

- [ ] `spec-audit` unchanged; grep confirms no M3/M4 name collision:

```bash
rg 'drift.report' packages/manifold/manifold/queries.py -n
# drift_report section must NOT call spec_audit_* functions
```

- [ ] Glossary coverage audit row for `drift-report` says **Present**

---

## v2 backlog (L17 — do NOT implement in this plan)

Track in `drift-report-design.md` only:

- `--with-llm` / rationale-match judge across realizations without per-node `llm_judge` config
- Finding accept/reject → optional `change_reason=pivot` on spec update
- Dedicated web dashboard widgets

---

## Plan self-review

| Design requirement | Task |
|---|---|
| Violated + unverified buckets | Task 1 classifier + query |
| Bottom layer default | `layer_names[-1]` in query |
| `--all-layers` | CLI + MCP + HTTP query param |
| `--repo` override | CLI `--repo`, MCP `project_root` |
| `--force` | Passed to `run_verdicts` |
| Terminal + `--format md` | Task 2 formatters |
| Exit 1 on violated only | `_cmd_drift_report` return |
| CLI + MCP + HTTP | Tasks 3–5 |
| No validation persist | Query calls `run_verdicts` only |
| No v2 LLM stub | Explicitly excluded |
| Docs / positioning | Task 6 |

No placeholders remain in task steps above.

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-06 | Initial implementation plan (Topic E v1 / L16) |
