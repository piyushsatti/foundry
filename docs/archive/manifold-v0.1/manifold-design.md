# manifold v0.1 — KAOS + DAG + Anti-Drift

> Design doc. Date: 2026-05-24. Single-author project; user is sole consumer.
>
> Decisions in this doc were settled in the brainstorming conversation immediately preceding this file. The lineage analysis is in [kaos-lineage.md](../../manifold/kaos-lineage.md).

## Goals

manifold v0.1 commits to three things at once:

1. **Structural lineage** — adopt KAOS as the formal home for manifold's primitive (AND-decomposition over Boolean satisfaction with layered abstraction). Relax strict-tree-across-layers to AND/OR DAG, matching KAOS's formal definition verbatim.
2. **Compass minimum** — make `target_status` a first-class authoring concern (default to `planned` on creation; advisory warning on `""`); expose `next-leaves` as the orchestrator's handoff surface.
3. **Anti-drift** — add `rationale` + `alternatives_considered` + structured `change_reason` so the spec survives six-month memory decay; add a `drift-report` mode that surfaces undocumented changes.

These three commitments are clubbed into one release because they share substrate work (schema migrations, validator updates, docs) and ship together as the "manifold becomes a compass" turn.

## What this release is NOT

Deferred to v0.5 (also clubbed): qualitative aggregation (NFR/SIG-style `Make/Help/Hurt/Break` labels), positional scalars beyond raw counts, weighted priority on `next-leaves`, multi-actor models (iStar-style actor dependencies OR orchestrator-owned), OR-refinement, obstacle analysis, refinement-pattern catalog.

All of these are *additive on top of KAOS* and don't require revisiting v0.1 substrate. The lineage decision in v0.4 makes them straightforward to layer in later.

## 1. Lineage

Citation hierarchy:

- **Primary:** Darimont, R. & van Lamsweerde, A. (1996). "Formal Refinement Patterns for Goal-Driven Requirements Elaboration." SIGSOFT FSE-4. §2: *"The goal refinement structure for a given system can be represented by an AND/OR directed acyclic graph."* This is the formalism manifold inherits verbatim.
- **Algorithmic:** Martelli, A. & Montanari, U. (1973). "Additive AND/OR Graphs." IJCAI. The pre-Wikipedia source for shared subproblems in problem-reduction.
- **Textbook:** van Lamsweerde, A. (2009). *Requirements Engineering: From System Goals to UML Models to Software Specifications.* Wiley. Canonical KAOS reference.

What manifold inherits from KAOS:
- AND-refinement (Boolean conjunction over children); maps to manifold's existing `verdict_status` propagation.
- AND/OR DAG across layers; replaces strict tree.
- Cycle prohibition (acyclic mandatory); already present.
- Coverage rule (every non-leaf has ≥1 child); already present.
- Constraint goals (apply rather than decompose); already present as `kind: constraint`.
- Layered abstraction (project-defined layers); already present.

What manifold deliberately leaves behind:
- KAOS's LTL semantics → replaced by manifold's pluggable verdict mechanisms (`automated_check`, `python_assertion`, `human_signoff`, `llm_judge`). Software-flavored LTL doesn't generalize to non-software domains; pluggable mechanisms do.
- KAOS's agent assignment → punted to orchestrator. Manifold stays agent-agnostic at the spec level.
- KAOS's operations layer → punted to orchestrator.

What manifold defers but acknowledges (v0.5+):
- OR-refinement, obstacles, refinement patterns, conflict detection.

## 2. Structural change: strict tree → AND/OR DAG

### What changes

