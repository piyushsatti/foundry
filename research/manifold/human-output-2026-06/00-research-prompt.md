# Research prompt — Topic K human output layer (v2)

Copy everything below this line into Claude Opus (or a research session with web access).

---

# Manifold research: Human output layer (Topic K)

## What this is

**Manifold** = project compass (SQLite spec graph, MCP/CLI). **Topic K** = human-readable **projections** of that graph — status brief, risk digest, roadmap, delivery view — without duplicating the source of truth.

**Study folder:** `research/manifold/human-output-2026-06/`

**Prior art in repo (read first, do not re-litigate basics):**

| Asset | Path |
|---|---|
| This prompt | `research/manifold/human-output-2026-06/00-research-prompt.md` |
| HTML demo mockups | `.gitignored/demos/human-layer-demo/` — `python3 -m http.server 8765` |
| Red vs Blue + Hats review | `.gitignored/demos/human-layer-demo/REVIEW-SYNTHESIS.md` |
| Landscape baseline | `research/manifold/landscape-2026-06/synthesis.md` |
| Existing web | `apps/manifold-web/` — node browse, spec-audit, drift-report, portfolio |
| Formatter pattern | `packages/manifold/manifold/portfolio_report.py`, `drift_report.py` |

---

## Decisions already locked (from review — do not reopen)

1. **Tri-surface, not binary.** Default surfaces:
   - **Agents** → JSON view-model via MCP (+ markdown export for PR paste)
   - **Humans** → HTML in browser (`manifold serve` / shareable URL)
   - **CI/logs** → text/markdown (`--format md`)
   
   HTML is the human **default**, not the only format.

2. **One view-model, many renderers.** Graph → Python `build_*_view(conn, project_id) → dict` → render HTML | md | JSON. CLI and web call the **same** builder (like drift-report today).

3. **Deterministic templates, not LLM prose as SoT.** Optional LLM summary layer on top only.

4. **Separate views per question** (brief / risk / roadmap / delivery) — not one mega-dashboard.

5. **Every human view includes metadata:** `project_id`, `generated_at` (ISO), optional `stale_warning` if data older than N hours.

6. **v1 defers:** Gantt/resource planning, full-graph Mermaid, Chart.js/D3, React SPA, ReqIF/PDF baselines, schema dates (`target_by`) unless research finds a cheap alternative.

7. **Glossary nouns to use:** `status-brief`, `risk-brief`, `delivery-view`, `Topic K`, `view-model` (propose additions in synthesis if needed).

---

## Research goal

Produce **`research/manifold/human-output-2026-06/synthesis.md`** with **two layers**:

