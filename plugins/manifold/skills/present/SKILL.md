---
name: present
description: Human-readable projections of manifold data — HTML pages, Mermaid flowcharts, mindmaps, status summaries. Use when user asks for diagram, mindmap, mermaid, visual roadmap, show me blockers graphically, human-readable status, presentation layer, or readable HTML from manifold.
argument-hint: "Project + what to visualize (blockers, decomposition, mindmap, status)"
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../../../../skills/manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| **suggests** | `manifold` | Soft handoff after this skill — suggest, do not auto-chain |

**Used by:** `manifold` (suggests)

<!-- foundry:dependencies:end -->

# Present

Route **human-facing** requests to manifold view-models, then render or link — never scrape HTML as data.

<HARD-GATE>
Do not invent graph state. Call manifold MCP for view-model JSON. Mermaid/mindmap strings come from formatters or the web UI, not from guessing edges.
</HARD-GATE>

## When to use

- User wants **Mermaid**, **mindmap**, **diagram**, or **visual** understanding of manifold projects
- User wants a **shareable URL** to open in browser (`manifold serve`)
- User asks "show me blockers / decomposition / flow" for a project

Use **manifold** skill (not this one) for writes, drift rituals, next-leaves execution, trajectory accept.

## Routing

| User says | MCP tool | Human surface |
|---|---|---|
| list views / what diagrams exist | `list_presentation_views()` | `GET /api/v1/presentation/views` |
| mermaid / diagram / blockers / who blocks whom | `peek_diagram(..., view_id=blockers)` or `diagram_type=blockers` | `/projects/<id>/diagram?focus=` or `/projects/<id>/views/blockers?focus=` |
| decomposition / layer tree / breakdown | `peek_diagram(..., view_id=decomposition)` | `/projects/<id>/views/decomposition?focus=` |
| trajectory plan diagram | `peek_diagram(..., view_id=trajectory, trajectory_id=)` | same + `trajectory_id` |
| mindmap / flow / steps visually | `peek_mindmap(..., view_id=mindmap-flow)` | `/projects/<id>/mindmap?focus=` or `/projects/<id>/views/mindmap-flow?focus=` |
| where are we / status brief | `peek_status_brief(project_id)` | `/projects/<id>/brief` |

HTML pages render **server-side SVG** (no CDN). Mermaid is export-only (`diagram-view --format md`). Same URLs return JSON with `Accept: application/json` or `?format=json`.

**Default focus:** omit `focus_node_id` to use first cross-blocked leaf or first next-leaf.

## Response pattern

1. Call the MCP tool; read structured JSON (`nodes`, `edges`, `tree`, or status-brief sections).
2. One-paragraph summary in plain language:
   - **Status brief:** lead with `overall.headline`; mention `blocked[]` count and `stale_warning` if set.
   - **Diagram/mindmap:** counts, focus node, truncated warning if any.
3. Give the **browser URL** assuming `manifold serve` on port 7779 unless user configured otherwise:

```
http://localhost:7779/projects/<project_id>/brief
http://localhost:7779/projects/<project_id>/brief?detail=summary
http://localhost:7779/projects/<project_id>/diagram?focus=<node_id>
http://localhost:7779/projects/<project_id>/views/blockers?focus=<node_id>
http://localhost:7779/projects/<project_id>/mindmap?focus=<node_id>
```

JSON view-model on brief/diagram paths: `?format=json` or `Accept: application/json`.

4. Optional: paste markdown from CLI:

```bash
packages/manifold/scripts/manifold render project <project> --template status-brief --format md
packages/manifold/scripts/manifold diagram-view <project> --format md --named-view blockers --focus <node>
```

## Bounds

- Subgraphs capped at ~12 nodes — if `truncated: true`, suggest a narrower `focus_node_id`.
- Never render the full portfolio graph as one Mermaid chart.
- For external roadmaps (Linear, Notion), link out — do not rebuild in manifold.

## References

- [`docs/manifold/human-presentation.md`](../../docs/manifold/human-presentation.md)
- [`research/manifold/human-output-2026-06/synthesis.md`](../../research/manifold/human-output-2026-06/synthesis.md)