v0.3 enforced that every node has at most one parent across layers. v0.4 allows multiple parents. The structure becomes an AND/OR directed acyclic graph (KAOS's formal definition).

Concretely:
- `node_edges` table already supports multiple `edge_kind='parent'` edges from one src to many dst. No schema change.
- The validator's `check_tree_property` enforces single-parent today. Rename to `check_dag_property` and drop the single-parent invariant. Keep cycle prohibition and layer ordering.
- Propagation already walks parents in `propagate_failures`. Needs verification that multi-parent works correctly (a failing child invalidates ALL its parents).

### What stays the same

- Intra-layer: strict DAG (cycles forbidden within a layer). Unchanged.
- Cross-layer acyclicity: enforced as before. Multi-parent is allowed; multi-parent cycles are not.
- Coverage rule: every non-leaf has ≥1 child. Unchanged.
- Layer membership: a node's `layer` value must match a layer declared in `spec.yaml`. Unchanged.

### `realized_by_external` becomes redundant

The `realized_by_external` field was the v0.3 escape hatch for "this node is realized at a node elsewhere in the tree." With multi-parent allowed, the same effect is achieved by giving the node multiple parents directly.

Plan: keep the column for backwards compatibility (existing specs that use it stay valid), but downgrade its semantic to **purely informational**:
- It no longer affects validation or propagation in v0.4.
- It serves as a documentation hint: "this node's canonical home for editing purposes is X."
- Deprecation warning emitted when used.
- Removed entirely in v0.5 or later if no one is using it.

### Render mode: primary-parent convention

Strict tree gave us free single-narrative rendering for `render --layer X` (manifold's "book at different bolding levels" view). DAG-rendered-as-book needs a rule.

Adopt: **first entry in `parents` is the primary parent for narrative rendering.** Other parents surface as cross-reference annotations.

- Single-parent nodes: behavior unchanged.
- Multi-parent nodes: appear once in the narrative (under their primary parent); a margin note ("also satisfies: P2, P3") cross-references their other parents.
- Web UI: node detail page shows ALL parents; the primary is visually distinguished.
- Authoring convention: when adding a multi-parent node, put the "main" parent first.

## 3. Compass minimum

### Default `target_status="planned"` on creation

`writes.create_node` currently leaves `target_status` empty unless explicitly set. v0.4 defaults to `"planned"`.

Backwards compatibility: existing rows with `target_status=""` are unaffected by this change. They become a defect-class (see advisory warning below) but continue to be valid storage.

### Advisory validator warning

`validate.check_targets` currently validates the state machine for non-empty `target_status` values. v0.4 adds:
- For each non-constraint node with `target_status=""`: emit an ADVISORY finding (`severity: advisory`, distinct from `severity: error`).
- Advisory findings are reported but do not fail validation.
- This nudges spec authors toward setting state without breaking projects that ignore it.

### `next-leaves` query

A leaf node is one with no children (computed via `node_edges`).

A node is **ready to realize** when:
- It is a leaf, AND
- Its `target_status` is in `{planned, in_progress, ""}` (`""` is included as implicit-planned; the advisory warning has already flagged it), AND
- It has not been soft-deleted

Note: we deliberately do NOT require "all parents achieved." The user's intent is to surface what *could* be worked on; the orchestrator decides whether parent-state matters. Manifold's job is to expose the list; the orchestrator's job is to pick from it.

API surfaces:
- **Python:** `queries.next_leaves(conn, project_id, layer=None)` → list of node dicts. Optional `layer` filter narrows to a specific layer.
- **CLI:** `manifold next-leaves <project> [--layer <name>]` → text table.
- **HTTP:** `GET /api/v1/projects/<id>/next-leaves[?layer=<name>]` → JSON.
- **MCP:** tool `manifold__next_leaves` with `project_id` (required) and `layer` (optional).

Output shape per leaf (JSON):
```json
{
  "node_id": "R.K9",
  "layer": "realizations",
  "title": "cli.py operator commands",
  "target_status": "planned",
  "verdict_status": "unknown",
  "verdict_mechanism": "automated_check",
  "parents": ["K.9"],
  "rationale": "..."
}
```

## 4. Anti-drift: rationale + alternatives + change_reason

### Schema additions

```sql
ALTER TABLE nodes ADD COLUMN rationale TEXT;
ALTER TABLE nodes ADD COLUMN alternatives_considered TEXT;
ALTER TABLE revisions ADD COLUMN change_reason TEXT;
```

All three columns are nullable; no data migration required for existing rows.

Update `schema_meta.schema_version` from 1 to 2. `db.bootstrap` detects the version mismatch and applies the ALTERs idempotently.

### `node.rationale` and `node.alternatives_considered`

Two prose fields on every node:
- **rationale**: short prose answering "why does this node exist?" — the problem it solves, the reason for its inclusion.
- **alternatives_considered**: short prose answering "what was considered and rejected, and why?" — the design decisions encoded in choosing THIS over alternatives.

Both are optional but advised. The validator emits an advisory warning if a non-constraint node lacks rationale.

`writes.create_node` and `writes.update_node` accept these as kwargs. They are stored on the node row AND captured in the revision snapshot.

### `revision.change_reason` enum

Every revision now carries a `change_reason` from this enum:
- `correction` — fixing a mistake (the prior revision was wrong)
- `evolution` — the world changed; the spec catches up
- `clarification` — the meaning was unclear; this revision makes it clearer (no semantic change)
- `refactor` — restructuring without intent change (rename, re-parent, split, merge)
- `drift` — author acknowledges this is a deviation from prior intent and is making it deliberately
- `other` — escape hatch with a required free-text justification in `change_summary`

`writes.update_node` accepts `change_reason` as a kwarg. Defaults to `evolution` if not provided (with an advisory warning).

### Render: rationale and alternatives in HTML

Node detail page (`/projects/<p>/nodes/<n>`):
- Above the body, a collapsible "Rationale" section with rationale + alternatives_considered.
- Revision timeline shows `change_reason` next to each revision.

Render mode (`render --layer X`): includes rationale as a footnote per node.

### `drift-report` mode

A new mode for surfacing potential drift:

CLI: `manifold drift-report <project> [--since <ISO-date>] [--include-other]`

Reports:
- All revisions with `change_reason=drift` (deliberate deviations — these are flagged for review)
- All revisions with `change_reason=other` (unless `--include-other` is false)
- All revisions with no `change_reason` set (advisory; old revisions from v0.3 era)
- Nodes whose rationale field has changed since `--since` without an accompanying revision of type `clarification` or `correction`

Output format:
- CLI: text table
- HTTP: HTML view at `/projects/<p>/drift-report?since=<date>`
- MCP: tool `manifold__drift_report`

## 5. Migration story

### Schema migration

On startup, `db.bootstrap` checks `schema_meta.schema_version`:
- If `1`: apply v0.4 ALTERs, update version to `2`.
- If `2`: no-op.
- If unknown: error.

The migration is idempotent (uses `ALTER TABLE ... ADD COLUMN` which fails gracefully if the column exists; wrapped in try/except for safety).

### Data backfill for existing 3 projects

Existing rows have `target_status=""` and `change_reason=""` and lack rationale/alternatives. We backfill:

**Script:** `scripts/v04-backfill.py` (one-off; lives in skills/manifold/scripts/ for traceability).

For each node with `target_status=""`:
- If `verdict_status="satisfied"`: set `target_status="achieved"` (the verdict cleared so it logically achieved)
- Else: set `target_status="planned"`

For each revision with `change_reason=""`:
- Set `change_reason="evolution"` and add a one-line note in `change_summary` indicating "(backfilled in v0.4 migration)"

rationale and alternatives_considered are NOT backfilled. They remain NULL for existing nodes. Authors fill them in over time as nodes are edited.

The backfill script writes to a fresh DB copy first, then the user reviews the copy before applying to the live DB. Procedure documented in `MIGRATION.md`.

## 6. What documents change

- `skills/manifold/README.md` — leads with the compass framing; cites KAOS as primary lineage.
- `skills/manifold/ARCHITECTURE.md` — adds KAOS citation; documents DAG-across-layers + rationale/alternatives + change_reason.
- `skills/manifold/USER.md` — adds CLI examples for `next-leaves` and `drift-report`; documents rationale/alternatives authoring; documents change_reason values.
- `skills/manifold/MIGRATION.md` — new file; development → v0.4 migration steps including backfill procedure.

## 7. Open questions

None. All decisions are made.

## 8. Acceptance criteria for v0.4

- All existing tests (300+) continue to pass after migration.
- DAG migration: multi-parent specs validate and propagate correctly. Add unit tests for shared-evidence pattern (research-paper-style).
- Compass minimum: `next-leaves` returns expected output on all 3 self-spec projects after backfill.
- Anti-drift: new fields round-trip through writes and reads; drift-report identifies the seeded drift revision in test fixtures.
- Backfill: re-running backfill is idempotent; produces expected target_status assignments for all 81 existing nodes.
- Docs: README's compass framing is the first thing a new reader sees; KAOS citation appears in ARCHITECTURE.md within the first 3 paragraphs.

## 9. Parallelization strategy (for the plan)

Three independent streams in Wave 1:
- **Stream A — DAG substrate:** validator + propagation + render
- **Stream B — Compass minimum:** defaults + advisory + next-leaves API
- **Stream C — Anti-drift:** schema migration + writes API + drift-report

Then Wave 2 (docs + backfill) depends on Wave 1.

See `manifold-v0.1-plan.md` for task-level decomposition.
