# manifold (skill)

Agent-facing entry point for the manifold project compass. **This folder is instructions only** — runtime code lives elsewhere in the repo.

## Repo layout

| Path | What |
|---|---|
| [`skills/manifold/`](.) | This skill — `SKILL.md` + docs for agents |
| [`packages/manifold/`](../../packages/manifold/) | Core library (DB, queries, writes, validate, CLI) |
| [`mcps/manifold/`](../../mcps/manifold/) | MCP server (38 tools) |
| [`apps/manifold-web/`](../../apps/manifold-web/) | Browser UI (`manifold serve`) |

## What manifold gives you

manifold is a project compass: what is this project, where are we, what's next, have we drifted. KAOS AND/OR DAG across user-defined layers; SQLite canonical store (`$MANIFOLD_DB`, default `~/.claude/manifold.db`).

- **Layers** — intent / capabilities / contracts / realizations (or custom)
- **Compass** — `next-leaves`, `target_status`, `spec-audit` (M3), `drift-report` (M4)
- **Verdicts** — automated_check, python_assertion, human_signoff, llm_judge

## Pick a doc

| You are… | Read this |
|---|---|
| **Why manifold? (start here)** | [`references/why-manifold.md`](references/why-manifold.md) |
| **Trying it out** | [`references/user-guide.md`](references/user-guide.md) |
| **Wiring verdicts / drift** | [`references/verdicts.md`](references/verdicts.md) |
| **Building on it (orchestrator, etc.)** | [`references/architecture.md`](references/architecture.md) + [`references/business-model.md`](references/business-model.md) + [`packages/manifold/README.md`](../../packages/manifold/README.md) |

## Quick start

```bash
# from repo root — adjust clone path
packages/manifold/scripts/manifold version
packages/manifold/scripts/manifold next-leaves <project>
```

Register MCP: [`mcps/manifold/.mcp.json.example`](../../mcps/manifold/.mcp.json.example)

## Evals

```bash
python3 scripts/run_skill_evals.py --skill manifold
```

## Tests

```bash
cd packages/manifold && python3 -m unittest discover -v
cd mcps/manifold && python3 -m unittest discover -v
cd apps/manifold-web && python3 -m unittest discover -v
```

## Status

**v0.1.0** — see [`references/changelog.md`](references/changelog.md).
