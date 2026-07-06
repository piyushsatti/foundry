#!/usr/bin/env python3
"""
mcp_server.py — progress-tracker MCP server (stdio transport, stdlib only).

Implements JSON-RPC 2.0 over stdin/stdout per the Model Context Protocol spec.
One message per line. No external dependencies — uses stdlib json + sqlite3.

Bundled in the plan-orchestrator plugin; auto-registered via the plugin's
.mcp.json using ${CLAUDE_PLUGIN_ROOT}. To register manually in a host MCP
config instead, point args at this file:

  {
    "mcpServers": {
      "progress-tracker": {
        "command": "python3",
        "args": ["/abs/path/to/plugins/plan-orchestrator/server/mcp_server.py"]
      }
    }
  }

Optional env var:
  PROGRESS_TRACKER_DB    path to SQLite DB (default ~/.claude/progress.db)
"""
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import db


PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "progress-tracker", "version": "0.1.0"}


# ============================================================
# Tool definitions
# ============================================================

TOOLS = [
    {
        "name": "todo_init",
        "description": "Initialize (or re-initialize) a dispatch's TODO list. Call this as your first action when dispatched.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dispatch_id": {"type": "string", "description": "Unique dispatch id (e.g. 'planner-P2-c1')."},
                "project_id": {"type": "string", "description": "Project slug (e.g. 'finance_analysis')."},
                "phase_id": {"type": "string", "description": "Phase id (e.g. 'P1', 'P2'). Use 'main' if not phase-based."},
                "role": {"type": "string", "description": "planner | implementer | reviewer | skeptic | audit | other"},
                "agent_model": {"type": "string", "description": "opus | sonnet | haiku | other"},
                "items": {"type": "array", "items": {"type": "string"}, "description": "Initial TODO items, in order."},
                "work_dir": {"type": "string", "description": "Optional absolute path to the project's work-dir."},
                "project_label": {"type": "string", "description": "Optional human-friendly project name."},
            },
            "required": ["dispatch_id", "project_id", "phase_id", "items"],
        },
    },
    {
        "name": "todo_start",
        "description": "Mark an item as in-progress. Call this before you start working on the item.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dispatch_id": {"type": "string"},
                "item_idx": {"type": "integer", "description": "Zero-based index into the items array."},
            },
            "required": ["dispatch_id", "item_idx"],
        },
    },
    {
        "name": "todo_done",
        "description": "Mark an item as done. Bumps the dispatch's progress counter.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dispatch_id": {"type": "string"},
                "item_idx": {"type": "integer"},
            },
            "required": ["dispatch_id", "item_idx"],
        },
    },
    {
        "name": "todo_block",
        "description": "Set status to BLOCKED with a one-line blocker description. Call this when you cannot proceed without external action.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dispatch_id": {"type": "string"},
                "blocker": {"type": "string", "description": "One-line description of what you need to unblock."},
            },
            "required": ["dispatch_id", "blocker"],
        },
    },
    {
        "name": "todo_halt",
        "description": "Set status to HALTED with a reason (typically 'context-budget'). The architect's continuation logic will re-dispatch with this TODO state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dispatch_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["dispatch_id", "reason"],
        },
    },
    {
        "name": "todo_finish",
        "description": "Mark dispatch DONE — all items done. Call this as your last action before returning to the architect.",
        "inputSchema": {
            "type": "object",
            "properties": {"dispatch_id": {"type": "string"}},
            "required": ["dispatch_id"],
        },
    },
    {
        "name": "todo_note",
        "description": "Add a free-form note to the audit log (no status change). Useful for surfacing observations or partial-progress signals between item flips.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dispatch_id": {"type": "string"},
                "text": {"type": "string"},
            },
            "required": ["dispatch_id", "text"],
        },
    },
    {
        "name": "peek_all",
        "description": "Return a rollup of every tracked project: status, progress, last_update. Cheap; safe to call from any agent.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "peek_project",
        "description": "Return one project's rollup including all phases (no per-dispatch item detail).",
        "inputSchema": {
            "type": "object",
            "properties": {"project_id": {"type": "string"}},
            "required": ["project_id"],
        },
    },
    {
        "name": "peek_phase",
        "description": "Return one phase's rollup with all its dispatches' headers (no per-item detail).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string"},
                "phase_id": {"type": "string"},
            },
            "required": ["project_id", "phase_id"],
        },
    },
    {
        "name": "peek_dispatch",
        "description": "Return one dispatch's full TODO including every item's state. Most expensive peek; use sparingly.",
        "inputSchema": {
            "type": "object",
            "properties": {"dispatch_id": {"type": "string"}},
            "required": ["dispatch_id"],
        },
    },
]


