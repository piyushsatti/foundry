# manifold — Architecture

For users who want to extend the system, audit the schema, or understand why things are the way they are.

For setup and CLI usage, read [`USER.md`](USER.md) instead.

---

## Theoretical foundations

manifold's primitive is the AND-refinement over Boolean satisfaction with layered abstraction. This places it squarely in the KAOS goal-oriented requirements engineering tradition.

**Primary citation:** Darimont, R. & van Lamsweerde, A. (1996). "Formal Refinement Patterns for Goal-Driven Requirements Elaboration." SIGSOFT FSE-4. §2: *"The goal refinement structure for a given system can be represented by an AND/OR directed acyclic graph."* manifold inherits this definition verbatim. The `node_edges` table stores the DAG edges; the validator enforces acyclicity and layer ordering; propagation walks the parent–child relationships to compute satisfaction bottom-up.

**Algorithmic lineage:** Martelli, A. & Montanari, U. (1973). "Additive AND/OR Graphs." IJCAI. Pre-Wikipedia source for shared-subproblem reduction — the intellectual precedent for treating a node with multiple parents as contributing to all of them simultaneously. This is the formal basis for manifold's multi-parent propagation rule: a failing child invalidates all of its parents, not just the primary one.

**Textbook reference:** van Lamsweerde, A. (2009). *Requirements Engineering: From System Goals to UML Models to Software Specifications.* Wiley. Canonical KAOS textbook; comprehensive treatment of goal elaboration, obstacle analysis, and agent assignment.

### What manifold inherits from KAOS

- **AND-refinement:** Boolean conjunction over children. A goal is satisfied only when all of its refinements are satisfied. This maps directly to manifold's `verdict_status` propagation: `propagate_failures` walks parent edges to fixed point; any violated child invalidates all ancestors.
- **AND/OR DAG across layers:** manifold uses an AND/OR DAG matching KAOS's formal definition — a node may have multiple parents across layers. `check_dag_property` enforces it; cycle prohibition and layer ordering are preserved.
- **Cycle prohibition:** Acyclicity is mandatory in both intra-layer (within a layer, `peers_depends_on` must be acyclic) and cross-layer directions.
- **Coverage rule:** Every non-leaf, non-constraint node must have at least one child at the next layer.
- **Constraint goals:** Nodes with `kind: constraint` apply to the system rather than decomposing further.
- **Layered abstraction:** Project-defined layers (intent, capabilities, contracts, realizations, or any user-specified set). Already present; unchanged.

### What manifold deliberately leaves behind

- **KAOS's LTL semantics:** KAOS uses Linear Temporal Logic to express goals formally. manifold replaces LTL with pluggable verdict mechanisms (`automated_check`, `python_assertion`, `human_signoff`, `llm_judge`). Software-flavored LTL does not generalize to non-software domains; pluggable mechanisms do.
- **KAOS's agent assignment:** In KAOS, goals are assigned to agents (software components or human roles). manifold stays agent-agnostic at the spec level; agent assignment is the orchestrator's responsibility, not the spec's.
- **KAOS's operations layer:** Manifold does not model system operations or domain properties. The bottom layer of a manifold spec is whatever the author calls it (commonly "realizations"); the spec ends there.

### What manifold defers to v0.2+

OR-refinement (a goal is satisfied when any one of its refinements is satisfied), obstacle analysis, refinement-pattern catalog, conflict detection. These are additive on top of the KAOS substrate and do not require revisiting the core data model.

---

## TL;DR

- **Substrate**: one SQLite database (`~/.claude/manifold.db`).
- **Three surfaces** sharing one Python query layer:
  - **CLI** (`scripts/manifold` + `manifold/cli.py`) — humans, shell scripts.
  - **MCP server** (`manifold/mcp_server.py`) — agents over stdio JSON-RPC.
  - **HTTP** (`manifold/web.py` + `manifold/html.py`) — browser-based editing.
- **Stdlib only.** No pyyaml, no requests, no SQLAlchemy.
- **Append-only history.** Every write creates a `revisions` row.
- **Optimistic concurrency.** Every write requires `expected_revision_id`.
- **Config resolution**: `env var > config file (~/.claude/manifold.json) > built-in default`.
  The file is read at most once per process and cached. `manifold/config.py` owns this logic.

---

## Why DB-canonical?

An earlier file-based design stored specs as markdown files. The obvious next step — "markdown files + a cache DB on top" — was rejected: it introduces drift between two sources of truth (files vs DB) and a sync discipline nobody wanted to maintain. So manifold inverts it: the DB is the spec. Markdown files become an *export* format, not the working surface.

Tradeoffs:
- ✅ One source of truth. No drift question.
- ✅ Cross-project queries are SQL, not file walks.
- ✅ History is structural, not "did I remember to commit."
- ✅ Tools build against a typed schema, not regex over frontmatter.
- ❌ Loses "spec lives in git as markdown" — that was real for human review.
- ❌ Loses zero-tool readability — to view a spec, you need manifold.

