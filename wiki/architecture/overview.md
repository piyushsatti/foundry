---
title: Architecture Overview
category: architecture
status: draft
summary: The repo map and the source→build→serve pipeline (bundles → plugins → marketplace catalog), plus the three-part identity of foundry.
sources:
  - README.md
  - AGENTS.md
  - CLAUDE.md
  - docs/README.md
related: [Why Bundling, Versioning, Design Philosophy, Glossary]
updated: 2026-07-20
---

# Architecture Overview

> **Status:** draft · **Consolidated from** `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/README.md`.

## Overview

<TODO: foundry's three-part identity — plugin marketplace + development
workspace + authored Claude Code tooling.>

## The source → build → serve pipeline

<TODO: bundles/ (source) → plugins/ (materialized, gitignored) → marketplace
catalog on main pointing at the release branch via git-subdir.>

## Repo layout

<TODO: the layout table — bundles/, plugins/, library/, packages/, apps/,
skills/, vendor/, home/, docs/, local/, .gitignored/.>

## Durable vs ephemeral docs

<TODO: tracked docs/ vs never-committed .gitignored/.>

## See also

- [Why bundling](bundling/why-bundling.md) · [Versioning](bundling/versioning.md) · [Design philosophy](design-philosophy.md)
