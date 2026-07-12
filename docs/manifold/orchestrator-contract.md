# Manifold ↔ orchestrator contract (Topic F v1.1)

**Status:** contract for integrators — manifold ships MCP/CLI; **`dispatch-orchestrator`** skill (future) implements dispatch.

**Related:** [`glossary.md`](glossary.md) (intent-broker), [`business-model.md`](../../bundles/manifold/skills/manifold/references/business-model.md), Topics H+I (cross-project blocking), Topic J (trajectory).

---

## Roles

| Layer | Holds | Does not hold |
|---|---|---|
| **Manifold** | Spec graph, revision history, compass queries, verdicts, trajectories | Tickets, PRs, live agent runs |
| **dispatch-orchestrator** (future) | Dispatch, worktrees, task assignment, progress-tracker handoff | Canonical spec (reads manifold) |
| **plan-orchestrator** | Multi-phase contract DAG planning | Spec graph mutations (separate skill) |

Manifold is the **intent-broker** — orchestrators read before acting.

**Skill split (Phase 4):** routine compass + spec writeback stays in **`manifold`** skill. Running agents moves to **`dispatch-orchestrator`** when that skill ships (`requires: [manifold]` in manifest).

---

## Pre-dispatch checklist (dispatch-orchestrator)

Before assigning work on project `P`, node `N`:

1. **`peek_project(P)`** — confirm project exists, layer taxonomy, archived state.
2. **`next_leaves(P)`** — open frontier; pick a leaf from this list (or defer).
3. **`list_cross_blocking_chain(P, N)`** — if non-empty, **do not dispatch** until blockers are `achieved` (Topics H+I).
4. **`list_blocking_chain(P, N)`** — same for in-project `blocks` edges.
5. **`drift_report(P)`** — optional gate: skip or flag nodes with `violated` verdicts before new work lands on stale realizations.

For company-theme visibility (exec, not dispatch): **`portfolio_report`** — not required per leaf.

---

## Spec evolution vs dispatch (Topic J)

| User intent | Skill / surface | Notes |
|---|---|---|
| Target brief — evolve spec toward to-be | **manifold** → `propose_trajectory` → `peek_trajectory` → `accept_trajectory_leg` | Plan/apply; propose never mutates |
| Pick next implementation leaf | **manifold** → `next_leaves` | After trajectory accept, or ad-hoc frontier |
| Run agents on a leaf | **dispatch-orchestrator** (future) | Reads manifold; does not own spec |

Do not dispatch against nodes with open **`violated`** drift unless explicitly overriding — record rationale in spec if you do.

---

## During / after work (agent via MCP)

| Action | Manifold tool |
|---|---|
| Mark progress | `transition_target` → `in_progress` / `achieved` |
| Edit spec (single change) | `update_node` with required `change_reason` |
| Evolve spec (target brief) | `propose_trajectory` → `accept_trajectory_leg` |
| Record satisfaction | `run_validation` with `--with-verdicts` (or agent calls `run_validation`) |
| Batch graph edits | `with_batch` |

Agents write **`actor`** on every mutation (`agent:<dispatch-id>`).

**Writeback contract (future v1.1 detail):** idempotency keys, fencing tokens, structured verdict payloads — see orchestrator design track in [`todo.md`](todo.md).

---

## Multi-project setups (L18)

- One **`$MANIFOLD_DB`** shared across team projects and reserved **`portfolio`** project.
- Parallel worktrees / agents: same DB path via `$MANIFOLD_DB` — optimistic concurrency via `expected_revision_id`.
- Cross-team blocking: **`create_cross_edge`** + **`list_cross_blocking_chain`** — not Slack, not Jira link types.

---

## Deferred (not contract v1)

- **`delegate_to` → orchestrator task shape** translator (Palimpsest quarry)
- Auto-sync Jira epics to `portfolio_links`
- Example C external refs (CRM, shadow work)
- Manifest `manifold.suggests: [dispatch-orchestrator]` — wire when dispatch skill ships

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-06 | Initial stub; adds `list_cross_blocking_chain` to pre-dispatch checklist (Topics H+I) |
| 2026-06-07 | Phase 4: dispatch-orchestrator boundary, trajectory vs dispatch table, skill split |
