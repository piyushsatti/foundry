---
title: Manifold Data Model
category: architecture
status: draft
summary: The DB-canonical architecture — the SQLite schema, three surfaces over one query layer, append-only revisions with optimistic concurrency, and the pluggable verdict engine.
sources:
  - bundles/manifold/skills/manifold/references/architecture.md
related: [KAOS Foundations, Manifold Overview, The Three Checks]
updated: 2026-07-20
---

# Manifold Data Model

> **Status:** draft · **Consolidated from** `references/architecture.md`. Note: source has stale MCP tool counts (38 vs 41) — verify against code when writing.

## Overview

<TODO: DB-canonical — the DB is the spec; markdown is export.>

## Schema

<TODO: the 10-table SQLite schema.>

## Three surfaces, one query layer

<TODO: CLI / MCP / HTTP over a shared query layer.>

## Revisions & concurrency

<TODO: append-only revisions + optimistic concurrency.>

## Verdict engine

<TODO: pluggable — automated_check / python_assertion / human_signoff / llm_judge.>

## See also

- [The three checks](the-three-checks.md)
