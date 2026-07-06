# Topics H + I — Portfolio (A) and cross-project links (B)

**Status:** shipped (2026-06-06). Example C (external integrations, governance) **out of scope**.

**Related:** [`glossary.md`](../../manifold/glossary.md), [`todo.md`](../../manifold/todo.md) (full **federation** deferred).

---

## Problem

Mid-sized orgs run **multiple team projects** in one manifold (software, AI, pipeline). Today:

| Gap | Symptom |
|---|---|
| **A — Portfolio** | No company theme roll-up; exec rebuilds slides from three team roadmaps |
| **B — Cross-project** | “Product blocked on AI” lives in Slack; `blocks` edges don’t cross `project_id` |

**Non-goal (Example C):** Salesforce SLAs, shadow notebooks, CRM — later with external integrations.

---

## Architecture (one manifold, many projects)

```
ONE $MANIFOLD_DB
├── project: portfolio          ← company themes (Topic H)
├── project: product-app        ← team graph
├── project: ai-platform
└── project: platform-pipeline

portfolio_links        ← theme → team node (A)
cross_project_edges    ← team node → team node across projects (B)
```

**Not** three manifold installations. **Not** “cross-manifold.”

---

## Locked decisions

| ID | Decision | Date |
|---|---|---|
| **L18** | **One DB, many projects** — cross-team = cross-**project** within one manifold | 2026-06-06 |
| **L19** | Reserved portfolio project id: **`portfolio`**; default theme layer: **`theme`** | 2026-06-06 |
| **L20** | **Portfolio link** (`portfolio_links` row) = theme **tracks** a team node; not a graph edge | 2026-06-06 |
| **L21** | Cross-team deps = **`cross-project edge`** (`cross_project_edges`); kinds: `blocks`, `depends_on` only in v1 | 2026-06-06 |
| **L22** | Reserve **federation** (Palimpsest `parents: [project:x@N]`) for future parent-refinement across projects — **not** v1 B | 2026-06-06 |
| **L23** | **node_ref** URI: `project_id/node_id` (e.g. `ai-platform/C.4`) in APIs, CLI, MCP | 2026-06-06 |
| **L24** | Human exec slide = **`render portfolio --template quarter-roadmap`**; roll-up CLI = **`portfolio-report`** | 2026-06-06 |
| **L25** | Cross-project chain MCP = **`list_cross_blocking_chain`** (mirrors `list_blocking_chain`) | 2026-06-06 |
| **L26** | `portfolio_links` keyed by **`theme_node_id`** only; themes always in project `portfolio` | 2026-06-06 |
| **L27** | **`render`** scoped: v1 = `render portfolio --template …`; layer narrative = future `render project --layer` | 2026-06-06 |
| **L28** | Report JSON key **`blocked_by`**: array of `node_ref` strings | 2026-06-06 |
| **L29** | Cross-edge **CLI deferred** — MCP-only v1 for create/delete/list | 2026-06-06 |
| **L30** | MCP write fields **`peers_depends_on`** / **`target_blocks`** = in-project `depends_on` / `blocks` edges | 2026-06-06 |

---

## Proper nouns (canonical)

See [`glossary.md`](../../manifold/glossary.md) sections **Portfolio** and **Cross-project links**.

---

## Topic H — Portfolio behavior

### Data model

**`portfolio` project** — register like any project:

```json
{
  "layers": [{"name": "theme"}]
}
```

**`portfolio_links` table:**

| Column | Meaning |
|---|---|
| `theme_node_id` | Node in `portfolio` project (layer `theme`) |
| `project_id` | Team project |
| `node_id` | Team node tracked by theme |
| `created_at` | Audit |

### Surfaces

| Surface | Path / command |
|---|---|
| CLI | `manifold portfolio-report [--theme T.1] [--format md\|text]` |
| CLI | `manifold render portfolio --template quarter-roadmap [--theme T.1] [--format md]` |
| MCP | `portfolio_report`, `link_portfolio`, `unlink_portfolio`, `list_portfolio_links` |
| HTTP HTML | `GET /reports/portfolio` |
| HTTP JSON | `GET /api/v1/reports/portfolio` |

Extends `/reports/targets`; does not replace `list_targets`.

---

## Topic I — Cross-project behavior

### Semantics

- **`blocks`:** `src` not ready until `dst` is `target_status=achieved`
- **`depends_on`:** v1 treated same as `blocks` for `next_leaves` exclusion

### Surfaces (v1)

| Surface | Name |
|---|---|
| MCP write | `create_cross_edge`, `delete_cross_edge` |
| MCP read | `list_cross_edges`, `list_cross_blocking_chain` |
| Query | `next_leaves` excludes cross-blocked leaves; `portfolio_report` populates `blocked_by` |

**Topic F note:** [`orchestrator-contract.md`](../../manifold/orchestrator-contract.md) — orchestrator must call `list_cross_blocking_chain` before dispatch.

---

## Implementation record (shipped)

### Master todo

**Topic H — Portfolio ✅:** H1–H11 (schema, writes, queries, CLI/MCP/HTTP, render, tests).

**Topic I — Cross-project ✅:** I1–I11 (schema, validation, `next_leaves` filter, MCP, tests).

**Docs ✅:** D1–D6 (glossary, business-model, architecture, user-guide, orchestrator stub, impl plan).

### Verification

```bash
cd packages/manifold && python3 -m unittest discover
cd mcps/manifold && python3 -m unittest tests.test_mcp_server
cd apps/manifold-web && python3 -m unittest discover -s tests -p 'test_*.py'
```

MCP tool count after ship: **38** (was 30).

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-06 | Initial design; A+B scope; C deferred; L18–L24 locked |
| 2026-06-06 | Shipped H+I; L25–L30 naming locks; glossary canonical |
| 2026-06-07 | Merged design + plan; moved to `docs/archive/topics/` |
