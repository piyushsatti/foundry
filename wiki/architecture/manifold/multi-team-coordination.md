---
title: Multi-Team Coordination
category: architecture
status: draft
summary: One DB, many projects — portfolio "tracks" for exec roll-up vs cross-project blocking edges; "cross-team = cross-project, never cross-manifold."
sources:
  - bundles/manifold/skills/manifold/references/business-model.md
  - docs/archive/topics/portfolio-cross-project.md
related: [Data Model, Manifold Overview]
updated: 2026-07-20
---

# Multi-Team Coordination

> **Status:** draft · **Consolidated from** business-model.md + archived portfolio-cross-project.md.

## Overview

<TODO: multi-team scaling via one DB / many projects (not multiple installs).>

## Portfolio roll-up

<TODO: portfolio_links "tracks" relationship (not a graph edge) for exec roll-up.>

## Cross-project blocking

<TODO: cross_project_edges (blocks/depends_on) with project_id/node_id node_ref URI;
these gate next-leaves. Federation deliberately deferred.>

## See also

- [Data model](data-model.md)
