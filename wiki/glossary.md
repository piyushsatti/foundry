# Glossary

**The high-level taxonomy.** Core nouns and verbs used across foundry. Domain-specific jargon lives in that domain's pages (e.g. manifold's `verdict`, crucible's `lens`).

> **Status:** draft

## Nouns — the things

| Noun | What it is |
|------|-----------|
| **bundle** | A self-contained plugin *source* under `bundles/<name>/` — one domain's skills, agents, hooks, server. |
| **plugin** | The *built, installable* output materialized from a bundle into `plugins/<name>/`. |
| **library** | Shared-capability target (`library/`) — a skill/agent lives here only when a 2nd bundle needs it. |
| **marketplace** | The catalog (`.claude-plugin/marketplace.json`) that points installs at each plugin. |
| **skill** | A packaged instruction set Claude invokes for a kind of task. |
| **agent** | A subagent definition with its own tools/model. |
| **hook** | A script the harness runs on an event (e.g. `PreToolUse`) to enforce or augment behavior. |
| **MCP server** | A tool/resource server a bundle ships (in `server/`), declared via `.mcp.json`. |
| **harness** | The runtime that runs the agent — Claude Code is foundry's; hooks attach to its lifecycle. |

## Verbs — the actions, and what they produce

| Verb | Action | Produces |
|------|--------|----------|
| **bundling** | packaging a domain's capabilities as a self-contained bundle | a **bundle** |
| **building** / materializing | `scripts/build.py` copies a bundle into `plugins/` | a **plugin** |
| **promoting** | Rule of Three — move shared code up when a 2nd bundle needs it | a **library** entry |
| **versioning** | bump the version in `plugin.json` | a new bundle version |
| **releasing** | publish built plugins to the `release` branch | an installable artifact |

> **The distinction that trips people up:** *bundling* is the verb; a *bundle* is the noun it produces. Same for *building* → *plugin*.

## Domain vocabularies

Deeper terms live with their domain:

- **manifold** — node, goal-graph, verdict, revision, trajectory, spec-audit, drift-report, next-leaves → [manifold/](plugins/manifold/overview)
- **crucible** — lens, stance, hat, wardrobe → [crucible/](plugins/crucible/overview)
- **meditate** — cell, atom, store, scope tier → [meditate/](plugins/meditate/overview)
- **cartographer** — session map, reducer → [cartographer/](plugins/cartographer/overview)

## See also

- [Distribution](distribution/overview) · [Organization](meta/organization)
