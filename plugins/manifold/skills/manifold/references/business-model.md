# Portfolio + cross-project — one DB, two coordination patterns

**Audience:** agents and humans wiring mid-size multi-team manifold setups.

**Canonical nouns:** [`glossary.md`](../../docs/manifold/glossary.md) (Portfolio + Cross-project sections).

---

## 1. One DB, many projects (L18)

Register separate team graphs as projects in one `$MANIFOLD_DB`:

- `product-app`, `ai-platform`, `platform-pipeline` — team specs
- `portfolio` — reserved project id for company **themes** (layer `theme`)

Cross-team coordination is **cross-project**, never “cross-manifold.”

---

## 2. Example A — Portfolio visibility (Topic H)

**Problem:** Exec wants “Q3 Reliability” status without merging three roadmaps by hand.

**Pattern:**

1. Create theme node `T.1` in project `portfolio`.
2. **Track** team nodes: `link_portfolio(theme=T.1, project=product-app, node=I.2)` etc.
3. Read roll-up: `portfolio-report` or `GET /reports/portfolio`.
4. Paste exec slide: `render portfolio --template quarter-roadmap`.

**Not this:** `list_targets` — that is a flat status filter, not theme-grouped.

---

## 3. Example B — Cross-project blocking (Topic I)

**Problem:** Product leaf is blocked on AI platform work; today that lives in Slack.

**Pattern:**

1. `create_cross_edge(src=product-app/R.12, dst=ai-platform/C.4, kind=blocks)`
2. `next_leaves(product-app)` excludes `R.12` until `C.4` is `achieved`.
3. `portfolio-report` shows **`blocked_by`**: `["ai-platform/C.4"]`.
4. Orchestrator (Topic F): call `list_cross_blocking_chain` before dispatch.

**Not this:** `realized_by_external` (deprecated in-project field) or **federation** parent refs (L22, future).

---

## 4. Example C — deferred

CRM refs, shadow notebooks, Salesforce SLAs — external integrations track, not v1.

---

## 5. Orchestrator handoff (Topic F)

Full pre-dispatch checklist: [`docs/manifold/orchestrator-contract.md`](../../../docs/manifold/orchestrator-contract.md).

Before dispatching work on a leaf, orchestrator skill should:

1. `peek_project` + `next_leaves(project_id)` — open frontier
2. `list_cross_blocking_chain(project_id, node_id)` — cross-project blockers
3. `list_blocking_chain(project_id, node_id)` — in-project blockers
4. `drift_report(project_id)` — optional spec↔code gate on realization layer

Manifold holds intent; orchestrator holds execution (Jira → PR).
