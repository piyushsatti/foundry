---
title: Memory Model
category: architecture
status: draft
summary: The two-axis memory model — scope tier × genericity fence — across three stores differentiated by loading model, plus the governance pipeline (terraform for memory).
sources:
  - bundles/meditate/docs/2026-06-24-memory-architecture-spec.md
  - bundles/meditate/README.md
related: [Operation Algebra, Execution Contract]
updated: 2026-07-20
---

# Memory Model

> **Status:** draft · **Consolidated from** the memory-architecture-spec + meditate README.

## Overview

<TODO: two axes — scope tier (Universal⊃Machine⊃Workspace⊃Project⊃Work-unit) ×
genericity (the generic/specific export fence).>

## Three stores by loading model

<TODO: CLAUDE.md rulebook / on-demand memory / serena code-coupled. Native
directory walk-up composition (zero @import). The "no agent files in git" rule.>

## Governance pipeline (terraform for memory)

<TODO: curate → review → apply = plan/show/apply; read-only proposer, human gate,
dumb applier; archive-never-delete; sha256 optimistic locks; one-verb-per-item.>

## See also

- [Operation algebra](operation-algebra.md) · [Execution contract](execution-contract.md)
