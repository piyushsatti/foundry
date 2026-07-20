---
title: Decisions
status: stable
summary: The locked-decision ledger (L1–L34) — the authoritative "why we chose X".
sources:
  - docs/manifold/todo.md
updated: 2026-07-20
---

# Decisions

**The authoritative index of manifold's locked decisions — do not re-litigate without new evidence.** Each `L#` records a choice that shipped or is committed; `todo.md` holds the full ledger.

> **Status:** stable. Numbering runs L1–L34 (no L12); dates are 2026-06-06 or 2026-06-07.

## Checks and drift

| # | Decision |
|---|---|
| L1 | Split M3 revision audit and M4 spec↔code into separate commands |
| L2 | M3 command = `spec-audit` / MCP `spec_audit` |
| L3 | M4 command = `drift-report` / MCP `drift_report` (shipped v1) |
| L4 | `change_reason = pivot` (was misnamed `drift`); bootstrap migration |
| L5 | No deprecation shim — old M3 `drift-report` removed entirely |
| L13 | Require explicit `change_reason` on `update_node`; mechanical ops may auto-set |
| L16 | drift-report v1 = verdict rollup on realizations + flag unverified |
| L17 | drift-report v2 (LLM rationale match) deferred |

## Positioning and scope

| # | Decision |
|---|---|
| L6 | Glossary is canonical — when code/docs disagree, fix code/docs |
| L7 | Lead with operational nouns; "ADRs that talk to your agent" |
| L8 | Interop with Spec Kit, don't compete — importer deferred |
| L9 | Out of scope: new SDD CLI, autonomous agent, mem0/Zep memory |
| L10 | Palimpsest quarry (`harvest`, `render`, `restructure`) — separate track |
| L11 | Product version stays v0.1.0 until Pi tags for external compatibility |
| L14 | Topic C deferred — no auto AGENTS.md compile; hand-curate host files |
| L15 | Topic D deferred — no Spec Kit importer; convenience only |

## Portfolio and cross-project

| # | Decision |
|---|---|
| L18 | One DB, many projects — cross-team = cross-project, not cross-manifold |
| L19 | Portfolio project id `portfolio`; theme layer `theme` |
| L20 | Portfolio link = theme **tracks** a team node (`portfolio_links`), not an edge |
| L21 | Cross-project edge (`blocks` \| `depends_on`) — not called federation in v1 |
| L22 | Reserve federation (Palimpsest parent refs) for later |
| L23 | `node_ref` = `project_id/node_id` in APIs |
| L24 | CLI `portfolio-report` + `render portfolio --template quarter-roadmap` |
| L25 | MCP `list_cross_blocking_chain` (mirrors `list_blocking_chain`) |
| L26 | `portfolio_links` keyed by `theme_node_id`; themes in project `portfolio` |
| L27 | `render` scoped: v1 portfolio templates; layer render deferred |
| L28 | JSON key `blocked_by`: array of `node_ref` |
| L29 | Cross-edge CLI deferred — MCP-only v1 |
| L30 | MCP `peers_depends_on` / `target_blocks` = in-project edge write fields |

## Trajectory

| # | Decision |
|---|---|
| L31 | Topic J artifact = `trajectory` (one word); component = `leg` |
| L32 | Draft action = `propose` (CLI `trajectory propose`, MCP `propose_trajectory`) |
| L33 | Trust model: propose never mutates; only `accept` applies legs |
| L34 | `trajectory show` includes impact preview (plan→apply); real `next-leaves` is execution-only |

## See also

- [Checks](checks.md) · [Coordination](coordination.md) · [Trajectory](trajectory.md) — the decisions in context.
