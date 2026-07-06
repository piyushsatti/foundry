# manifold (plugin)

The manifold MCP server — 46 tools (27 read + 19 write) over the `packages/manifold`
library (`manifold-lib`), the KAOS project-compass engine.

This is a Claude Code plugin: its MCP server is declared in [`.mcp.json`](.mcp.json) and
auto-loads when the plugin is installed — no manual host registration. The server is
launched as `${CLAUDE_PLUGIN_ROOT}/server/mcp_server.py` with its database at
`${CLAUDE_PLUGIN_DATA}/manifold.db`.

## Install prerequisite

The server imports the `manifold` library. Install it once per machine so the import
resolves after the plugin is copied to `~/.claude/plugins/cache/`:

```bash
pip install -e packages/manifold      # from the foundry repo root
```

When run from inside the repo (development), the server also walks up to find
`packages/manifold` automatically, so the pip install is only strictly required for the
installed/cached plugin outside the repo tree.

## Tests

```bash
# from the foundry repo root
python3 -m unittest discover -s plugins/manifold/tests -p 'test_*.py'
```

The library's own suite (372 tests) lives separately under `packages/manifold/tests`.
