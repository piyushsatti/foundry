---
title: Why Bundling
category: architecture
status: draft
summary: The rationale for the bundle abstraction — why capabilities are packaged as self-contained, independently versioned bundles rather than a flat skill/agent pile.
sources:
  - docs/adr/0001-materialized-plugin-bundles.md
  - bundles/devtools/README.md
  - README.md
  - AGENTS.md
related: [Versioning, Architecture Overview, Glossary, Decisions Ledger]
updated: 2026-07-20
---

# Why Bundling

> **Status:** draft · **Consolidated from** `docs/adr/0001-materialized-plugin-bundles.md`, `bundles/devtools/README.md`, `README.md`.

## Overview

<TODO: 2-4 sentences — a *bundle* is the unit of packaging and versioning; why
this abstraction exists at all.>

## The problem bundling solves

<TODO: from ADR-0001 — physical copy over symlinks, independent per-bundle
versioning, the "wrong abstraction is worse than duplication" stance.>

## Domain boundaries — when a capability earns its own bundle

<TODO: from bundles/devtools/README.md — worktree tooling is its own domain,
distinct from review/spec/orchestration/memory.>

## The Rule of Three (promotion to `library/`)

<TODO: a skill/agent moves to library/ only when a 2nd bundle needs it.>

## Invariants

<TODO: CI-enforced no-cross-bundle-path-reference; version lives only in plugin.json.>

## See also

- [Versioning](versioning.md)
- [Architecture Overview](../overview.md)
- [Decisions ledger](../decisions-ledger.md)