Mitigation: `manifold dump` produces a lossless NDJSON portable format; `manifold export` produces a human-readable markdown tree for git-friendly archival. Files become an *exportable* artifact rather than the canonical one.

The trade was deliberate, and was validated by three independent design audits (schema, MCP API, HTTP API) before implementation.

---

## File structure

```
skills/manifold/
├── skill.md                            # Claude Code skill metadata
├── README.md                           # Top-level entry (pointers + compass framing)
├── USER.md                             # User guide
├── ARCHITECTURE.md                     # You are here
├── .gitignore
├── .mcp.json.example                   # MCP registration template
├── schema.sql                          # Canonical DDL (tables + indexes)
├── manifold/                           # The Python package
│   ├── __init__.py
│   ├── __main__.py                     # python -m manifold → cli.main
│   ├── config.py                       # MANIFOLD_DB, MANIFOLD_SNAPSHOT_INTERVAL, SCHEMA_VERSION
│   ├── db.py                           # sqlite3.connect with WAL + foreign keys
│   ├── schema.py                       # Bootstrap schema.sql + seed schema_meta
│   ├── queries.py                      # Read functions
│   ├── writes.py                       # Write functions + state machine + with_batch
│   ├── importer.py                     # v0.2 markdown spec → DB, git-log replay
│   ├── durability.py                   # snapshot / dump / restore
│   ├── cli.py                          # argparse + subcommand dispatch
│   ├── errors.py                       # Error envelope + writes-exception mapping
│   └── mcp_server.py                   # stdio JSON-RPC + 41 tools
├── scripts/
│   └── manifold                        # bash shim → python3 -m manifold
└── tests/
    ├── conftest.py                     # fresh_db fixture
    ├── test_config.py
    ├── test_db.py
    ├── test_schema.py
    ├── test_queries.py
    ├── test_writes.py
    ├── test_importer.py
    ├── test_durability.py
    ├── test_cli.py
    ├── test_errors.py
    ├── test_mcp_server.py
    ├── test_phase_a_smoke.py           # Imports the live v0.2 self-spec
    ├── test_phase_b_smoke.py           # Runs MCP server as subprocess
    └── fixtures/
        └── build_mini_repo.py          # Builds a tiny v0.2-style repo at test time
```

---

## DB schema

Ten tables. Source of truth: `schema.sql` (in `packages/manifold/`).

### `projects`
Registered projects. Soft-delete via `archived_at`.

```sql
project_id        TEXT PRIMARY KEY     -- slug, e.g. "manifold", "auth-service"
label             TEXT
spec_config       TEXT NOT NULL         -- JSON: {layers: [{name, purpose, verdict_default, authoring_stance}]}
created_at        TEXT NOT NULL
archived_at       TEXT
last_revision_id  INTEGER
```

### `nodes`
Current state of each node. Denormalized for query speed.

Key columns (full list in `schema.sql`):
- Identity: `project_id`, `node_id` (PK); `layer`, `title`, `kind`
- Body: `body` (markdown text), `realized_by_external` (informational only; deprecated, use multi-parent edges instead)
- Target: `target_status` (defaults to `"planned"`), `target_shape`, `target_achieved_when`, `target_achieved_at`, `target_superseded_by`
- Verdict: `verdict_mechanism`, `verdict_check` / `verdict_assertion` / `verdict_judge_prompt`, `verdict_status`, `verdict_evidence_ref`
- Rationale: `rationale` (prose: why does this node exist?), `alternatives_considered` (prose: what was rejected and why?)
- Contract (JSON): `contract` (`{version, locked, field_anchors}`), `delegate_to`
- Soft-delete: `deleted_at`
- Pointer to history: `current_revision_id` (nullable; two-phase insert pattern — write revision first, then update nodes)
- Last modified: `last_modified_at`

The "list of IDs" fields (`parents`, `peers_depends_on`, `target_blocks`) are **not** columns. They live in `node_edges` instead — see below.

### `node_edges`
The audit-mandated edges table. One row per relationship between two nodes.

```sql
project_id   TEXT
src_node_id  TEXT
dst_node_id  TEXT
edge_kind    TEXT       -- "parent" | "depends_on" | "blocks" | "realizes" | "superseded_by"
created_at   TEXT
PRIMARY KEY (project_id, src_node_id, dst_node_id, edge_kind)
```

Indexes on `(project_id, dst_node_id, edge_kind)` and `(project_id, src_node_id, edge_kind)`. Recursive CTEs over this table answer transitive queries like "everything blocked by K.7."

### `revisions`
Append-only per-node history.

