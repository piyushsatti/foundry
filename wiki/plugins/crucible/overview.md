---
title: Crucible Overview
status: stable
summary: A lens × stance × model × effort review system built on one shared hat wardrobe.
sources:
  - bundles/crucible/README.md
updated: 2026-07-20
---

# Crucible Overview

**Crucible is a code/artifact review plugin where every reviewer is a tuple `(lens, stance, model, effort)` drawn from one shared hat wardrobe.** Four entry points compose preset tuples so a lens is defined once and consumed everywhere.

> **Status:** stable

## The reviewer tuple

A reviewer is fully described by four coordinates:

| Coordinate | What it sets | Values |
|------------|--------------|--------|
| **lens** | what the reviewer cares about | architect, security, frontend, … |
| **stance** | how it engages | `attack` · `verify` · `neutral` · `partner` |
| **model** | capability tier | pinned per stance agent |
| **effort** | reasoning budget | pinned per stance agent |

**The lens is defined once, in the shared wardrobe** — one file per professional lens — so no persona is re-described across skills. The wardrobe is a reference library (`skills/wardrobe/hats/HATS.md`), not itself invocable; its v1 roster is 14 hats (10 general-software, 4 agentic-infra).

## Entry points

**Each entry point composes wardrobe lenses into a preset stance topology:**

| Entry point | Stance | Job |
|-------------|--------|-----|
| `consult` | partner | One lens, in-thread conversational brainstorm/validate |
| `audit` | neutral | Neutral single reviewer over the shared wardrobe |
| `hats` | neutral | 3–4 distinct lenses, blind parallel panel, structured synthesis |
| `red-vs-blue` | attack + verify | Adversarial attack/verify pair + adjudicated verdict, gated by a worthiness check |

`consult` runs in-thread at the session model — no subagent, no pin (it is conversational by design). The other topologies dispatch **stance agents** (`red-attacker`, `blue-verifier`, `adjudicator`, `panelist`) that carry pinned model/effort.

## Model/effort pins are provisional

**Claude Code honors both `model:` and `effort:` in agent frontmatter, so the pins take effect** (verified 2026-07-05). What stays provisional is the chosen *values* — placeholders pending the **Phase 3 seeded-flaw benchmark**, which has not yet run. Whether the pins apply is settled; whether the values are optimal is not.

## See also

- [Methodology](methodology.md) — the D1–D17 evidence basis behind these design choices.
