---
title: Plan Orchestrator
category: architecture
status: draft
summary: The contract-DAG multi-agent orchestration framework — a context-sharding engine using contracts as cut lines, with staged gates, verification-class-matches-error-class, and a cheap MCP progress store.
sources:
  - bundles/plan-orchestrator/skills/plan-orchestrator/design-notes.md
  - bundles/plan-orchestrator/skills/plan-orchestrator/SKILL.md
  - bundles/plan-orchestrator/skills/progress-tracker/README.md
related: [Orchestrator Boundary, Crucible, Decisions Ledger]
updated: 2026-07-20
---

# Plan Orchestrator

> **Status:** draft · **Consolidated from** design-notes.md (decisions 1–72), SKILL.md, progress-tracker README.

## Overview

<TODO: the skill as a "context-sharding engine using contracts as cut lines.">

## The five stages

<TODO: Spec / Framing / Planning / Implementation / Close-out; input contract +
overkill detector.>

## Verification toolbox

<TODO: verification-class-matches-error-class (Structural / Alignment / Judgment);
skeptic-for-omissions; four-condition automatic gate.>

## progress-tracker — why DB + MCP, not files

<TODO: cheap ORIENT-cycle status; one DB + one MCP contract beats per-agent
*.todo.md files (~900 lines of churn per dispatch).>

## Harness-fit caveats

<TODO: per-dispatch thinking not exposed; all-or-nothing parallel tool calls; $N hazard.>

## See also

- [Orchestrator boundary](manifold/orchestrator-boundary.md)
