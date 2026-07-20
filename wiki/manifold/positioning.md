---
title: Positioning
status: stable
summary: The thesis — intent decays faster than code, so make "why" a typed, queryable field.
sources:
  - bundles/manifold/skills/manifold/references/why-manifold.md
updated: 2026-07-20
---

# Positioning

**Software loses its *why* faster than its code, and AI agents make it worse; manifold is typed external memory for intent.** The idea isn't novel — the packaging for long-horizon agent work is.

> **Status:** stable

## The thesis

Requirements drift, docs become fiction, and agents ship fast without durable intent because session context resets. The field already names the failure but nothing agent-native combines the pieces:

> ADRs that talk to your agent, version your intent, and produce a drift report when code diverges.

The wedge is a **queryable, versioned graph of intent** with **typed revision discipline** (`change_reason`, `spec-audit`) and a **"what's next" API** for orchestrators.

## The problem, named

| Failure | Symptom | What catches it |
|---|---|---|
| **Bug** | Code fails its own spec | Tests, CI |
| **Intent drift** | Code passes tests but no longer matches *why* | Almost nothing by default |

Intent drift is "the lost why that diffs cannot reveal." Requirement drift is structural — requirements, design, and code live in separate systems with no live connection. Agents amplify it: long-horizon work needs external memory, not just bigger context windows.

## Competitive framing

| Neighbor | What it does | Where manifold differs |
|---|---|---|
| **Spec Kit / SDD** | Starts work from a spec (markdown in git) | Sustains intent across months (DB, revisions, drift) |
| **DOORS / Polarion (ALM)** | Enterprise traceability | SQLite, stdlib, MCP-first, single-operator scale |
| **CLAUDE.md / RAG memory** | Static rules / freeform facts | Layered requirements with history and verdicts |
| **Linear / Jira** | Track work items | Models *why the system must satisfy goal G* |
| **progress-tracker** | What agents are doing now | What the project should become |

**Use Spec Kit** for a one-shot feature; **use manifold** when the project outlives one feature.

## Don't conflate three "intent drifts"

Intent-Based Networking (telecom KPIs) and agent-safety goal drift are different lineages — cite them only for etymology. Manifold's lane is **spec ↔ code**: valid code, lost *why*.

## See also

- [Overview](overview.md) — the compass identity.
- [Checks](checks.md) — `spec-audit` and `drift-report` in practice.
