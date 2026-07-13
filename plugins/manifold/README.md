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
3. the copy vendored under `server/_vendor/` — present only in the **built**
   plugin (a marketplace install ships only `plugins/manifold/`).

Because of (3), the built plugin works from a clean `/plugin install manifold@foundry`
with **no extra setup** — the library (stdlib-only) and `schema.sql` travel with it.

`_vendor/` is not tracked in source: `scripts/build.py` (repo root) materializes it
from `packages/manifold` (package tree + `schema.sql` sidecar, per this bundle's
`bundle.yaml`), and `tests/test_build_determinism.py` fails if the vendored output
drifts from the canonical source.

## Tests

```bash
# from the foundry repo root
python3 -m unittest discover -s bundles/manifold/tests -p 'test_*.py'
```

The library's own suite (372 tests) lives separately under `packages/manifold/tests`.
