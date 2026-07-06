"""
manifold web server — stdlib http.server + route dispatch.

Two surfaces:
- HTML at `/`, `/projects/<p>`, `/projects/<p>/nodes/<n>`, etc.
- JSON API at `/api/v1/*`

Both consume the same Python query/write layer. Run via:
    python3 -m manifold serve [--port 7779]
"""
import json
import re
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html import escape
from pathlib import Path
from typing import Callable, Optional

from manifold import config, db, errors, markdown, queries, schema, writes

from manifold_web import html


# ============================================================
# Routes
# ============================================================

# Each route: (method, regex, handler_name, content_type)
# Handlers are bound at request time so they can use the request's conn.

ROUTES_HTML: list[tuple[str, re.Pattern, str]] = [
    ("GET",    re.compile(r"^/?$"),                                                       "html_index"),
    ("GET",    re.compile(r"^/projects$"),                                                "html_index"),
    # /projects/archived must come before the generic /projects/<id> route below.
    ("GET",    re.compile(r"^/projects/archived$"),                                       "html_archived_projects"),
    # /projects/<p>/spec-audit and drift-report must come before generic node routes
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/spec-audit$"),             "html_spec_audit"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/drift-report$"),         "html_drift_report"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/brief$"),               "html_brief"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/diagram$"),              "html_diagram"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/mindmap$"),             "html_mindmap"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/views/(?P<view_id>[^/]+)$"), "html_view"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)$"),                          "html_project"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)$"), "html_node"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)/edit$"), "html_node_edit_get"),
    ("POST",   re.compile(r"^/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)$"), "html_node_edit_post"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)/revisions/(?P<revision_id>[0-9]+)$"), "html_revision_detail"),
    ("POST",   re.compile(r"^/projects/(?P<project_id>[^/]+)/validations$"),              "html_run_validation_post"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/validations/(?P<validation_id>[0-9]+)$"), "html_validation_detail"),
    ("POST",   re.compile(r"^/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)/delete$"), "html_soft_delete_node"),
    ("POST",   re.compile(r"^/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)/restore$"), "html_restore_node"),
    ("GET",    re.compile(r"^/projects/(?P<project_id>[^/]+)/deleted$"),                  "html_deleted_nodes"),
    ("POST",   re.compile(r"^/projects/(?P<project_id>[^/]+)/archive$"),                  "html_archive_project"),
    ("POST",   re.compile(r"^/projects/(?P<project_id>[^/]+)/unarchive$"),                "html_unarchive_project"),
    ("GET",    re.compile(r"^/reports/targets$"),                                         "html_targets"),
    ("GET",    re.compile(r"^/reports/flips$"),                                           "html_flips"),
    ("GET",    re.compile(r"^/reports/portfolio$"),                                       "html_portfolio"),
    ("GET",    re.compile(r"^/trajectories/(?P<trajectory_id>[^/]+)$"),                  "html_trajectory"),
]

ROUTES_API: list[tuple[str, re.Pattern, str]] = [
    ("GET",    re.compile(r"^/api/v1/projects$"),                                          "api_list_projects"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)$"),                    "api_get_project"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/nodes$"),              "api_list_nodes"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/next-leaves$"),        "api_next_leaves"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/spec-audit$"),       "api_spec_audit"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/drift-report$"),     "api_drift_report"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/brief$"),           "api_brief"),
    ("GET",    re.compile(r"^/api/v1/presentation/views$"),                            "api_list_presentation_views"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/diagram$"),          "api_diagram"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/mindmap$"),         "api_mindmap"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/views/(?P<view_id>[^/]+)$"), "api_view"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)$"), "api_get_node"),
    ("PATCH",  re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)$"), "api_patch_node"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/nodes/(?P<node_id>[^/]+)/revisions$"), "api_list_revisions"),
    ("GET",    re.compile(r"^/api/v1/reports/targets$"),                                   "api_list_targets"),
    ("GET",    re.compile(r"^/api/v1/reports/flips$"),                                     "api_list_flips"),
    ("GET",    re.compile(r"^/api/v1/reports/portfolio$"),                                "api_portfolio_report"),
    ("POST",   re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/validations$"),        "api_run_validation"),
    ("GET",    re.compile(r"^/api/v1/projects/(?P<project_id>[^/]+)/validations/(?P<validation_id>[0-9]+)$"), "api_get_validation"),
    ("POST",   re.compile(r"^/api/v1/projects$"),                                          "api_register_project"),
    ("GET",    re.compile(r"^/api/v1/trajectories/(?P<trajectory_id>[^/]+)$"),             "api_peek_trajectory"),
    ("POST",   re.compile(r"^/api/v1/trajectories/propose$"),                             "api_propose_trajectory"),
    ("POST",   re.compile(r"^/api/v1/trajectories/(?P<trajectory_id>[^/]+)/accept$"),      "api_accept_trajectory"),
]

STATIC_PREFIX = "/static/"
STATIC_ROOT = Path(__file__).resolve().parent.parent / "web" / "static"

_NEGOTIABLE_HTML = frozenset({
    "html_diagram", "html_mindmap", "html_view", "html_brief",
})


# ============================================================
# Request handler
# ============================================================

