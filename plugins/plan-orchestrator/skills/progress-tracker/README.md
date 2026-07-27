# progress-tracker

Agent-skill wrapper for the progress-tracker MCP, bundled in the
**plan-orchestrator** plugin. The MCP server code is the source of truth:
[`../../server/`](../../server/) (`mcp_server.py`, `web_server.py`, `db.py`, `schema.sql`).

The MCP auto-registers via the plugin's `.mcp.json` (`${CLAUDE_PLUGIN_ROOT}`);
installing the plan-orchestrator plugin brings the server, web viewer, and
scripts with it. See the [plugin README](../../README.md) for architecture and
the full tool surface.
