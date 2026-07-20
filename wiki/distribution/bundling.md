---
title: Bundling
status: stable
summary: Why plugins are self-contained bundles and how shared capabilities are promoted.
sources:
  - docs/adr/0001-materialized-plugin-bundles.md
  - bundles/devtools/README.md
  - README.md
updated: 2026-07-20
---

# Bundling

**Each plugin is a self-contained bundle in `bundles/<name>/`** — skills, agents, hooks, server, and `bundle.yaml`. A bundle is one domain (review, spec, orchestration, memory, dev-tooling); it grows by adding skills, not by leaking into others.

> **Status:** stable

## How it works

- **Self-contained source.** Everything a plugin needs lives under its bundle.
- **Materialized copy, not symlinks.** `scripts/build.py` copies source into `plugins/<name>/`. Physical copies give independent per-bundle versioning — two bundles may ship different vintages of a shared capability — and survive tools that don't dereference symlinks. Cost: a build step; accepted.

## Rule of Three

Shared code does **not** start shared. A skill or agent moves to `library/{skills,agents}/` only when a **second** bundle needs it; consumers pull it back via `compose:` in `bundle.yaml`. A day-one shared library would be indirection with no dedup (Fowler's Rule of Three; Metz's "wrong abstraction").

## Invariant

CI (`scripts/check_boundaries.py`) enforces: a bundle may reference `library/` and `packages/`, **never another bundle's internals by path**. Namespaced runtime dispatch between plugins stays legal. This makes promotion the only legal reuse path.
