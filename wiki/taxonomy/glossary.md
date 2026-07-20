---
title: Glossary
category: taxonomy
status: draft
summary: The shared vocabulary of foundry — what the nouns mean, what the verbs do, and how they relate.
sources:
  - docs/manifold/glossary.md
  - README.md
  - docs/adr/0001-materialized-plugin-bundles.md
related: [Why Bundling, Versioning, Architecture Overview]
updated: 2026-07-20
---

# Glossary

> **Status:** draft · **Consolidated from** `docs/manifold/glossary.md` (widen from manifold-only to whole-repo) + `README.md` + `ADR-0001`.

## Overview

The repo mixes several vocabularies (packaging, review, spec/goal-graph, memory).
This page is the one place that defines each term and — critically — separates
the **nouns** (the things) from the **verbs** (the actions), because they are
easy to confuse: *bundling* is an action; a *bundle* is what it produces.

## Nouns (the things)

| Noun | Meaning |
|------|---------|
| bundle | <TODO> |
| plugin | <TODO — the materialized output of a bundle> |
| skill | <TODO> |
| agent | <TODO> |
| library | <TODO — shared-capability promotion target> |
| MCP server | <TODO> |
| marketplace | <TODO> |
| hook | <TODO> |
| lens / stance / hat / wardrobe | <TODO — crucible review vocab> |
| node / goal-graph / verdict / revision / trajectory | <TODO — manifold vocab> |
| session map | <TODO — cartographer artifact> |
| cell / atom / store / scope tier | <TODO — meditate memory vocab> |

## Verbs (the actions) → what they produce

| Verb | Action | Produces |
|------|--------|----------|
| bundling | <TODO> | a bundle |
| building / materializing | `scripts/build.py` | a plugin under `plugins/` |
| promoting | Rule of Three | a `library/` entry |
| versioning | bump `plugin.json` | a new bundle version |
| releasing | publish to `release` branch | installable plugin |
| curating | meditate disposition | a memory change |
| dispatching | plan-orchestrator run | agent work |

## Disambiguations

<TODO: from manifold glossary — the three "intent drift" lineages, human-label
vs API-term crosswalk, terms to avoid.>

## See also

- [Why bundling](../architecture/bundling/why-bundling.md)
- [Versioning](../architecture/bundling/versioning.md)
