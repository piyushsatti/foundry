"""
Validation for manifold.

Structural checks operate on a DB-rooted nodes_by_id dict (built once via
_build_nodes_by_id) and return a list of issue dicts. Verdict runners
operate on a single node dict and return (status, evidence_text).

Soft-fail discipline: every check runs; one failure does not abort the
others. The caller (writes.run_validation) aggregates all issues into the
validations row, and writes one verdicts row per node when with_verdicts
is True.
"""
import ast as _ast
import hashlib
import json
import os
import subprocess
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


from manifold import config

FRAMEWORK_VERSION = config.MANIFOLD_VERSION


# ============================================================
# DB → nodes_by_id projection
# ============================================================

def _build_nodes_by_id(conn: sqlite3.Connection, project_id: str) -> dict:
    """Read all non-deleted nodes plus their edges for the project.

    Returns dict node_id → node dict (row fields + parents,
    peers_depends_on, target_blocks as lists).
    """
    rows = conn.execute(
        "SELECT * FROM nodes WHERE project_id = ? AND deleted_at IS NULL",
        (project_id,),
    ).fetchall()
    result = {}
    for row in rows:
        d = dict(row)
        d["parents"] = []
        d["peers_depends_on"] = []
        d["target_blocks"] = []
        result[row["node_id"]] = d
    edges = conn.execute(
        "SELECT src_node_id, dst_node_id, edge_kind FROM node_edges "
        "WHERE project_id = ?",
        (project_id,),
    ).fetchall()
    edge_field = {"parent": "parents", "depends_on": "peers_depends_on",
                  "blocks": "target_blocks"}
    for e in edges:
        nid = e["src_node_id"]
        if nid not in result:
            continue
        field = edge_field.get(e["edge_kind"])
        if field:
            result[nid][field].append(e["dst_node_id"])
    return result


# ============================================================
# Structural checks
# ============================================================

def check_layer_membership(layer_names, nodes_by_id):
    """Every node's layer must be one of the declared layers."""
    legal = set(layer_names)
    issues = []
    for nid, node in nodes_by_id.items():
        layer = node.get("layer", "")
        if layer not in legal:
            issues.append({
                "kind": "layer_membership",
                "node": nid,
                "message": (
                    f"Node {nid} declares layer='{layer}', not in spec "
                    f"layers {sorted(legal)}."
                ),
            })
    return issues


def check_tree_property(layer_names, nodes_by_id):
    """Backwards-compat alias for check_dag_property.

    Deprecated; callers should migrate to check_dag_property.
    """
    return check_dag_property(layer_names, nodes_by_id)


