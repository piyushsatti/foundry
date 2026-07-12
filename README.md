# foundry

Piyush's canonical home for agentic infrastructure — the Claude Code plugins, skills, MCP servers, and supporting libraries I build and run, in one repo.

foundry is three things under one roof:

- **A plugin marketplace** — versioned, installable Claude Code plugins, sourced from `bundles/`, built to `plugins/`, cataloged in `.claude-plugin/marketplace.json`.
- **A development workspace** — the libraries, MCP servers, and apps those plugins build on (`packages/`, `apps/`).
- **Authored Claude Code tooling** — hooks, commands, statuslines, and subagents I built (`home/`; live `~/.claude` state is not mirrored).

## Layout

| Path | What lives here |
|------|-----------------|
| `.claude-plugin/marketplace.json` | Marketplace catalog — lists every plugin |
| `bundles/` | Self-contained, versioned plugin SOURCE: `meditate`, `manifold`, `plan-orchestrator`, `crucible` |
| `plugins/` | Gitignored build output, materialized from `bundles/` by `scripts/build.py` — what the marketplace serves |
| `library/` | Shared-capability promotion target for skills/agents used by 2+ bundles |
| `packages/` | Importable libraries (e.g. `manifold-lib`, the KAOS engine) |
| `apps/` | Human-facing apps (e.g. `manifold-web`) |
| `skills/` | Authored skills in staging — not yet promoted to a bundle |
| `vendor/skills/` | Vendored upstream skills (pinned) |
| `home/` | Authored Claude Code tooling — hooks, commands, statuslines, subagents (live `~/.claude` state is not mirrored here) |
| `docs/` · `research/` · `archived/` | Design docs, landscape studies, deprecated reference |
| `local/` | Work-sensitive, machine-bound (gitignored) |
| `scripts/` | Registry + sync tooling |

## Using the plugins

Add the marketplace once, then install what you want:

```bash
/plugin marketplace add piyushsatti/foundry
/plugin install manifold@foundry
/plugin install plan-orchestrator@foundry
/plugin install meditate@foundry
/plugin install crucible@foundry
```

The `manifold` plugin's MCP server imports the `manifold-lib` package. From this checkout:

```bash
pip install -e packages/manifold
```

## Developing

- **New plugin** → `bundles/<name>/` with `.claude-plugin/plugin.json` (see `bundles/meditate` as the reference); `scripts/build.py` materializes it to `plugins/<name>/`.
- **New skill (staging)** → `skills/<name>/SKILL.md`, registered in `skills/manifest.yaml`; promote to a bundle when it earns a version.
- **Shared library** → `packages/<name>/` with a `pyproject.toml`.

See `docs/` for design notes, and `docs/manifold/todo.md` / `skills/todo.md` for open items.

## License

MIT — see `LICENSE`.
