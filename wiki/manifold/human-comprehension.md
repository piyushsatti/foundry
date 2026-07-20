---
title: Human Comprehension
status: draft
summary: Making manifold readable for humans without letting projections become truth.
sources:
  - docs/manifold/human-comprehension-redesign-plan.md
  - docs/manifold/human-presentation.md
updated: 2026-07-20
---

# Human Comprehension

**Humans should answer basic questions about a project without learning the graph internals — while the graph stays the only source of truth.** The design principle is projection-first, graph-canonical.

> **Status:** draft — in progress. Topic K human output shipped; the wider redesign is a phased plan.

## Graph-canonical

**Renderers format semantics; they never invent them.** One builder produces a view-model dict; each surface only formats it.

| Layer | Rule |
|---|---|
| Canonical truth | SQLite graph, revisions, verdicts, target statuses |
| Agent contract | MCP JSON and structured view-models |
| Human presentation | HTML, Markdown, diagrams, mindmaps, summaries |
| Safety | Renderers format semantics; they do not invent them |

```
Graph → build_*_view() → dict → HTML | MCP JSON | Mermaid/markdown export
```

Mermaid and mindmaps are **projections**, never stored as truth. HTML renders server-side SVG (no CDN); Mermaid is export-only.

## One builder, many renderers

Each named view answers **one** primary question and feeds JSON, HTML, and Markdown from the same builder. Diagram/mindmap slices are hard-capped (≤12 nodes) and link to a narrower focus rather than growing into a hairball.

| View | Primary question |
|---|---|
| Status brief | Where are we? |
| Risk brief | Can I trust this? |
| Delivery view | What's ready next? |
| Trajectory preview | What will change? |

## Evidence posture

Every claim carries an evidence level — High / Medium / Low / Unknown — and the language is bounded accordingly ("manifold supports…" vs "we believe…"). Surfaces must show `generated_at`, stale warnings, and unverified / errored counts so a page never looks more authoritative than its data.

## Anti-overclaim rules

Human framing must not outrun what the graph proves:

| Avoid | Say instead |
|---|---|
| "Manifold is compliance-ready" | "audit-friendly traceability primitives" |
| "Status brief proves the project is healthy" | "summarizes current graph and evidence state" |
| "`next-leaves` prioritizes work" | "identifies graph-ready frontier work" |
| "No violations = all clear" | show unverified / errored / stale explicitly |

## See also

- [Checks](checks.md) — the status/evidence/priority axes these views expose.
- [Data model](data-model.md) — the canonical graph behind every projection.
