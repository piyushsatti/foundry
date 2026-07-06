# foundry

Piyush's agentic-infrastructure monorepo: a Claude Code plugin marketplace, the libraries / MCP servers / apps behind it, and a personal `~/.claude` kit.

**Opening a session here?** `README.md` covers the layout; `docs/` has design notes.

**Open work queue:** an approved 7-item buildout (from the 2026-07-04 transcript mining) is pending — sequence 0→1→3→6→2→5→4, one fresh session per item, Pi approves builds one by one. Start at `.gitignored/plans/buildout-2026-07/README.md`; each item file has a paste-ready kickoff prompt. Do not start an item unprompted — Pi initiates each one.

## What's here

| Path | Role |
|------|------|
| `plugins/` | Versioned Claude Code plugins — `meditate`, `manifold`, `plan-orchestrator`, `crucible` |
| `packages/manifold/` | `manifold-lib` — the KAOS engine (pip-installable; the manifold MCP imports it) |
| `apps/manifold-web/` | Browser UI |
| `skills/` | Authored skills in staging (not yet plugins); registry: `skills/manifest.yaml` |
| `vendor/skills/` | Vendored upstream skills |
| `home/` | Personal `~/.claude` kit — global `CLAUDE.md`, settings, hooks, commands, memory, statuslines |
| `docs/` · `research/` · `archived/` | Design docs, studies, deprecated reference |
| `local/` | Work-sensitive (gitignored) |
| `.gitignored/` | Local scratch — plans, audits, handoffs (never committed) |

## manifold

```bash
pip install -e packages/manifold            # makes `import manifold` work everywhere
python3 -m manifold version
cd packages/manifold && python3 -m unittest discover   # 372 tests
```

DB: `$MANIFOLD_DB` (default: a per-idea file under `~/.claude/`). One DB file per product idea.

## Plugins

Each plugin is self-contained under `plugins/<name>/` with `.claude-plugin/plugin.json`. MCP servers live inside their plugin (`server/`) and are declared in the plugin's `.mcp.json` via `${CLAUDE_PLUGIN_ROOT}`. The marketplace catalog is `.claude-plugin/marketplace.json`.

## Skills registry

`skills/manifest.yaml` is the source of truth for authored + vendored skills.

```bash
python3 scripts/skills_manifest.py validate
```
