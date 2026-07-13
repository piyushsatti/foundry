#!/usr/bin/env python3
"""
web_server.py — local HTTP server for the progress-tracker web viewer.

Serves the single-page HTML viewer at / and JSON endpoints under /api/.
The HTML polls /api/all every 2 seconds; click-through drills into project/phase/dispatch.

Usage:
    python3 web_server.py [--port 7777] [--bind 127.0.0.1]

Open http://localhost:7777 in your browser.

Stdlib only.
"""
import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db


HTML_PATH = Path(__file__).resolve().parent.parent / "web" / "index.html"


class Handler(BaseHTTPRequestHandler):
    server_version = "progress-tracker/0.1"

    def log_message(self, fmt, *args):
        # Quieter logs — only errors
        if args and isinstance(args[0], str) and args[0].startswith(("4", "5")):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, obj, code=200):
        body = json.dumps(obj, default=str, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self):
        if not HTML_PATH.is_file():
            self.send_error(500, "index.html missing")
            return
        body = HTML_PATH.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        parts = [p for p in url.path.split("/") if p]
        qs = parse_qs(url.query)

        if not parts:
            return self._send_html()

        if parts[0] != "api":
            return self.send_error(404, "not found")

        conn = db.connect()

        try:
            if parts[1:] == ["all"]:
                return self._send_json(db.peek_all(conn))

            if len(parts) == 3 and parts[1] == "project":
                p = db.peek_project(conn, parts[2])
                if p is None:
                    return self.send_error(404, "project not found")
                return self._send_json(p)

            if len(parts) == 4 and parts[1] == "phase":
                p = db.peek_phase(conn, parts[2], parts[3])
                if p is None:
                    return self.send_error(404, "phase not found")
                return self._send_json(p)

            if len(parts) == 3 and parts[1] == "dispatch":
                d = db.peek_dispatch(conn, parts[2])
                if d is None:
                    return self.send_error(404, "dispatch not found")
                return self._send_json(d)

            if parts[1:] == ["events"]:
                limit = int(qs.get("limit", ["50"])[0])
                project_id = qs.get("project", [None])[0]
                return self._send_json(db.recent_events(conn, limit=limit, project_id=project_id))

            return self.send_error(404, "unknown endpoint")
        finally:
            conn.close()


def main():
    parser = argparse.ArgumentParser(description="progress-tracker web viewer.")
    parser.add_argument("--port", type=int, default=7777)
    parser.add_argument("--bind", default="127.0.0.1")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    url = f"http://{args.bind}:{args.port}/"
    print(f"progress-tracker viewer at {url}")
    print(f"  db: {db.DEFAULT_DB}")
    print("Press Ctrl-C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down.")


if __name__ == "__main__":
    main()
