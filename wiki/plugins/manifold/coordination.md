# Coordination

**Multiple team graphs live as separate projects in one `$MANIFOLD_DB`; cross-team coordination is cross-project, never cross-manifold.** Two patterns sit on top: portfolio tracks for roll-up and cross-project edges for blocking.

> **Status:** stable

## One DB, many projects

Register each team graph as a project in the same database; reserve the `portfolio` project id for company themes (layer `theme`).

```
ONE $MANIFOLD_DB
├── portfolio          ← company themes
├── product-app        ← team graph
├── ai-platform
└── platform-pipeline
```

Not three installations. Not "cross-manifold." A `node_ref` is `project_id/node_id` (e.g. `ai-platform/C.4`).

## Portfolio tracks (roll-up)

**A theme *tracks* a team node — an association, not a graph edge.** Use it for exec visibility without merging roadmaps by hand.

1. Create theme node in `portfolio`.
2. `link_portfolio(theme, project, node)` for each tracked node.
3. Read `portfolio-report` (or `render portfolio --template quarter-roadmap` for a slide).

`portfolio_links` rows are roll-up membership. Don't reach for `list_targets` (a flat status filter) or `depends_on` (a dependency).

## Cross-project edges (blocking)

**A `blocks` / `depends_on` edge between nodes in different projects.** Use it when one team's leaf waits on another's work.

1. `create_cross_edge(src, dst, kind=blocks)`.
2. `next-leaves` excludes the blocked leaf until the blocker is `achieved`.
3. `portfolio-report` populates `blocked_by` with the blocker's `node_ref`.

Cross-edges are MCP-only in v1 (no CLI subcommand). Don't use the deprecated `realized_by_external` field.

## Tracks vs edges

| | Portfolio track | Cross-project edge |
|---|---|---|
| Shape | association (membership) | directed dependency |
| Table | `portfolio_links` | `cross_project_edges` |
| Purpose | exec roll-up | blocking / readiness |
| Verb | theme **tracks** node | node **blocks** node |

## Federation deferred

Palimpsest-style parent refinement across projects (`parents: [project:auth@K.3]`) is reserved for later. For cross-team blocking, use a cross-project edge — not federation.

## See also

- [Checks](checks) — how blocking affects `next-leaves`.
- [Orchestrator boundary](orchestrator-boundary) — the pre-dispatch cross-blocker check.
