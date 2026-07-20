---
title: Meditate Overview
status: stable
summary: Reflective memory curation — the curate → review → apply pipeline on three separated parties.
sources:
  - bundles/meditate/README.md
updated: 2026-07-20
---

# Meditate Overview

**Meditate is terraform for memory** — a `plan → show → apply` pipeline that keeps an agent's accreting memory (CLAUDE.md rules, recalled facts, serena code notes) from rotting into staleness, duplication, and mis-scoped leaks.

> **Status:** stable

## The pipeline

Three commands, mirroring terraform's `plan / show / apply`:

| Command | Role | What it does |
|---------|------|--------------|
| `/meditate:curate` | **plan** | Dispatches a read-only Opus curator over opted-in stores; classifies every item, checks destinations for collisions, and emits a YAML *manifest* of proposals to disk. |
| `/meditate:review` | **show** | Renders a pending manifest read-only: disposition table, destructive-op flags, an explicit `⚠ CLAUDE.md changes` line, needs-human questions. |
| *(you edit the manifest)* | **gate** | Approve by leaving a block, reject by deleting it, modify by editing any `proposed:` field. Nothing self-executes. |
| `/meditate:apply` | **apply** | A dumb executor: re-verifies a per-item sha256 lock, then runs exactly what each approved block says. |

```mermaid
graph LR
  A[curate<br/>read-only proposer] --> B[manifest on disk]
  B --> C[review<br/>show + flag]
  C --> D[you<br/>human gate]
  D --> E[apply<br/>dumb executor]
```

## Three separated parties

Meditate's core safety bet is that **propose, approve, and execute are three different parties with different privileges** — never one write-path judge:

- **Read-only proposer.** The curator's tool grant has no Write, no Edit, no Bash. It cannot mutate a store — it can only emit proposals.
- **Human gate.** Every mutation is approved by a person. The field's center of gravity is fully-automated curation; meditate deliberately is not, because standing instructions steer every future session.
- **Dumb applier.** Makes no semantic decisions. It executes the human-approved manifest verbatim.

## Load-bearing invariants

- **Archive-never-delete.** Every destructive verb archives a pre-image first and leaves a tombstone with a back-pointer. Reversibility is a system property, not a user habit.
- **sha256 optimistic locks.** A per-item hash captured at curation is re-verified at apply; if a file changed since, that item is skipped, not clobbered.
- **One verb per item.** No candidate may reference a path another candidate creates or destroys — what makes an order-free applier possible.
- **Conservative defaults.** Over-promotion is the cardinal sin; unsure → keep separate, unsure → `specific`. A zero-finding sweep is a success.

## See also

- [Memory model](memory-model.md) — the two-axis scope × genericity model and three stores.
- [Operation algebra](operation-algebra.md) — the verbs as a conserved algebra over a knowledge grid.
- [Execution contract](execution-contract.md) — the dumb-applier spec and frozen interface.
- [Decisions](decisions.md) — verified environment findings and locked decisions.
