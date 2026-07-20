---
title: Manifold Overview
status: stable
summary: The project compass — a DB-canonical goal graph that preserves and answers "why".
sources:
  - docs/manifold/README.md
  - docs/manifold/how-to-use.md
  - bundles/manifold/skills/manifold/references/why-manifold.md
  - docs/manifold/glossary.md
updated: 2026-07-20
---

# Manifold Overview

**Manifold is a project compass: a versioned goal graph in SQLite that answers orientation questions for long-horizon work.** Code loses its *why* faster than its *what*; manifold keeps intent queryable, typed, and durable.

> **Status:** stable

## What it is

A **compass orients; it does not walk.** Manifold holds a layered graph of intent (KAOS lineage — see [foundations.md](foundations.md)) and exposes it over three surfaces — CLI, MCP, web — on [one query layer](data-model.md).

You don't memorize the tool surface. You ask **compass questions** in plain language; an agent with the manifold skill maps them to the right query.

| Compass question | Primary surface |
|---|---|
| What is this project? | `peek_project`, `list_nodes` |
| Where are we? | `list_targets`, node status |
| What's ready next? | `next-leaves` (readiness, not priority) |
| Are spec revisions explained? | `spec-audit` |
| Does code match spec? | `drift-report` |
| How do we evolve toward X? | `trajectory` propose → show → accept |

`spec-audit` vs `drift-report` are distinct checks — see [checks.md](checks.md). Trajectory is preview-before-mutate — see [trajectory.md](trajectory.md).

## What manifold is not

- **Not a ticket tracker** — use Linear / Issues. A node is not a ticket.
- **Not a dispatch engine** — dispatch is a future separate skill ([orchestrator-boundary.md](orchestrator-boundary.md)).
- **Not live agent telemetry** — that's the progress-tracker MCP.
- **Not a one-shot spec workflow** — use Spec Kit for greenfield feature specs; manifold sustains intent across months.

## See also

- [Positioning](positioning.md) — the thesis and competitive framing.
- [Foundations](foundations.md) — the KAOS goal-graph lineage.
- [Data model](data-model.md) — DB-canonical, three surfaces, one query layer.
