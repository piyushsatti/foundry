---
title: Cartographer
category: architecture
status: parked
summary: A state-faithful session-visualization tool — a background reducer maintains a consolidated session map (state-primacy over log-faithful), rendered on a React Flow canvas. Parked in Phase 1.
sources:
  - bundles/cartographer/MISSION.md
  - bundles/cartographer/brief.md
  - bundles/cartographer/decisions.md
  - bundles/cartographer/design/
related: [Roadmap, Plan Orchestrator]
updated: 2026-07-20
---

# Cartographer

> **Status:** parked (Phase 1, design exploration) · Gate 1 (a render the owner loves) never closed. **Consolidated from** the cartographer bundle's MISSION / brief / decisions / design set.

## Overview

<TODO: state-faithful session map — rework UPDATES nodes in place instead of
appending, so the map reads clean top-to-bottom. The reducer is the invention;
the renderer borrows from prior art. Human transparency tool first.>

## Design arc

<TODO: 16 paradigms → 4 directions → the Switchyard transit-map visual language
(three laws: icons augment not replace; every meaning two channels; strict hue
budget) → tiered MAP/OUTLINE/SECTOR IA → the "geometry cannot narrate" lesson
(schema v2) → the pivot to an infinite React Flow canvas.>

## Key decisions

<TODO: vocab locked (cartographer / session map / /map); human-value-first
identity; design-first prime directive; React Flow (@xyflow/react, MIT) ratified
2026-07-11; per-session opt-in with a declared decomposable goal; no GitHub ever.>

## Status

<TODO: React Flow prototype rendering schema-v2 mocks; canvas "feel" ratified but
not signed off; taxonomy/mereology workstream just begun. Phases 2–4 specified,
unstarted. See Issue #5 (revive or archive).>

## See also

- [Roadmap](../roadmap/roadmap.md)
