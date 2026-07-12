# progress-tracker

MCP server for real-time dispatch progress across projects, phases, and agents — without reading full agent context.

When a multi-agent orchestrator has several agents in flight, the architect needs cheap ORIENT-cycle status (`peek_project`, `peek_phase`) instead of re-reading thousands of tokens of plan content. Dispatched agents report via small MCP writes (`todo_start`, `todo_done`, …).

This MCP server is bundled in the **plan-orchestrator** plugin and auto-registers via the plugin's [`.mcp.json`](.mcp.json) (using `${CLAUDE_PLUGIN_ROOT}`) when the plugin is installed — no manual host config needed. The orchestration skills that drive it live in [`skills/`](skills/).

## Architecture

- **SQLite** at `~/.claude/progress.db` by default (override with `PROGRESS_TRACKER_DB`)
- **MCP server** — `server/mcp_server.py` (stdio JSON-RPC, stdlib only)
- **Web viewer** — `server/web_server.py` (default `http://localhost:7777`, 2s poll)
- **CLI** — `scripts/progress` (same data, no MCP)
- WAL mode for concurrent agent writes + viewer reads

## Quick start

```bash
# Installing the plan-orchestrator plugin registers the MCP automatically.
# To exercise the server directly from a clone (paths relative to this plugin dir):

# Smoke data + viewer
python3 examples/smoke_test.py
python3 server/web_server.py &
open http://127.0.0.1:7777/
```

## MCP tool surface

Writers (agents call these as they work):

| Tool | When the agent calls it |
|---|---|
| `todo_init(dispatch_id, project_id, phase_id, role, agent_model, items[])` | First action on dispatch. Decompose your work into items. |
| `todo_start(dispatch_id, item_idx)` | Before starting an item. |
| `todo_done(dispatch_id, item_idx)` | After finishing an item. |
| `todo_block(dispatch_id, blocker)` | When you can't proceed without external action. |
| `todo_halt(dispatch_id, reason)` | Context-budget halt; architect re-dispatches later. |
| `todo_finish(dispatch_id)` | Last action before returning. All items done. |
| `todo_note(dispatch_id, text)` | Free-form audit note (no status change). |

Readers (architect ORIENT cycles):

| Tool | Returns |
|---|---|
| `peek_all` | All projects, status + progress + last_update |
| `peek_project(project_id)` | One project, including all phases |
| `peek_phase(project_id, phase_id)` | One phase, including all dispatches' headers |
| `peek_dispatch(dispatch_id)` | One dispatch's full TODO with every item's state |

Use `peek_dispatch` only when you need full item detail; the first three are cheap rollups.

## Status state machine

```
PENDING  →  IN_PROGRESS  →  DONE
                ↓
            BLOCKED  ←→  IN_PROGRESS
                ↓
            HALTED
```

Phase and project status roll up from dispatches (any HALTED → HALTED, any BLOCKED → BLOCKED, etc.).

## Smoke test

```bash
python3 examples/smoke_test.py
```

## Why DB + MCP instead of files

Per-agent `*.todo.md` files cause context churn (~900 lines of redundant rewrites per dispatch) and fragment across skills. One DB + one MCP contract serves any orchestrator.

## Deliberate limits

- Localhost-only web viewer (no auth)
- 2s polling (no SSE yet)
- Local DB only (no cross-machine sync)
- `todo_init` replaces whole TODO (scope expansion → new dispatch)

## Files

```
plugins/plan-orchestrator/
  .mcp.json        auto-registration (${CLAUDE_PLUGIN_ROOT})
  README.md
  server/          mcp_server.py, web_server.py, db.py, schema.sql
  web/             index.html viewer
  scripts/         progress CLI
  examples/        smoke_test.py
  skills/          plan-orchestrator, progress-tracker
```
