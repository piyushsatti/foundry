---
title: Decisions Ledger
category: architecture
status: draft
summary: A single index of the repo's decision records — ADR-0001 plus the locked-decision tables scattered across manifold, meditate, and plan-orchestrator.
sources:
  - docs/adr/0001-materialized-plugin-bundles.md
  - docs/manifold/todo.md
  - bundles/meditate/docs/meditate-decisions-and-findings.md
  - bundles/plan-orchestrator/skills/plan-orchestrator/design-notes.md
related: [Why Bundling, Versioning, Architecture Overview]
updated: 2026-07-20
---

# Decisions Ledger

> **Status:** draft · Indexes the "why we chose X" records that currently live in 4 different places.

## Overview

<TODO: an index/pointer page — the authoritative ledgers stay in their homes;
this cross-links them so a decision can be found without knowing which bundle.>

## ADR-0001 — Materialized plugin bundles

<TODO: physical copy over symlinks, gitignored output + release ref, Rule of
Three, CI no-cross-bundle-reference invariant, version-in-plugin.json-only.>

## manifold — locked decisions L1–L34

<TODO: from docs/manifold/todo.md.>

## meditate — locked decisions & findings

<TODO: from meditate-decisions-and-findings.md.>

## plan-orchestrator — design log (decisions 1–72)

<TODO: from design-notes.md.>

## See also

- [Why bundling](bundling/why-bundling.md)
