"""
v0.2 markdown spec → DB importer.

Reads spec files from a repo, walks git history, populates the DB with
revisions tagged by git_sha. Idempotent.

The YAML parser is vendored from v0.2's `validate.py` (`_parse_yaml_fallback`
plus the supporting helpers). Stdlib-only — no pyyaml dependency.
"""
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ============================================================
# Frontmatter + YAML
# ============================================================

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)$", re.DOTALL)


def parse_node_file(text: str) -> dict:
    """Split a manifold v0.2 node-file string into frontmatter + body."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {"frontmatter": {}, "body": (text or "").strip()}
    fm_text, body = m.group(1), m.group(2)
    fm = _parse_yaml(fm_text)
    if not isinstance(fm, dict):
        fm = {}
    return {"frontmatter": fm, "body": body}


def _parse_yaml(text: str) -> dict:
    """Hand-rolled YAML parser for manifold v0.2's schema (vendored from v0.2 validate.py).

    Handles: scalars, quoted strings (with double-quoted escape sequences),
    flow lists, block lists of mappings, nested mappings, block scalars (>|>-|+).
    Does NOT handle: anchors, aliases, complex multi-line strings outside block scalars.
    """
    text = text.replace("\t", "  ")

    lines = []
    for raw in text.splitlines():
        commented = raw
        hash_idx = raw.find("#")
        if hash_idx >= 0 and not _hash_inside_quotes(raw, hash_idx):
            commented = raw[:hash_idx].rstrip()
        if not commented.strip():
            continue
        indent = len(commented) - len(commented.lstrip(" "))
        content = commented.strip()
        lines.append((indent, content))

    pos = [0]
    BLOCK_SCALAR_INDICATORS = (">", "|", ">-", "|-", ">+", "|+")

    def _consume_block_scalar(folded, base_indent):
        chunks = []
        while pos[0] < len(lines):
            ni, nc = lines[pos[0]]
            if ni <= base_indent:
                break
            chunks.append(nc)
            pos[0] += 1
        joiner = " " if folded else "\n"
        return joiner.join(chunks).strip()

    def parse_block(min_indent):
        if pos[0] >= len(lines):
            return None
        first_indent, first_content = lines[pos[0]]
        if first_indent < min_indent:
            return None
        if first_content.startswith("- "):
            return parse_list(first_indent)
        return parse_mapping(first_indent)

    def parse_mapping(my_indent):
        out = {}
        while pos[0] < len(lines):
            indent, content = lines[pos[0]]
            if indent < my_indent:
                break
            if indent > my_indent:
                pos[0] += 1
                continue
            if content.startswith("- "):
                break
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", content)
            if not m:
                pos[0] += 1
                continue
            key, val = m.group(1), m.group(2)
            pos[0] += 1
            if val in BLOCK_SCALAR_INDICATORS:
                folded = val.startswith(">")
                out[key] = _consume_block_scalar(folded, my_indent)
            elif val == "":
                nested = parse_block(my_indent + 1)
                out[key] = nested if nested is not None else ""
            else:
                out[key] = _coerce(val)
        return out

    def parse_list(my_indent):
        out = []
        while pos[0] < len(lines):
            indent, content = lines[pos[0]]
            if indent < my_indent or not content.startswith("- "):
                break
            if indent > my_indent:
                pos[0] += 1
                continue
            rest = content[2:].strip()
            pos[0] += 1
            inline = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", rest)
            if inline:
                item = {}
                key, val = inline.group(1), inline.group(2)
                if val in BLOCK_SCALAR_INDICATORS:
                    item[key] = _consume_block_scalar(val.startswith(">"), my_indent)
                elif val == "":
                    item[key] = parse_block(my_indent + 2)
                else:
                    item[key] = _coerce(val)
                while pos[0] < len(lines):
                    next_indent, next_content = lines[pos[0]]
                    if next_indent <= my_indent:
                        break
                    if next_content.startswith("- "):
                        break
                    sub = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", next_content)
                    if not sub:
                        pos[0] += 1
                        continue
                    sk, sv = sub.group(1), sub.group(2)
                    pos[0] += 1
                    if sv in BLOCK_SCALAR_INDICATORS:
                        item[sk] = _consume_block_scalar(sv.startswith(">"), next_indent)
                    elif sv == "":
                        item[sk] = parse_block(next_indent + 1)
                    else:
                        item[sk] = _coerce(sv)
                out.append(item)
            else:
                out.append(_coerce(rest))
        return out

    result = parse_mapping(0)
    return result if isinstance(result, dict) else {}


def _hash_inside_quotes(s, idx):
    in_quote = False
    quote_char = ""
    for i, ch in enumerate(s):
        if i == idx:
            return in_quote
        if not in_quote and ch in ('"', "'"):
            in_quote = True
            quote_char = ch
        elif in_quote and ch == quote_char:
            in_quote = False
    return False


def _coerce(val: str):
    val = val.strip()
    if (len(val) >= 2) and (val[0] == val[-1]) and (val[0] in ('"', "'")):
        inner = val[1:-1]
        if val[0] == '"':
            return _decode_double_quoted(inner)
        return inner.replace("''", "'")
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [_coerce(x) for x in _split_list(inner)]
    if val.lower() in ("true", "false"):
        return val.lower() == "true"
    if val.lower() in ("null", "~", ""):
        return ""
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        return val


def _decode_double_quoted(s: str) -> str:
    out = []
    i = 0
    escapes = {"\\": "\\", '"': '"', "n": "\n", "t": "\t",
               "r": "\r", "0": "\0", "/": "/"}
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            esc = escapes.get(s[i + 1])
            if esc is not None:
                out.append(esc)
                i += 2
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def _split_list(inner: str) -> list[str]:
    items, buf, in_q, qc = [], "", False, ""
    for ch in inner:
        if not in_q and ch == ",":
            items.append(buf.strip())
            buf = ""
            continue
        if not in_q and ch in ('"', "'"):
            in_q, qc = True, ch
        elif in_q and ch == qc:
            in_q = False
        buf += ch
    if buf.strip():
        items.append(buf.strip())
    return items


# ============================================================
# Git helpers
# ============================================================

def _git(args: list[str], repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo)] + args,
        capture_output=True, text=True,
    )


def _git_toplevel(repo: Path) -> Path:
    """Return the git repo root containing `repo`."""
    result = _git(["rev-parse", "--show-toplevel"], repo)
    if result.returncode != 0:
        raise FileNotFoundError(f"{repo} is not inside a git working tree")
    return Path(result.stdout.strip())


def _spec_path_prefix(repo: Path) -> str:
    """Return the repo-root-relative path prefix to `repo/specs/`.

    e.g. if repo is `~/code/agent-skills/skills/manifold` and the git repo root
    is `~/code/agent-skills`, returns `skills/manifold/specs`.
    """
    toplevel = _git_toplevel(repo)
    rel = Path(repo).resolve().relative_to(toplevel)
    if rel == Path("."):
        return "specs"
    return (rel / "specs").as_posix()


def _git_log(toplevel: Path, paths: str) -> list[tuple[str, str]]:
    """Return [(sha, iso_ts), ...] for commits that touched `paths`, OLDEST first.

    `paths` is REPO-ROOT-relative; we run with -C <toplevel> so cwd == repo root.
    """
    result = _git(["log", "--reverse", "--pretty=format:%H %aI", "--", paths], toplevel)
    if result.returncode != 0:
        return []
    out = []
    for line in result.stdout.strip().splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            out.append((parts[0], parts[1]))
    return out


def _git_show(toplevel: Path, sha: str, path: str) -> Optional[str]:
    """`path` is REPO-ROOT-relative (matches what git_ls_tree returns)."""
    result = _git(["show", f"{sha}:{path}"], toplevel)
    if result.returncode != 0:
        return None
    return result.stdout


def _git_ls_tree_md(toplevel: Path, sha: str, prefix: str) -> list[str]:
    """List *.md files under `prefix` at `sha`. `prefix` is REPO-ROOT-relative.

    Returns repo-root-relative paths.
    """
    p = prefix if prefix.endswith("/") else prefix + "/"
    result = _git(["ls-tree", "-r", "--name-only", sha, p], toplevel)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.endswith(".md")]


# ============================================================
# Change summary
# ============================================================

def _compute_change_summary(prev: Optional[dict], curr: dict) -> Optional[list]:
    """Diff field-by-field. Returns None if there's no prior revision."""
    if prev is None:
        return None
    diff = []
    keys = set(prev) | set(curr)
    for key in sorted(keys):
        if key.startswith("_"):
            continue
        if prev.get(key) != curr.get(key):
            diff.append({"field": key, "old": prev.get(key), "new": curr.get(key)})
    return diff