```sql
revision_id      INTEGER PRIMARY KEY AUTOINCREMENT
project_id       TEXT
node_id          TEXT
ts               TEXT                    -- ISO-8601
change_type      TEXT                    -- "created" | "updated" | "deleted" | "imported" | "reverted" | "restored"
prev_revision_id INTEGER                 -- chain pointer
snapshot         TEXT NOT NULL           -- JSON: full state at this revision
change_summary   TEXT                    -- JSON: [{field, old, new}, ...]
batch_id         TEXT                    -- groups logical agent operations
source           TEXT                    -- "web_ui" | "mcp" | "cli" | "import" | "validate"
actor            TEXT NOT NULL           -- "human:user" or "agent:dispatch-id"
git_sha          TEXT                    -- set when importer wrote this revision
note             TEXT
change_reason    TEXT                    -- "correction"|"evolution"|"clarification"|"refactor"|"pivot"|"other"
```

`change_reason` classifies why a revision happened. **`update_node` requires an explicit value** — no silent default. Mechanical ops (`transition_target`, `revert`, delete/restore) set implicit reasons. Values: `correction` (prior revision wrong), `evolution` (world changed), `clarification` (wording only), `refactor` (structure, same intent), `pivot` (deliberate intent shift on the spec), `other` (escape hatch). Legacy DB rows may still show `drift` until bootstrap migrates them to `pivot`.

**`spec-audit`** surfaces revisions with `pivot`, unset/`other` `change_reason`, and rationale edits not tagged `clarification`/`correction`. **`drift-report`** covers spec↔code intent drift (violated verdicts + unverified realizations) — not revision hygiene.

`snapshot` is the **full state**, not a delta. Time-travel queries become trivial:

```sql
SELECT snapshot FROM revisions
WHERE project_id=? AND node_id=? AND ts <= ?
ORDER BY ts DESC LIMIT 1;
```

`change_summary` is computed at write time so the UI doesn't have to diff two snapshots on every history page load.

### `validations` and `verdicts`

```sql
validations (
    validation_id     INTEGER PK AUTOINCREMENT,
    project_id        TEXT,
    started_at, finished_at,
    status             -- "in_progress" | "completed" | "failed"
    nodes_total, issues_total,
    verdicts_run, targets_run, framework_version
);

verdicts (
    verdict_id      INTEGER PK AUTOINCREMENT,
    validation_id   INTEGER,
    project_id, node_id,
    mechanism, status, source,
    evidence_ref, evidence_hash
);
```

Append-only. The window-function CTE in `list_unstable_verdicts` walks `verdicts` to detect status flips across the last K validations.

### `events`
Append-only audit log for project-scoped events (not node-scoped — those go in `revisions`):

```sql
event_id    INTEGER PK
ts          TEXT
project_id  TEXT NULL    -- nullable for global events
event_type  TEXT          -- "project_registered" | "import_started" | "import_finished" | "validation_started"
detail      TEXT          -- JSON
```

### `portfolio_links` (Topic H)

Theme → team node associations. Not graph edges — a theme **tracks** team nodes for exec roll-up.

```sql
theme_node_id  TEXT NOT NULL   -- node in project portfolio, layer theme
project_id     TEXT NOT NULL   -- team project
node_id        TEXT NOT NULL   -- team node
created_at     TEXT NOT NULL
PRIMARY KEY (theme_node_id, project_id, node_id)
```

Reserved project id: **`portfolio`** (`manifold.constants.PORTFOLIO_PROJECT_ID`). Theme layer: **`theme`**.

### `cross_project_edges` (Topic I)

Directed edges between nodes in **different** projects. Same `edge_kind` vocabulary as in-project `node_edges`: `blocks`, `depends_on`.

```sql
src_project_id, src_node_id   -- dependent (blocked) side
dst_project_id, dst_node_id   -- prerequisite / blocker side
edge_kind       TEXT           -- "blocks" | "depends_on"
created_at      TEXT
PRIMARY KEY (src_project_id, src_node_id, dst_project_id, dst_node_id, edge_kind)
```

**Semantics:** `blocks` — src not ready until dst is `target_status=achieved`. v1: both kinds exclude leaves from `next_leaves` when dst unsatisfied.

**node_ref** URI: `project_id/node_id` in APIs and report JSON (`blocked_by` array).

### `schema_meta`
One row. Global schema version pin. Current **`schema_version`**: **1** (product version is separate — see `MANIFOLD_VERSION`).

### Indexes
See `schema.sql` for the full list. Highlights:
- `nodes(project_id, layer)` — for "all nodes at this layer"
- `nodes(target_status, last_modified_at DESC)` (no `project_id` prefix) — for cross-project `/targets`
- `node_edges(project_id, dst_node_id, edge_kind)` — backwards edge lookups (the audit-flagged transitive-blocks query)
- `revisions(project_id, node_id, ts DESC)` — node history
- `revisions(git_sha)` — importer idempotency