class ManifoldHandler(BaseHTTPRequestHandler):
    server_version = f"manifold/{config.MANIFOLD_VERSION}"

    # Disable noisy default logging unless verbose
    def log_message(self, format, *args):
        if getattr(self.server, "verbose", False):
            super().log_message(format, *args)

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PATCH(self):
        self._dispatch("PATCH")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def _dispatch(self, method: str):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Static files
        if path.startswith(STATIC_PREFIX):
            return self._serve_static(path[len(STATIC_PREFIX):])

        # Match routes
        for m, pat, handler_name in ROUTES_API:
            if m != method:
                continue
            mtch = pat.match(path)
            if mtch:
                return self._call_json(handler_name, mtch.groupdict(),
                                        parsed.query)
        for m, pat, handler_name in ROUTES_HTML:
            if m != method:
                continue
            mtch = pat.match(path)
            if mtch:
                return self._call_html(handler_name, mtch.groupdict(),
                                        parsed.query)
        self._404()

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _form_data(self) -> dict:
        """Parse application/x-www-form-urlencoded body.

        Single-value fields return str; multi-value fields (checkboxes,
        list inputs that submit the same name multiple times) return list[str].
        Callers that only ever expect single values can use form.get(key, "")
        and trust they'll get a string back when the form actually submitted one.
        """
        ctype = self.headers.get("Content-Type", "")
        body = self._read_body()
        if "application/x-www-form-urlencoded" not in ctype and body:
            ctype = "application/x-www-form-urlencoded"
        parsed = urllib.parse.parse_qs(body.decode("utf-8"), keep_blank_values=True)
        out: dict = {}
        for k, vs in parsed.items():
            out[k] = vs[0] if len(vs) == 1 else vs
        return out

    def _json_body(self) -> dict:
        body = self._read_body()
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def _call_html(self, name: str, kwargs: dict, query: str):
        handler: Callable = HANDLERS_HTML[name]
        try:
            result = handler(self, kwargs, urllib.parse.parse_qs(query))
        except writes.WritesError as exc:
            env = errors.from_writes_exception(
                exc,
                project_id=kwargs.get("project_id"),
                node_id=kwargs.get("node_id"),
            )
            html_str = html.render_page(
                "Error",
                f'<h1>Error: {escape(env["error"]["code"])}</h1>'
                f'<p>{escape(env["error"]["message"])}</p>',
                error=env["error"]["code"],
            )
            self._send_html(html_str, status=400)
            return
        except Exception as exc:
            html_str = html.render_page(
                "Internal Error",
                f"<h1>Internal Error</h1><pre>{escape(repr(exc))}</pre>",
                error="INTERNAL_ERROR",
            )
            self._send_html(html_str, status=500)
            return

        if isinstance(result, tuple) and len(result) == 3 and result[0] == "json":
            self._send_json(result[1], status=result[2], vary=name in _NEGOTIABLE_HTML)
            return
        html_str, status = result
        self._send_html(html_str, status=status, vary=name in _NEGOTIABLE_HTML)

    def _call_json(self, name: str, kwargs: dict, query: str):
        handler: Callable = HANDLERS_API[name]
        try:
            payload, status = handler(self, kwargs, urllib.parse.parse_qs(query))
        except writes.WritesError as exc:
            payload = errors.from_writes_exception(
                exc,
                project_id=kwargs.get("project_id"),
                node_id=kwargs.get("node_id"),
            )
            status = 409 if "STALE" in payload["error"]["code"] else 400
        except Exception as exc:
            payload = errors.envelope(errors.INTERNAL_ERROR, f"{type(exc).__name__}: {exc}")
            status = 500
        self._send_json(payload, status=status)

    def _serve_static(self, rel: str):
        # Prevent path traversal
        target = (STATIC_ROOT / rel).resolve()
        if not str(target).startswith(str(STATIC_ROOT.resolve())):
            return self._404()
        if not target.is_file():
            return self._404()
        ct = _guess_content_type(target.name)
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(data)))
        # Static assets are immutable for a given version; cache aggressively.
        self.send_header("Cache-Control", "public, max-age=86400")
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, html_str: str, status: int = 200, *, vary: bool = False):
        data = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        if vary:
            self.send_header("Vary", "Accept")
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, obj, status: int = 200, *, vary: bool = False):
        data = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        if vary:
            self.send_header("Vary", "Accept")
        self.end_headers()
        self.wfile.write(data)

    def _redirect(self, location: str):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _404(self):
        body = html.render_page("Not Found", "<h1>404 Not Found</h1>", error="NOT_FOUND")
        self._send_html(body, status=404)


