# foundry

Piyush's agentic-infrastructure monorepo: a Claude Code plugin marketplace, the
libraries / MCP servers / apps behind it, and a personal `~/.claude` kit.

**Opening a session here?** Read [`docs/README.md`](docs/README.md) first; `README.md`
covers the layout and `CLAUDE.md` has the working conventions.

## What's here

| Path | Role |
|------|------|
| `bundles/` | Versioned plugin SOURCE — `meditate`, `manifold`, `plan-orchestrator`, `crucible`. Each is self-contained under `bundles/<name>/` with `.claude-plugin/plugin.json`; MCP servers live in `bundles/<name>/server/` and are declared in the plugin's `.mcp.json`. |
| `plugins/` | Gitignored build output, materialized from `bundles/` by `scripts/build.py`; this is what the marketplace serves. |
| `library/` | Shared-capability promotion target — a skill/agent moves here only when a second bundle needs it (Rule of Three); bundles pull it via `compose.skills/agents` in `bundle.yaml`. |
| `packages/manifold/` | `manifold-lib` — the KAOS engine (pip-installable; the manifold MCP imports it). |
| `apps/manifold-web/` | Browser UI. |
| `skills/` | Authored skills in staging (not yet bundles); registry `skills/manifest.yaml`. |
| `vendor/skills/` | Vendored upstream skills (pinned). |
| `home/` | Personal `~/.claude` kit — global `CLAUDE.md`, settings, hooks, commands, memory, statuslines. |
| `local/` | Work-sensitive (gitignored). |
| `docs/` · `research/` · `archived/` | Design docs, studies, deprecated reference. |
| `.gitignored/` | Local scratch — plans, audits, handoffs (never committed). |

The marketplace catalog is `.claude-plugin/marketplace.json` at the repo root.

## manifold

```bash
pip install -e packages/manifold            # makes `import manifold` work everywhere
python3 -m manifold version
cd packages/manifold && python3 -m unittest discover   # 372 tests
```

DB: `$MANIFOLD_DB` (default: a per-idea file under `~/.claude/`). One DB file per product idea.
Use `python3 -m manifold`, not `python3 -m manifold.cli`.

## Skills registry

`skills/manifest.yaml` is the source of truth for authored + vendored skills.

```bash
python3 scripts/skills_manifest.py validate
python3 scripts/skills_manifest.py sync-docs
```
