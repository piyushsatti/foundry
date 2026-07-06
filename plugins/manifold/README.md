# manifold (plugin)

The manifold MCP server — 46 tools (27 read + 19 write) over the `packages/manifold`
library (`manifold-lib`), the KAOS project-compass engine.

This is a Claude Code plugin: its MCP server is declared in [`.mcp.json`](.mcp.json) and
auto-loads when the plugin is installed — no manual host registration. The server is
launched as `${CLAUDE_PLUGIN_ROOT}/server/mcp_server.py` with its database at
`${CLAUDE_PLUGIN_DATA}/manifold.db`.

## Bundled library — self-contained

The server imports the `manifold` library and resolves it in this order:

1. a pip-installed copy (`pip install -e packages/manifold`) — the repo dev flow;
2. the sibling `packages/manifold` tree when running from a repo checkout;
3. the copy **vendored under [`server/_vendor/`](server/_vendor/)** — used by a
   marketplace install, which ships only `plugins/manifold/`.

Because of (3), the plugin works from a clean `/plugin install manifold@foundry`
with **no extra setup** — the library (stdlib-only) and `schema.sql` travel with it.

The vendored copy is generated from `packages/manifold` and must stay in sync:

```bash
python3 plugins/manifold/scripts/vendor_sync.py   # regenerate after changing the lib
```

`tests/test_vendor_parity.py` fails the build if the vendored copy drifts.

## Tests

```bash
# from the foundry repo root
python3 -m unittest discover -s plugins/manifold/tests -p 'test_*.py'
```

The library's own suite (372 tests) lives separately under `packages/manifold/tests`.
