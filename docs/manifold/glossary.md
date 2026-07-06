# Manifold proper-noun inventory

**Status:** canonical naming reference. When code, docs, or CLI disagree with this file, **fix the code** — not the glossary.

**Sources:** KAOS / goal-oriented RE (van Lamsweerde), IEEE RE & traceability practice, ADRs (Nygard), configuration management, landscape research [`synthesis.md`](../../research/manifold/landscape-2026-06/synthesis.md), shipped schema.

**Rule:** Use the **Manifold noun** in CLI, MCP, and user-facing docs. Use **In the books** when explaining to RE/architecture audiences. Never use **Avoid** for product surfaces.

**Last codebase audit:** 2026-06-06 — see [Coverage audit](#coverage-audit-2026-06-06) at bottom.

**How to use:** [`how-to-use.md`](how-to-use.md) · **Master todo:** [`todo.md`](todo.md) — decisions + full task list for Topics A–G.

---

## Human terms vs API terms

Use this table when writing onboarding docs, chat summaries, HTML labels, or support explanations. Keep the canonical Manifold noun in CLI, MCP, schema, tests, and precise reference docs.

| Canonical term | Human-facing label | Use in first-run explanations | Precision rule |
|---|---|---|---|
| `node` | spec item / requirement / project item | "spec item" | A node is not a ticket unless explicitly linked to one. |
| `next-leaves` | ready next work | "ready next work" | This is graph frontier/readiness, not business priority. |
| `target_status` | planned / in progress / achieved state | "work state" | This says where work is in the spec graph; it does not prove implementation correctness. |
| `verdict` / `verdict_status` | evidence check result | "evidence status" | This says whether a configured check is satisfied, violated, errored, or unknown. |
| `drift-report` | code/spec evidence report | "code/spec evidence report" | Not an all-clear unless violated, errored, and unverified counts are acceptable. |
| `spec-audit` | spec history audit | "spec history audit" | Does not read source code; it reviews revision discipline. |
| `trajectory` | proposed change plan | "proposed change plan" | `propose` and `show` preview; only `accept` mutates the graph. |
| `leg` | proposed change step | Avoid in first-run docs | Fine in trajectory reference docs and JSON. |
| `project_id/node_id` | project item reference | "project item" when informal | Use full `node_ref` in logs, APIs, and ambiguity-prone contexts. |

When in doubt, lead with the human label and include the canonical term in parentheses: "ready next work (`next-leaves`)".

---

## Compass questions

Plain-language questions the product answers. Each maps to one primary surface.

| Question | Plain language | Primary surface | Not this |
|---|---|---|---|
| What is this project? | Layered spec graph — the preserved *why* structure | `peek_project`, `list_nodes`, web project view | README alone |
| Where are we? | Per-node `target_status` + `verdict_status` | `list_targets`, node detail | git branch |
| What next? | Open frontier leaves ready for work | `next-leaves` | ticket backlog |
| Are spec revisions explained? | Revision discipline — not code reconciliation | `spec-audit` | code reconciliation |
| Does code match spec? | Verdict rollup on realizations — violated + unverified | `drift-report` | `spec-audit` (revision hygiene) |
| How are company themes tracking? | Theme roll-up across team projects | `portfolio-report` | `list_targets` (flat status filter) |
| Where are we headed? | Planned path from as-is spec to stated target — review before merge | **`trajectory`** + **`propose`** | roadmap (generic), migration runbook |

Do **not** say "is the spec honest" in docs without glossing it — use **"Are spec revisions properly explained?"** (same as `spec-audit`).

---

## Compass & orientation

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **project compass** | Orients long-horizon work: what the project is, where it is, what's next, whether the spec story holds. Does not dispatch agents or track live runs. | Goal-oriented RE "compass" metaphor; KAOS goal models orient analysis, not execution | Skill metaphor | orchestrator, task manager, IDE |
| **next-leaves** | Smallest open frontier nodes in the spec graph — leaves with `target_status` in `planned` / `in_progress` / unset, ready for work. | **Operational refinement front** (KAOS); "next eligible leaf" in AND/OR DAG terms; not quite "critical path" (CPM assumes tasks, not goals) | CLI `next-leaves`, MCP `next_leaves` | next tasks, backlog, todo list |
| **target_status** | Per-node work orientation: is this spec item planned, in progress, achieved, superseded? | **Work-item state** on a requirement artifact; weaker than ALM workflow states | Node field | ticket status, Jira column |
| **layer** | Named refinement altitude (e.g. intent → capability → contract → realization). | **KAOS abstraction level**; refinement layer in goal-oriented RE | `spec_config.layers` | phase, sprint, epic (agile execution) |
| **node** | One specification unit in the graph: title, body, parents, rationale, verdict config. | **Requirement / goal / specification artifact** (IEEE 830 / ISO 29148 family); KAOS **goal** or **requirement** | DB `nodes` | file, ticket, story (unless explicitly mapped) |
| **project** | Top-level container: `project_id`, `spec_config`, archived or active. | **Project** / **specification baseline** container | DB `projects` | repo (parallel — import links them) |
| **spec_config** | JSON project config; required `layers` list defines refinement altitudes. | **Specification schema** / layer taxonomy | `projects.spec_config` | folder layout |
| **body** | Markdown prose of the node — the *what* at this layer. | **Requirement text** / **specification statement** | Node field | code |
| **contract** | Middle-layer structured obligation (pre/postconditions) where applicable. | **Software contract**; design-by-contract | Node field | API schema file |
| **title** | Short node label; used in `resolve_node` search. | **Requirement title** | Node field | filename |

## History & rationale (M3)

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **revision** | Immutable snapshot of a node after create/update/revert; full field snapshot + `change_summary`. | **Version** or **revision** (CM); requirements **baseline** history (IEEE) | DB `revisions` | commit (git — parallel, not substitute) |
| **rationale** | Why this node exists — the preserved *why* on the spec artifact. | KAOS **goal annotation**; ADR **Context** + **Decision**; design **rationale** (Burgess / RE texts) | Node field | description, notes (too weak) |
| **alternatives_considered** | Options rejected when this node was chosen. | ADR **Consequences** / rejected options; **trade study** record | Node field | comments |
| **change_reason** | Typed classification of *why this revision happened* (enum on the revision row). **Required** on every `update_node` call — no silent default. | **Change reason** / **change request category** (CM); RE **change log semantics** | Revision field; required on content edits | free-text only, git message |
| **change_reason = correction** | Prior revision was wrong. | **Defect repair** against spec | Enum value | bug fix (code sense) |
| **change_reason = evolution** | External world changed; spec catches up. | **Requirements evolution** | Enum value | drift |
| **change_reason = clarification** | Wording only; no semantic change. | **Clarification** (no change of baseline intent) | Enum value | typo |
| **change_reason = refactor** | Structural/graph change; same intent. | **Refactoring** (Fowler) applied to spec structure | Enum value | rewrite |
| **change_reason = pivot** | Author deliberately changed spec intent (was: misnamed `drift`). | **Scope / intent pivot**; **requirements change** with intent shift | Enum value | **drift** (reserved for spec↔code — see below) |
| **change_reason = other** | Escape hatch; needs human-readable note. | **Other** change category | Enum value | (unset) |
| **change_summary** | Machine-computed per-field diff list stored on each revision. | **Change log detail** | Revision field | git diff |
| **change_type** | `created` / `updated` / `reverted` — kind of revision event. | **Change event type** (CM) | Revision field | — |
| **actor** | Who made the write (`human:…`, agent id). | **Author** / **change author** | Revision + write APIs | git author (parallel) |
| **batch_id** | UUID grouping revisions from one `with_batch` MCP call. | **Change set** / **transaction id** | Revision field | — |
| **revert** | Copy a past revision snapshot forward as a new revision. | **Rollback** (forward-only — new revision, not delete) | MCP `revert`, writes | git revert (different semantics) |

---

## Spec audit (M3 hygiene — shipped)

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **spec-audit** | Report on **spec graph discipline**: revisions missing `change_reason`, author-flagged `pivot`, `other`, and rationale edits not tagged clarification/correction. Does **not** read source code. | **Requirements audit**; **change control review**; **configuration audit** (CM) | CLI `spec-audit`, MCP `spec_audit`, HTTP `/spec-audit` | drift-report (old name); drift detection |
| **flagged revisions** | Revisions surfaced by spec-audit section 1 (`pivot`, unset, `other`). | Revisions **pending classification** in change log | JSON/MCP key `flagged_revisions` | drift revisions |
| **unclarified rationale changes** | Revisions where `rationale` changed without `clarification` or `correction`. | **Undocumented rationale change** — audit finding | JSON/MCP key `unclarified_rationale_changes` | drift |

---

## Intent drift report (M4 — shipped, Topic E v1)

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **intent drift** (narrow sense) | Code/tests acceptable but implementation no longer matches preserved *why*. | **Requirements drift** / **specification drift** (RE); Stonewall **intent drift** (spec↔code); **traceability gap** | Category in docs — qualify lineage | model drift, data drift, IBN intent drift, agent goal drift |
| **drift-report** | Spec↔code reconciliation: violated verdicts + unverified realizations + **errored** checks (could not run). v2: LLM rationale match (L17). | **Verification & validation** against requirements (IEEE V&V); **consistency check** (StrictDoc, DOORS); RealityCheck-style **DRIFT_DETECTED** | CLI `drift-report`, MCP `drift_report`, HTTP `/drift-report` (Topic E v1) | Do not use for spec-audit |
| **intent drift report** | Same as `drift-report` — spell out in prose when category label is ambiguous. | Same as above | Prose | detection (alone — polluted term) |

### Three lineages of "intent drift" (disambiguation)

| Lineage | In the books | Manifold stance |
|---|---|---|
| Intent-Based Networking | Muonagor & Bensalem, arXiv:2404.15091 | Cite for etymology only |
| Agent safety / runtime goal drift | Arike et al., arXiv:2505.02709 | Different audience — disambiguate |
| **Spec↔code** | Stonewall, Tricentis, Zenn IDD | **Our lane** — `drift-report` (v1: verdict rollup; v2: LLM rationale match) |

---

## Verification (M6)

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **verdict** | Satisfaction result for a node: satisfied, violated, unknown, etc. | **Validation outcome**; KAOS **obstacle** resolution status | `verdict_status`, `verdicts` table | test result (unless mapped) |
| **verdict_mechanism** | How satisfaction is checked — see values below. | **Verification method** (IEEE V&V); **acceptance criteria** mechanism | Node field | test type |
| **verdict_mechanism = automated_check** | Shell command in `verdict_check`; exit 0 = satisfied. | **Automated test hook** | Enum value | unit test runner (external) |
| **verdict_mechanism = python_assertion** | Python expression in `verdict_assertion` against project root. | **Executable assertion** | Enum value | pytest |
| **verdict_mechanism = human_signoff** | Manual; uses `verdict_evidence_ref`. | **Manual sign-off** (regulated workflows) | Enum value | approval ticket |
| **verdict_mechanism = llm_judge** | LLM prompt in `verdict_judge_prompt`; optional judge command. | **Expert review** / **qualitative assessment** | Enum value | vibe check |
| **verdict_status** | Cached on node: `satisfied`, `violated`, `unknown`, `judge_required`, … | **Validation status** | Node field | CI badge |
| **run_validation** | Execute validate pipeline; write `validations` + `verdicts` rows. | **Verification run** | MCP `run_validation`, CLI `validate` | CI job |
| **list_unstable_verdicts** | Nodes whose `llm_judge` verdict **flipped** in last K runs. | **Flaky validation** detection | MCP tool | — |
| **validate** | Run structural rules + optional verdict/target checks over the graph. | **Consistency check** + **validation** pass | CLI `validate` | CI (external) |
| **validation run** | One recorded execution of validate; issues + verdict rows. | **Verification run** record | DB `validations` | build |
| **evidence_hash** | Cache key for verdict inputs — skip unchanged re-runs. | **Input fingerprint** (CM) | Node + verdict rows | — |

### Validation issue kinds (`issues[].kind`)

Emitted by `validate.py`; surfaced in `peek_validation` / web validation view.

| Issue kind | Meaning |
|---|---|
| `coverage` | Parent has no child in next layer |
| `missing_rationale` | Node lacks rationale text |
| `missing_target_status` | Node has no `target_status` |
| `target_stale_planned` | `planned` too long without progress |
| `target_unresolved_block` | Blocked by unsatisfied blocker |
| `target_blocks_cycle` | Circular `blocks` edges |
| `layer_membership` | Node layer not in `spec_config.layers` |
| `cycle_across_layers` | Parent chain crosses layers incorrectly |
| `dag_property` | Multi-parent / DAG constraint violation |
| `intra_layer_edge` | Invalid edge within same layer |
| `intra_layer_cycle` | Cycle within one layer |
| `external_realization` | `realized_by_external` target invalid |
| `external_realization_cycle` | Cycle via external realization links |
| `cross_project_edge_invalid_ref` | Cross-project edge points at missing node |
| `cross_project_edge_cycle` | Cycle in cross-project `blocks` graph |
| `deprecated_field` | Node uses removed schema field |

---

## Graph & traceability (M2)

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **parent edge** | Refinement link: child node contributes to satisfying parent(s). | KAOS **AND-refinement** / **OR-refinement** link | `edge_kind = parent` | depends on (execution) |
| **depends_on edge** | Ordering / prerequisite between nodes (in-project, same DB). | **Dependency link** (not refinement) | `edge_kind = depends_on`; MCP write field `peers_depends_on` | parent (refinement) |
| **blocks edge** | Node A blocks node B until blocker is satisfied (in-project). | **Blocking dependency**; **wait-for** | `edge_kind = blocks`; MCP write field `target_blocks` | Jira blocker |
| **list_blocking_chain** | Transitive in-project blockers for a node. | **Dependency chain analysis** | MCP `list_blocking_chain` | `list_cross_blocking_chain` |
| **peers_depends_on** | MCP/`create_node` field name for outgoing `depends_on` edges. | Same as depends_on edge | Write API | `depends_on` (edge_kind in DB) |
| **target_blocks** | MCP/`create_node` field name for outgoing `blocks` edges. | Same as blocks edge | Write API | `blocks` (edge_kind in DB) |
| **multi-parent** | DAG across layers — one capability satisfies multiple intents. | KAOS **shared refinement** | Graph shape | duplicate nodes |
| **realized_by_external** | Cross-cutting realization without duplicating subtree. | **External trace link**; realization mapping | Node field | import |
| **kind = spec** | Default decomposable specification unit. | **Requirement** / **goal** | Node `kind` (default) | — |
| **kind = constraint** | Non-decomposable rule; waives coverage expectations. | **Constraint** (KAOS) | Node `kind` | lint rule |
| **coverage rule** | Every non-constraint parent must have ≥1 child (validator). | **Refinement completeness** (KAOS) | `validate.py` | narrative completeness |
| **list_uncovered** | Parents in layer L with no children in layer L+1. | **Coverage gap** report | MCP `list_uncovered` | — |
| **transition_target** | Move `target_status` along the state machine. | **State transition** on work item | MCP tool | edit field directly |
| **target_status = planned** | Default; not started. | **Planned** | Enum value | backlog |
| **target_status = in_progress** | Active work. | **In progress** | Enum value | — |
| **target_status = achieved** | Done; sets `target_achieved_at`. | **Achieved** / **implemented** | Enum value | closed ticket |
| **target_status = abandoned** | Stopped; can revive → planned. | **Cancelled** / **deferred** | Enum value | — |
| **target_status = superseded** | Replaced; requires `target_superseded_by`. | **Superseded requirement** (IEEE) | Enum value | deleted |
| **target_superseded_by** | Node id that replaced this one. | **Supersedes** link | Node field | — |
| **delegate_to** | External agent or skill id responsible for realizing this node (orchestrator handoff target). | **Assignment** / **delegate** | Node field; v0.2 export `delegate_to:` | owner (people) |
| **applies_to** | JSON scope: which repos, paths, or deployables this node governs. | **Applicability** / **scope** | Node field; v0.2 export `applies_to:` | tags |
| **contract** | JSON block `{version, locked, field_anchors}` — locked handoff shape for orchestrator consumption. | **Interface contract** | Node field; v0.2 export `contract:` | full node body |
| **target_shape** | Expected deliverable shape when achieved (exported as `shape:`). | **Work product description** | Node field | spec body |
| **target_achieved_when** | Human-readable definition-of-done for marking `achieved`. | **Acceptance condition** (prose) | Node field; export `achieved_when:` | verdict_check |
| **target_rationale_ref** | Optional node id — rationale lives elsewhere; this node points to it. | **Rationale trace link** | Node field; export `rationale_ref:` | duplicate rationale |
| **stale revision** | `update_node` rejected — `expected_revision_id` mismatch. | **Optimistic concurrency conflict** | Error `StaleRevision` | — |
| **expected_revision_id** | Required on `update_node` for conflict detection. | **Version token** / **ETag** | Write API | — |
| **soft_delete_node** | Sets `deleted_at`; hidden from default queries. | **Soft delete** | MCP tool | hard delete |
| **archive_project** | Project hidden from default lists; data retained. | **Archive** | MCP tool | delete project |

---

## Portfolio (Topic H — shipped)

One `$MANIFOLD_DB`, reserved project **`portfolio`** for company themes (L18–L19).

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **portfolio** | Reserved `project_id` (`portfolio`) for company-wide theme nodes. | **Portfolio** / program container | DB project | second database, “org manifold” |
| **theme** | Company bet / quarter initiative; node in `portfolio` project, layer `theme`. | **Strategic theme** / initiative | Node | epic, OKR object (unless mapped in prose) |
| **portfolio link** | Row in `portfolio_links`: a theme **tracks** a team node. Not a graph edge. | **Trace link** / roll-up membership | DB `portfolio_links` | Jira epic link, `depends_on` |
| **tracks** | Verb: theme portfolio-link tracks a team node. | **Roll-up membership** | MCP `link_portfolio` / `unlink_portfolio` | “depends on” (use cross-project edge) |
| **portfolio-report** | Theme roll-up: linked nodes' `target_status`, `verdict_status`, `blocked_by`. | **Portfolio status report** | CLI `portfolio-report`, MCP `portfolio_report`, HTTP `/reports/portfolio` | roadmap (alone), Gantt |
| **portfolio roadmap** | Business phrase for theme roll-up view — prose only. | Executive summary | Prose | CLI command name |
| **render** | Stitched table or narrative for a chosen audience (v1: portfolio templates). | **View** at exec altitude | CLI `render portfolio --template …` | `export` (file tree dump) |
| **quarter-roadmap** | Template id: theme × team × status table for execs. | **Roadmap view** | `render portfolio --template quarter-roadmap` | PowerPoint SoT |
| **list_targets** | Flat cross-project filter on `target_status`. | **Status rollup** | MCP `list_targets`, `/reports/targets` | `portfolio-report` (theme-grouped) |

**Report JSON keys (portfolio-report):** `themes[]`, each with `links[]` rows carrying `node_ref`, `target_status`, `verdict_status`, **`blocked_by`** (array of `node_ref` strings).

---

## Cross-project links (Topic I — shipped)

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **cross-project edge** | Directed edge between nodes in different projects (`blocks` \| `depends_on`). | **Cross-project dependency** | DB `cross_project_edges` | cross-manifold, federation (v1) |
| **node_ref** | Stable pointer `project_id/node_id` (e.g. `ai-platform/C.4`). | **Qualified reference** | API, MCP, validation messages | bare `node_id` |
| **external blocker** | Cross-project `blocks` target not yet `achieved` — excludes leaf from `next-leaves`. | **External wait-for** | Query logic | `realized_by_external`, `external_realization` |
| **list_cross_blocking_chain** | Transitive cross-project blockers for a node (mirrors `list_blocking_chain`). | **Cross-project dependency chain** | MCP `list_cross_blocking_chain` | `list_blocking_chain` (in-project only) |
| **link_portfolio** vs **create_cross_edge** | Portfolio links are associations; cross edges are directed graph deps. | Membership vs dependency | MCP writes | using same verb for both |

**v1 surfaces:** MCP `create_cross_edge`, `delete_cross_edge`, `list_cross_edges`, `list_cross_blocking_chain`. No CLI `cross-edges` subcommand in v1 (L29).

---

## Trajectory (Topic J — shipped v1)

As-is → to-be planning: draft a reviewable path toward a **target brief**; **accept** applies legs to the graph. Design: [`archive/topics/trajectory.md`](../archive/topics/trajectory.md). **Shipped v1** (J1–J2): schema, impact preview, CLI/MCP/web API.

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **trajectory** | Reviewable proposal: ordered **legs** from current graph toward a target brief; status `draft` / `accepted` / `rejected` / `partial`. Graph unchanged until **accept**. | **Transition plan** / requirements evolution path | DB `trajectories`, CLI `trajectory show`, MCP `peek_trajectory` | vector (ML), roadmap (generic), migration (code-only) |
| **propose** | Draft a trajectory from target brief + current graph — no writes to nodes | **Change proposal** initiation | CLI **`trajectory propose`**, MCP **`propose_trajectory`** | plan_trajectory, rechart, realign |
| **leg** | One proposed graph change on a trajectory (add / modify / supersede / edge / portfolio link) | **Change item** / delta step | DB `trajectory_legs`, MCP `accept_trajectory_leg` | step (generic), op, diff |
| **target brief** | Markdown input: desired to-be state (not a stored product tier — field on trajectory) | **Target architecture statement** | `target_brief` on propose | requirements doc (too heavy) |
| **accept** | Apply pending leg(s) via normal write APIs + required `change_reason` | **Change approval** / baseline update | CLI `trajectory accept`, MCP `accept_trajectory_leg` | auto-merge, silent agent write |
| **impact preview** | Simulated post-**accept** graph: leg diff + **`next_leaves_after`**, portfolio/blocker deltas — no writes (Terraform **plan** before **apply**) | **Impact analysis** / dry-run | JSON key on **`trajectory show`**, web diff panel | running real `next-leaves` inside propose |

**Workflow (locked):** **`propose`** → **`show`** (includes impact preview) → **`accept`** → graph updated.

**Execution (separate track):** after accept, call real **`next-leaves`** when picking implementation work — not step 4 of trajectory (L34).

**Trust model:** Agents may **propose**; only **accept** mutates the canonical graph (L33).

---

## Integration roles (product)

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **intent-broker** | MCP layer that holds canonical spec graph; orchestrators read before acting. | **Product context layer** (Jama MCP pattern); **single source of truth** server | Positioning (Topic F) | orchestrator, MCP server (generic) |
| **AGENTS.md compile** | *Deferred (L14):* no auto export. Users maintain host files (`CLAUDE.md`, etc.) manually; graph stays in DB/MCP. | **Agent context file** (AAIF) | — | primary store |
| **ReqIF export** | *Future:* enterprise interchange of requirements. | **ReqIF** (OMG); DOORS/Polarion interop | Topic G | graph dump |

---

## Palimpsest quarry (L10 — planned, not shipped)

Ideas mined from Palimpsest (manifold's file-based ancestor). **Not product nouns until shipped.**

| Term | What it would mean | Tier | Avoid until shipped |
|---|---|---|---|
| **harvest** | Reverse-init: synthesize an initial layered spec from existing code + README + tests (LLM-assisted, human-reviewed). | 1 | import |
| **render** | *Partially shipped (L27):* `render portfolio --template quarter-roadmap`. Layer narrative (`render project --layer intent`) still planned. | 1 | export, web layer list |
| **restructure** | Insert/rename/split/merge layers without renumbering chaos (e.g. add `audiences` above `intent`). | 1 | manual re-parent |
| **judge calibration** | N-of-3 majority vote when `llm_judge` verdict flips in last K runs. Partial today: `list_unstable_verdicts` detects flips only. | 2 | single judge call |
| **validate budget ceiling** | Hard cost/token stop during `validate`; partial report with `skipped_over_budget` nodes. | 2 | `--force` only |
| **cross-spec federation** | `parents: [project:auth@K.3]` — **deferred (L22)**; use **cross-project edge** for B | 3 | duplicate import |
| **orchestrator contract translator** | Map manifold `contract` JSON → orchestrator `C<n>` shape. | 3 | raw `delegate_to` |

**Dropped on purpose:** Palimpsest sequential-ID merge collisions — moot under DB-canonical identity.

---

## Storage & surfaces

| Manifold noun | What it means | In the books | Surface | Avoid |
|---|---|---|---|---|
| **DB-canonical** | SQLite is source of truth; markdown export is derivative. | **Repository** as SoT vs **views** | Architecture | markdown-first |
| **export** | Current-state v0.2 markdown tree (not full history). | **View** / **extract** | CLI `export` | backup |
| **import** | v0.2 markdown tree → DB with git history replay. | **Load** / **ingest** | CLI `import` | sync |
| **dump / restore** | Lossless NDJSON backup of all tables. | **Full backup / restore** | CLI | export |

### Web routes (human surface)

| Route | Noun / view |
|---|---|
| `/projects/<p>/spec-audit` | Spec audit report (`flagged_revisions`, `unclarified_rationale_changes`) |
| `/api/v1/projects/<p>/spec-audit` | Same data as JSON |
| `/projects/<p>/drift-report` | Spec↔code drift report (`violated`, `unverified`, summary) |
| `/api/v1/projects/<p>/drift-report` | Same data as JSON |
| `/reports/targets` | Cross-project `target_status` rollup (`list_targets`) |
| `/reports/flips` | Cross-project unstable `llm_judge` verdict flips |
| `/reports/portfolio` | Portfolio theme roll-up (`portfolio_report`) |
| `/api/v1/reports/portfolio` | Same data as JSON |

---

## MCP tools (40+ — agent surface)

Grouped by role. Snake_case in MCP; kebab-case only where CLI mirrors (`next-leaves`, `spec-audit`, `portfolio-report`).

| Group | Tools |
|---|---|
| **Read / peek** | `list_projects`, `peek_project`, `peek_node`, `peek_node_full`, `peek_validation` |
| **Read / list** | `list_nodes`, `list_targets`, `list_revisions`, `list_changes_since`, `list_uncovered`, `list_validations`, `list_unstable_verdicts`, `list_blocking_chain`, `list_cross_blocking_chain`, `list_cross_edges`, `list_portfolio_links`, `diff_revisions`, `resolve_node` |
| **Compass / audit** | `next_leaves`, `spec_audit`, `drift_report`, `portfolio_report` |
| **Write** | `register_project`, `import_project`, `create_node`, `update_node`, `transition_target`, `revert`, `soft_delete_node`, `restore_node`, `with_batch`, `run_validation`, `archive_project`, `unarchive_project`, `link_portfolio`, `unlink_portfolio`, `create_cross_edge`, `delete_cross_edge` |

**Peek pattern:** composite read (`peek_node_full`) bundles parents, children, revisions — reduces agent round-trips.

---

## CLI commands (operational — not compass nouns)

| Command | Role |
|---|---|
| `import` / `export` | DB ↔ v0.2 markdown tree |
| `show` / `edit` | Human tty read/edit one node |
| `validate` | Run validation engine |
| `next-leaves` / `spec-audit` / `drift-report` / `portfolio-report` | Compass queries (also MCP) |
| `render` | Human-readable templates (v1: `render portfolio --template quarter-roadmap`) |
| `dump` / `restore` / `snapshot` | Backup |
| `serve` / `status` | Web UI |
| `version` / `config` | Meta |

---

## Research axes (M1–M7 — framework, not code identifiers)

Used in landscape synthesis to score competitors. Inform product language; not stored in schema.

| Axis | Meaning |
|---|---|
| M1 | Single source of truth |
| M2 | Layered graph |
| M3 | Revision history |
| M4 | Drift detection (spec↔reality) |
| M5 | Compass queries |
| M6 | Verdict engine |
| M7 | Agent-native (MCP/API) |

---

## Reserved & deprecated

| Term | Status | Notes |
|---|---|---|
| `drift-report` (CLI/MCP for M3) | **Removed 2026-06-06** | Was misnamed revision audit; use `spec-audit` |
| `change_reason = drift` | **Migrated → `pivot`** on bootstrap | DB migration |
| `drift_revisions` (API key) | **Removed** | Use `flagged_revisions` |

---

## Positioning sentence (locked from research)

> Everyone agrees intent drift is the problem. Manifold makes *why* a typed field — ADRs that talk to your agent, version your intent, and produce an **intent drift report** when code diverges.

All three clauses ship for projects with verdicts wired on realization nodes: typed **`rationale`**, required **`change_reason`**, and **`drift-report`** (v1: violated + unverified rollup). v2 LLM rationale match (L17) is deferred.

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-06 | Initial inventory; Option 1 locked — `spec-audit` + reserve `drift-report`; `change_reason` `drift` → `pivot` |
| 2026-06-06 | Coverage audit: target machine, edge kinds, verdict mechanisms, MCP index, compass questions |
| 2026-06-06 | **T7.2–T7.3:** Node export fields + Palimpsest quarry section added |
| 2026-06-06 | **T7.1:** Coverage audit re-run post Topic E |
| 2026-06-06 | **Topics H+I:** Portfolio + cross-project nouns; compass Q6; MCP 38 tools |
| 2026-06-07 | **Topic J:** Trajectory nouns locked (L31–L33); compass Q7; **`propose`** + **`trajectory`** |
| 2026-06-07 | **L34:** **impact preview** on `trajectory show` (plan/apply); next-leaves execution-only |

---

## Coverage audit (2026-06-06 — post Topics H+I)

Poll of `packages/manifold/`, `mcps/manifold/`, `apps/manifold-web/`, `skills/manifold/` against this glossary.

### Code — aligned ✅

| Area | Status |
|---|---|
| CLI compass nouns | `next-leaves`, `spec-audit`, `drift-report`, `portfolio-report`, `render portfolio` |
| MCP tools (**38**) | Matches [MCP tools](#mcp-tools-40--agent-surface) table exactly |
| `change_reason` enum | `correction`, `evolution`, `clarification`, `refactor`, `pivot`, `other` — no live `drift` |
| `drift_report` vs `spec_audit` | Separate tools; descriptions cross-reference glossary |
| `target_status` FSM | All states documented |
| `edge_kind` | `parent`, `depends_on`, `blocks` documented |
| `verdict_mechanism` | All four values documented |
| Validation issue kinds (16) | All listed incl. cross-project edge kinds |
| Portfolio / cross-project | `portfolio_links`, `cross_project_edges`, `node_ref`, `blocked_by` |
| Node export fields | `delegate_to`, `applies_to`, `contract`, `target_shape`, `target_achieved_when`, `target_rationale_ref` — [documented](#graph--traceability-m2) (T7.2) |

### Docs — aligned ✅ (post red-team 2026-06-07)

Skill refs, package README, landscape todo/plan — counts and drift-report meaning updated 2026-06-07 (RT2). **Installed skill** at `~/.claude/skills/manifold` may still lag — see T0.4 / RT6.

### Stale artifacts — flagged

| Artifact | Issue | Action |
|---|---|---|
| `docs/archive/orchestrator-2026-05/` | May orchestrator brainstorm | Historical |
| `docs/archive/manifold-v0.1/` | Pre-landscape design + plan | Superseded by landscape + glossary |

### Reserved — not in code (correct)

| Term | Expected |
|---|---|
| `drift-report` v2 (`--with-llm`) | Deferred (L17) |
| `AGENTS.md compile`, Spec Kit import | Deferred (L14, L15) |
| `ReqIF export`, baselines | Topic G |
| Palimpsest quarry (`harvest`, layer `render`, …) | Partial: portfolio `render` shipped; layer render deferred |
| **Trajectory** (`propose`, `leg`, `accept`, impact preview) | Topic J — L31–L34 locked; not in code |
