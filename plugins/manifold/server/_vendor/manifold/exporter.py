"""
Export a manifold project to an on-disk v0.2-style spec tree.

Inverse of `importer.import_project`, in shape: writes
    <out_dir>/specs/spec.yaml
    <out_dir>/specs/<layer>/<node-id>-<slug>.md      (per node)

The output is round-trippable: `manifold import <out_dir>` reads what
this writes back into a fresh DB. NOT a substitute for `dump` / `restore`
which preserve full revision history and validation results — export
only writes current state. Useful for:
  - Git-friendly archival (diffable markdown).
  - Handoff to external tools that consume the v0.2 file shape.
  - Bridging the DB to operators who prefer files.

YAML emitter is hand-rolled and tailored to the manifold-known schema.
It produces output that manifold's own parser (importer._parse_yaml)
reads back identically.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(title: str, max_len: int = 60) -> str:
    """Title → kebab-case slug. Empty title falls back to 'node'."""
    s = _SLUG_RE.sub("-", (title or "").strip().lower()).strip("-")
    return (s or "node")[:max_len]


def _scalar(v) -> str:
    """Emit a YAML scalar — string, int, bool, null."""
    if v is None or v == "":
        return '""'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    # Quote if it contains characters that would confuse the parser.
    needs_quotes = any(ch in s for ch in (":", "#", "{", "}", "[", "]",
                                            ",", "&", "*", "!", "|", ">",
                                            "'", '"', "%", "@", "`", "\n"))
    if not needs_quotes and not (s and s[0] in " -?"):
        return s
    # Double-quote and escape backslash + double-quote.
    escaped = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _flow_list(items) -> str:
    """Emit a flow list `[a, b, c]`. Items are scalars."""
    return "[" + ", ".join(_scalar(x) for x in (items or [])) + "]"


def _emit_frontmatter(fields: dict, *, indent: int = 0) -> str:
    """Render a frontmatter mapping into YAML lines.

    Handles:
      - scalars via _scalar
      - lists → flow when items are short scalars
      - nested dicts via recursion (block mappings)
    """
    out = []
    pad = "  " * indent
    for key, val in fields.items():
        if val is None or val == "":
            continue
        if isinstance(val, dict):
            if not val:
                continue
            out.append(f"{pad}{key}:")
            out.append(_emit_frontmatter(val, indent=indent + 1))
        elif isinstance(val, list):
            out.append(f"{pad}{key}: {_flow_list(val)}")
        else:
            out.append(f"{pad}{key}: {_scalar(val)}")
    return "\n".join(out)


def _node_frontmatter(node: dict, parents: list, peers: list,
                       blocks: list) -> dict:
    """Build the nested-dict frontmatter for one node, in v0.2 shape.

    Manifold's parser expects `target` and `verdict` as nested mappings
    (not flat columns). We rebuild them here so the output round-trips
    through the importer.
    """
    fm: dict = {
        "id": node["node_id"],
        "title": node.get("title") or "",
        "layer": node["layer"],
        "kind": node.get("kind") or "spec",
    }
    if parents:
        fm["parents"] = parents
    if peers:
        fm["peers_depends_on"] = peers
    if (node.get("realized_by_external") or "").strip():
        fm["realized_by_external"] = node["realized_by_external"]

    target = {}
    for src, dst in (("target_status", "status"),
                      ("target_shape", "shape"),
                      ("target_achieved_when", "achieved_when"),
                      ("target_achieved_at", "achieved_at"),
                      ("target_superseded_by", "superseded_by"),
                      ("target_rationale_ref", "rationale_ref")):
        val = node.get(src)
        if val:
            target[dst] = val
    if blocks:
        target["blocks"] = blocks
    if target:
        fm["target"] = target

    verdict = {}
    for src, dst in (("verdict_mechanism", "mechanism"),
                      ("verdict_check", "check"),
                      ("verdict_assertion", "assertion"),
                      ("verdict_judge_prompt", "judge_prompt"),
                      ("verdict_status", "status"),
                      ("verdict_evidence_ref", "evidence_ref"),
                      ("verdict_evidence_hash", "evidence_hash"),
                      ("verdict_last_checked", "last_checked")):
        val = node.get(src)
        if val:
            verdict[dst] = val
    if verdict:
        fm["verdict"] = verdict

    if node.get("delegate_to"):
        fm["delegate_to"] = node["delegate_to"]

    # contract and applies_to are JSON columns; emit if present.
    if node.get("contract"):
        try:
            fm["contract"] = (json.loads(node["contract"])
                                if isinstance(node["contract"], str)
                                else node["contract"])
        except (json.JSONDecodeError, TypeError):
            pass
    if node.get("applies_to"):
        try:
            fm["applies_to"] = (json.loads(node["applies_to"])
                                  if isinstance(node["applies_to"], str)
                                  else node["applies_to"])
        except (json.JSONDecodeError, TypeError):
            pass

    return fm


def _emit_spec_yaml(project_id: str, spec_config: dict) -> str:
    """Emit spec.yaml content from the project's spec_config."""
    fields: dict = {
        "name": spec_config.get("name") or project_id,
    }
    layers = spec_config.get("layers") or []
    if layers:
        fields["layers"] = None  # placeholder; handled below
    judge_command = (spec_config.get("judge_command") or "").strip()
    if judge_command:
        fields["judge_command"] = judge_command
    framework_version = spec_config.get("framework_version")
    if framework_version:
        fields["framework_version"] = framework_version

    out_lines = []
    for key, val in fields.items():
        if val is None and key != "layers":
            continue
        if key == "layers":
            out_lines.append("layers:")
            for layer in layers:
                if isinstance(layer, dict) and layer.get("name"):
                    out_lines.append(f"  - name: {_scalar(layer['name'])}")
                    for k, v in layer.items():
                        if k == "name":
                            continue
                        if v not in (None, ""):
                            out_lines.append(f"    {k}: {_scalar(v)}")
                else:
                    out_lines.append(f"  - {_scalar(layer)}")
        else:
            out_lines.append(f"{key}: {_scalar(val)}")
    return "\n".join(out_lines) + "\n"


