---
status: complete
study: manifold-human-output-2026-06
topic: manifold
type: study-index
tags:
  - manifold
  - topic-k
  - human-output
  - status-brief
  - html
completed: 2026-06-07
---

# Topic K — Human output layer (2026-06)

**Status: complete.** Research for how manifold projects the spec graph into human-usable surfaces (HTML briefs, view-models, tri-surface delivery).

**Primary deliverable:** [`synthesis.md`](synthesis.md) — R0 landscape refresh, cognitive comparison, v1 `status-brief` spec, implementation checklist.

**Prompt (provenance):** [`00-research-prompt.md`](00-research-prompt.md)

**Demo mockups (local):** `.gitignored/demos/human-layer-demo/` — Acme Checkout HTML used as test bed in synthesis.

---

## Reading order

| Order | Document | Why |
|---|---|---|
| 1 | [`synthesis.md`](synthesis.md) | Executive summary + v1 P0 checklist |
| 2 | [`00-research-prompt.md`](00-research-prompt.md) | Original research charter |
| 3 | `.gitignored/demos/human-layer-demo/` | Visual mockups referenced in R1 |

---

## v1 recommendation (from synthesis)

Ship **one** wired prose view: `status-brief` (K1–K7, planned).

**Product decision (2026-06):** Mermaid diagrams + mindmaps are **day-1 P0** (K8–K12) — bounded subgraphs from graph, not full hairball. See [`../../../docs/manifold/human-presentation.md`](../../../docs/manifold/human-presentation.md).

Distill into product when implementing: `packages/manifold/`, `apps/manifold-web/`, `skills/present/`.