# ============================================================
# Import
# ============================================================

def import_project(conn, repo: Path, project_id: Optional[str] = None, *,
                   actor: str) -> dict:
    """Import a v0.2 spec dir into the DB. Replays git log of specs/.

    Idempotent: re-running advances from the last imported git_sha onward.
    """
    from manifold import writes
    repo = Path(repo).resolve()

    spec_yaml_path = repo / "specs" / "spec.yaml"
    if not spec_yaml_path.is_file():
        raise FileNotFoundError(f"{spec_yaml_path} not found")

    spec_yaml_text = spec_yaml_path.read_text(encoding="utf-8")
    spec_config = _parse_yaml(spec_yaml_text)

    if not project_id:
        project_id = spec_config.get("name") or repo.name

    # Ensure project row
    existing = conn.execute(
        "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
    ).fetchone()
    if not existing:
        writes.register_project(conn, project_id, spec_config,
                                 label=spec_config.get("name", project_id))

    # Idempotency: find last imported git_sha for this project
    last_sha_row = conn.execute(
        "SELECT git_sha FROM revisions WHERE project_id = ? AND git_sha IS NOT NULL "
        "ORDER BY revision_id DESC LIMIT 1", (project_id,)
    ).fetchone()
    skip_through = last_sha_row["git_sha"] if last_sha_row else None

    # Use repo-root-relative paths consistently and run git commands from the
    # toplevel; this handles both standalone repos and subdirectory-of-larger-repo
    # cases uniformly.
    toplevel = _git_toplevel(repo)
    spec_prefix = _spec_path_prefix(repo)
    commits = _git_log(toplevel, spec_prefix)
    if not commits:
        return {"project_id": project_id, "nodes_imported": 0, "revisions_imported": 0}

    # Pre-load existing last_snapshot_per_node if this is a resume
    last_snapshot_per_node: dict[str, dict] = {}
    if skip_through:
        rows = conn.execute(
            "SELECT node_id, snapshot FROM revisions r "
            "WHERE project_id = ? AND revision_id = ("
            "  SELECT MAX(revision_id) FROM revisions WHERE project_id = ? "
            "  AND node_id = r.node_id"
            ")",
            (project_id, project_id),
        ).fetchall()
        for r in rows:
            try:
                last_snapshot_per_node[r["node_id"]] = json.loads(r["snapshot"])
            except (json.JSONDecodeError, TypeError):
                pass

    revisions_imported = 0
    nodes_seen = set()
    started = (skip_through is None)
    now_actor = actor

    for sha, ts in commits:
        if not started:
            if sha == skip_through:
                started = True
            continue

        files = _git_ls_tree_md(toplevel, sha, spec_prefix)
        # Skip spec.yaml itself; node files must be under a layer/ subdir.
        spec_yaml_full = f"{spec_prefix}/spec.yaml"
        files = [f for f in files
                  if f != spec_yaml_full
                  and f.startswith(spec_prefix + "/")
                  and "/" in f[len(spec_prefix) + 1:]]
        files_at_commit_ids: set[str] = set()

        for f in files:
            content = _git_show(toplevel, sha, f)
            if content is None:
                continue
            parsed = parse_node_file(content)
            fm = parsed["frontmatter"]
            nid = fm.get("id")
            if not nid:
                continue
            files_at_commit_ids.add(nid)
            snapshot = {
                "node_id": nid,
                "layer": fm.get("layer", ""),
                "title": fm.get("title", ""),
                "kind": fm.get("kind", "spec"),
                "body": parsed["body"],
                "parents": fm.get("parents") or [],
                "peers_depends_on": fm.get("peers_depends_on") or [],
                "target_blocks": (fm.get("target") or {}).get("blocks", []) if isinstance(fm.get("target"), dict) else [],
                "target_status": (fm.get("target") or {}).get("status", "") if isinstance(fm.get("target"), dict) else "",
                "realized_by_external": fm.get("realized_by_external") or "",
            }
            prev = last_snapshot_per_node.get(nid)
            if prev is not None and prev == snapshot:
                continue       # no-op at this commit for this node
            change_type = "created" if prev is None else "updated"
            change_summary = _compute_change_summary(prev, snapshot)
            conn.execute(
                "INSERT INTO revisions (project_id, node_id, ts, change_type, "
                "snapshot, change_summary, source, actor, git_sha) "
                "VALUES (?, ?, ?, ?, ?, ?, 'import', ?, ?)",
                (project_id, nid, ts, change_type,
                 json.dumps(snapshot, sort_keys=True),
                 json.dumps(change_summary) if change_summary else None,
                 now_actor, sha),
            )
            revisions_imported += 1
            nodes_seen.add(nid)
            last_snapshot_per_node[nid] = snapshot

        # Detect deletes: nodes we'd seen before that disappear at this commit
        for nid in list(last_snapshot_per_node):
            if nid in files_at_commit_ids:
                continue
            snap = last_snapshot_per_node[nid]
            if snap.get("_deleted"):
                continue
            conn.execute(
                "INSERT INTO revisions (project_id, node_id, ts, change_type, "
                "snapshot, source, actor, git_sha) "
                "VALUES (?, ?, ?, 'deleted', ?, 'import', ?, ?)",
                (project_id, nid, ts, json.dumps(snap, sort_keys=True),
                 now_actor, sha),
            )
            revisions_imported += 1
            snap["_deleted"] = True

    # Sync nodes table to HEAD state
    _sync_nodes_to_head(conn, project_id, last_snapshot_per_node)

    conn.execute(
        "INSERT INTO events (ts, project_id, event_type, detail) "
        "VALUES (?, ?, 'import_finished', ?)",
        (datetime.now(timezone.utc).isoformat(), project_id,
         json.dumps({"nodes_imported": len(nodes_seen),
                     "revisions_imported": revisions_imported})),
    )

    return {
        "project_id": project_id,
        "nodes_imported": len(nodes_seen),
        "revisions_imported": revisions_imported,
    }