def check_dag_property(layer_names, nodes_by_id):
    """Relaxed from strict tree. Allows multi-parent across layers (AND/OR DAG).

    Enforces:
    - Acyclic across layers (DFS back-edge detection).
    - Layer ordering: all parents of a node must be at the layer immediately above.
    - Top-layer nodes have no parents.
    - Non-top-layer nodes have at least one parent.
    - All referenced parents must exist.

    No longer enforces single-parent (≤1 parent). Multi-parent is valid.

    Also emits an advisory finding for nodes that set realized_by_external,
    which is deprecated (use multi-parent edges instead).
    """
    issues = []
    layer_index = {name: i for i, name in enumerate(layer_names)}

    # Acyclic check across layers — DFS from each node, fail on back-edge.
    # Build parent map: node_id → [parent_ids]
    parents_map = {nid: list(node.get("parents") or []) for nid, node in nodes_by_id.items()}

    def has_cycle(start):
        stack = [(start, frozenset([start]))]
        while stack:
            node_id, path = stack.pop()
            for parent in parents_map.get(node_id, []):
                if parent in path:
                    return True
                if parent in nodes_by_id:
                    stack.append((parent, path | {parent}))
        return False

    for node_id in nodes_by_id:
        if has_cycle(node_id):
            issues.append({
                "kind": "cycle_across_layers",
                "node": node_id,
                "severity": "error",
                "message": (
                    f"Node {node_id} is part of a cycle in the cross-layer "
                    f"parent graph."
                ),
            })

    # Layer ordering checks (preserve existing logic; allow multiple parents).
    for nid, node in nodes_by_id.items():
        layer = node.get("layer", "")
        layer_idx = layer_index.get(layer, -1)
        parents = node.get("parents") or []

        if layer_idx == 0 and parents:
            issues.append({
                "kind": "dag_property",
                "node": nid,
                "severity": "error",
                "message": (
                    f"Node {nid} is at top layer '{layer}' but has "
                    f"parents {parents}."
                ),
            })

        if layer_idx > 0:
            expected_parent_layer = layer_names[layer_idx - 1]
            if not parents:
                issues.append({
                    "kind": "dag_property",
                    "node": nid,
                    "severity": "error",
                    "message": (
                        f"Node {nid} at layer '{layer}' has no parent; "
                        f"expected one at '{expected_parent_layer}'."
                    ),
                })
            for pid in parents:
                if pid not in nodes_by_id:
                    issues.append({
                        "kind": "dag_property",
                        "node": nid,
                        "severity": "error",
                        "message": (
                            f"Node {nid} references nonexistent parent '{pid}'."
                        ),
                    })
                    continue
                pl = nodes_by_id[pid].get("layer", "")
                if pl != expected_parent_layer:
                    issues.append({
                        "kind": "dag_property",
                        "node": nid,
                        "severity": "error",
                        "message": (
                            f"Node {nid} at layer '{layer}' points to parent "
                            f"'{pid}' at layer '{pl}'; expected layer "
                            f"'{expected_parent_layer}'."
                        ),
                    })

        # Deprecation advisory for realized_by_external.
        if node.get("realized_by_external"):
            issues.append({
                "kind": "deprecated_field",
                "node": nid,
                "field": "realized_by_external",
                "severity": "advisory",
                "message": (
                    "realized_by_external is deprecated; "
                    "multi-parent edges replace it."
                ),
            })

    return issues


