---
title: Roadmap
status: draft
summary: What we want to build — the cleanup epic, the approved buildout, and parked/shelved ideas.
sources:
  - CLAUDE.md
  - docs/access-tier-roadmap.md
updated: 2026-07-20
---

# Roadmap

**Forward work, in one place.** GitHub issues are canonical for the epic; this is the durable narrative index. Parked/shelved ideas each get their own page here.

> **Status:** draft

## Cleanup & initialization epic (Issue #1)

Post-restructure debt. Sub-issues, each self-contained:

| # | Item |
|---|------|
| #2 | License-clean replacements for 3 vendor skills (grill-with-docs priority) |
| #3 | Hooks overhaul — review, wire, productize 33 unwired `home/hooks` |
| #4 | Per-bundle manifest fragments (kill the flat cross-bundle registry) |
| #5 | Cartographer — revive or archive the parked bundle |
| #6 | Vendor skill licenses — capture before continued redistribution |
| #7 | Crucible eval debt — adjudicator benchmark + harder corpus v2 |
| #8 | os-doctor — decide fate (delete / move / keep) |

## Approved buildout

A 7-item buildout is approved, sequence **0→1→3→6→2→5→4**, one session per item, Pi initiates each. Detail lives in `.gitignored/plans/buildout-2026-07/` (local scratch, not committed).

## Parked / shelved

- **[Session Message Bus](session-message-bus.md)** — shelved 2026-07-18.
- **[Cartographer](../cartographer/overview.md)** — parked, Phase 1.
- **Access-tier roadmap** — guard-capability wishlist (read-only `/mnt`, SSH copy-then-read), none implemented. See `docs/access-tier-roadmap.md`.

## See also

- [Distribution](../distribution/overview.md) · [Glossary](../glossary.md)
