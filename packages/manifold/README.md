# manifold (core library)

DB-canonical **project compass** — KAOS AND/OR DAG substrate. Stdlib-only Python. **v0.1.0**.

This is the **importable core** used by the skill, MCP server, web UI, CLI, and (future) orchestrator.

## What it is

Manifold holds a project's *why* in a queryable graph: layered intent → capabilities → contracts → realizations (or custom layers). Three compass questions are first-class:

| Question | Surface |
|---|---|
| What next? | `next-leaves` / MCP `next_leaves` |
| Are spec revisions explained? | `spec-audit` / MCP `spec_audit` |
| Does code match spec? | `drift-report` / MCP `drift_report` |
| How are themes tracking? | `portfolio-report` / MCP `portfolio_report` |
| Where are we? | `target_status`, verdicts, `list_targets` |

**Positioning:** ADRs that talk to your agent — typed `rationale`, required `change_reason`, revision history, and **`drift-report`** when code diverges (v1: verdict rollup on wired realizations).

**Interop:** manifold is self-contained (MCP, CLI, v0.2 import). Spec Kit interop deferred (L15) — not a capability gap.

**Not:** task tickets, live agent telemetry (see progress-tracker), or dispatch (see orchestrator).

Proper nouns: [`docs/manifold/glossary.md`](../../docs/manifold/glossary.md) · Checklist: [`docs/manifold/todo.md`](../../docs/manifold/todo.md) · How to use: [`docs/manifold/how-to-use.md`](../../docs/manifold/how-to-use.md)

## Layout

```
packages/manifold/
├── schema.sql              # canonical schema (schema_version=1)
├── scripts/manifold        # CLI shim (sets PYTHONPATH for web UI)
├── manifold/
│   ├── cli.py              # subcommands incl. spec-audit, drift-report, next-leaves
│   ├── db.py, schema.py, queries.py, writes.py, validate.py
│   ├── importer.py, exporter.py, markdown.py, durability.py
│   └── config.py, errors.py
└── tests/
```

## Run

From repo root:

```bash
export PYTHONPATH="$PWD/packages/manifold:$PWD/apps/manifold-web"
cd packages/manifold
python3 -m manifold version
python3 -m manifold next-leaves <project>
python3 -m manifold spec-audit <project>
python3 -m manifold drift-report <project>
```

Or use the shim:

```bash
packages/manifold/scripts/manifold version
```

## Consumers

| Consumer | Path |
|---|---|
| Skill (agent instructions) | `plugins/manifold/skills/manifold/` |
| MCP server (42 tools) | `plugins/manifold/server/` |
| Web UI | `apps/manifold-web/` |

## Tests

```bash
cd packages/manifold && python3 -m unittest discover -v
```
