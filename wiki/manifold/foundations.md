---
title: Foundations
status: stable
summary: Manifold's KAOS lineage — an AND/OR DAG of goals across layers, and what it inherits, drops, and defers.
sources:
  - docs/manifold/kaos-lineage.md
  - bundles/manifold/skills/manifold/references/architecture.md
  - docs/archive/manifold-v0.1/manifold-design.md
updated: 2026-07-20
---

# Foundations

**Manifold's primitive is AND-refinement over Boolean satisfaction with layered abstraction — the KAOS goal-oriented requirements-engineering tradition.** A goal is satisfied only when all its refinements are; that maps directly to verdict propagation up the graph.

> **Status:** stable

## Lineage

- **Primary:** Darimont & van Lamsweerde (1996), *Formal Refinement Patterns* — *"the goal refinement structure … can be represented by an AND/OR directed acyclic graph."* Manifold inherits this definition verbatim.
- **Algorithmic:** Martelli & Montanari (1973), *Additive AND/OR Graphs* — the pre-Wikipedia source for shared subproblems; the basis for multi-parent propagation (a failing child invalidates **all** its parents).
- **Textbook:** van Lamsweerde (2009), *Requirements Engineering*.

## Why DAG, not tree

**A node may have multiple parents across layers** — one capability can satisfy several intents. A design brief surveyed four formal traditions (grammar, refinement calculus, goal-oriented RE, AND/OR graphs / HTN): three of four define decomposition as a DAG, and even proof theory — a tree only in its formal definition — shares subproofs as DAGs in every real proof assistant. Strict tree is costly in the three closest traditions; strict DAG is cheap in the one that prefers trees. Manifold relaxed single-parent-across-layers to the KAOS AND/OR DAG; intra-layer stays acyclic, cross-layer cycles stay forbidden.

## Inherit / leave behind / defer

| Inherits from KAOS | Leaves behind | Defers (additive later) |
|---|---|---|
| AND-refinement (Boolean conjunction over children) | LTL semantics → replaced by [pluggable verdicts](data-model.md) | OR-refinement |
| AND/OR DAG across layers | Built-in agent assignment → orchestrator's job | Obstacle analysis |
| Cycle prohibition | Operations layer | Refinement-pattern catalog |
| Coverage rule (non-leaf, non-constraint → ≥1 child) | | Conflict detection |
| Constraint goals (apply, don't decompose) | | Qualitative aggregation (Make/Help/Hurt/Break) |
| Layered abstraction (project-defined layers) | | |

Deferred items sit on top of the substrate and don't require revisiting the core data model. Pluggable verdict mechanisms (not LTL) are what let manifold generalize beyond software.

## See also

- [Data model](data-model.md) — how the DAG lives in SQLite.
- [Overview](overview.md) — the compass identity.
