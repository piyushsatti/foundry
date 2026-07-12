# Canvas Use Cases — Four Questions Before Committing to React Flow

Date: 2026-07-11. Companion to `research-canvas-frameworks.md` (ranked survey) and `canvas-data-structures.md` (data-model comparison). Those picked React Flow (`@xyflow/react`) + our own JSON store + MCP on top. Pi asked for four use cases to be checked before committing. API claims below verified against reactflow.dev docs (Context7, 2026-07); Excalidraw/tldraw contrast only where they differ materially.

## UC1 — Custom node shapes, colors, customization depth

**Answer: a custom node is an arbitrary React component. The presentation ceiling is "anything React can render."**

Mechanics, verified: you register components in a `nodeTypes` map, set `node.type` to pick one, and the component receives `NodeProps` — `data`, `selected`, `isConnectable`, etc. Inside it you render whatever you want: SVG shapes, CSS-clipped cards, icons, badges, progress bars, even live `<input>`/`<textarea>` elements (the docs' own first custom-node example is a text-updater node with an input). Connection points are `<Handle type="source"|"target" position={Position.Left|Right|Top|Bottom} id="…"/>` — as many per node as you like, each individually addressable from edges via `sourceHandle`/`targetHandle`.

A cartographer-style card node, everything driven by `node.data`:

```tsx
import { Handle, Position, type NodeProps } from '@xyflow/react';

const KIND_ICON = { decision: '◆', artifact: '▣', event: '●' };
const STATUS_COLOR = { open: '#d97706', settled: '#16a34a', superseded: '#9ca3af' };

export const CardNode = memo(({ data, selected }: NodeProps) => (
  <div className="card" style={{ borderColor: STATUS_COLOR[data.status],
                                 boxShadow: selected ? '0 0 0 2px #6366f1' : undefined }}>
    <header>
      <span className="kind-icon">{KIND_ICON[data.kind]}</span>
      <span className="title">{data.title}</span>
      {data.openQuestions > 0 && <span className="dot" style={{ background: '#f59e0b' }} />}
    </header>
    <Handle type="target" position={Position.Top} />
    <Handle type="source" position={Position.Bottom} />
  </div>
));

const nodeTypes = { card: CardNode };  // <ReactFlow nodeTypes={nodeTypes} …/>
```

**Custom edges** are the same story. Built-in per-edge JSON fields already cover most needs: `style: { stroke, strokeWidth, strokeDasharray }` (color/dashed), `animated: true` (marching-ants), `label`, and `markerEnd`/`markerStart` (`MarkerType.Arrow` / `ArrowClosed` with `color`, or fully custom SVG `<marker>` defs). Beyond that, `edgeTypes` registers custom edge components: `BaseEdge` renders a path you compute with `getBezierPath` / `getSmoothStepPath` / `getStraightPath`, and `EdgeLabelRenderer` portals arbitrary HTML (buttons, chips) onto the edge at `labelX/labelY`. The docs' animating-edges example runs an SVG `<animateMotion>` circle along the path — edges are as programmable as nodes.

Excalidraw/tldraw contrast (material): both limit you to their shape vocabularies. Excalidraw nodes are its drawing primitives — styling is stroke/fill/roughness fields, no React components inside elements, no interactive widgets in shapes. tldraw allows custom shape utils (real React), but you write a `ShapeUtil` class against its schema rather than a plain component. React Flow is the only one of the three where "node = your React component" is the primary, documented idiom.

## UC2 — Limits on what data a node can carry / the graph can represent

**Answer: `node.data` is arbitrary JSON the library never interprets. The real limits are render performance, and a short list of graph shapes React Flow can't express natively.**

**Performance ceilings (honest numbers).** The docs give techniques, not numbers. Community evidence: SingleStore's Visual Explain rebuild reports React Flow "quite performant even on large queries with thousands of … nodes" *when custom nodes are memoized*; xyflow discussion #4975 (large-graph performance) converges on the same recipe. Realistic expectation: hundreds of nodes are effortless with default settings; low thousands are fine with `React.memo` nodes + `onlyRenderVisibleElements` + lean CSS (avoid shadows/gradients/filters at scale); tens of thousands is fighting the DOM — wrong tool. Cartographer session maps are tens of nodes; we are two orders of magnitude below the first ceiling.

- `onlyRenderVisibleElements` (default `false`) skips rendering off-viewport nodes/edges — helps large graphs, adds bookkeeping overhead on small ones (so leave it off until needed). Known caveat: all nodes still render once initially (xyflow #3883), and an edge can vanish if one endpoint is offscreen without measured dimensions (#4516).
- Heavy `node.data` doesn't hurt by itself — the library never reads it — but any nodes-array update re-renders un-memoized custom nodes. Mitigations, straight from the docs' performance page: `memo()` every custom node/edge, declare `nodeTypes`/`edgeTypes` outside the component (or `useMemo`), `useCallback` handlers, and read derived state through narrow store selectors instead of subscribing to the whole `nodes` array.

**What does NOT belong in `node.data`:** derived/recomputable values (layout results, tallies — recompute or cache outside), and large blobs (transcript spans, images, artifact bodies). Store *references* — `{ artifactRef: "artifacts/report-3.md", span: [t14, t22] }` — and resolve on demand. This also keeps snapshots small, which UC4 depends on.

**Non-graph data:** React Flow's document is only `{nodes, edges, viewport}` — there is no place for session-level metadata, and that's correct: our file wrapper owns it. Cartographer's on-disk format is `{ session: { intent, frontier, artifacts, … }, nodes, edges, viewport }` — the schema-v2 fields live beside the arrays, not smuggled into a fake node.

**What React Flow cannot represent natively:** hyperedges (one edge, 3+ endpoints), edge-to-edge connections (edges connect node handles only — an annotation on an edge means a junction node or an `EdgeLabelRenderer` widget), and containment semantics richer than `parentId` (single-parent tree only; no overlapping sets/regions — a node in two regions needs region as `data` field + rendered hull, DIY). None of these are in cartographer's schema today; the merge/diverge DAG from round 3 is plain nodes-and-edges and fits fine.

Contrast (material): Excalidraw and tldraw are drawings, so they represent even *less* graph semantics natively — Excalidraw has no typed data slot except `customData`, tldraw's `meta` bag is equivalent to `data` but inside a proprietary-licensed store.

## UC3 — Nesting: click a node, open a sub-diagram

**Answer: two real mechanisms, both cheap; plus semantic zoom as a third pattern we already designed with.**

**(a) Built-in subflows — nesting ON one canvas.** Verified: a child node sets `parentId: 'parent-id'` (renamed from `parentNode` in v12) and its `position` becomes relative to the parent's top-left. `extent: 'parent'` clamps dragging inside the parent; dragging the parent moves all children. `type: 'group'` is a convenience parent (no handles), but any node type can be a parent. One docs-stated constraint: parents must appear before their children in the `nodes` array. Edges may cross subflow boundaries freely. This gives Miro-style visual grouping, not information hiding — everything is still rendered on one canvas (collapse/expand is app code: filter children out of the array).

**(b) Drill-down navigation — a sub-diagram per node.** Nothing built in, and nothing needed: the document is inert JSON we own, so "open sub-diagram" is swapping which `{nodes, edges}` we hand to `<ReactFlow>`. `onNodeClick` is `(event, node) => void`; the sketch:

```tsx
const [stack, setStack] = useState([rootGraphId]);          // breadcrumb
const graph = loadGraph(stack.at(-1));                      // {nodes, edges} from our store

<ReactFlow nodes={graph.nodes} edges={graph.edges}
  onNodeClick={(_, node) => node.data.childGraph && setStack(s => [...s, node.data.childGraph])} />
<Breadcrumb trail={stack} onJump={(i) => setStack(s => s.slice(0, i + 1))} />
```

Ten lines, standard React state. `node.data.childGraph` is just a ref into our file (a sub-map ID); back is popping the stack; `fitView({ nodes: […], duration })` animates the transition. This is exactly the tiered-map spec's MAP → SECTOR click-through.

**(c) Semantic zoom — third pattern.** `useViewport()` returns live `{x, y, zoom}` inside any node component; render different detail by band (`zoom < 0.5` → dot + icon; `< 1.2` → title; else full card). We already committed to semantic-zoom drill-in in earlier design rounds ("drill-in = semantic zoom in place, one camera") — this is its direct implementation.

Contrast (material): Excalidraw has frames (visual grouping) but no drill-down or nesting semantics — you'd rebuild (b) around scene files. tldraw has frames *and* pages (real separate canvases you can route between), the closest built-in analog to (b) — but license-blocked, and (b) is ~10 lines anyway.

## UC4 — Versions and history: previous iterations, before-vs-now

**Answer: React Flow has no built-in history — undo/redo exists only as a paid Pro *example* (implementation guide, not a library feature; Carto's case study built their own from it). Because the document is inert JSON we own, versioning is our layer — and that's the feature, not the gap.**

- **Snapshots are cheap.** A session map is a few KB of JSON. Snapshot per change-batch or per session turn: append-only JSONL (`snapshots.jsonl`, one `{ts, actor, nodes, edges}` per line) or git-backed (`map.canvas` committed per session — diffs, blame, and history UI for free). For finer-grained undo/redo, record JSON Patch (RFC 6902) or immer patches per mutation and replay/invert — standard libraries, an afternoon.
- **Diffing two snapshots is a structural diff on stable IDs** — the payoff of the inert-JSON choice. Join `nodes` by `id`: present-only-in-new = added; only-in-old = removed; `position` changed = moved; `data` fields changed = edited. Same for edges. Example diff between yesterday and now:

```jsonc
{ "added":   [ { "id": "n12", "data": { "title": "Cache invalidation spike" } } ],
  "removed": [],
  "moved":   [ { "id": "n07", "from": {"x":480,"y":100}, "to": {"x":412,"y":248} } ],
  "changed": [ { "id": "n03", "field": "data.status", "from": "open", "to": "settled" } ] }
```

- **Rendering "what changed since yesterday":** feed the *current* graph to React Flow and paint the diff through `node.data` + node/edge styling — added nodes get a highlight ring (`data.diff: 'added'` → CSS class in the custom node), changed fields get a badge, and removed nodes render as **ghost nodes**: include them in the array with `data.diff: 'removed'`, styled at 35% opacity + dashed border, `selectable: false`. Because a custom node is any React component (UC1), a diff view is just a props variant of the same `CardNode`.
- **Composes with cartographer's schema.** The schema already has node-level `node@version` semantics (version chips, onion-skin diffs, `superseded_because` — SECTOR view). Node versioning = *content* history of one idea; canvas snapshots = *map* history (what existed/where). They layer without touching: a snapshot diff says "n03 changed," the node's own version chain says how, and per the no-internal-IDs law both surface to humans as titles, never IDs.

Contrast (material): tldraw genuinely wins here out of the box — built-in undo/redo, `store.listen` diffs, snapshot/time-travel-ish store — it's the design to imitate, but license-blocked. Excalidraw has in-session undo only; durable history is DIY there too, over a much noisier format (version/versionNonce churn makes structural diffs muddy). React Flow's plain arrays are the *easiest* of the three to version externally.

## Verdict

| Use case | React Flow answer | Effort | Risk |
|---|---|---|---|
| 1. Custom shapes/colors | Nodes and edges are arbitrary React components; ceiling = "anything React renders" | Built-in | None |
| 2. Data scope limits | `data` is uninterpreted JSON; hundreds of nodes free, low-thousands with memoization + `onlyRenderVisibleElements`; no hyperedges/edge-to-edge natively | Built-in (+ discipline: memoize, store refs not blobs) | Low — cartographer is 100× below the ceiling |
| 3. Nesting / drill-down | Subflows (`parentId` + `extent:'parent'`) built in; drill-down = ~10 lines of app state; semantic zoom via `useViewport` | Built-in (a, c) / thin app code (b) | Low |
| 4. Versions / history | Nothing built in (undo/redo is a Pro example only); snapshots + JSON Patch + stable-ID structural diff on our own store; ghost-node diff view via `data` | Thin app code (snapshots/diff) → real work only if we want full undo/redo UI | Low-medium — it's our code to write, but small and on our schedule |

**Does anything change the recommendation? No.** Use cases 1–2 are React Flow's core competency and confirm the presentation and data ceilings are above anything cartographer needs. Use cases 3–4 are app-layer — and that is precisely the property we chose React Flow for: the document is inert JSON we own, so drill-down is a state swap and history is a file-format decision, both under our control and both composing cleanly with cartographer's existing schema (tiered views, node@version). The only genuine out-of-the-box losses versus alternatives are tldraw's built-in undo/history (license-blocked) and nothing from Excalidraw. No blocker found; React Flow + owned JSON store + MCP stands.

Sources: [reactflow.dev custom nodes](https://reactflow.dev/learn/customization/custom-nodes) · [Handle](https://reactflow.dev/api-reference/components/handle) · [custom edges](https://reactflow.dev/learn/customization/custom-edges) · [EdgeLabelRenderer](https://reactflow.dev/api-reference/components/edge-label-renderer) · [performance guide](https://reactflow.dev/learn/advanced-use/performance) · [ReactFlow props / onlyRenderVisibleElements](https://reactflow.dev/api-reference/react-flow) · [sub-flows](https://reactflow.dev/learn/layouting/sub-flows) · [useViewport](https://reactflow.dev/api-reference/hooks/use-viewport) · [undo/redo (Pro example)](https://reactflow.dev/examples/interaction/undo-redo) · [xyflow discussion #4975](https://github.com/xyflow/xyflow/discussions/4975) · [issue #3883](https://github.com/xyflow/xyflow/issues/3883) · [SingleStore Visual Explain on React Flow](https://www.singlestore.com/blog/refactoring-singlestores-visual-explain-to-use-react-flow/)