def _detect_cycle(graph):
    """DFS cycle detector. Returns first cycle as a list, or None."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in graph}
    stack = []

    def visit(n):
        color[n] = GRAY
        stack.append(n)
        for m in graph.get(n, []):
            if m not in graph:
                continue
            if color[m] == GRAY:
                idx = stack.index(m)
                return stack[idx:] + [m]
            if color[m] == WHITE:
                c = visit(m)
                if c:
                    return c
        stack.pop()
        color[n] = BLACK
        return None

    for n in graph:
        if color[n] == WHITE:
            cyc = visit(n)
            if cyc:
                return cyc
    return None


def check_intra_layer_dag(nodes_by_id):
    """peers_depends_on within a layer must be acyclic, refs within the layer."""
    by_layer = {}
    for nid, node in nodes_by_id.items():
        by_layer.setdefault(node.get("layer", ""), []).append(node)

    issues = []
    for layer, nodes in by_layer.items():
        ids_in_layer = {n["node_id"] for n in nodes}
        graph = {}
        for node in nodes:
            nid = node["node_id"]
            deps = node.get("peers_depends_on") or []
            valid = []
            for d in deps:
                if d not in ids_in_layer:
                    issues.append({
                        "kind": "intra_layer_edge",
                        "node": nid,
                        "message": (
                            f"Node {nid}: peers_depends_on references '{d}', "
                            f"not in layer '{layer}'."
                        ),
                    })
                    continue
                valid.append(d)
            graph[nid] = valid
        cycle = _detect_cycle(graph)
        if cycle:
            issues.append({
                "kind": "intra_layer_cycle",
                "layer": layer,
                "cycle": cycle,
                "message": (
                    f"Cycle in intra-layer DAG of '{layer}': "
                    f"{' → '.join(cycle)}"
                ),
            })
    return issues


def check_external_realization(nodes_by_id):
    """realized_by_external: graph acyclic; target exists; node has no children.

    Returns (issues, children_of) — the children_of map is reused by check_coverage.
    """
    issues = []
    graph = {}
    has_external = {}

    for nid, node in nodes_by_id.items():
        target = (node.get("realized_by_external") or "").strip()
        has_external[nid] = bool(target)
        if not target:
            continue
        if target not in nodes_by_id:
            issues.append({
                "kind": "external_realization",
                "node": nid,
                "message": (
                    f"Node {nid}: realized_by_external '{target}' not found."
                ),
            })
            continue
        graph[nid] = [target]

    cycle = _detect_cycle(graph)
    if cycle:
        issues.append({
            "kind": "external_realization_cycle",
            "cycle": cycle,
            "message": (
                f"Cycle in realized_by_external graph: {' → '.join(cycle)}"
            ),
        })

    children_of = {nid: [] for nid in nodes_by_id}
    for nid, node in nodes_by_id.items():
        for p in node.get("parents") or []:
            if p in children_of:
                children_of[p].append(nid)

    for nid in nodes_by_id:
        if has_external.get(nid) and children_of.get(nid):
            issues.append({
                "kind": "external_realization",
                "node": nid,
                "message": (
                    f"Node {nid} has realized_by_external set, so it must "
                    f"have no children; found children: {children_of[nid]}."
                ),
            })

    return issues, children_of


def check_coverage(layer_names, nodes_by_id, children_of):
    """Every non-leaf, non-constraint, non-external-realized node has ≥1 child."""
    issues = []
    last_layer = layer_names[-1] if layer_names else ""
    for nid, node in nodes_by_id.items():
        layer = node.get("layer", "")
        kind = node.get("kind", "spec") or "spec"
        external = bool((node.get("realized_by_external") or "").strip())

        if layer == last_layer:
            continue
        if kind == "constraint":
            continue
        if external:
            continue
        if not children_of.get(nid):
            issues.append({
                "kind": "coverage",
                "node": nid,
                "message": (
                    f"Node {nid} at layer '{layer}' has no children at the "
                    f"next layer down. Either decompose it, mark it "
                    f"kind:constraint, or set realized_by_external."
                ),
            })
    return issues


def check_rationale(nodes_by_id):
    """Advisory warning for non-constraint nodes that have no rationale set.

    Rationale captures *why* a node exists. Nodes without rationale are
    valid but represent a potential anti-drift risk — the intent behind
    the decision is undocumented.

    Skips: constraint-kind nodes (they represent invariants, not decisions).
    """
    issues = []
    for node_id, node in nodes_by_id.items():
        if node.get("kind") == "constraint":
            continue
        rationale = node.get("rationale")
        if not rationale or (isinstance(rationale, str) and not rationale.strip()):
            issues.append({
                "kind": "missing_rationale",
                "node_id": node_id,
                "node": node_id,
                "severity": "advisory",
                "message": (
                    f"Node {node_id}: rationale is unset. "
                    "Add WHY this node exists to support anti-drift."
                ),
            })
    return issues


def check_targets(nodes_by_id, stale_days=180):
    """target_blocks DAG; stale planned targets surfaced as advisory issues.

    Also emits an advisory for nodes with empty/unset target_status.
    """
    issues = []
    graph = {}

    for nid, node in nodes_by_id.items():
        blocks = node.get("target_blocks") or []
        for bid in blocks:
            if bid not in nodes_by_id:
                issues.append({
                    "kind": "target_unresolved_block",
                    "node": nid,
                    "blocked_by": bid,
                    "message": (
                        f"Node {nid}: target.blocks references nonexistent "
                        f"node '{bid}'."
                    ),
                })
        graph[nid] = [b for b in blocks if b in nodes_by_id]

        # advisory for unset target_status (skip constraint nodes)
        if node.get("kind") != "constraint":
            ts = node.get("target_status")
            if ts is None or (isinstance(ts, str) and ts.strip() == ""):
                issues.append({
                    "kind": "missing_target_status",
                    "node_id": nid,
                    "node": nid,
                    "severity": "advisory",
                    "message": (
                        f"Node {nid}: target_status is unset. "
                        "Default to 'planned' on next edit."
                    ),
                })

        status = (node.get("target_status") or "").strip()
        if status == "planned":
            last_mod = node.get("last_modified_at") or ""
            try:
                ts = datetime.fromisoformat(last_mod.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - ts).total_seconds() / 86400
                if age > stale_days:
                    aw = (node.get("target_achieved_when") or "").strip()
                    msg = (
                        f"Node {nid}: target.status is 'planned' and the "
                        f"node hasn't been touched in {int(age)} days. "
                    )
                    if aw:
                        msg += f"achieved_when: {aw!r} — has this become true?"
                    else:
                        msg += "No achieved_when set; consider flipping."
                    issues.append({
                        "kind": "target_stale_planned",
                        "node": nid,
                        "age_days": int(age),
                        "message": msg,
                    })
            except (ValueError, AttributeError):
                pass

    cycle = _detect_cycle(graph)
    if cycle:
        issues.append({
            "kind": "target_blocks_cycle",
            "cycle": cycle,
            "message": f"Cycle in target.blocks graph: {' → '.join(cycle)}",
        })

    return issues


def check_cross_project_edges(conn: sqlite3.Connection) -> list[dict]:
    """Validate cross_project_edges refs and detect cycles (Topic I)."""
    issues: list[dict] = []
    rows = conn.execute(
        "SELECT src_project_id, src_node_id, dst_project_id, dst_node_id, "
        "edge_kind FROM cross_project_edges"
    ).fetchall()

    graph: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for r in rows:
        src = (r["src_project_id"], r["src_node_id"])
        dst = (r["dst_project_id"], r["dst_node_id"])
        for pid, nid in (src, dst):
            exists = conn.execute(
                "SELECT 1 FROM nodes WHERE project_id = ? AND node_id = ? "
                "AND deleted_at IS NULL",
                (pid, nid),
            ).fetchone()
            if exists is None:
                issues.append({
                    "kind": "cross_project_edge_invalid_ref",
                    "project_id": pid,
                    "node_id": nid,
                    "message": (
                        f"Cross-project edge references missing node "
                        f"{pid}/{nid}"
                    ),
                })
        if r["edge_kind"] == "blocks":
            graph.setdefault(src, []).append(dst)

    # Cycle detection on blocks graph (src blocked until dst achieved).
    visited: set[tuple[str, str]] = set()
    stack: set[tuple[str, str]] = set()
    cycle_path: list[tuple[str, str]] = []

    def dfs(node: tuple[str, str]) -> bool:
        if node in stack:
            cycle_path.append(node)
            return True
        if node in visited:
            return False
        visited.add(node)
        stack.add(node)
        for nxt in graph.get(node, []):
            if dfs(nxt):
                if node not in cycle_path:
                    cycle_path.insert(0, node)
                return True
        stack.discard(node)
        return False

    for start in graph:
        cycle_path.clear()
        if dfs(start) and cycle_path:
            refs = [f"{p}/{n}" for p, n in cycle_path]
            issues.append({
                "kind": "cross_project_edge_cycle",
                "cycle": refs,
                "message": (
                    "Cycle in cross-project blocks graph: "
                    + " → ".join(refs)
                ),
            })
            break

    return issues


# ============================================================
# Verdict runners (single-node)
# ============================================================

def run_automated_check(node, project_root):
    """Shell out to node.verdict_check. Returns (status, evidence)."""
    check_cmd = (node.get("verdict_check") or "").strip()
    if not check_cmd:
        return "unknown", "no verdict_check command specified"

    try:
        result = subprocess.run(
            check_cmd, shell=True,
            cwd=str(project_root) if project_root else None,
            capture_output=True, text=True, timeout=300,
        )
        status = "satisfied" if result.returncode == 0 else "violated"
        evidence = (result.stdout + "\n" + result.stderr).strip()[:2000]
        return status, evidence
    except subprocess.TimeoutExpired:
        return "errored", f"check exceeded 300s timeout: {check_cmd}"
    except OSError as exc:
        return "errored", f"check failed to execute: {exc}"


def _assertion_helpers(project_root):
    """Helper namespace exposed to python_assertion expressions.

    Pure read-only ops, all paths resolved relative to project_root. No
    filesystem writes, no subprocess, no network. The helpers below are
    the entire surface a python_assertion expression can call.
    """
    base = Path(project_root) if project_root else Path.cwd()

    def _path(p):
        return base / str(p)

    def _read(p):
        try:
            return _path(p).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""

    def _parse(p):
        text = _read(p)
        if not text:
            return None
        try:
            return _ast.parse(text)
        except SyntaxError:
            return None

    def file_exists(p):
        return _path(p).exists()

    def file_contains(p, needle):
        return str(needle) in _read(p)

    def ast_has_call(p, name):
        tree = _parse(p)
        if tree is None:
            return False
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Call):
                func = node.func
                while isinstance(func, _ast.Attribute):
                    func = func.value
                if isinstance(func, _ast.Name) and func.id == name:
                    return True
                if isinstance(node.func, _ast.Attribute) and node.func.attr == name:
                    return True
        return False

    def ast_has_import(p, name):
        tree = _parse(p)
        if tree is None:
            return False
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    bound = alias.asname or alias.name.split(".")[0]
                    if bound == name:
                        return True
            elif isinstance(node, _ast.ImportFrom):
                for alias in node.names:
                    bound = alias.asname or alias.name
                    if bound == name:
                        return True
        return False

    def ast_has_def(p, name):
        tree = _parse(p)
        if tree is None:
            return False
        for node in _ast.walk(tree):
            if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef,
                                  _ast.ClassDef)):
                if node.name == name:
                    return True
        return False

    def ast_has_call_with_kwarg(p, func_name, kwarg_name):
        tree = _parse(p)
        if tree is None:
            return False
        for node in _ast.walk(tree):
            if not isinstance(node, _ast.Call):
                continue
            target = node.func
            while isinstance(target, _ast.Attribute):
                target = target.value
            matched = (
                (isinstance(target, _ast.Name) and target.id == func_name)
                or (isinstance(node.func, _ast.Attribute)
                    and node.func.attr == func_name)
            )
            if not matched:
                continue
            for kw in node.keywords or []:
                if kw.arg == kwarg_name:
                    return True
        return False

    return {
        "file_exists": file_exists,
        "file_contains": file_contains,
        "ast_has_call": ast_has_call,
        "ast_has_import": ast_has_import,
        "ast_has_def": ast_has_def,
        "ast_has_call_with_kwarg": ast_has_call_with_kwarg,
    }


def _eval_assertion_ast(node, helpers):
    """Walk a tiny expression AST. Allowed surface:
       - constants (str/int/bool/None)
       - boolean ops: and/or/not
       - comparisons: == != < > <= >=
       - helper function calls with constant arguments

    No name lookups, no attribute access, no subscripts, no imports.
    Raises ValueError on anything outside this surface.
    """
    if isinstance(node, _ast.Constant):
        return node.value
    if isinstance(node, _ast.BoolOp):
        if isinstance(node.op, _ast.And):
            for v in node.values:
                if not _eval_assertion_ast(v, helpers):
                    return False
            return True
        if isinstance(node.op, _ast.Or):
            for v in node.values:
                if _eval_assertion_ast(v, helpers):
                    return True
            return False
    if isinstance(node, _ast.UnaryOp) and isinstance(node.op, _ast.Not):
        return not _eval_assertion_ast(node.operand, helpers)
    if isinstance(node, _ast.Compare):
        left = _eval_assertion_ast(node.left, helpers)
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_assertion_ast(comparator, helpers)
            if isinstance(op, _ast.Eq) and not (left == right):
                return False
            if isinstance(op, _ast.NotEq) and not (left != right):
                return False
            if isinstance(op, _ast.Lt) and not (left < right):
                return False
            if isinstance(op, _ast.LtE) and not (left <= right):
                return False
            if isinstance(op, _ast.Gt) and not (left > right):
                return False
            if isinstance(op, _ast.GtE) and not (left >= right):
                return False
            left = right
        return True
    if isinstance(node, _ast.Call):
        if not isinstance(node.func, _ast.Name):
            raise ValueError(
                f"only direct function calls allowed, got "
                f"{type(node.func).__name__}"
            )
        fname = node.func.id
        if fname not in helpers:
            raise ValueError(
                f"unknown helper {fname!r}; available: {sorted(helpers)}"
            )
        if node.keywords:
            raise ValueError("keyword arguments are not supported")
        args = [_eval_assertion_ast(a, helpers) for a in node.args]
        return helpers[fname](*args)
    raise ValueError(
        f"disallowed node type in assertion: {type(node).__name__}"
    )


def run_python_assertion(node, project_root):
    """Evaluate verdict_assertion as a Python expression via sandboxed AST walker.

    Truthy → satisfied. Falsy → violated. Disallowed construct or runtime
    error → violated with the error text as evidence.
    """
    assertion = (node.get("verdict_assertion") or "").strip()
    if not assertion:
        return "unknown", "no verdict_assertion specified"

    try:
        tree = _ast.parse(assertion, mode="eval")
    except SyntaxError as exc:
        return "violated", f"assertion is not valid Python expression: {exc}"

    helpers = _assertion_helpers(project_root)
    try:
        result = _eval_assertion_ast(tree.body, helpers)
    except ValueError as exc:
        return "violated", f"assertion rejected: {exc}"
    except Exception as exc:
        return "violated", f"assertion raised {type(exc).__name__}: {exc}"

    if result:
        return "satisfied", f"assertion {assertion!r} → {result!r}"
    return "violated", f"assertion {assertion!r} → {result!r}"


def run_human_signoff(node):
    """Trust the human-set verdict_status column. Returns (status, evidence)."""
    status = (node.get("verdict_status") or "unknown") or "unknown"
    evidence = (node.get("verdict_evidence_ref") or "").strip()
    if not evidence:
        evidence = "human_signoff: no evidence_ref recorded"
    return status, evidence


def _resolve_judge_command(spec_config: dict, env=None) -> str:
    """Find the configured judge command.

    Resolution order:
      1. MANIFOLD_JUDGE_CMD env var (override per-run).
      2. spec_config["judge_command"] (per-project setting in DB).
      3. config file judge_command (machine-global setting).
    Returns empty string if none is set.
    """
    env = env if env is not None else os.environ
    cmd = (env.get("MANIFOLD_JUDGE_CMD") or "").strip()
    if cmd:
        return cmd
    if spec_config:
        project_cmd = (spec_config.get("judge_command") or "").strip()
        if project_cmd:
            return project_cmd
    # Third tier: machine-global config file
    from manifold import config as _config
    file_cfg = _config.load_config()
    file_cmd = (file_cfg.get("judge_command") or "").strip()
    return file_cmd


def _build_judge_prompt(node: dict, parent_node, judge_prompt_override: str = "") -> str:
    """Construct the deterministic prompt fed to the judge command's stdin.

    The same node + parent always produce the same prompt, so the judge can
    cache, log, or diff inputs across runs.
    """
    parent_title = (parent_node.get("title") if parent_node else "") or ""
    parent_body = (parent_node.get("body") if parent_node else "") or "(no parent — top-layer node)"
    child_title = node.get("title", "") or ""
    child_layer = node.get("layer", "") or ""
    child_body = node.get("body", "") or ""

    def _indent(text, prefix):
        return "\n".join(prefix + line for line in (text or "").splitlines())

    sections = [
        "You are judging whether a specification node satisfies its parent contract.",
        "",
        "PARENT (the contract being satisfied):",
        f"  title: {parent_title}",
        "  body:",
        _indent(parent_body, "    "),
        "",
        "CHILD (the claim under review):",
        f"  title: {child_title}",
        f"  layer: {child_layer}",
        "  body:",
        _indent(child_body, "    "),
    ]
    if judge_prompt_override:
        sections.extend([
            "",
            "ADDITIONAL CRITERIA (from the node's verdict_judge_prompt):",
            str(judge_prompt_override),
        ])
    sections.extend([
        "",
        "Reply with EXACTLY one of `satisfied` or `violated` on the FIRST LINE,",
        "then a short paragraph of rationale on subsequent lines.",
    ])
    return "\n".join(sections)


def run_llm_judge(node: dict, parent_node, judge_cmd: str = "") -> tuple:
    """Shell out to the configured judge command. Returns (status, evidence).

    Falls back to ('judge_required', reason) when the command is unset or
    fails to run / returns unparseable output. This is the manifold-side
    contract; the operator is responsible for the actual judge binary
    (claude CLI, gpt CLI, custom script, whatever).
    """
    if not judge_cmd:
        return "judge_required", (
            "no judge command configured "
            "(set MANIFOLD_JUDGE_CMD or spec_config.judge_command)"
        )
    prompt = _build_judge_prompt(
        node, parent_node,
        node.get("verdict_judge_prompt") or "",
    )
    try:
        result = subprocess.run(
            judge_cmd, shell=True, input=prompt,
            capture_output=True, text=True, timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "judge_required", f"judge command exceeded 300s timeout: {judge_cmd}"
    except OSError as exc:
        return "judge_required", f"judge command failed to execute: {exc}"

    if result.returncode != 0:
        return "judge_required", (
            f"judge command exited {result.returncode}; "
            f"stderr: {(result.stderr or '').strip()[:500]}"
        )
    out = (result.stdout or "").strip()
    if not out:
        return "judge_required", "judge command emitted no stdout"

    first_line, _, rest = out.partition("\n")
    first = first_line.strip().lower()
    if first == "satisfied":
        status = "satisfied"
    elif first == "violated":
        status = "violated"
    else:
        return "judge_required", (
            f"judge first line was {first_line!r}, not satisfied/violated"
        )
    evidence = rest.strip()[:2000] or first_line.strip()
    return status, evidence


# ============================================================
# Verdict orchestrator + cache
# ============================================================

def compute_input_hash(node, parent_statuses):
    """Stable SHA-256 over node's verdict-relevant fields + parents' statuses.

    Reused-input → cache hit. Any change in verdict mechanism/check/assertion,
    body, layer, kind, realized_by_external, target_status, OR any parent's
    verdict status causes the hash to change → cache miss → re-evaluate.
    """
    fields = {
        "node_id": node.get("node_id"),
        "layer": node.get("layer"),
        "kind": node.get("kind"),
        "body": node.get("body"),
        "realized_by_external": node.get("realized_by_external"),
        "target_status": node.get("target_status"),
        "verdict_mechanism": node.get("verdict_mechanism"),
        "verdict_check": node.get("verdict_check"),
        "verdict_assertion": node.get("verdict_assertion"),
    }
    payload = json.dumps(fields, sort_keys=True, default=str)
    parents = json.dumps(sorted(parent_statuses.items()), default=str)
    return hashlib.sha256(
        (payload + "\n---\n" + parents).encode("utf-8")
    ).hexdigest()


def run_verdicts(conn, project_id, nodes_by_id, project_root, force,
                  judge_cmd: str = ""):
    """Compute verdicts for every node, using the verdicts table as cache.

    Returns dict node_id → {status, evidence_ref, evidence_hash, source}.
    `source` is one of: cache, automated, python_assertion, human, llm_judge,
    judge_required, no_mechanism, external:<id>.

    Cache key: (project_id, node_id, evidence_hash). If a prior verdict row
    with the same hash exists, reuse it instead of recomputing.

    judge_cmd is the resolved LLM judge shell command; empty string means
    nodes with verdict_mechanism='llm_judge' return ('judge_required', ...).
    """
    verdicts = {}
    now = datetime.now(timezone.utc).isoformat()
    judge_cmd_tag = (hashlib.sha256(judge_cmd.encode("utf-8")).hexdigest()[:12]
                      if judge_cmd else "none")

    for nid, node in nodes_by_id.items():
        parent_ctx = {
            p: (nodes_by_id.get(p, {}).get("verdict_status") or "unknown")
            for p in (node.get("parents") or [])
        }
        # Tag llm_judge entries with the judge command's hash so swapping
        # judge implementations invalidates their cached verdicts.
        if (node.get("verdict_mechanism") or "") == "llm_judge":
            parent_ctx["__judge_cmd__"] = judge_cmd_tag
        h = compute_input_hash(node, parent_ctx)

        if not force:
            cached = conn.execute(
                "SELECT status, source, evidence_ref FROM verdicts "
                "WHERE project_id = ? AND node_id = ? AND evidence_hash = ? "
                "ORDER BY verdict_id DESC LIMIT 1",
                (project_id, nid, h),
            ).fetchone()
            if cached and cached["status"] not in ("", None, "unknown"):
                verdicts[nid] = {
                    "status": cached["status"],
                    "evidence_hash": h,
                    "evidence_ref": cached["evidence_ref"] or "",
                    "last_checked": now,
                    "source": "cache",
                }
                continue

        external = (node.get("realized_by_external") or "").strip()
        if external:
            verdicts[nid] = {
                "status": "deferred_external",
                "evidence_hash": h,
                "evidence_ref": external,
                "last_checked": now,
                "source": f"external:{external}",
            }
            continue

        mechanism = (node.get("verdict_mechanism") or "").strip()
        if mechanism == "automated_check":
            status, evidence = run_automated_check(node, project_root)
            source = "automated"
        elif mechanism == "python_assertion":
            status, evidence = run_python_assertion(node, project_root)
            source = "python_assertion"
        elif mechanism == "human_signoff":
            status, evidence = run_human_signoff(node)
            source = "human"
        elif mechanism == "llm_judge":
            parent_ids = node.get("parents") or []
            parent_node = nodes_by_id.get(parent_ids[0]) if parent_ids else None
            status, evidence = run_llm_judge(node, parent_node, judge_cmd)
            source = "llm_judge" if status in ("satisfied", "violated") \
                else "judge_required"
        else:
            status, evidence = "unknown", f"no verdict_mechanism on {nid}"
            source = "no_mechanism"

        truncated = (evidence or "")[:400]
        if evidence and len(evidence) > 400:
            truncated += "…"
        verdicts[nid] = {
            "status": status,
            "evidence_hash": h,
            "evidence_ref": truncated,
            "last_checked": now,
            "source": source,
        }

    return verdicts


def resolve_external(verdicts, nodes_by_id):
    """realized_by_external links: a node's status follows its target's."""
    for nid, node in nodes_by_id.items():
        target = (node.get("realized_by_external") or "").strip()
        if not target or target not in verdicts:
            continue
        target_status = verdicts[target]["status"]
        if target_status in ("satisfied", "violated",
                              "invalidated_by_descendant"):
            verdicts[nid] = {
                **verdicts[nid],
                "status": target_status,
                "source": f"external:{target}",
            }


def propagate_failures(verdicts, nodes_by_id):
    """Walk bottom-up: any node with a violated descendant becomes
    invalidated_by_descendant. Iterates to a fixed point."""
    parents_of = {
        nid: list(node.get("parents") or [])
        for nid, node in nodes_by_id.items()
    }

    failed = {
        nid for nid, v in verdicts.items()
        if v["status"] in ("violated", "invalidated_by_descendant")
    }
    changed = True
    while changed:
        changed = False
        for nid in list(failed):
            for p in parents_of.get(nid, []):
                if p not in nodes_by_id or p not in verdicts:
                    continue
                if verdicts[p]["status"] in ("violated",
                                              "invalidated_by_descendant"):
                    continue
                verdicts[p] = {
                    **verdicts[p],
                    "status": "invalidated_by_descendant",
                    "source": f"propagated_from:{nid}",
                }
                failed.add(p)
                changed = True