1. **Landscape (R0)** — what's already done/available elsewhere for human-readable project status, roadmaps, and reports (bounded scan).
2. **Manifold v1 (R1–R4)** — what we should ship, informed by R0 (steal patterns, don't rebuild Notion).

> **What should manifold ship in v1 for human output, and what existing tools already solved parts of this?**

Support implementation starting with **one** wired view: `status-brief`.

**Do not:** 60-tool landscape re-run, full Jama/DOORS teardown, or 40-page HCI thesis. Use existing repo research as baseline.

**Read first (avoid duplicate work):**

- `research/manifold/landscape-2026-06/synthesis.md` — M4/M5 gaps, Roady/Linear/ALM mentions
- `apps/manifold-web/` — current human surfaces (partial viewer; no next-leaves HTML)
- `docs/manifold/todo.md` — RT* audit follow-ups (2026-06-07)

---

## Required research questions (answer all five)

### R0. Landscape — what's done & available (bounded)

**Purpose:** Manifold is not inventing “status briefs” from zero. Before R1–R4, scan what humans already use and what surfaces exist — so v1 **steals** proven patterns and **doesn't** rebuild Linear/Notion.

**Scope cap:** ~12 tools/patterns max. ~2 pages in synthesis. Group by **human question**, not vendor category.

**Start from repo baseline** — extend/update, don't re-research from scratch:

| Already in landscape synthesis | Relevant to Topic K |
|---|---|
| Roady, RealityCheck | plan status, drift, human-facing reports |
| Linear, Notion, Jira | roadmap/status UI (human HTML) |
| GitHub Actions job summary | HTML report in CI — pattern steal |
| Jama, Polarion, StrictDoc | exec/traceability views (brief only) |
| Grafana / dashboards | ops metrics — boundary, not competitor |
| Mermaid / GitHub rendering | diagram-as-code in docs |
| manifold shipped today | portfolio-report, drift HTML, web partial |

**Deliver: landscape table** (one row per tool/pattern):

| Name | Human question(s) answered | Primary surface | HTML/report quality | API/agent surface | Steal for manifold? | Gap vs manifold graph |
|---|---|---|---|---|---|---|
| e.g. Roady | what's next, drift | CLI + md + MCP? | … | … | **steal / skip / interop** | no rationale ledger |
| e.g. GH Actions summary | CI pass/fail digest | HTML in UI | … | API | **steal** layout pattern | not spec graph |
| … | … | … | … | … | … | … |

**Must include at least one row each for:**

- Ticket/roadmap SaaS (Linear or Notion)
- Plan-of-record OSS (Roady or closest)
- CI HTML summary pattern (GitHub Actions or similar)
- Enterprise ALM exec view (one of Jama/Polarion — 1 paragraph max)
- **Manifold today** (what's already shipped in `manifold-web` + `render` + md formatters)

**Must conclude with:**

- **Steal list** — 3–5 concrete UI/patterns to copy (with URLs/screenshot refs if public)
- **Skip list** — what looks tempting but is out of scope or wrong altitude
- **Interop list** — what manifold links to rather than replaces (Jira dates, Notion board)
- **White space confirmed** — 2–3 sentences: what *still* no tool does with a **queryable spec graph** (tie to landscape M5/M4)

**Optional quick scan (1 row each if found):** Plane, Height, Productboard, Statuspage, Confluence status macro, Backstage software catalog UI.

### R1. Cognitive comparison (evidence-based, concise)

Using the **Acme Checkout demo** (`.gitignored/demos/human-layer-demo/brief.html` vs `compare.html` terminal/md columns):

| Human question | Compare 3 surfaces | Metric |
|---|---|---|
| Where are we? | terminal · md table · HTML brief | Time-to-answer, error rate on blockers |
| What's at risk? | 3 CLI outputs · merged HTML risk | Working memory / scan path |
| What next? | `next-leaves` text · HTML delivery view | Engineer vs lead audience |

**Deliver:** 1-page comparison table + **3–5 citations** (Nielsen, Tufte, GOV.UK, or comparable — no blog spam).

**Must conclude:** Which HTML capabilities are **v1 must-have** vs v2 vs avoid:

- Semantic color / status encoding
- LOD via `?detail=summary|standard|full` (query param, not localStorage)
- Modals / drill-down to node pages
- Deep links / shareable URLs
- Static export (email/Slack screenshot/PDF) vs live serve

### R2. Visual vocabulary (diagrams & charts)

Manifold data is already a graph. Research **when humans want each visual** and what manifold should auto-generate.

**Build and extend this matrix** — every row must end with **v1 / v2 / don't**:

| Human question | Best visual | Manifold data | Notes |
|---|---|---|---|
| Where are we? (counts) | Stat cards / simple bar | `list_targets` rollup | CSS-only ok? |
| Who blocks whom? | Small flowchart (≤8 nodes) | `cross_project_edges`, `blocked_by` | Not full graph |
| Spec decomposition | Layer tree / swimlane | `parents`, `layer` | Cap at N nodes |
| Plan as-is → to-be | Numbered leg sequence | `trajectory_legs` | Prefer over Gantt in v1 |
| Company bet map | Theme × team matrix | `portfolio-report` | Extend existing table? |
| What changed recently? | Delta list / timeline | `list_changes_since` | PM-critical — include in brief? |
| Code vs spec | Severity-sorted list | `drift-report` buckets | Merge into risk-brief |

**Mermaid (v1 scope only — research must pick one):**

- **Option A:** Defer all Mermaid to v2
- **Option B:** Blocker subgraph only (cross-project `blocks` edges, max 8 nodes)
- **Option C:** Intent-layer tree only (capabilities under root intent)

Recommend one option with rationale. Cover: server-side SVG vs vendored mermaid vs md export fence for agents. **No CDN dependency** in product (demo CDN is mock-only).

**Charts:** When CSS stat cards suffice vs when a library is worth the dependency (stdlib constraint).

**Anti-patterns to explicitly reject:** full-graph hairball, Mermaid as second SoT, Gantt as PM, chartjunk donuts with wrong proportions.

### R3. Architecture & agent parity

Propose concrete shape for foundry:

```
SQLite → queries → build_status_brief_view() → dict (view-model)
                      ├→ MCP peek_status_brief (JSON)     ← agents / skill
                      ├→ GET /projects/{id}/brief (HTML)  ← humans
                      ├→ CLI render project … --format md ← CI/PR
                      └→ optional --format html (stdout/file)
```

Answer:

- View-model **JSON schema sketch** for `status-brief` (fields: `generated_at`, `overall`, `shipped[]`, `in_flight[]`, `blocked[]`, `at_risk[]`, `theme_link?`, `changes_since[]?`)
- Should agents **scrape HTML**? (Expected answer: no — MCP JSON is canonical)
- How skill routes chat: summarize from JSON + offer URL to human
- Reuse `manifold_web/html.py` CSS vs new module
- Content negotiation / Accept header — needed in v1?

Reference **2–3 comparables from R0** — do not introduce new tools here without adding them to R0 table first.

### R4. v1 ship list vs defer (actionable)

**Must output a ranked table:**

| Priority | Item | Rationale | Effort (S/M/L) |
|---|---|---|---|
| P0 | … | … | … |

Minimum expected P0 items (validate or reorder):

- `build_status_brief_view()` + golden JSON fixture from test portfolio data
- `GET /projects/<id>/brief` HTML route
- MCP `peek_status_brief` (or extend existing read tool)
- `generated_at` + project label on every view
- Skill routing: human question → view-model / URL

Defer candidates (validate): roadmap HTML, risk-brief merge, Mermaid, trajectory HTML, PDF export, `target_by` schema.

---

## Out of scope (do not spend words)

- Replacing Notion/Jira/Linear
- Topic C AGENTS.md compile (unless 1 paragraph boundary)
- Enterprise ReqIF baselines (Topic G)
- Building the demo into production code (research only)
- Implementing manifold changes in foundry

---

## Deliverable structure (strict)

Write to **`research/manifold/human-output-2026-06/synthesis.md`**:

```markdown
# HTML human output — research synthesis (YYYY-MM-DD)

## Executive summary (≤8 bullets)

## R0 Landscape — what's done & available (table + steal/skip/interop lists)

## R1 Cognitive comparison (table + citations)

## R2 Visual vocabulary (matrix with v1/v2/don't on every row)

## R3 Architecture (diagram + view-model JSON sketch + MCP tool name)

## R4 v1 ship list (ranked P0/P1/P2 table)

## Disputed items for user decision (≤3 rows)

## References (linked, ≤20)
```

Optional raw notes, screenshots, session paste → `research/manifold/human-output-2026-06/results/`

**Length cap:** ~3,000–5,000 words. If over, trim R0 optional scans and HCI citations first — **do not drop R0 entirely**.

---

## Constraints

- Manifold web: **stdlib Python**, no React v1
- Single writer DB; views are read-only projections
- Foundry: `~/Developer/projects/foundry`
- Glossary: `docs/manifold/glossary.md`
- Test fixture reference: `seed_portfolio_fixture` in `packages/manifold/tests/conftest.py`

---

## Review findings to incorporate (not re-debate)

From Red vs Blue + Hats (2026-06-07) — full notes: `.gitignored/demos/human-layer-demo/REVIEW-SYNTHESIS.md`

| Finding | Research must address |
|---|---|
| HTML looks authoritative without timestamps | Mandate `generated_at` / staleness UX |
| PMs need deltas | Include `list_changes_since` in brief or v1 defer with reason |
| Blockers need team names not bare `node_ref` | Propose label resolution (`project_id` → team name from registry?) |
| Research scope was too wide | R0 bounded (~12 rows); R1–R4 stay narrow |
| MCP JSON same as HTML brain | R3 view-model is central deliverable |
| Mermaid explodes on real graphs | R2 must pick bounded v1 option or defer |
| Chat users need URL + short summary | R3 skill routing |
| Portfolio altitude | Brief should link up to theme when `portfolio_links` exist |

---

## Optional (only if under word cap)

- a11y minimum bar for internal briefs (1 paragraph)
- Print/PDF path (defer recommendation ok)
- Trajectory `show` as HTML plan/apply page vs md

**Do not commit to foundry unless asked.**
