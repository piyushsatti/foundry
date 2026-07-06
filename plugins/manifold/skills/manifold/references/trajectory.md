# Trajectory (Topic J)

Plan/apply workflow for spec evolution: draft a reviewable path from as-is to a **target brief**, preview impact, then **accept** to mutate the graph. Design: [`docs/manifold/archive/topics/trajectory.md`](../../../docs/manifold/archive/topics/trajectory.md). Nouns: [`docs/manifold/glossary.md`](../../../docs/manifold/glossary.md) § Trajectory.

---

## Trust model (L33)

| Action | Mutates graph? |
|---|---|
| **`propose`** / **`propose_trajectory`** | **No** — creates draft trajectory + pending legs |
| **`show`** / **`peek_trajectory`** | **No** — reads trajectory + computes **impact preview** |
| **`accept`** / **`accept_trajectory_leg`** | **Yes** — applies legs via normal write APIs |

Never chain `update_node` when the user gave a **target brief** — use trajectory instead.

---

## Plan / apply (L34)

```
target brief → propose → show (impact preview) → accept → next-leaves
```

- **Impact preview** simulates post-accept state (SAVEPOINT + rollback) — includes `next_leaves_after`, nodes touched, deltas.
- **Do not** call real `next-leaves` inside propose/show — that is execution-only after accept.

---

## Leg kinds (v1)

| `leg_kind` | Payload keys |
|---|---|
| `update_node` | `node_id`, `fields`, **`change_reason`** (required) |
| `create_node` | `layer`, `node_id`, `title`, optional body/parents/status |
| `transition_target` | `node_id`, `to_status` |

**Propose-time validation:** `transition_target` legs are checked against the target state machine at **propose** (not only at peek/accept). Invalid transitions (e.g. `planned→planned`, unknown status like `deferred`) fail immediately with `allowed: [...]`.

**Leg shape vs direct MCP calls:** each leg requires `node_id` (and `to_status` for transitions) **inside `payload`**, in addition to optional top-level `node_ref`. Trajectory apply injects `expected_revision_id` at accept time — leg payloads omit it (unlike direct `update_node` / `transition_target` calls).

---

## Worked leg examples (`legs.json`)

### `transition_target` — achieve a realization

```json
[
  {
    "leg_kind": "transition_target",
    "node_ref": "R.1",
    "payload": {
      "node_id": "R.1",
      "to_status": "achieved"
    }
  }
]
```

Valid `to_status` values depend on current status: from `planned` → `in_progress`, `achieved`, or `abandoned` (not `deferred` — that is not a status).

### `update_node` — wire a verdict check

```json
[
  {
    "leg_kind": "update_node",
    "node_ref": "R.1",
    "payload": {
      "node_id": "R.1",
      "change_reason": "evolution",
      "fields": {
        "verdict_mechanism": "automated_check",
        "verdict_check": "curl -sf http://127.0.0.1:8000/health | grep -q ok"
      }
    }
  }
]
```

No `expected_revision_id` in the leg — the engine reads current revision at accept.

### `create_node` — add a realization under intent

```json
[
  {
    "leg_kind": "create_node",
    "node_ref": "R.2",
    "payload": {
      "layer": "realizations",
      "node_id": "R.2",
      "title": "Structured request logging",
      "parents": ["I.1"],
      "target_status": "planned"
    }
  }
]
```

### Multi-leg trajectory (typical plan)

```json
[
  {
    "leg_kind": "update_node",
    "node_ref": "R.2",
    "payload": {
      "node_id": "R.2",
      "change_reason": "evolution",
      "fields": { "body": "Emit JSON log line per request." }
    }
  },
  {
    "leg_kind": "transition_target",
    "node_ref": "R.1",
    "payload": { "node_id": "R.1", "to_status": "achieved" }
  }
]
```

---

## CLI

```bash
# Propose from files (agent-friendly):
packages/manifold/scripts/manifold trajectory propose <project> \
  --target-brief-file brief.md --legs-file legs.json

# Show impact preview (markdown or json):
packages/manifold/scripts/manifold trajectory show <trajectory_id> --format md

# Apply all pending legs (or --leg-seq 1,2):
packages/manifold/scripts/manifold trajectory accept <trajectory_id>

# Discard a failed draft (no graph writes):
packages/manifold/scripts/manifold trajectory reject <trajectory_id>
```

---

## MCP

| Intent | Tool |
|---|---|
| Draft | `propose_trajectory` — `project_id`, `target_brief`, `legs[]`, `proposed_by` |
| Preview | `peek_trajectory` — `trajectory_id`, optional `leg_seqs` |
| Apply | `accept_trajectory_leg` — `trajectory_id`, `actor`, optional `leg_seqs` |
| Discard draft | `reject_trajectory` — `trajectory_id`, `actor` (draft only) |

---

## Web

- **HTML:** `GET /trajectories/<trajectory_id>` — markdown preview in page
- **API:** `GET /api/v1/trajectories/<id>`, `POST /api/v1/trajectories/propose`, `POST /api/v1/trajectories/<id>/accept`

---

## Anti-patterns

- Ad-hoc `update_node` chains when user stated a to-be target → use **propose**
- Running `next-leaves` during propose/show → use **impact preview** only
- Accepting without showing preview on multi-leg trajectories → always **show** first
- Skipping `change_reason` on `update_node` legs → validation fails at propose time

---

## After accept

1. Run real **`next-leaves`** to pick implementation work — should match preview if **all** pending legs were accepted in one pass.
2. Optional **`spec-audit`** if legs included rationale/evolution edits.
3. **`run_validation`** / **`drift-report`** if realization verdicts changed.

**Partial accept nuance:** impact preview simulates *all* pending legs. After accepting a subset, the real leaf set can differ from the last preview — preview only guaranteed to match when every pending leg is accepted together. Body-only legs that don't change `target_status` often match anyway; status transitions may not.