def _sync_nodes_to_head(conn, project_id: str, snapshots: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    for nid, snap in snapshots.items():
        if snap.get("_deleted"):
            # Ensure deleted_at is set on any nodes row that may exist
            conn.execute(
                "UPDATE nodes SET deleted_at = ? WHERE project_id = ? AND node_id = ? "
                "AND deleted_at IS NULL",
                (now, project_id, nid),
            )
            continue
        rev = conn.execute(
            "SELECT revision_id FROM revisions WHERE project_id = ? AND node_id = ? "
            "ORDER BY revision_id DESC LIMIT 1",
            (project_id, nid),
        ).fetchone()
        rev_id = rev["revision_id"] if rev else None
        conn.execute(
            "INSERT OR REPLACE INTO nodes (project_id, node_id, layer, title, "
            "kind, body, realized_by_external, target_status, "
            "current_revision_id, last_modified_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, nid, snap.get("layer", ""), snap.get("title", ""),
             snap.get("kind", "spec"), snap.get("body", ""),
             snap.get("realized_by_external", "") or None,
             snap.get("target_status", "") or None,
             rev_id, now),
        )
        # Replace edges
        for src_field, kind in (("parents", "parent"),
                                 ("peers_depends_on", "depends_on"),
                                 ("target_blocks", "blocks")):
            targets = snap.get(src_field) or []
            conn.execute(
                "DELETE FROM node_edges WHERE project_id = ? AND src_node_id = ? "
                "AND edge_kind = ?",
                (project_id, nid, kind),
            )
            for t in targets:
                conn.execute(
                    "INSERT OR IGNORE INTO node_edges (project_id, src_node_id, "
                    "dst_node_id, edge_kind, created_at) VALUES (?, ?, ?, ?, ?)",
                    (project_id, nid, t, kind, now),
                )
