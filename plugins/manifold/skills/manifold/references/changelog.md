# Changelog

All notable changes to manifold. Product version is **v0.1.0** until Pi tags for external compatibility.

`schema_version` in the DB is separate from product version — currently **1**.

---

## v0.1.0 — ongoing  (2026-05-24 → present)

Pre-1.0: ship features freely; bump product version only when external users require compatibility discipline.

### 2026-06-07 — skill Phase 2: verdicts reference + drift ritual (S2)

- **`references/verdicts.md`** — four mechanisms, attach via `update_node`, `project_root` / `--repo`, drift buckets, dogfood bootstrap script.
- **`SKILL.md`** — `## Drift-report ritual` (exit 1 = violated only; always pass repo root).
- **`references/rituals.md`** — step 2 links verdicts + `--repo` requirement.
- Eval #6 — drift report on manifold dogfood with repo path.

### 2026-06-06 — naming honesty + spec-audit + drift-report v1

Landscape research checkpoint. No git tag (L11).

#### Naming split (Topic A)

- **`spec-audit`** / MCP `spec_audit` / HTTP `/spec-audit` — M3 revision discipline (was misnamed `drift-report`).
- **`drift-report`** — M3 name reclaimed for M4 spec↔code; reserved at Topic A, **shipped Topic E v1** (see below).
- `change_reason = pivot` (was `drift`); bootstrap migration on DB open.
- **No deprecation shim** — old M3 `drift-report` command removed.

#### Strict revision discipline (D2)

- **`change_reason` required** on every `update_node` — no silent default to `evolution`.
- CLI `edit` requires `--reason`. Web edit form includes `change_reason` dropdown.
- Mechanical writes (`transition_target`, `revert`, delete/restore) auto-set implicit reasons.

#### Docs

- [`docs/manifold/glossary.md`](../../docs/manifold/glossary.md) — canonical proper nouns.
- [`docs/manifold/todo.md`](../../docs/manifold/todo.md) — master checklist.
- [`docs/manifold/how-to-use.md`](../../docs/manifold/how-to-use.md) — chat-first usage guide.

#### Topic E v1 — drift-report (2026-06-06)

- **`drift-report`** / MCP `drift_report` / HTTP `/drift-report` — M4 spec↔code report on realization layer.
- v1: violated verdicts + unverified realizations (no `verdict_mechanism`); reuses `validate.run_verdicts` without persisting a validation row.
- CLI: `--format md`, `--force`, `--repo`; exits 1 on violated.
- Positioning clause ("when code diverges") is factual for projects with verdicts wired. v2 LLM rationale match (L17) deferred.

### 2026-05-24 — first release

Shipped as `manifold-v0.1.0` tag.

#### Headline

manifold is a **project compass**: it answers four questions for any project — what is this project (root), where are we now (current state), where do we go next (next leaves), and have we drifted from prior intent (drift detection). Built on the KAOS goal-oriented requirements engineering formalism with AND/OR DAG across layers.

#### Substrate

- **AND/OR DAG across layers** (KAOS formalism). Multi-parent nodes are first-class. Primary citation: Darimont & van Lamsweerde 1996 §2 — *"The goal refinement structure for a given system can be represented by an AND/OR directed acyclic graph."* Algorithmic lineage: Martelli & Montanari 1973.
- **Boolean satisfaction with upstream propagation** — parent satisfied iff all children satisfied. Failure invalidates parents.
- **Constraint nodes** (`kind: constraint`) — apply rather than decompose. Skip the coverage rule.
- **Cycles forbidden** (acyclic mandatory).
- **Coverage rule** — every non-leaf has ≥1 child.
- **Three surfaces**: CLI, MCP, HTTP, all sharing one Python query/write layer.

#### Compass

- Default `target_status="planned"` on node creation. Advisory warning when unset.
- `manifold next-leaves <project> [--layer X]` — leaves ready to realize. CLI + HTTP + MCP.
- Project framing in README + ARCHITECTURE leads with the compass questions.

#### Anti-drift

- `node.rationale` (why this node exists), `node.alternatives_considered` (what was rejected and why).
- `revision.change_reason` — enum: correction / evolution / clarification / refactor / drift / other. Stored per revision.
- `manifold drift-report <project> [--since DATE]` — lists revisions tagged drift/other/unset and rationale changes without clarification. CLI + HTTP + MCP.
- HTML node detail shows rationale prominently; revision timeline shows change_reason badges.

#### Schema

- SQLite at `~/.claude/manifold.db` by default. WAL mode. `schema_version=2` in `schema_meta`.
- Schema bootstrap is idempotent (safe to re-run).
- Lossless NDJSON dump + restore. `VACUUM INTO` snapshots.

#### CLI

- `manifold version` — print version, schema, install path, db path
- `manifold import <repo>` — import a markdown spec tree into the DB (idempotent via git log)
- `manifold show <project> [node]` — markdown view
- `manifold edit <project> <node>` — edit body in `$EDITOR`
- `manifold validate <project>` — run structural + verdict checks
- `manifold next-leaves <project>` — leaves ready to realize
- `manifold drift-report <project>` — drift surfacing
- `manifold serve [--pidfile]` — start HTTP + HTML UI on 127.0.0.1
- `manifold status` — runtime check
- `manifold config <path|show|init>` — machine-local config (`~/.claude/manifold.json`): three-tier resolution (env > file > default)
- `manifold export <project> <dir>` — write DB state as markdown tree (round-trippable)
- `manifold snapshot` / `dump` / `restore` — backup tools

#### What's deferred

- Qualitative aggregation (NFR/SIG-style Make/Help/Hurt/Break labels)
- Weighted priority on `next-leaves`
- Positional scalars beyond raw counts
- Multi-actor models (iStar-style actor dependencies) — decision deferred
- OR-refinement (KAOS feature; additive when needed)
- Obstacle analysis (KAOS feature)
- Orchestrator integration (consumer of `next-leaves`) — separate `orchestrator` skill, currently alpha (design only)

#### Stats

- 449 unit + smoke tests.
- v0.2-style spec trees import cleanly (git-log replay).
- Round-trip verified (export → fresh import → identical node set + bodies + edges).
- Web UI feature-complete for the compass framing.
