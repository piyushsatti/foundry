# Orchestrator Boundary

**Manifold holds intent; something else holds execution.** Manifold is the intent-broker — orchestrators read the spec graph before acting and write verdicts back, but manifold never dispatches agents.

> **Status:** draft — the `dispatch-orchestrator` skill is unbuilt; this is the contract it will implement.

## Roles

| Layer | Holds | Does not hold |
|---|---|---|
| **manifold** | Spec graph, revisions, compass queries, verdicts, trajectories | Tickets, PRs, live agent runs |
| **dispatch-orchestrator** (future) | Dispatch, worktrees, task assignment | Canonical spec (reads manifold) |

Routine compass and spec writeback stay in the `manifold` skill; running agents moves to `dispatch-orchestrator` when it ships.

## Pre-dispatch checklist

Before assigning work on project `P`, node `N`, the orchestrator should:

1. **`peek_project(P)`** — confirm project, layers, archived state.
2. **`next_leaves(P)`** — pick a leaf from the open frontier (or defer).
3. **`list_cross_blocking_chain(P, N)`** — if non-empty, do not dispatch until blockers are `achieved`.
4. **`list_blocking_chain(P, N)`** — same for in-project `blocks` edges.
5. **`drift_report(P)`** — optional gate; flag `violated` realizations before new work lands on stale code.

Spec evolution (a target brief) goes through [trajectory](trajectory) — propose/show/accept — not raw dispatch. Agents write `actor` (`agent:<dispatch-id>`) on every mutation.

## Agent handoff pattern

At session end an agent produces a structured handoff — validated on a real transcript — that makes "what got done" substantive and honest:

- **`narrative_handoff`** — a short structured message: branch state, key wins with concrete numbers, where-to-look pointers.
- **`deliberately_not_done[]`** — a negative-space catalog, each entry with `attributed_to: human | agent`. This is attribution-as-honesty: the agent's evidence that it did not make unilateral calls.
- **`handoff_doc_path`** — optional longer in-repo doc for deep debugging.

Downstream: `deliberately_not_done` entries attributed to a human become individual `change_reason=evolution` writebacks, so explicit defers are traced. Vacuous handoffs (a claimed `achieved` with an empty narrative) auto-downgrade to `needs_review`.

## See also

- [Coordination](coordination) — cross-project blocking the checklist relies on.
- [Trajectory](trajectory) — spec evolution vs dispatch.