---

## Three-surface architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Audiences                                                       │
│  Humans (terminal) → CLI                                        │
│  Agents (Claude)   → MCP                                        │
│  Humans (browser)  → HTTP                                       │
└──────┬──────────────────┬─────────────────┬────────────────────┘
       │                  │                 │
       ▼                  ▼                 ▼
   cli.py             mcp_server.py    web/
       │                  │                 │
       └──────────────────┴─────────────────┘
                          │
                          ▼
                Shared Python query layer
                  queries.py / writes.py
                          │
                          ▼
                        db.py
                          │
                          ▼
                       SQLite
                  ~/.claude/manifold.db
```

The key architectural insight from the audits: **the three surfaces share queries, not URLs**. Each surface composes the query layer for its audience:
- CLI: composes for tty humans (markdown rendering of `get_node`, $EDITOR for body).
- MCP: composes for agents (`peek_node_full` bundles parents + verdict to cut round-trips).
- HTTP: composes for browsers (page handlers will pull from the same `get_*` and `list_*` functions).

If we mirrored surfaces, each one would have to copy logic. The query layer is the contract.

---

## Query layer (`queries.py`)

Read functions (plus helpers). All take `sqlite3.Connection` as first arg.

| Function | Purpose |
|---|---|
| `get_project(conn, project_id)` | Project row + parsed `spec_config` JSON |
| `list_projects(conn, ...)` | Paginated; excludes archived by default |
| `get_node(conn, p, n, include_deleted=False)` | Single node + parsed JSON fields |
| `list_nodes(conn, p, layer=None, ...)` | Paginated, filterable by layer |
| `list_targets(conn, p=None, status=None, older_than_days=None, ...)` | Cross-project; filterable by status + staleness |
| `list_revisions(conn, p, n, since=None, before=None, limit=20)` | Node history newest-first |
| `list_changes_since(conn, p=None, since_ts=None, since_revision_id=None, ...)` | Cross-node activity log |
| `diff_revisions(conn, p, n, from, to)` | Per-field diff + unified body diff |
| `list_unstable_verdicts(conn, p=None, k=3, ...)` | Window-function CTE; flip detection |
| `get_validation(conn, vid)` / `list_validations(conn, p=None, ...)` | Validation rows |
| `list_blocking_chain(conn, p, n, direct_only=False)` | Recursive CTE for transitive blockers |
| `list_uncovered(conn, p, layer)` | Parent-layer nodes with no children at `layer` |
| `resolve_node(conn, p, query)` | Fuzzy id-prefix / title-substring lookup |
| `peek_node_full(conn, p, n, include=...)` | Composite: parents + children + blockers + verdict_history + revisions |
| `next_leaves(conn, p, layer=None)` | Leaf nodes ready for work; excludes in-project and **cross-project** blockers |
| `portfolio_report(conn, theme_node_id=None)` | Theme roll-up: linked nodes + `blocked_by` node_refs |
| `list_portfolio_links(conn, theme_node_id=None, project_id=None)` | Raw `portfolio_links` rows |
| `list_cross_edges(conn, project_id=None, node_ref=None)` | Cross-project edge list with `src_ref` / `dst_ref` |
| `list_cross_blocking_chain(conn, p, n)` | Transitive cross-project blockers (mirrors `list_blocking_chain`) |
| `is_cross_blocked(conn, p, n)` | Bool — any unsatisfied cross-project `blocks` target |
| `spec_audit_flagged_revisions(conn, p, since=None)` | Revisions needing review: pivot/unset/other |
| `spec_audit_unclarified_rationale(conn, p, since=None)` | Rationale changed without clarification/correction |
| `drift_report(conn, p, project_root=None, layer=None, all_layers=False, force=False)` | Spec↔code rollup: runs `validate.run_verdicts` (no validation row), classifies violated/unverified/satisfied |

Pagination convention: every `list_*` takes `limit` and `cursor`. Cursors are opaque strings of the form `"id:<value>"`.

---

## Write layer (`writes.py`)

11 write functions + portfolio/cross-project helpers + the state machine + error types.

### Error types
- `WritesError` — base
- `NodeAlreadyExists`, `NodeNotFound`, `ProjectNotFound`
- `StaleRevision` (carries `current_revision_id` for the client to retry)
- `MissingActor`, `InvalidTransition`, `BatchFailed`

### Write functions
- `create_node` — creates a node + initial revision + edges. Requires `actor`. Rejects duplicates.
- `update_node(fields, expected_revision_id, change_reason, ...)` — REQUIRES `expected_revision_id` and **`change_reason`** on content edits. Server-side enforcement via `MANIFOLD_STRICT_CONCURRENCY` (default true). Mismatch → `StaleRevision`. Computes `change_summary` at write time.
- `transition_target(to_status, ...)` — validates against the state machine.
- `revert(to_revision_id)` — copies a past snapshot forward as a new revision.
- `soft_delete_node` / `restore_node` — sets/clears `deleted_at`.
- `with_batch(label, ops)` — uuid `batch_id` + BEGIN/COMMIT/ROLLBACK around N ops. All ops share `batch_id` so the UI can group them in the timeline.
- `register_project` / `archive_project` / `unarchive_project`.
- `run_validation(...)` — runs structural checks (and verdict / target checks when requested), writes a `validations` row, returns `validation_id`.
- `link_portfolio` / `unlink_portfolio` — theme tracks team node (`portfolio_links`).
- `create_cross_edge` / `delete_cross_edge` — cross-project `blocks` / `depends_on`.

### Target state machine
```
""           → planned
planned      → in_progress | abandoned | achieved
in_progress  → achieved | abandoned
achieved     → superseded   (requires superseded_by)
abandoned    → planned       (revival)
superseded   → (terminal)
```

Anything not listed → `InvalidTransition`.

### Optimistic concurrency
`expected_revision_id` is mandatory in the signature. The server config flag `MANIFOLD_STRICT_CONCURRENCY=false` lets it be ignored (legacy migration helper); default is strict.

---

## MCP server (`mcp_server.py`)

41 tools (23 read + 18 write) over stdio JSON-RPC 2.0. Source: `mcps/manifold/server/mcp_server.py`.

### Protocol
- `initialize` → server capabilities + `serverInfo.name = "manifold"`
- `notifications/initialized` → no-op (per MCP spec)
- `tools/list` → array of `{name, description, inputSchema}` per tool
- `tools/call` with `{name, arguments}` → `{isError, content: [{type: "text", text: <JSON>}]}`

### Tool inventory

**Read tools (22)**

| Tool | Wraps |
|---|---|
| `list_projects` | `queries.list_projects` |
| `peek_project` | `queries.get_project` + rollup |
| `peek_node` | `queries.get_node` |
| `peek_node_full` | `queries.peek_node_full` (composite) |
| `peek_validation` | `queries.get_validation` |
| `list_nodes` | `queries.list_nodes` |
| `list_targets` | `queries.list_targets` |
| `list_unstable_verdicts` | `queries.list_unstable_verdicts` |
| `list_blocking_chain` | `queries.list_blocking_chain` |
| `list_cross_blocking_chain` | `queries.list_cross_blocking_chain` |
| `list_cross_edges` | `queries.list_cross_edges` |
| `list_portfolio_links` | `queries.list_portfolio_links` |
| `list_revisions` | `queries.list_revisions` |
| `list_changes_since` | `queries.list_changes_since` |
| `list_uncovered` | `queries.list_uncovered` |
| `list_validations` | `queries.list_validations` |
| `diff_revisions` | `queries.diff_revisions` |
| `resolve_node` | `queries.resolve_node` |
| `next_leaves` | `queries.next_leaves` |
| `spec_audit` | `queries.spec_audit_flagged_revisions` + `spec_audit_unclarified_rationale` |
| `drift_report` | `queries.drift_report` |
| `portfolio_report` | `queries.portfolio_report` |

**Write tools (16)**

| Tool | Wraps |
|---|---|
| `register_project` | `writes.register_project` |
| `import_project` | `importer.import_project` |
| `create_node` | `writes.create_node` |
| `update_node` | `writes.update_node` |
| `transition_target` | `writes.transition_target` |
| `revert` | `writes.revert` |
| `soft_delete_node` | `writes.soft_delete_node` |
| `restore_node` | `writes.restore_node` |
| `with_batch` | `writes.with_batch` |
| `run_validation` | `writes.run_validation` |
| `archive_project` | `writes.archive_project` |
| `unarchive_project` | `writes.unarchive_project` |
| `link_portfolio` | `writes.link_portfolio` |
| `unlink_portfolio` | `writes.unlink_portfolio` |
| `create_cross_edge` | `writes.create_cross_edge` |
| `delete_cross_edge` | `writes.delete_cross_edge` |

### Error envelope

Frozen at v0.1.0. Every tool error returns:

```json
{
  "error": {
    "code": "NODE_NOT_FOUND",
    "message": "No node 'C.3' in project 'manifold'.",
    "retry": "no" | "with_backoff" | "with_new_args",
    "suggest": ["list_nodes(project_id='manifold')"],
    "context": {"project_id": "manifold", "node_id": "C.3"}
  }
}
```

Stable codes (see `errors.py`): `NODE_NOT_FOUND`, `PROJECT_NOT_FOUND`, `STALE_REVISION` (with `current_revision_id` in context), `PARENT_NOT_FOUND`, `INVALID_TRANSITION`, `NOT_A_SPEC_REPO`, `VALIDATION_IN_PROGRESS`, `BATCH_FAILED`, `MISSING_ACTOR`, `NODE_ALREADY_EXISTS`, `UNKNOWN_TOOL`, `INVALID_ARGUMENTS`, `VALIDATION_NOT_FOUND`, `INTERNAL_ERROR`. `RATE_LIMITED` reserved for a future version.

---

## Importer (`importer.py`)

`import_project(conn, repo, project_id, actor)`:

1. Read `<repo>/specs/spec.yaml` → populate `projects.spec_config`.
2. Identify the git toplevel via `git rev-parse --show-toplevel`. Compute the repo-root-relative path prefix for the spec dir (handles both standalone repos and subdirectory-in-larger-repo cases).
3. Walk `git log` of the spec prefix in chronological order. For each commit:
   - `git ls-tree` lists `*.md` files at the prefix.
   - For each file, `git show` reads its content at that commit.
   - Parse frontmatter + body.
   - If state differs from prior revision: write a `revisions` row with `git_sha=<sha>`, `ts=<commit author iso>`, `change_type=created|updated|deleted`.
4. Detect deletes: nodes that previously existed but aren't present at this commit → `change_type='deleted'` revision.
5. Sync the `nodes` table to HEAD state.
6. Emit `import_started` / `import_finished` events.

**Idempotency**: re-running `import_project` checks the last imported `git_sha` and replays only newer commits.

**Vendored YAML parser**: stdlib-only, hand-rolled. Supports flow lists, block scalars (`>`/`|`), nested mappings, list-of-mappings, double-quoted escape sequences. Vendored from `_parse_yaml_fallback` in `validate.py`.

---

## Durability (`durability.py`)

The trade-off of canonical-DB is that you own the durability. Three primitives:

- `snapshot(db_path) → Path` — `VACUUM INTO` a sibling file. Atomic, fast, leaves a valid SQLite db.
- `dump(conn, out_path)` — newline-delimited JSON of every table. First line is a header; subsequent lines are `{"table": "...", "row": {...}}`. Atomic via `.tmp` rename.
- `restore(dump_path, target_db)` — bootstraps schema then re-INSERTs every row. Refuses to clobber an existing DB.

`MANIFOLD_SNAPSHOT_INTERVAL=3600` (seconds) is a documented env var but no built-in scheduler — wire to cron or launchd.

---

## CLI (`cli.py`)

Seventeen subcommands, all thin shells over the query/write/durability layers. The data-movement core:

| Subcommand | Implementation |
|---|---|
| `import <repo>` | `importer.import_project(conn, ..., actor=f"human:{getlogin()}")` |
| `show <project> <node>` | `queries.get_node(conn, ...)` + markdown header rendering |
| `edit <project> <node> --reason <enum>` | `get_node` → tmpfile body → `$EDITOR` → `writes.update_node` with `change_reason` |
| `snapshot` | `durability.snapshot(config.db_path())` |
| `dump <path>` | `durability.dump(conn, path)` |
| `restore <path>` | `durability.restore(path, config.db_path())` |

Plus `serve` (HTTP server), `status` (server liveness via pidfile), `export` (DB → markdown tree), `validate` (run the validation engine), `next-leaves`, **`spec-audit`** (M3 revision audit), **`drift-report`** (M4 spec↔code), **`portfolio-report`** (H theme roll-up), **`render portfolio --template quarter-roadmap`**, `version`, and `config` (machine-local config).

CLI writes auto-populate `actor` from `os.getlogin()`. Agents must provide their own `actor` via MCP.

---

## Concurrency

### Single process
Single process. Web server / MCP server / CLI all funnel through one Python process holding one SQLite connection (WAL mode). Concurrent writes serialize via SQLite's locking.

The API requires `expected_revision_id` from day one — even though manifold is currently single-process. This is non-negotiable per the audit. `MANIFOLD_STRICT_CONCURRENCY` defaults to true; the non-strict path is a compatibility shim that may be removed in a future version.

### Postgres (future)
Optional Postgres backend if SQLite hits a real ceiling (concurrent writers, very large dataset). `expected_revision_id` becomes load-bearing under real concurrency. The schema is forward-compatible — no fields change shape.

**Auth is NOT planned.** A single operator hitting one DB from multiple machines doesn't need authentication — Tailscale/SSH-tunnel/reverse-proxy handles the network perimeter. The `actor` field already differentiates humans from agents in the audit log. Auth only becomes necessary when multiple humans share an instance with distinct permissions; defer until that need ever materializes.

---

## Validation engine (`validate.py`)

`writes.run_validation` is the synchronous entry point. It builds an in-memory `nodes_by_id` projection from the DB (`_build_nodes_by_id` walks `nodes` + `node_edges`), runs the structural checks, optionally runs verdict checks, and writes a `validations` row + one `verdicts` row per node.

### Structural checks

All return `[{kind, node, message}]`. Soft-fail discipline: every check runs; one failure does not abort the others.

- `check_layer_membership` — every node's `layer` matches a name in `spec_config.layers`.
- `check_dag_property` — every parent edge must point to a node one layer up. Multiple parents are allowed (AND/OR DAG). Cross-layer cycles are forbidden. Top-layer nodes must have no parent.
- `check_intra_layer_dag` — `peers_depends_on` edges within a layer must be acyclic, and every dependency must be in the same layer.
- `check_external_realization` — `realized_by_external` is deprecated (advisory warning); the chain must be acyclic if used; external-realized nodes must have no children.
- `check_coverage` — every non-leaf, non-`constraint` node must have ≥1 child. Bottom layer is exempt.
- `check_targets` (opt-in via `--with-targets`) — `target_blocks` graph acyclic; `target_status='planned'` nodes older than `stale_days` (default 180) surface an advisory; nodes with `target_status=""` surface a "missing_target_status" advisory.
- `check_cross_project_edges` — cross-project refs exist; no cycle in cross-project `blocks` graph (`cross_project_edge_invalid_ref`, `cross_project_edge_cycle`).
- `check_rationale` — non-constraint nodes without a `rationale` field surface a "missing_rationale" advisory.

### Verdict runners

Four mechanisms, schema-level:

- **`automated_check`** — `subprocess.run(verdict_check, shell=True, cwd=project_root, timeout=300)`. Exit 0 → satisfied.
- **`python_assertion`** — `verdict_assertion` parsed with `ast.parse(mode='eval')`, then walked manually via `_eval_assertion_ast`. The walker only allows constants, boolean ops, comparisons, and whitelisted helper calls (`file_exists`, `file_contains`, `ast_has_call`, `ast_has_import`, `ast_has_def`, `ast_has_call_with_kwarg`). No name lookups, no attribute access, no dynamic-code-execution primitive. Does NOT use Python's `eval` builtin — by design.
- **`human_signoff`** — reads the `verdict_status` column. Trusts the human; no recomputation.
- **`llm_judge`** — shells out to `$MANIFOLD_JUDGE_CMD` or `spec_config.judge_command`. manifold's side is just subprocess; the operator wires in their LLM CLI.

### Caching

`compute_input_hash(node, parent_statuses)` is a stable SHA-256 over the node's verdict-relevant fields (body, layer, kind, mechanism + check/assertion, target_status, realized_by_external) plus sorted parent verdict statuses. `run_verdicts` looks up the most recent `verdicts` row with the same hash for the node; if found and not `force`, reuses its status with `source='cache'`. Any change to inputs (this node's body, the mechanism, a parent's status) invalidates the cache automatically.

### Propagation

After the per-node runners finish:
- `resolve_external` makes `realized_by_external` nodes inherit their target's status.
- `propagate_failures` walks parents upward to fixed point: any node with a violated child becomes `invalidated_by_descendant`.

The final per-node `verdict_status` column is updated to the resolved status so `/reports/flips` and the node detail page reflect the latest run.

### Surfaces

- **CLI**: `manifold validate <project> [--with-verdicts] [--with-targets] [--force]`.
- **HTTP**: `POST /api/v1/projects/<p>/validations` (body: `{actor, with_verdicts?, with_targets?, force?}`); `GET .../validations/<id>` returns the row + its verdicts.
- **MCP**: `run_validation` tool — same shape as CLI/HTTP, returns `{validation_id, status, issues, verdicts_run, nodes_total}`.

---

## Adding a new MCP tool

1. Write the underlying function in `queries.py` or `writes.py` (TDD: write the test first).
2. Add a handler in `mcp_server.py` (e.g. `h_my_new_tool(conn, args)`).
3. Add a descriptor to the `TOOLS` list with `inputSchema`.
4. Add a unit test in `test_mcp_server.py` (call `_tool_call(conn, "my_new_tool", {...})` and assert on the payload).
5. If the tool can fail in a new way, add a code to `errors.py` and a mapping in `from_writes_exception` if needed.

The dispatch table is the single source of truth — `TOOLS_BY_NAME` is built from `TOOLS`. No separate registry to keep in sync.

---

## Design lineage

manifold descends from two earlier file-based experiments: a fixed-taxonomy prototype with a single LLM-judge verdict, then a configurable file-based skill with four verdict mechanisms and a target-state vector. The **DB-canonical rewrite** (v0.1.0 product line) — SQLite source of truth, three surfaces (CLI, MCP, HTTP) over a shared query layer, KAOS-grounded AND/OR DAG, compass (`next-leaves`, `target_status`, **`portfolio-report`**, cross-project blocking), and revision discipline (`rationale`, `alternatives_considered`, `change_reason`, **`spec-audit`**). Canonical `schema_version = 1`.

The DB-canonical design was put through three independent audits (schema, MCP API, HTTP API) before implementation. Two audit-mandated decisions worth calling out: the `node_edges` table (rejected JSON-list-of-IDs columns) and the `expected_revision_id` requirement from day one.

---

## Roadmap

v0.1.0 ships the full substrate described above. Possible future work, all additive on top of it:

| Item | Status | Description |
|---|---|---|
| v0.2 | maybe | OR-refinement, obstacle analysis, qualitative aggregation (Make/Help/Hurt/Break), weighted priority on `next-leaves`. |
| Postgres | maybe | Only if SQLite hits a real ceiling. Multi-machine = network perimeter (Tailscale/SSH), not auth. |
| Auth | maybe | Only if multiple humans share an instance with different permissions. Defer until that need is real. |

---

## HTTP surface

Built on stdlib `http.server.ThreadingHTTPServer`. Single connection across worker threads (`check_same_thread=False`; WAL mode handles concurrency). Run via `manifold serve [--host 127.0.0.1] [--port 7779]`.

### HTML routes

| Path | Purpose |
|---|---|
| `GET /` and `/projects` | Project list |
| `GET /projects/<p>` | Dashboard cards + validation trigger form + layer-by-layer tree |
| `GET /projects/<p>/nodes/<n>` | Node detail + history timeline (revisions are links) |
| `GET /projects/<p>/nodes/<n>/edit` | CodeMirror body editor + structural-fields panel |
| `POST /projects/<p>/nodes/<n>` | Apply form: optional state-machine transition + field updates |
| `GET /projects/<p>/nodes/<n>/revisions/<rev>` | Field-by-field diff + unified body diff |
| `POST /projects/<p>/validations` | Trigger validation, redirect to detail |
| `GET /projects/<p>/validations/<id>` | Validation result (issues + verdicts tables) |
| `GET /projects/<p>/nodes/<n>/edit` | CodeMirror body editor |
| `POST /projects/<p>/nodes/<n>` | Save body edit (form-encoded; optimistic concurrency via hidden `expected_revision_id`) |
| `GET /reports/targets` | Cross-project targets |
| `GET /reports/flips` | Cross-project unstable verdicts |
| `GET /reports/portfolio` | Portfolio theme roll-up (Topics H+I) |
| `GET /static/*` | Static assets (CodeMirror, etc.); path traversal blocked |

### JSON API (`/api/v1/`)

Versioned, resource-oriented. Decoupled from HTML route grammar — both surfaces consume the shared `queries.py`/`writes.py` layer.

| Method + Path | Purpose |
|---|---|
| `GET /api/v1/projects` | List projects (paginated) |
| `GET /api/v1/projects/<p>` | Project row + parsed `spec_config` |
| `GET /api/v1/projects/<p>/nodes` | List nodes; `?layer=...&limit=...&cursor=...` |
| `GET /api/v1/projects/<p>/nodes/<n>` | Node row (current state, all fields) |
| `PATCH /api/v1/projects/<p>/nodes/<n>` | Update node fields. **Requires `If-Match: <revision_id>` header.** 409 on mismatch. |
| `GET /api/v1/projects/<p>/nodes/<n>/revisions` | Node history |
| `GET /api/v1/reports/targets` | Cross-project targets |
| `GET /api/v1/reports/flips` | Cross-project unstable verdicts |
| `GET /api/v1/reports/portfolio` | Portfolio report JSON (`?theme=T.1` optional) |
| `GET /api/v1/projects/<p>/spec-audit` | Spec audit report |
| `GET /api/v1/projects/<p>/drift-report` | Drift report |
| `GET /api/v1/projects/<p>/next-leaves` | Open frontier leaves |

Errors return the same envelope as the MCP surface (per `errors.py`).

### CodeMirror

CodeMirror 5 (`5.65.16` from cdnjs at install time) vendored under `web/static/codemirror/`:

- `codemirror.min.js` + `codemirror.min.css` — core
- `mode/markdown/markdown.min.js` — markdown syntax mode
- `addon/edit/continuelist.min.js` — auto-continue list markers on Enter

~190 KB total. Offline-capable; no CDN dependency at runtime.

Why CM5 over CM6: CM5 ships as static script tags with no bundler dependency. CM6 is more modular but requires npm + a bundler (rollup/esbuild) to produce a usable single-file bundle. For simplicity, CM5's feature set is more than adequate for a markdown body editor; CM6 migration can land in a later phase if the dev surface demands it.

### Single-process concurrency

All write tools accept (and the API requires) `expected_revision_id` / `If-Match` from day one. The server's worker threads share one SQLite connection with `check_same_thread=False`; WAL mode + SQLite's lock manager keeps concurrent reads/writes safe. If/when a Postgres backend ships, the API contract doesn't change.
