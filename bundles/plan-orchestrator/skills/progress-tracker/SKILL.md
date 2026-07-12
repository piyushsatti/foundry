---
name: progress-tracker
description: Live dispatch progress for multi-agent orchestration. Use when tracking what dispatched agents are doing, peek_project/peek_phase status, todo_init/todo_done discipline, progress viewer, or "what are agents working on". NOT for spec graph (manifold) or static plans (plan-orchestrator alone). Requires MCP registration.
argument-hint: "project_id or dispatch_id to peek; or setup smoke test"
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../../../../skills/manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| **suggests** | `plan-orchestrator`, `manifold` | Soft handoff after this skill — suggest, do not auto-chain |

**Used by:** `plan-orchestrator` (requires)

<!-- foundry:dependencies:end -->

# Progress tracker

Real-time **dispatch telemetry** — what agents are doing right now — without reading full agent context.

<HARD-GATE>
This is runtime status, not spec truth. For "what should we build?" use **manifold**. For "what is agent X doing?" use progress-tracker MCP.
</HARD-GATE>

## When to use

- Architect ORIENT cycle: "how are dispatches going?"
- Subagent on dispatch: `todo_init` → `todo_start` / `todo_done` → `todo_finish`
- Human wants the **web viewer** (`http://127.0.0.1:7777/`)

## MCP tools

**Writers (dispatched agents):** `todo_init`, `todo_start`, `todo_done`, `todo_block`, `todo_halt`, `todo_finish`, `todo_note`

**Readers (architect / human):** `peek_all`, `peek_project`, `peek_phase`, `peek_dispatch`

## Setup

Register MCP (see installed `.mcp.json.example`). DB default: `~/.claude/progress.db` (`$PROGRESS_TRACKER_DB`).

```bash
python3 ~/.claude/skills/progress-tracker/examples/smoke_test.py
python3 ~/.claude/skills/progress-tracker/server/web_server.py
```

Full reference: [`README.md`](README.md) (bundled from `plugins/plan-orchestrator/server` on install).