_CT = {
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".json": "application/json",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def _guess_content_type(filename: str) -> str:
    for ext, ct in _CT.items():
        if filename.endswith(ext):
            return ct
    return "application/octet-stream"


# ============================================================
# HTML handlers
# Each handler returns (html_str, status).
# ============================================================

def _conn(handler):
    """Each handler shares the server's single connection (single-process)."""
    return handler.server.conn


def html_index(handler, kwargs, query):
    conn = _conn(handler)
    projects = queries.list_projects(conn)
    rows = []
    for p in projects:
        rows.append([
            html.raw(html.link(f"/projects/{p['project_id']}", p["project_id"])),
            p["label"] or "",
            p["created_at"][:10] if p["created_at"] else "",
        ])
    body = "<h1>Projects</h1>"
    if not projects:
        body += "<p class='muted'>No projects yet. Import one with: <code>manifold import &lt;repo&gt;</code></p>"
    else:
        body += html.table(["ID", "Label", "Created"], rows)
    return html.render_page("manifold", body), 200


def html_project(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    proj = queries.get_project(conn, pid)
    if proj is None:
        return html.render_page("Not Found",
                                  f"<h1>Project not found: {escape(pid)}</h1>"), 404
    layers = [l.get("name") for l in (proj["spec_config"] or {}).get("layers") or []
              if isinstance(l, dict)]
    stats = queries.project_dashboard_stats(conn, pid)
    archive_form = (
        f"<form method='post' action='/projects/{escape(pid)}/archive' "
        f"style='display:inline' "
        f"onsubmit='return confirm(\"Archive this project? It stays in the DB; just hidden.\")'>"
        f"<button type='submit' class='secondary'>Archive</button></form>"
    )
    body = [f"<div class='page-hero'><h1>{escape(proj['label'] or pid)}</h1>"
            f"<p class='subtitle'><code>{escape(pid)}</code></p></div>",
            html.project_viz_nav(pid, active="project"),
            html.dashboard_cards(stats, pid),
            html.validation_trigger_form(pid)]
    for layer in layers:
        body.append(f"<h2>Layer: <code>{escape(layer)}</code></h2>")
        nodes = queries.list_nodes(conn, pid, layer=layer, limit=200)
        if not nodes:
            body.append("<p class='muted'>(empty)</p>")
            continue
        rows = []
        for n in nodes:
            target_badge = (html.raw(html.badge(n["target_status"], "target"))
                            if n["target_status"] else "")
            verdict_badge = (html.raw(html.badge(n["verdict_status"],
                                                   f"status-{n['verdict_status']}"))
                             if n["verdict_status"] else "")
            rows.append([
                html.raw(html.link(f"/projects/{pid}/nodes/{n['node_id']}",
                                     n["node_id"])),
                n["title"] or "",
                target_badge,
                verdict_badge,
            ])
        body.append(html.table(["ID", "Title", "Target", "Verdict"], rows))
    body.append(
        f"<p class='muted' style='margin-top:24px'>"
        f"{archive_form} · "
        f"<a href='/projects/{escape(pid)}/deleted'>deleted nodes</a></p>"
    )
    return html.render_page(f"manifold · {pid}", "\n".join(body), main_class="page-wide"), 200


def html_node(handler, kwargs, query):
    conn = _conn(handler)
    pid, nid = kwargs["project_id"], kwargs["node_id"]
    node = queries.get_node(conn, pid, nid)
    if node is None:
        return html.render_page("Not Found",
                                  f"<h1>Node not found: {escape(pid)}:{escape(nid)}</h1>"), 404
    revs = queries.list_revisions(conn, pid, nid, limit=10)

    # Fetch parents ordered by insertion (rowid) to honour primary-parent convention.
    # The first entry is the primary parent for narrative rendering.
    parent_rows = conn.execute(
        "SELECT dst_node_id FROM node_edges "
        "WHERE project_id = ? AND src_node_id = ? AND edge_kind = 'parent' "
        "ORDER BY rowid",
        (pid, nid),
    ).fetchall()
    parents_ordered = [r["dst_node_id"] for r in parent_rows]

    title = node["title"] or nid
    rev = int(node['current_revision_id'] or 0)
    delete_form = (
        f"<form method='post' "
        f"action='/projects/{escape(pid)}/nodes/{escape(nid)}/delete' "
        f"style='display:inline' "
        f"onsubmit='return confirm(\"Soft-delete this node?\")'>"
        f"<input type='hidden' name='expected_revision_id' value='{rev}'>"
        f"<button type='submit' class='secondary'>Delete</button></form>"
    )
    body = [
        f"<h1>{escape(nid)} · {escape(title)}</h1>",
        f"<p class='muted'>Layer: <code>{escape(node['layer'])}</code> · "
        f"Kind: <code>{escape(node['kind'])}</code> · "
        f"Revision: <code>{rev}</code></p>",
        f'<p><a href="/projects/{escape(pid)}/nodes/{escape(nid)}/edit">Edit</a> · '
        f'<a href="/projects/{escape(pid)}">Back to project</a> · '
        f'{delete_form}</p>',
    ]

    # parents panel (primary-parent convention)
    panel = html.parents_panel(parents_ordered)
    if panel:
        body.append(f"<h2>Parents</h2>{panel}")

    if node["target_status"]:
        body.append(f"<h2>Target</h2><p>Status: {html.badge(node['target_status'], 'target')}</p>")
        if node["target_achieved_when"]:
            body.append(f"<p><strong>Achieved when:</strong> {escape(node['target_achieved_when'])}</p>")

    body.append("<h2>Body</h2>")
    body.append(f"<div class='rendered'>{markdown.render(node['body'] or '')}</div>")

    # rationale + alternatives collapsible section
    rationale_html = html.rationale_section(node)
    if rationale_html:
        body.append(rationale_html)

    # Fetch change_reason for revision timeline (queries.list_revisions omits it).
    if revs:
        rev_ids = [r["revision_id"] for r in revs]
        placeholders = ",".join("?" * len(rev_ids))
        cr_rows = conn.execute(
            f"SELECT revision_id, change_reason FROM revisions "
            f"WHERE revision_id IN ({placeholders})",
            rev_ids,
        ).fetchall()
        change_reasons = {r["revision_id"]: r["change_reason"] for r in cr_rows}
    else:
        change_reasons = {}

    body.append("<h2>History</h2>")
    if not revs:
        body.append("<p class='muted'>(no revisions)</p>")
    else:
        body.append("<div class='timeline'>")
        for r in revs:
            rev_link = (f"<a href=\"/projects/{escape(pid)}/nodes/{escape(nid)}"
                        f"/revisions/{r['revision_id']}\">"
                        f"<code>r{r['revision_id']}</code></a>")
            cr_badge = html.change_reason_badge(
                change_reasons.get(r["revision_id"])
            )
            body.append(
                f"<div class='timeline-item'>"
                f"<div class='timeline-ts'>{escape(r['ts'])}</div>"
                f"<div>{escape(r['change_type'])} · "
                f"{rev_link} · by {escape(r['actor'])}"
                f"{cr_badge}</div>"
                f"</div>"
            )
        body.append("</div>")

    return html.render_page(f"manifold · {pid} · {nid}", "\n".join(body)), 200


def html_node_edit_get(handler, kwargs, query):
    conn = _conn(handler)
    pid, nid = kwargs["project_id"], kwargs["node_id"]
    node = queries.get_node(conn, pid, nid)
    if node is None:
        return html.render_page("Not Found",
                                  f"<h1>Node not found: {escape(pid)}:{escape(nid)}</h1>"), 404
    proj = queries.get_project(conn, pid)
    layers = [l.get("name") for l in (proj["spec_config"] or {}).get("layers") or []
              if isinstance(l, dict)] if proj else []
    parents = [r["dst_node_id"] for r in conn.execute(
        "SELECT dst_node_id FROM node_edges WHERE project_id = ? AND src_node_id = ? "
        "AND edge_kind = 'parent' ORDER BY dst_node_id", (pid, nid)).fetchall()]
    peers = [r["dst_node_id"] for r in conn.execute(
        "SELECT dst_node_id FROM node_edges WHERE project_id = ? AND src_node_id = ? "
        "AND edge_kind = 'depends_on' ORDER BY dst_node_id", (pid, nid)).fetchall()]

    title = node["title"] or nid
    structural = html.structural_fields_panel(node, layers, parents, peers)
    body = [
        f"<h1>Edit · {escape(nid)} · {escape(title)}</h1>",
        f"<p class='muted'>Layer: <code>{escape(node['layer'])}</code> · "
        f"Revision: <code>{int(node['current_revision_id'] or 0)}</code></p>",
        html.codemirror_edit_form(
            action=f"/projects/{pid}/nodes/{nid}",
            body=node["body"] or "",
            expected_revision_id=int(node["current_revision_id"] or 0),
            structural_html=structural,
        ),
    ]
    return html.render_page(f"manifold · edit {nid}", "\n".join(body)), 200


def html_node_edit_post(handler, kwargs, query):
    conn = _conn(handler)
    pid, nid = kwargs["project_id"], kwargs["node_id"]
    form = handler._form_data()
    expected = int(form.get("expected_revision_id", "0") or 0)
    actor = form.get("actor") or f"human:{_shell_user()}"

    node = queries.get_node(conn, pid, nid)
    if node is None:
        return html.render_page("Not Found",
                                  f"<h1>Node not found: {escape(pid)}:{escape(nid)}</h1>"), 404

    # Validate list-field IDs (parents, peers_depends_on) before any DB write
    list_fields_present = {}
    for key in ("parents", "peers_depends_on"):
        if key in form:
            raw = form[key]
            raw_str = raw if isinstance(raw, str) else ",".join(raw)
            ids = [s.strip() for s in raw_str.split(",") if s.strip()]
            list_fields_present[key] = ids
            for i in ids:
                exists = conn.execute(
                    "SELECT 1 FROM nodes WHERE project_id = ? AND node_id = ?",
                    (pid, i)).fetchone()
                if not exists:
                    return html.render_page(
                        "Bad Request",
                        f"<h1>Bad request</h1><p>{escape(key)} references "
                        f"nonexistent node: <code>{escape(i)}</code></p>",
                        error="INVALID_ARGUMENTS",
                    ), 400

    current_expected = expected
    try:
        # Step 1: transition target if a non-empty target_status was submitted
        ts = (form.get("target_status") or "").strip() if isinstance(form.get("target_status"), str) else ""
        if ts:
            tr = writes.transition_target(
                conn, pid, nid, ts,
                expected_revision_id=current_expected,
                actor=actor, source="web_ui",
            )
            current_expected = tr["revision_id"]

        # Step 2: update other fields
        fields = {}
        for key in ("title", "kind", "verdict_mechanism",
                    "verdict_check", "verdict_assertion",
                    "target_achieved_when", "realized_by_external", "body"):
            if key in form:
                v = form[key]
                v_str = v if isinstance(v, str) else (v[0] if v else "")
                fields[key] = v_str if v_str != "" else None
        # layer may be present but unchanged — only include if different
        if "layer" in form and form["layer"] != node["layer"]:
            fields["layer"] = form["layer"]
        for k, v in list_fields_present.items():
            fields[k] = v
        if fields:
            cr = (form.get("change_reason") or "").strip()
            writes.update_node(
                conn, pid, nid, fields,
                expected_revision_id=current_expected,
                actor=actor, source="web_ui",
                change_reason=cr or None,
            )
    except writes.StaleRevision as exc:
        body = [
            "<h1>Conflict: node was changed by someone else</h1>",
            f"<p>The node has revision <code>r{exc.current_revision_id}</code>, "
            f"but your form was based on <code>r{expected}</code>.</p>",
            f'<p><a href="/projects/{escape(pid)}/nodes/{escape(nid)}">Back to node</a> '
            f'to re-read the current state, then re-apply your edit.</p>',
        ]
        return html.render_page("Conflict", "\n".join(body), error="STALE_REVISION"), 409
    except writes.InvalidTransition as exc:
        return html.render_page(
            "Bad Request",
            f"<h1>Invalid transition</h1><p>{escape(str(exc))}</p>",
            error="INVALID_TRANSITION",
        ), 400
    except writes.WritesError as exc:
        return html.render_page(
            "Bad Request",
            f"<h1>Write failed</h1><p>{escape(str(exc))}</p>",
            error="INVALID_ARGUMENTS",
        ), 400

    handler._redirect(f"/projects/{pid}/nodes/{nid}")
    return "", 0   # response already sent; return placeholder


def html_targets(handler, kwargs, query):
    conn = _conn(handler)
    pid = (query.get("project_id") or [None])[0]
    status = (query.get("status") or [None])[0]
    layer = (query.get("layer") or [None])[0]
    targets = queries.list_targets(conn, project_id=pid, status=status,
                                     layer=layer, limit=200)
    # Build the filter form. Discover known projects + layers for dropdowns.
    projects = [p["project_id"] for p in queries.list_projects(conn, limit=200)]
    layer_set = set()
    for p in projects:
        proj = queries.get_project(conn, p)
        for L in (proj["spec_config"] or {}).get("layers") or []:
            if isinstance(L, dict) and L.get("name"):
                layer_set.add(L["name"])
    body = ["<h1>Targets</h1>",
             html.filter_form("/reports/targets", [
                 ("project_id", "Project", sorted(projects), pid),
                 ("status", "Status",
                  ["planned", "in_progress", "achieved", "abandoned",
                   "superseded"], status),
                 ("layer", "Layer", sorted(layer_set), layer),
             ])]
    if not targets:
        body.append("<p>No targets matching the filter.</p>")
    else:
        rows = []
        for n in targets:
            rows.append([
                n["project_id"],
                html.raw(html.link(
                    f"/projects/{n['project_id']}/nodes/{n['node_id']}", n["node_id"])),
                n["title"] or "",
                html.raw(html.badge(n["target_status"], "target")),
                n["target_achieved_when"] or "",
            ])
        body.append(html.table(
            ["Project", "Node", "Title", "Status", "Achieved when"], rows))
    return html.render_page("manifold · targets", "\n".join(body)), 200


def html_flips(handler, kwargs, query):
    conn = _conn(handler)
    k = int((query.get("k") or ["3"])[0])
    pid = (query.get("project_id") or [None])[0]
    mech = (query.get("mechanism") or [None])[0]
    flips = queries.list_unstable_verdicts(
        conn, project_id=pid, k=k, mechanism=mech, limit=200)
    projects = [p["project_id"] for p in queries.list_projects(conn, limit=200)]
    body = [f"<h1>Unstable verdicts (last {k} validations)</h1>",
             html.filter_form("/reports/flips", [
                 ("project_id", "Project", sorted(projects), pid),
                 ("mechanism", "Mechanism",
                  ["automated_check", "python_assertion",
                   "human_signoff", "llm_judge"], mech),
                 ("k", "K", ["1", "2", "3", "5", "10"], str(k)),
             ])]
    if not flips:
        body.append("<p>No verdict flips in the last K runs.</p>")
    else:
        rows = []
        for f in flips:
            rows.append([
                f["project_id"],
                html.raw(html.link(
                    f"/projects/{f['project_id']}/nodes/{f['node_id']}", f["node_id"])),
                f["statuses"],
            ])
        body.append(html.table(["Project", "Node", "Statuses (last K)"], rows))
    return html.render_page("manifold · flips", "\n".join(body)), 200


def html_portfolio(handler, kwargs, query):
    conn = _conn(handler)
    theme = (query.get("theme") or [None])[0]
    report = queries.portfolio_report(conn, theme_node_id=theme)
    body = ["<h1>Portfolio</h1>"]
    themes = report.get("themes") or []
    if not themes:
        body.append(
            "<p>No themes yet. Register project <code>portfolio</code> "
            "with a <code>theme</code> layer and add theme nodes.</p>"
        )
    else:
        for t in themes:
            tid = t.get("theme_node_id") or ""
            title = t.get("title") or ""
            summary = t.get("summary") or {}
            body.append(f"<h2>{escape(tid)}: {escape(title)}</h2>")
            body.append(
                f"<p>Planned {summary.get('planned', 0)} · "
                f"In progress {summary.get('in_progress', 0)} · "
                f"Achieved {summary.get('achieved', 0)} · "
                f"Blocked {summary.get('blocked', 0)}</p>"
            )
            rows = []
            for link in t.get("links") or []:
                ref = link.get("node_ref") or ""
                pid, nid = ref.split("/", 1) if "/" in ref else ("", ref)
                blocked = ", ".join(link.get("blocked_by") or []) or "—"
                rows.append([
                    html.raw(html.link(f"/projects/{pid}/nodes/{nid}", ref)),
                    link.get("title") or "",
                    html.raw(html.badge(link.get("target_status"), "target")),
                    link.get("verdict_status") or "",
                    blocked,
                ])
            body.append(html.table(
                ["node_ref", "Title", "Status", "Verdict", "Blocked by"], rows))
    return html.render_page("manifold · portfolio", "\n".join(body)), 200


# ============================================================
# revision detail, validation trigger + detail
# ============================================================

def html_revision_detail(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    nid = kwargs["node_id"]
    rev_id = int(kwargs["revision_id"])
    curr = conn.execute(
        "SELECT * FROM revisions WHERE revision_id = ? AND project_id = ? "
        "AND node_id = ?",
        (rev_id, pid, nid),
    ).fetchone()
    if curr is None:
        return html.render_page(
            "Not Found",
            f"<h1>Revision not found: r{rev_id}</h1>"
            f"<p><a href='/projects/{escape(pid)}/nodes/{escape(nid)}'>"
            f"Back to node</a></p>",
            error="NOT_FOUND",
        ), 404
    prev_row = None
    if curr["prev_revision_id"]:
        prev_row = conn.execute(
            "SELECT snapshot FROM revisions WHERE revision_id = ?",
            (curr["prev_revision_id"],),
        ).fetchone()
    prev_snap = json.loads(prev_row["snapshot"]) if prev_row else {}
    curr_snap = json.loads(curr["snapshot"])
    change_summary = (json.loads(curr["change_summary"])
                       if curr["change_summary"] else None)
    diff_table = html.revision_diff_table(change_summary)
    body_diff = html.unified_body_diff(prev_snap.get("body", ""),
                                         curr_snap.get("body", ""))
    body = (
        f"<h1>Revision r{rev_id} · "
        f"<a href='/projects/{escape(pid)}/nodes/{escape(nid)}'>"
        f"{escape(pid)}:{escape(nid)}</a></h1>"
        f"<p class='muted'>Type: <code>{escape(curr['change_type'])}</code> · "
        f"Source: <code>{escape(curr['source'])}</code> · "
        f"Actor: <code>{escape(curr['actor'])}</code> · "
        f"At: <code>{escape(curr['ts'])}</code>"
        + (f" · Prev: <a href='/projects/{escape(pid)}/nodes/{escape(nid)}"
           f"/revisions/{curr['prev_revision_id']}'>r{curr['prev_revision_id']}</a>"
           if curr['prev_revision_id'] else "")
        + "</p>"
        f"<h2>Field changes</h2>"
        + (diff_table or "<p class='muted'>(none)</p>")
        + f"<h2>Body diff</h2>"
        + (body_diff or "<p class='muted'>(unchanged)</p>")
    )
    return html.render_page(
        f"manifold · r{rev_id} · {pid}:{nid}", body), 200


def html_run_validation_post(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    form = handler._form_data()
    actor = f"web_ui:{handler.client_address[0]}"
    result = writes.run_validation(
        conn, pid,
        with_verdicts=bool(form.get("with_verdicts")),
        with_targets=bool(form.get("with_targets")),
        actor=actor,
    )
    handler._redirect(f"/projects/{pid}/validations/{result['validation_id']}")
    return "", 0


def html_validation_detail(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    val_id = int(kwargs["validation_id"])
    val_row = conn.execute(
        "SELECT * FROM validations WHERE validation_id = ? AND project_id = ?",
        (val_id, pid),
    ).fetchone()
    if val_row is None:
        return html.render_page(
            "Not Found",
            f"<h1>Validation #{val_id} not found</h1>"
            f"<p><a href='/projects/{escape(pid)}'>Back to project</a></p>",
            error="NOT_FOUND",
        ), 404
    verdict_rows = conn.execute(
        "SELECT * FROM verdicts WHERE validation_id = ? "
        "ORDER BY CASE status WHEN 'violated' THEN 0 "
        "WHEN 'invalidated_by_descendant' THEN 1 "
        "WHEN 'judge_required' THEN 2 "
        "WHEN 'deferred_external' THEN 3 "
        "WHEN 'unknown' THEN 4 ELSE 5 END, node_id",
        (val_id,),
    ).fetchall()
    body = html.validation_detail_body(
        pid, dict(val_row), [dict(r) for r in verdict_rows],
    )
    return html.render_page(
        f"manifold · validation #{val_id}", body), 200


# ============================================================
# soft-delete + archive UI handlers
# ============================================================

def html_soft_delete_node(handler, kwargs, query):
    conn = _conn(handler)
    pid, nid = kwargs["project_id"], kwargs["node_id"]
    form = handler._form_data()
    expected = int(form.get("expected_revision_id", "0") or 0)
    actor = f"web_ui:{handler.client_address[0]}"
    try:
        writes.soft_delete_node(conn, pid, nid,
                                  expected_revision_id=expected,
                                  actor=actor, source="web_ui")
    except writes.StaleRevision:
        return html.render_page(
            "Conflict",
            f"<h1>Stale revision</h1><p>Reload the node and try again.</p>"
            f"<p><a href='/projects/{escape(pid)}/nodes/{escape(nid)}'>Back</a></p>",
            error="STALE_REVISION",
        ), 409
    except writes.WritesError as exc:
        return html.render_page(
            "Bad Request",
            f"<h1>Delete failed</h1><p>{escape(str(exc))}</p>",
        ), 400
    handler._redirect(f"/projects/{pid}")
    return "", 0


def html_restore_node(handler, kwargs, query):
    conn = _conn(handler)
    pid, nid = kwargs["project_id"], kwargs["node_id"]
    actor = f"web_ui:{handler.client_address[0]}"
    try:
        writes.restore_node(conn, pid, nid, actor=actor, source="web_ui")
    except writes.WritesError as exc:
        return html.render_page(
            "Bad Request",
            f"<h1>Restore failed</h1><p>{escape(str(exc))}</p>",
        ), 400
    handler._redirect(f"/projects/{pid}/nodes/{nid}")
    return "", 0


def html_deleted_nodes(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    proj = queries.get_project(conn, pid)
    if proj is None:
        return html.render_page(
            "Not Found",
            f"<h1>Project not found: {escape(pid)}</h1>"), 404
    deleted = queries.list_deleted_nodes(conn, pid)
    body = [f"<h1>Deleted nodes — {escape(pid)}</h1>",
             f"<p><a href='/projects/{escape(pid)}'>← back to project</a></p>"]
    if not deleted:
        body.append("<p class='muted'>(no deleted nodes)</p>")
    else:
        rows = []
        for n in deleted:
            restore_form = (
                f"<form method='post' "
                f"action='/projects/{escape(pid)}/nodes/{escape(n['node_id'])}/restore' "
                f"style='display:inline'>"
                f"<button type='submit'>Restore</button></form>"
            )
            rows.append([
                n["node_id"], n["title"] or "", n["layer"] or "",
                n.get("deleted_at") or "",
                html.raw(restore_form),
            ])
        body.append(html.table(
            ["ID", "Title", "Layer", "Deleted at", ""], rows))
    return html.render_page(f"manifold · deleted · {pid}", "\n".join(body)), 200


def html_archive_project(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    try:
        writes.archive_project(conn, pid)
    except writes.WritesError as exc:
        return html.render_page(
            "Bad Request", f"<h1>Archive failed</h1><p>{escape(str(exc))}</p>",
        ), 400
    handler._redirect("/")
    return "", 0


def html_unarchive_project(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    try:
        writes.unarchive_project(conn, pid)
    except writes.WritesError as exc:
        return html.render_page(
            "Bad Request", f"<h1>Unarchive failed</h1><p>{escape(str(exc))}</p>",
        ), 400
    handler._redirect(f"/projects/{pid}")
    return "", 0


def html_archived_projects(handler, kwargs, query):
    conn = _conn(handler)
    all_projects = queries.list_projects(conn, include_archived=True, limit=200)
    archived = [p for p in all_projects if p.get("archived_at")]
    body = ["<h1>Archived projects</h1>",
             "<p><a href='/'>← back to active projects</a></p>"]
    if not archived:
        body.append("<p class='muted'>(no archived projects)</p>")
    else:
        rows = []
        for p in archived:
            unarchive_form = (
                f"<form method='post' action='/projects/{escape(p['project_id'])}/unarchive' "
                f"style='display:inline'><button type='submit'>Unarchive</button></form>"
            )
            rows.append([
                p["project_id"], p["label"] or "",
                p.get("archived_at") or "",
                html.raw(unarchive_form),
            ])
        body.append(html.table(["ID", "Label", "Archived at", ""], rows))
    return html.render_page("manifold · archived projects", "\n".join(body)), 200


def html_spec_audit(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    proj = queries.get_project(conn, pid)
    if proj is None:
        return html.render_page(
            "Not Found",
            f"<h1>Project not found: {escape(pid)}</h1>"), 404
    since = _first(query.get("since"))
    flagged = queries.spec_audit_flagged_revisions(conn, pid, since=since)
    rationale_changes = queries.spec_audit_unclarified_rationale(conn, pid, since=since)
    body = html.spec_audit_body(pid, flagged, rationale_changes, since)
    return html.render_page(f"manifold · spec-audit · {pid}", body), 200


def html_drift_report(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    if queries.get_project(conn, pid) is None:
        return html.render_page(
            "Not Found",
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


def html_brief(handler, kwargs, query):
    from manifold import status_brief

    conn = _conn(handler)
    pid = kwargs["project_id"]
    if queries.get_project(conn, pid) is None:
        return html.render_page("Not Found", f"<h1>Project not found: {escape(pid)}</h1>"), 404

    view = status_brief.build_status_brief_view(conn, pid)
    if _wants_json(handler, query):
        return ("json", view, 200)

    detail = _first(query.get("detail")) or "standard"
    body = html.status_brief_body(pid, view, detail=detail)
    return html.render_page(f"manifold · brief · {pid}", body, main_class="page-wide"), 200


def html_diagram(handler, kwargs, query):
    return _presentation_html_response(
        handler, kwargs, query, kind_hint="diagram", view_label="Diagram",
    )


def html_mindmap(handler, kwargs, query):
    return _presentation_html_response(
        handler, kwargs, query, kind_hint="mindmap", view_label="Mindmap",
    )


def html_view(handler, kwargs, query):
    view_id = kwargs.get("view_id") or _first(query.get("view"))
    if not view_id:
        return html.render_page("Bad Request", "<h1>Missing view_id</h1>"), 400
    q = dict(query)
    q["view"] = [view_id]
    label = view_id.replace("-", " ").title()
    return _presentation_html_response(
        handler, kwargs, q, kind_hint=None, view_label=label,
    )


def api_brief(handler, kwargs, query):
    from manifold import status_brief

    conn = _conn(handler)
    return status_brief.build_status_brief_view(conn, kwargs["project_id"]), 200


def api_diagram(handler, kwargs, query):
    view = _resolve_presentation_view(_conn(handler), kwargs["project_id"], query,
                                      kind_hint="diagram")
    return view, 200


def api_mindmap(handler, kwargs, query):
    view = _resolve_presentation_view(_conn(handler), kwargs["project_id"], query,
                                      kind_hint="mindmap")
    return view, 200


def api_view(handler, kwargs, query):
    q = dict(query)
    q["view"] = [kwargs["view_id"]]
    view = _resolve_presentation_view(_conn(handler), kwargs["project_id"], q,
                                      kind_hint=None)
    return view, 200


def api_list_presentation_views(handler, kwargs, query):
    from manifold import view_registry
    return {"views": view_registry.list_views()}, 200


# ============================================================
# API handlers (return (payload, status))
# ============================================================

def api_list_projects(handler, kwargs, query):
    conn = _conn(handler)
    return {"projects": queries.list_projects(
        conn,
        include_archived=_bool(query.get("include_archived")),
        limit=_int(query.get("limit"), 50),
        cursor=_first(query.get("cursor")),
    )}, 200


def api_get_project(handler, kwargs, query):
    conn = _conn(handler)
    p = queries.get_project(conn, kwargs["project_id"])
    if p is None:
        return errors.not_found_envelope("project", project_id=kwargs["project_id"]), 404
    return p, 200


def api_list_nodes(handler, kwargs, query):
    conn = _conn(handler)
    return {"nodes": queries.list_nodes(
        conn, kwargs["project_id"],
        layer=_first(query.get("layer")),
        limit=_int(query.get("limit"), 50),
        cursor=_first(query.get("cursor")),
    )}, 200


def api_get_node(handler, kwargs, query):
    conn = _conn(handler)
    n = queries.get_node(conn, kwargs["project_id"], kwargs["node_id"])
    if n is None:
        return errors.not_found_envelope("node",
                                          project_id=kwargs["project_id"],
                                          node_id=kwargs["node_id"]), 404
    return n, 200


def api_patch_node(handler, kwargs, query):
    conn = _conn(handler)
    body = handler._json_body()
    if_match = handler.headers.get("If-Match")
    if if_match is None:
        return errors.envelope(
            errors.INVALID_ARGUMENTS, "PATCH requires If-Match header",
            retry=errors.RETRY_WITH_NEW_ARGS,
        ), 400
    try:
        expected = int(if_match)
    except ValueError:
        return errors.envelope(
            errors.INVALID_ARGUMENTS, "If-Match must be an integer revision_id",
            retry=errors.RETRY_WITH_NEW_ARGS,
        ), 400
    actor = body.get("actor") or "api:unknown"
    fields = body.get("fields") or {}
    result = writes.update_node(
        conn, kwargs["project_id"], kwargs["node_id"], fields,
        expected_revision_id=expected, actor=actor, source="api",
        change_reason=body.get("change_reason"),
    )
    return result, 200


def api_list_revisions(handler, kwargs, query):
    conn = _conn(handler)
    return {"revisions": queries.list_revisions(
        conn, kwargs["project_id"], kwargs["node_id"],
        limit=_int(query.get("limit"), 20),
    )}, 200


def api_list_targets(handler, kwargs, query):
    conn = _conn(handler)
    return {"targets": queries.list_targets(
        conn,
        project_id=_first(query.get("project_id")),
        status=_first(query.get("status")),
        older_than_days=_int(query.get("older_than_days"), None),
        limit=_int(query.get("limit"), 50),
    )}, 200


def api_list_flips(handler, kwargs, query):
    conn = _conn(handler)
    return {"nodes": queries.list_unstable_verdicts(
        conn,
        project_id=_first(query.get("project_id")),
        k=_int(query.get("k"), 3),
        limit=_int(query.get("limit"), 50),
    )}, 200


def api_portfolio_report(handler, kwargs, query):
    conn = _conn(handler)
    theme = _first(query.get("theme"))
    return queries.portfolio_report(conn, theme_node_id=theme), 200


def api_run_validation(handler, kwargs, query):
    conn = _conn(handler)
    body = handler._json_body()
    actor = body.get("actor") or "api:unknown"
    result = writes.run_validation(
        conn, kwargs["project_id"],
        with_verdicts=bool(body.get("with_verdicts")),
        with_targets=bool(body.get("with_targets")),
        force=bool(body.get("force")),
        actor=actor,
    )
    return result, 200


def api_get_validation(handler, kwargs, query):
    conn = _conn(handler)
    row = conn.execute(
        "SELECT * FROM validations WHERE validation_id = ? AND project_id = ?",
        (int(kwargs["validation_id"]), kwargs["project_id"]),
    ).fetchone()
    if row is None:
        return errors.not_found_envelope(
            "validation", validation_id=kwargs["validation_id"],
        ), 404
    v_rows = conn.execute(
        "SELECT * FROM verdicts WHERE validation_id = ?",
        (row["validation_id"],),
    ).fetchall()
    return {
        "validation": dict(row),
        "verdicts": [dict(r) for r in v_rows],
    }, 200


def api_next_leaves(handler, kwargs, query):
    conn = _conn(handler)
    layer = _first(query.get("layer"))
    rows = queries.next_leaves(conn, kwargs["project_id"], layer=layer)
    return rows, 200


def api_spec_audit(handler, kwargs, query):
    conn = _conn(handler)
    pid = kwargs["project_id"]
    since = _first(query.get("since"))
    flagged = queries.spec_audit_flagged_revisions(conn, pid, since=since)
    rationale_changes = queries.spec_audit_unclarified_rationale(conn, pid, since=since)
    return {
        "flagged_revisions": flagged,
        "unclarified_rationale_changes": rationale_changes,
    }, 200


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


def api_peek_trajectory(handler, kwargs, query):
    from manifold import trajectory as traj
    conn = _conn(handler)
    leg_seqs_raw = _first(query.get("leg_seqs"))
    leg_seqs = None
    if leg_seqs_raw:
        leg_seqs = [int(x.strip()) for x in leg_seqs_raw.split(",") if x.strip()]
    try:
        return traj.peek_trajectory(
            conn, kwargs["trajectory_id"], leg_seqs=leg_seqs,
        ), 200
    except traj.TrajectoryError as exc:
        return errors.envelope(errors.NOT_FOUND, str(exc)), 404


def api_propose_trajectory(handler, kwargs, query):
    from manifold import trajectory as traj
    conn = _conn(handler)
    body = handler._json_body()
    try:
        result = traj.propose_trajectory(
            conn,
            body.get("project_id", ""),
            body.get("target_brief", ""),
            body.get("legs") or [],
            proposed_by=body.get("proposed_by") or f"human:{_shell_user()}",
            scope=body.get("scope"),
        )
        conn.commit()
        return result, 201
    except traj.TrajectoryError as exc:
        return errors.envelope(
            errors.INVALID_ARGUMENTS, str(exc),
            retry=errors.RETRY_WITH_NEW_ARGS,
        ), 400


def api_accept_trajectory(handler, kwargs, query):
    from manifold import trajectory as traj
    conn = _conn(handler)
    body = handler._json_body() or {}
    try:
        result = traj.accept_trajectory_legs(
            conn,
            kwargs["trajectory_id"],
            leg_seqs=body.get("leg_seqs"),
            actor=body.get("actor") or f"human:{_shell_user()}",
        )
        conn.commit()
        return result, 200
    except traj.TrajectoryError as exc:
        return errors.envelope(
            errors.INVALID_ARGUMENTS, str(exc),
            retry=errors.RETRY_WITH_NEW_ARGS,
        ), 400


def html_trajectory(handler, kwargs, query):
    from manifold import trajectory as traj
    conn = _conn(handler)
    tid = kwargs["trajectory_id"]
    try:
        report = traj.peek_trajectory(conn, tid)
    except traj.TrajectoryError:
        return html.render_page("manifold · trajectory", "<p>Not found.</p>"), 404
    body = f"<pre>{escape(traj.format_show_markdown(report))}</pre>"
    return html.render_page(f"manifold · trajectory · {escape(tid)}", body), 200


def api_register_project(handler, kwargs, query):
    conn = _conn(handler)
    body = handler._json_body()
    project_id = (body.get("project_id") or "").strip()
    if not project_id:
        return errors.envelope(
            errors.INVALID_ARGUMENTS, "project_id is required",
            retry=errors.RETRY_WITH_NEW_ARGS,
        ), 400
    spec_config = body.get("spec_config") or {}
    label = body.get("label")
    result = writes.register_project(conn, project_id, spec_config, label=label)
    return result, 200


# ============================================================
# Helpers
# ============================================================

def _wants_json(handler, query: dict) -> bool:
    """Content negotiation: ?format=json or Accept: application/json (without html)."""
    if _first(query.get("format")) == "json":
        return True
    accept = getattr(handler, "headers", None)
    if accept is None:
        return False
    raw = (accept.get("Accept", "*/*") if hasattr(accept, "get") else "").lower()
    if "application/json" in raw and "text/html" not in raw:
        return True
    return raw.strip().startswith("application/json")


def _resolve_presentation_view(conn, project_id: str, query: dict, *,
                               kind_hint: Optional[str]):
    """Build a view-model from registry id (?view=) or legacy type params."""
    from manifold import presentation_views, view_registry

    view_id = _first(query.get("view"))
    focus = _first(query.get("focus"))
    traj = _first(query.get("trajectory_id"))
    max_nodes = _int(query.get("max_nodes"), 0) or None
    max_depth = _int(query.get("max_depth"), 0) or None

    if view_id:
        return view_registry.build_registered_view(
            conn, project_id, view_id,
            focus_node_id=focus,
            trajectory_id=traj,
            max_nodes=max_nodes,
            max_depth=max_depth,
        )
    if kind_hint == "mindmap":
        kwargs = dict(
            conn=conn,
            project_id=project_id,
            mindmap_type=_first(query.get("type")) or "flow",
            focus_node_id=focus,
        )
        if max_nodes is not None:
            kwargs["max_nodes"] = max_nodes
        if max_depth is not None:
            kwargs["max_depth"] = max_depth
        return presentation_views.build_mindmap_view(**kwargs)
    if kind_hint == "diagram":
        kwargs = dict(
            conn=conn,
            project_id=project_id,
            diagram_type=_first(query.get("type")) or "blockers",
            focus_node_id=focus,
            trajectory_id=traj,
        )
        if max_nodes is not None:
            kwargs["max_nodes"] = max_nodes
        return presentation_views.build_diagram_view(**kwargs)
    raise ValueError("kind_hint required when view id absent")


def _presentation_mermaid_source(view: dict) -> str:
    from manifold import presentation_format

    if view.get("view_kind") == "mindmap":
        return presentation_format.format_mermaid_mindmap(view)
    return presentation_format.format_mermaid_flowchart(view)


def _presentation_html_response(handler, kwargs, query, *, kind_hint: Optional[str],
                                view_label: str):
    from manifold import presentation_svg

    conn = _conn(handler)
    pid = kwargs["project_id"]
    if queries.get_project(conn, pid) is None:
        return html.render_page("Not Found", f"<h1>Project not found: {escape(pid)}</h1>"), 404

    view = _resolve_presentation_view(conn, pid, query, kind_hint=kind_hint)
    if _wants_json(handler, query):
        return ("json", view, 200)

    mmd = _presentation_mermaid_source(view)
    svg = presentation_svg.render_view_svg(view)
    focus_id = view.get("focus_node_id") or _first(query.get("focus")) or "I.1"
    view_id = kwargs.get("view_id")
    form_action = _presentation_form_action(pid, kind_hint, view_id)
    focus_options = _focus_picker_options(conn, pid)
    body = html.presentation_view_body(
        pid, view, mmd, view_label=view_label, svg_html=svg,
        focus_options=focus_options,
        form_action=form_action,
        current_focus=focus_id,
    )
    title = f"manifold · {view_label.lower()} · {pid}"
    return html.render_presentation_page(title, body, with_pan_zoom=True), 200


def _focus_picker_options(conn, project_id: str, *, limit_per_layer: int = 40) -> list[dict]:
    """Nodes suitable for focus picker (intent, capabilities, realizations)."""
    options: list[dict] = []
    for layer in ("intent", "capabilities", "realizations"):
        for n in queries.list_nodes(conn, project_id, layer=layer, limit=limit_per_layer):
            title = (n.get("title") or n.get("node_id") or "").strip()
            if len(title) > 50:
                title = title[:47] + "..."
            options.append({
                "node_id": n["node_id"],
                "title": title,
                "layer": layer,
            })
    return options


def _presentation_form_action(project_id: str, kind_hint: Optional[str],
                              view_id: Optional[str] = None) -> str:
    if kind_hint == "mindmap":
        return f"/projects/{project_id}/mindmap"
    if kind_hint == "diagram":
        return f"/projects/{project_id}/diagram"
    if view_id:
        return f"/projects/{project_id}/views/{view_id}"
    return f"/projects/{project_id}/diagram"


def _first(vals):
    if not vals:
        return None
    return vals[0]


def _int(vals, default):
    v = _first(vals)
    if v is None:
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def _bool(vals):
    v = _first(vals)
    return v not in (None, "", "0", "false", "False")


def _shell_user():
    import os
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USER", "unknown")


HANDLERS_HTML = {
    "html_index": html_index,
    "html_project": html_project,
    "html_node": html_node,
    "html_node_edit_get": html_node_edit_get,
    "html_node_edit_post": html_node_edit_post,
    "html_targets": html_targets,
    "html_flips": html_flips,
    "html_portfolio": html_portfolio,
    "html_revision_detail": html_revision_detail,
    "html_run_validation_post": html_run_validation_post,
    "html_validation_detail": html_validation_detail,
    "html_soft_delete_node": html_soft_delete_node,
    "html_restore_node": html_restore_node,
    "html_deleted_nodes": html_deleted_nodes,
    "html_archive_project": html_archive_project,
    "html_unarchive_project": html_unarchive_project,
    "html_archived_projects": html_archived_projects,
    "html_spec_audit": html_spec_audit,
    "html_drift_report": html_drift_report,
    "html_brief": html_brief,
    "html_diagram": html_diagram,
    "html_mindmap": html_mindmap,
    "html_view": html_view,
    "html_trajectory": html_trajectory,
}
HANDLERS_API = {
    "api_list_projects": api_list_projects,
    "api_get_project": api_get_project,
    "api_list_nodes": api_list_nodes,
    "api_next_leaves": api_next_leaves,
    "api_spec_audit": api_spec_audit,
    "api_drift_report": api_drift_report,
    "api_brief": api_brief,
    "api_list_presentation_views": api_list_presentation_views,
    "api_diagram": api_diagram,
    "api_mindmap": api_mindmap,
    "api_view": api_view,
    "api_peek_trajectory": api_peek_trajectory,
    "api_propose_trajectory": api_propose_trajectory,
    "api_accept_trajectory": api_accept_trajectory,
    "api_get_node": api_get_node,
    "api_patch_node": api_patch_node,
    "api_list_revisions": api_list_revisions,
    "api_list_targets": api_list_targets,
    "api_list_flips": api_list_flips,
    "api_portfolio_report": api_portfolio_report,
    "api_run_validation": api_run_validation,
    "api_get_validation": api_get_validation,
    "api_register_project": api_register_project,
}


# ============================================================
# Server entry
# ============================================================

def serve(host: str = "127.0.0.1", port: int = 7779, *, verbose: bool = False) -> int:
    """Start the HTTP server. Blocks until interrupted."""
    # check_same_thread=False because ThreadingHTTPServer dispatches each
    # request on a worker thread; we share one connection (WAL serializes writes).
    conn = db.connect(check_same_thread=False)
    schema.bootstrap(conn)
    server = ThreadingHTTPServer((host, port), ManifoldHandler)
    # Stash on the server so handlers can reach it
    server.conn = conn
    server.verbose = verbose
    print(f"manifold web server at http://{host}:{port}/", file=sys.stderr)
    print(f"DB: {config.db_path()}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping...", file=sys.stderr)
    finally:
        server.server_close()
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(serve())
