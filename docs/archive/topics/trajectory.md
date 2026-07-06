# Topic J — Trajectory (as-is → to-be)

> **Superseded — trajectory shipped v1 (Topic J). Original design snapshot; see [../../manifold/glossary.md](../../manifold/glossary.md) for current state.**

**Status:** nouns locked (L31–L34, 2026-06-07). Not shipped.

**Related:** [`glossary.md`](../../manifold/glossary.md) § Trajectory, [`todo.md`](../../manifold/todo.md).

---

## Problem

Current graph vs **target brief**. No first-class **propose → preview → accept** toward a target.

---

## Locked nouns (L31–L34)

| ID | Noun | Meaning | Surface |
|---|---|---|---|
| **L31** | **trajectory** | Draft proposal: ordered **legs** + target brief | DB `trajectories`, `trajectory show` |
| **L32** | **propose** | Create draft — no graph writes | **`trajectory propose`**, MCP **`propose_trajectory`** |
| **L33** | *(trust)* | Only **accept** mutates graph | `trajectory accept`, `accept_trajectory_leg` |
| **L34** | **impact preview** | Simulated post-accept state on **show** — Terraform **plan** before **apply** | JSON on `trajectory show`; web diff panel |

**Component:** **`leg`** — one proposed change.

**Input:** **`target brief`** — markdown to-be description.

---

## Workflow (locked) — plan / apply

```text
SPEC EVOLUTION (trajectory)              EXECUTION (separate)
────────────────────────────             ────────────────────
target brief
  → propose          draft trajectory
  → show             legs + impact preview   ← like terraform plan
  → accept           merge to graph          ← like terraform apply

                                           → next-leaves (real)
                                           → validate / code / orchestrator
```

**`next-leaves` is NOT step 4 of trajectory.** After **accept**, the graph is real; you call **`next-leaves`** when starting implementation (L34).

---

## Impact preview (L34)

**`trajectory show`** returns leg diff **plus** simulated impact if all (or selected) legs were accepted — **without writing**.

| Preview field | Meaning |
|---|---|
| `legs[]` | Each leg: kind, node_ref, payload summary, `change_reason` |
| **`next_leaves_after`** | What **`next-leaves`** would return post-accept (simulated) |
| **`next_leaves_removed`** | Leaves that would drop off (superseded / blocked) |
| **`portfolio_delta`** | Optional: theme roll-up changes |
| **`blocked_by_delta`** | Cross-project blocker changes |
| **`nodes_touched`** | Count / list for review |

Implementation sketch: apply legs to an in-memory graph snapshot (or SQL transaction rolled back) and run existing `next_leaves` query — no persistence until **accept**.

**CLI:** `manifold trajectory show tr-a7f2 --format md` prints human plan.

**Web:** side-by-side “current graph” vs “after accept” + highlighted leaves.

---

## Worked example (impact preview)

**Draft `tr-a7f2`** — legs 1–3 accepted if user confirms; leg 4 pending.

**`trajectory show tr-a7f2`** (excerpt):

```markdown
# Trajectory tr-a7f2 (draft) — impact preview

## Legs (4 pending)
…

## Impact preview (if legs 1–3 accepted)
next_leaves_after:
  R.8   realizations   planned   Bedrock inference deployment
  C.7   contracts      planned   Model API on AWS Bedrock

next_leaves_removed:
  R.5   (superseded by trajectory leg 2→3 chain)

portfolio_delta:
  T.2 tracks I.1 → target_status in_progress (was achieved)

blocked_by_delta:
  (leg 4 not in preview — not selected)
```

User runs **`trajectory accept tr-a7f2 --legs 1,2,3`**. Graph updates.

**Later (implementation):** `manifold next-leaves ai-platform` — real query, should match preview if legs 1–3 were accepted as simulated.

---

## Scope (implementation — not started)

J1 schema + manual legs + impact preview engine · J2 MCP/CLI · J3 web inbox · J4 LLM propose · J5 T4.5 · J6 restructure legs.

---

## Data model (sketch)

```sql
CREATE TABLE trajectories (
  trajectory_id   TEXT PRIMARY KEY,
  project_id      TEXT NOT NULL,
  status          TEXT NOT NULL,
  target_brief    TEXT NOT NULL,
  scope_json      TEXT,
  proposed_by     TEXT NOT NULL,
  created_at      TEXT NOT NULL,
  resolved_at     TEXT
);

CREATE TABLE trajectory_legs (
  leg_id          TEXT PRIMARY KEY,
  trajectory_id   TEXT NOT NULL,
  seq             INTEGER NOT NULL,
  leg_kind        TEXT NOT NULL,
  node_ref        TEXT,
  payload_json    TEXT NOT NULL,
  status          TEXT NOT NULL,
  applied_revision_id INTEGER
);
```

Impact preview is **computed at show time** — not stored (recompute if graph drifted since propose).

---

## Surfaces (v1 target)

| Surface | Name |
|---|---|
| CLI | `trajectory propose`, **`trajectory show`** (plan + impact preview), `trajectory accept` |
| MCP | `propose_trajectory`, **`peek_trajectory`** (includes impact preview), `accept_trajectory_leg` |
| Web | Plan/apply UI: preview panel → accept button |

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-07 | L31–L33: trajectory, propose, accept trust model |
| 2026-06-07 | **L34:** impact preview on show; next-leaves execution-only; Terraform plan/apply analogy |
