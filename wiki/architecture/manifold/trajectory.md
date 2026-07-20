---
title: Manifold Trajectory
category: architecture
status: draft
summary: The plan/apply spec-evolution model — propose → show (impact preview) → accept, modeled on Terraform, where only accept mutates.
sources:
  - bundles/manifold/skills/manifold/references/trajectory.md
  - docs/archive/topics/trajectory.md
  - docs/manifold/todo.md
related: [The Three Checks, Data Model, Orchestrator Boundary]
updated: 2026-07-20
---

# Manifold Trajectory

> **Status:** draft · **Consolidated from** trajectory.md (references + archive) + todo.md L33/L34.

## Overview

<TODO: target brief → propose → show → accept → next-leaves.>

## The Terraform plan/apply analogy

<TODO: propose creates a draft (no writes); show returns an impact preview
computed via a rolled-back transaction (never persisted); accept is the only mutation.>

## Trust model

<TODO: only accept writes; partial-accept nuance (preview guaranteed only if all
legs accepted together).>

## See also

- [The three checks](the-three-checks.md)
