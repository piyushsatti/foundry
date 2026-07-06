# Human presentation layer

How manifold surfaces graph data for **human parsing** — HTML, Mermaid, mindmaps — without duplicating the source of truth.

**Research:** [`../../research/manifold/human-output-2026-06/synthesis.md`](../../research/manifold/human-output-2026-06/synthesis.md)  
**Redesign plan:** [`human-comprehension-redesign-plan.md`](human-comprehension-redesign-plan.md)
**Skill routing:** [`../../skills/present/SKILL.md`](../../skills/present/SKILL.md)

---

## Split

| Layer | Owns | Does not own |
|---|---|---|
| **Manifold (compass)** | SQLite graph, queries, view-model JSON builders | Diagram layout aesthetics, LLM prose |
| **Presentation** | Mermaid/mindmap render, HTML pages, chat summaries + URLs | Graph writes, drift semantics |

```
Graph → build_*_view() → dict  →  SVG HTML | MCP JSON | Mermaid/md export
```

Graph is authoritative. Mermaid and mindmaps are **projections**, never stored as truth.

**v2 (current):** HTML pages render **server-side SVG** (no CDN). Mermaid source is export-only (`--format md`, CLI). Named views live in `presentation_views.json`; same URLs negotiate JSON via `Accept: application/json` or `?format=json`.

---

## v1 surfaces (shipped incrementally)

| View | Registry id | Builder | MCP | HTML |
|---|---|---|---|---|
| Blocker flowchart | `blockers` | `build_diagram_view(type=blockers)` | `peek_diagram` | `GET /projects/<id>/diagram?focus=` |
| Decomposition flow | `decomposition` | `build_diagram_view(type=decomposition)` | `peek_diagram` | same route |
| Trajectory flow | `trajectory` | `build_diagram_view(type=trajectory&trajectory_id=)` | `peek_diagram` | same route |
| Mindmap tree | `mindmap-flow` | `build_mindmap_view()` | `peek_mindmap` | `GET /projects/<id>/mindmap?focus=` |
| Any catalog view | `<view_id>` | `build_registered_view()` | `view_id` param | `GET /projects/<id>/views/<view_id>` |
| Status brief | `status-brief` | `build_status_brief_view()` | `peek_status_brief` | `GET /projects/<id>/brief` |

List catalog: `list_presentation_views` (MCP) or `GET /api/v1/presentation/views`.

**Caps:** ≤12 nodes per diagram/mindmap slice; truncated views link to narrower focus.

**Content negotiation:** `/brief`, `/diagram`, `/mindmap`, and `/views/<id>` return JSON when `Accept: application/json` (without `text/html`) or `?format=json`. Responses include `Vary: Accept`.

---

## When to use the `present` skill vs `manifold` skill

| User intent | Skill |
|---|---|
| Where are we / drift / next-leaves / writeback | **manifold** |
| Show me a diagram / mindmap / readable HTML | **present** |
| Mermaid for blockers on checkout | **present** → `peek_diagram` → browser URL |

Agents consume **JSON view-models** via MCP. Humans get **HTML** from `manifold serve`. Chat returns a short summary + shareable URL.

---

## Code layout

| Path | Role |
|---|---|
| `packages/manifold/manifold/presentation_views.py` | View-model builders |
| `packages/manifold/manifold/presentation_format.py` | Mermaid + markdown formatters (export) |
| `packages/manifold/manifold/presentation_svg.py` | Server-side SVG renderers |
| `packages/manifold/manifold/data/presentation_views.json` | Named view catalog |
| `packages/manifold/manifold/status_brief.py` | Status-brief view-model builder |
| `packages/manifold/manifold/view_registry.py` | Registry loader + `build_registered_view()` |
| `apps/manifold-web/manifold_web/html.py` | HTML bodies (brief pills, SVG, export blocks) |
| `skills/present/` | Chat routing for human surfaces |

Demo mockups (Acme Checkout) — kept locally, not tracked in git.