# ============================================================
# Tool execution
# ============================================================

def _text_result(s):
    return {"content": [{"type": "text", "text": s}]}


def _json_result(obj):
    return {"content": [{"type": "text", "text": json.dumps(obj, indent=2, default=str)}]}


def call_tool(conn, name, args):
    if name == "todo_init":
        if args.get("project_label") or args.get("work_dir"):
            db.ensure_project(conn, args["project_id"], label=args.get("project_label"), work_dir=args.get("work_dir"))
        db.init_dispatch(
            conn,
            args["dispatch_id"], args["project_id"], args["phase_id"],
            args.get("role"), args.get("agent_model"),
            args["items"],
        )
        return _text_result(f"initialized {args['dispatch_id']} with {len(args['items'])} item(s)")

    if name == "todo_start":
        db.start_item(conn, args["dispatch_id"], args["item_idx"])
        d = db.peek_dispatch(conn, args["dispatch_id"])
        return _text_result(f"[-] item {args['item_idx']}: {d['items'][args['item_idx']]['description']}")

    if name == "todo_done":
        db.done_item(conn, args["dispatch_id"], args["item_idx"])
        d = db.peek_dispatch(conn, args["dispatch_id"])
        return _text_result(f"[x] {d['progress_done']}/{d['progress_total']}: {d['items'][args['item_idx']]['description']}")

    if name == "todo_block":
        db.block_dispatch(conn, args["dispatch_id"], args["blocker"])
        return _text_result(f"BLOCKED: {args['blocker']}")

    if name == "todo_halt":
        db.halt_dispatch(conn, args["dispatch_id"], args["reason"])
        return _text_result(f"HALTED: {args['reason']}")

    if name == "todo_finish":
        db.finish_dispatch(conn, args["dispatch_id"])
        d = db.peek_dispatch(conn, args["dispatch_id"])
        return _text_result(f"DONE: {d['progress_done']}/{d['progress_total']}")

    if name == "todo_note":
        db.add_note(conn, args["dispatch_id"], args["text"])
        return _text_result("noted")

    if name == "peek_all":
        return _json_result(db.peek_all(conn))

    if name == "peek_project":
        result = db.peek_project(conn, args["project_id"])
        if result is None:
            return _text_result(f"project '{args['project_id']}' not found")
        return _json_result(result)

    if name == "peek_phase":
        result = db.peek_phase(conn, args["project_id"], args["phase_id"])
        if result is None:
            return _text_result(f"phase {args['project_id']}/{args['phase_id']} not found")
        return _json_result(result)

    if name == "peek_dispatch":
        result = db.peek_dispatch(conn, args["dispatch_id"])
        if result is None:
            return _text_result(f"dispatch '{args['dispatch_id']}' not found")
        return _json_result(result)

    raise ValueError(f"unknown tool: {name}")


# ============================================================
# JSON-RPC dispatcher
# ============================================================

def make_response(req_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": req_id}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    return msg


def handle_request(conn, msg):
    method = msg.get("method", "")
    params = msg.get("params") or {}
    req_id = msg.get("id")

    if method == "initialize":
        return make_response(req_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        })

    if method == "initialized" or method == "notifications/initialized":
        return None  # notification, no response

    if method == "tools/list":
        return make_response(req_id, {"tools": TOOLS})

    if method == "tools/call":
        try:
            result = call_tool(conn, params["name"], params.get("arguments") or {})
            return make_response(req_id, result)
        except KeyError as e:
            return make_response(req_id, error={"code": -32602, "message": f"not found: {e}"})
        except Exception as e:
            tb = traceback.format_exc()
            return make_response(req_id, error={"code": -32603, "message": f"{type(e).__name__}: {e}", "data": tb})

    if method == "ping":
        return make_response(req_id, {})

    if req_id is None:
        return None  # unknown notification — ignore

    return make_response(req_id, error={"code": -32601, "message": f"method not found: {method}"})


def main():
    conn = db.connect()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"parse error: {e}"}}
            print(json.dumps(err), flush=True)
            continue

        response = handle_request(conn, msg)
        if response is not None:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