def _write_node_file(path: Path, fm: dict, body: str) -> None:
    fm_text = _emit_frontmatter(fm)
    body_text = (body or "").rstrip("\n")
    content = f"---\n{fm_text}\n---\n{body_text}\n"
    path.write_text(content, encoding="utf-8")


def export_project(conn, project_id: str, out_dir: Path) -> dict:
    """Write `project_id` as an on-disk spec tree under `out_dir`.

    Creates `out_dir/specs/spec.yaml` and `out_dir/specs/<layer>/<id>-<slug>.md`
    per non-deleted node. Refuses to overwrite an existing specs/ directory
    (move or delete the old one first).

    Returns {project_id, nodes_exported, out_dir}.
    """
    out_dir = Path(out_dir)
    specs_dir = out_dir / "specs"
    if specs_dir.exists():
        raise FileExistsError(
            f"refusing to overwrite existing directory: {specs_dir}"
        )

    proj = conn.execute(
        "SELECT project_id, label, spec_config FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if proj is None:
        raise ValueError(f"project not found: {project_id!r}")
    try:
        spec_config = json.loads(proj["spec_config"]) if proj["spec_config"] else {}
    except (json.JSONDecodeError, TypeError):
        spec_config = {}

    specs_dir.mkdir(parents=True)
    (specs_dir / "spec.yaml").write_text(
        _emit_spec_yaml(project_id, spec_config), encoding="utf-8",
    )

    layer_names = [L.get("name") for L in (spec_config.get("layers") or [])
                    if isinstance(L, dict) and L.get("name")]

    node_rows = conn.execute(
        "SELECT * FROM nodes WHERE project_id = ? AND deleted_at IS NULL "
        "ORDER BY layer, node_id",
        (project_id,),
    ).fetchall()

    # Pre-bucket edges so we don't query per-node.
    edges_by_src: dict = {}
    for e in conn.execute(
        "SELECT src_node_id, dst_node_id, edge_kind FROM node_edges "
        "WHERE project_id = ?", (project_id,),
    ).fetchall():
        edges_by_src.setdefault(e["src_node_id"], []).append(e)

    nodes_exported = 0
    for row in node_rows:
        node = dict(row)
        nid = node["node_id"]
        layer = node["layer"]
        parents = [e["dst_node_id"] for e in edges_by_src.get(nid, [])
                    if e["edge_kind"] == "parent"]
        peers = [e["dst_node_id"] for e in edges_by_src.get(nid, [])
                  if e["edge_kind"] == "depends_on"]
        blocks = [e["dst_node_id"] for e in edges_by_src.get(nid, [])
                   if e["edge_kind"] == "blocks"]

        layer_dir = specs_dir / layer
        layer_dir.mkdir(parents=True, exist_ok=True)
        slug = _slug(node.get("title") or nid)
        out_file = layer_dir / f"{nid}-{slug}.md"
        fm = _node_frontmatter(node, parents, peers, blocks)
        _write_node_file(out_file, fm, node.get("body") or "")
        nodes_exported += 1

    # Also create empty directories for layers that have no nodes — so the
    # round-tripped import sees the full layer list even when empty.
    for layer in layer_names:
        (specs_dir / layer).mkdir(parents=True, exist_ok=True)

    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'project_exported', ?)",
        (datetime.now(timezone.utc).isoformat(), project_id,
         json.dumps({"out_dir": str(out_dir),
                     "nodes_exported": nodes_exported})),
    )

    return {"project_id": project_id, "nodes_exported": nodes_exported,
            "out_dir": str(out_dir)}
