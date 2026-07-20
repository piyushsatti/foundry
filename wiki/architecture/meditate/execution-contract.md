---
title: Execution Contract
category: architecture
status: draft
summary: The dumb-applier execution spec and the frozen interface contract — smart-propose/dumb-apply/human-gate, reversible mechanical execution, and the frozen frontmatter/verb/manifest/curator schemas.
sources:
  - bundles/meditate/docs/mem-arch-applier-design.md
  - bundles/meditate/docs/mem-arch-interface-contract.md
related: [Memory Model, Operation Algebra]
updated: 2026-07-20
---

# Execution Contract

> **Status:** draft · **Consolidated from** applier-design + interface-contract (FROZEN v3).

## Overview

<TODO: smart-propose / dumb-apply / human-gate separation.>

## The dumb applier

<TODO: per-verb execution table; memory dir is read-only to shells so deletes are
impossible → cold-archive + tombstone; coupled-safety ordering (rule lands before
source is dropped); idempotent re-run.>

## Frozen interface contract

<TODO: frontmatter state vocabulary (schema_version 2), axis-separated verb
lexicon, manifest schema, curator agent contract (Opus xhigh, sole promoter).
Freeze discipline via a surfaced-issues protocol.>

## See also

- [Memory model](memory-model.md)
