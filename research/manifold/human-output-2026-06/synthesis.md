# HTML human output — research synthesis (2026-06-07)

## Executive summary

- Manifold's v1 "Topic K" human output layer should ship a single deterministic projection — `status-brief` — as a tri-surface (MCP JSON · HTML page · markdown export) built from one `build_status_brief_view(conn, project_id) → dict` builder, mirroring the existing `drift_report.py` formatter pattern. Everything else (risk-brief, delivery-view, Mermaid, roadmap HTML) is v2.
- The landscape is crowded with tools that answer "where are we?" but none combine a queryable spec graph, drift detection (M4), compass queries (M5) and MCP-native delivery (M7) — the white space already identified in the 2026-06 landscape research holds. The right v1 posture is steal proven UI patterns (Linear's plain-text "Project Update" with health pill; GitHub Actions `$GITHUB_STEP_SUMMARY` markdown; GOV.UK Tag/Summary-list patterns; Statuspage's component-status roll-up) and link out (Jira, Linear, Notion) instead of replacing them.
- Three review-driven non-negotiables: (1) every view shows `generated_at` ISO timestamp + optional stale_warning (HTML "looks authoritative" without it); (2) `list_changes_since` deltas appear inside the status-brief, not in a separate view (PMs need them on the first scan); (3) Mermaid is bounded to one optional subgraph (blocker map ≤8 nodes) or deferred — Mermaid's official config schema documents `maxEdges` default at exactly 500 (mermaid.js.org/config/schema-docs/config-properties-maxedges.html, v11.15.0), and the historic hard-coded ceiling was 280 edges (mermaid-js/mermaid issue #5042: `if (gk.length < 280) … else throw new Error('Too many edges')` in v10.6.1 before PR #5086), so a "compile the whole graph" view will crash on real portfolios.
- Cognitive evidence (Nielsen Norman F-pattern, progressive disclosure, GOV.UK Tag guidance, Tufte data-ink) supports: semantic status pills, LOD `?detail=summary|standard|full` via query param, deep-linkable URLs, deltas above the fold. Avoid: tabs/accordions for primary content, color-only encoding, donut charts, chartjunk, fake Gantt.
- View-model JSON is canonical for agents (MCP `peek_status_brief`); humans get HTML at `GET /projects/<id>/brief` (default surface); CI gets `manifold render project --format md` for PR paste. Skill routing for chat: summarize from the JSON view-model and offer the shareable URL — agents never scrape the HTML.
- v1 P0 (5 items): `build_status_brief_view()` + golden fixture; HTML route reusing `manifold_web/html.py` CSS; MCP `peek_status_brief` tool returning structured JSON; `generated_at` + project label + team-name resolution on every render; chat skill that returns "1-paragraph summary + URL." Defer: roadmap, risk-brief merge, delivery-view HTML, Mermaid, PDF, `target_by` schema.
- Disputed for user decision: (a) Mermaid v1 — Option B (blocker subgraph) vs Option A (defer entirely); (b) risk-brief merge into status-brief vs separate view; (c) content-negotiation via `Accept` header vs explicit `?format=` query param.

---

## R0 Landscape — what's done & available

The landscape research from 2026-06 already surveyed ~60 tools. This R0 is a bounded refresh focused on the human-output question: *what's already shipped for "status brief / risk / roadmap" surfaces*, grouped by the human question they answer. Cap: 12 rows.

| # | Name | Human question(s) | Primary surface | HTML/report quality | API/agent surface | Steal / Skip / Interop | Gap vs manifold graph |
|---|---|---|---|---|---|---|---|
| 1 | **Linear — Project Updates** | "Where are we?" / "Is it on track?" | SaaS web + Slack mirror | High; structured "plain-text update + health indicator (on track / at risk / off track)"; weekly cadence with reminders | GraphQL API; Slack channel mirror; markdown copy via ⌘K | **Steal** — the health-pill + short prose + auto-broadcast loop is the gold standard | Not graph-aware; updates are author-written prose, not derived from a spec |
| 2 | **Notion — project DB + status property** | "Where are we?" / "What's the roadmap?" | Composable DBs (board / timeline / list) | Medium; pretty but author-curated; status is a custom property | Public API; embeds | **Interop** — link from manifold brief to a Notion roadmap page when one exists; do not rebuild | Author-maintained; no drift detection; no queryable structure beyond the DB you build |
| 3 | **Jira — boards/dashboards** | "Where are we?" / "What's blocked?" | Enterprise web | Medium; configurable gadgets; status fields per workflow | REST API | **Interop** — link out for ticket-level dates and assignees | Not a spec graph; no decomposition layer; no MCP |
| 4 | **GitHub Actions — `$GITHUB_STEP_SUMMARY`** | "Did CI pass? what changed?" | Markdown in CI run page | Excellent for ephemeral run reports; GFM tables, headings, native Mermaid | File-append from any step; consumable by `austenstone/job-summary` etc. | **Steal** — exact pattern manifold should use for `--format md` (write to `$GITHUB_STEP_SUMMARY` from CI) | Per-run, not per-project; no persistence; no graph |
| 5 | **StrictDoc** | "Are requirements covered & traced?" | Static HTML + FastAPI web (Jinja, Turbo/Stimulus, "HTML over the wire") | High for traceability; multiple export formats (HTML, RST, ReqIF, PDF, JSON, Excel); Diff/Changelog screen | Python API; JSON export; web UI | **Steal** — the "one model → many renderers (HTML/RST/PDF/JSON)" architecture is exactly the manifold pattern; Hotwire/no-React stance also matches v1 constraints | StrictDoc is doc-shaped, not project-shaped; no "where are we" brief; no MCP |
| 6 | **Roady / RealityCheck** (prior landscape baseline) | "Is the plan still real?" | CLI + lightweight HTML | Plan-of-record + drift; closest philosophical neighbor; small footprint | CLI; file-based | **Steal** — drift framing and "plan-as-text" discipline | Not MCP-native; no compass queries; no portfolio altitude |
| 7 | **Jama Connect** (enterprise ALM) | "Are we compliant? what's the trace?" | Per-project dashboards (≤20 widgets), Velocity reports, traceability matrix | High but heavyweight; PNG/CSV/PDF export per widget | REST | **Skip** for v1; **interop** later via export. Steal one idea: the *project dashboard as the landing surface*, with widgets you can toggle. | Heavy; license-bound; not graph-native; no MCP |
| 8 | **Polarion ALM — LiveDocs + My Polarion dashboards** | "What's the status of this spec?" | Browser-based "live, always up-to-date, fully configurable" dashboards; LiveDocs with per-paragraph identifiers; document workflow with states like "in rework" / "reviewed" | High enterprise quality | Open API; custom widgets | **Skip** (out of altitude) but note: per-paragraph identifiers + document-workflow states echo manifold's node addressing | Heavy ALM; no MCP; not OSS |
| 9 | **GitHub-rendered Mermaid in markdown** | "What does this depend on?" | Mermaid fenced block, native render in MD/issues/PRs/gists since Feb 14 2022 (GitHub Blog, Woodward & Biagianti) | Excellent for ≤~50 nodes; default `maxEdges = 500` in v11.15+, hard cap of 280 in v10.6.1 and earlier (issue #5042) | Server-renders to inline iframe SVG | **Steal for `--format md` only** (text fence) — works free in GitHub & many docs platforms | Not interactive; not graph-queryable; degrades on large graphs |
| 10 | **Backstage Software Catalog (CNCF)** | "Who owns this? what's in our portfolio?" | React SPA, entity pages with About card, owners, tags, relations | High but plugin-heavy; YAML-as-source-of-truth pattern is relevant | REST + plugin SDK | **Steal** the "entity page = About card + tabs (overview / quality / docs)" layout idea for manifold's per-project page | Not status-oriented; ownership catalog, not delivery view; React, which v1 forbids |
| 11 | **Statuspage (Atlassian) / OneUptime / Cachet** | "Is the service up? what's degraded?" | Public status page with component roll-up: investigating/identified/monitoring/resolved; component-level "operational / degraded / outage" | Excellent at a glance; very small visual vocabulary; subscribe to updates | REST `summary.json` returns the whole page state; webhook | **Steal** the *roll-up indicator + per-component status list* pattern for "overall: in-flight" + per-leaf status | Ops-altitude, not project-altitude — boundary not competitor |
| 12 | **Confluence — Status macro + Page Properties Report** | "What's the status of these initiatives?" | "Status macro displays a coloured lozenge (a rounded box) that is useful for reporting project status" (Atlassian Confluence Data Center docs); Page Properties Report macro "lets you create a summary page that pulls in information from multiple pages" — max 60 labels, max 3000 pages | Medium; widely used inside enterprises for "status board" pages | API | **Interop** (link out) and **steal**: the Status lozenge text + color is a 20-year-old pattern that lands instantly with non-engineer audiences | Author-maintained; no graph; aggregation is by label, not relationship |
| 13 (already shipped) | **manifold today** — `portfolio_report.py`, `drift_report.py`, partial web app (node browse, spec-audit, drift HTML) | "What's drifting?" / "What's in the portfolio?" | CLI + partial stdlib HTML | Drift HTML is the pattern to extend; portfolio_report a working "one builder → multiple renderers" example | MCP (compass queries M5, drift M4) | n/a — this *is* the surface | Doesn't yet answer "where are we?" in one human-readable brief; web parity gaps |

**Optional quick scan** (one-line each, requested):
- **Plane** (open-source Linear alternative): Kanban + cycles + modules, native MCP server, projects-as-YAML; close philosophical neighbor but operates at ticket altitude, not spec altitude — **interop** candidate, not competitor.
- **Productboard / Height**: feature/product roadmap surfaces with bet maps; **interop** later via export.

### STEAL LIST (concrete UI/patterns to copy)

1. **Linear's Project Update format** — short plain-text "what shipped / what's at risk / next" + a single health pill ("On track / At risk / Off track"). Source: `linear.app/now/how-we-built-project-updates`. Manifold's `status-brief` should look like a Linear Project Update *generated from the graph*, not authored manually.
2. **GitHub Actions `$GITHUB_STEP_SUMMARY` markdown** — exact pattern for the `--format md` CLI surface. Write GFM tables and headings to a single markdown string; in CI, append to `$GITHUB_STEP_SUMMARY`; outside CI, print to stdout. Source: Konrad Pabjan, *Supercharging GitHub Actions with Job Summaries*, GitHub Blog, May 9 2022.
3. **GOV.UK Tag + Summary-list components** — accessible, text-first status lozenges (no color-only encoding; adjectives not verbs; not interactive). Use the Summary-list `<dl>` pattern for the project metadata block (generated_at, layer, last drift run). Source: `design-system.service.gov.uk/components/tag/` and `/summary-list/`.
4. **Statuspage component roll-up** — one overall indicator ("All Systems Operational" / "Partial Outage") plus a flat list of components with per-component status. Manifold's brief should similarly carry one project-level health pill plus per-leaf state.
5. **StrictDoc's "one model → many renderers"** — the architecture for v1: builder → dict → render HTML | md | JSON, with the same generators used by CLI export and the web app. Source: `strictdoc.readthedocs.io` Design Document.

### SKIP LIST

- **Notion-style composable databases / drag-drop board builder**: manifold is not authoring tickets; the spec graph is the source of truth.
- **Jama / Polarion enterprise dashboards with 20+ widget palettes**: wrong altitude; configurability becomes a liability.
- **Gantt and resource-planning views**: schema doesn't carry dates in v1; faking a Gantt from `trajectory_legs` would mislead. Tufte: "above all else show the data" — don't fabricate a time axis.
- **Live Mermaid of the full graph**: see R2; breaks on real graphs.
- **React SPA**: v1 constraint, also not justified — StrictDoc proves Hotwire/server-rendered HTML scales to thousands of nodes.

### INTEROP LIST

- **Jira / Linear**: link out from the brief when `external_ref` is present on a leaf; never re-render their data.
- **Notion roadmap pages**: link from a project's brief up to a portfolio/theme Notion page when `portfolio_links` exists.
- **GitHub PRs and Actions**: emit the `--format md` brief into `$GITHUB_STEP_SUMMARY`; link drift findings to PR review comments.
- **Confluence Page Properties Report**: organizations that already maintain a "status board" Confluence page can paste the manifold markdown brief into a child page and let Confluence aggregate — no manifold work needed.

### WHITE SPACE CONFIRMED

The 2026-06 landscape's M4+M5+M7 finding holds: no surveyed tool combines drift detection against a code-and-spec graph (M4), structured compass queries against that graph (M5), and MCP-native delivery to agents (M7). Linear and Notion are author-maintained; Jama/Polarion are heavyweight ALMs without MCP; Statuspage and GitHub Job Summaries are run-shaped, not project-shaped; Backstage is a catalog, not a status surface. Manifold's edge is that the *brief is a query over a live graph the agent already updates*, so it is automatically consistent with code and with drift findings — not a doc someone forgot to update.

---

## R1 Cognitive comparison

Comparison per the three human questions, using the Acme Checkout demo mockups (brief.html, compare.html, risk.html) as the test bed.

| Question | Terminal output | Markdown table | HTML brief | Time-to-answer (best) | Working memory load |
|---|---|---|---|---|---|
| **"Where are we?"** | `manifold list_targets --rollup` — fast but linear stream; user must mentally tally states from text | `--format md` table — scannable in a Slack/PR context; still requires reading row by row | HTML brief w/ overall pill + shipped/in-flight/blocked sections + Summary/Standard/Full LOD toggle | **HTML brief** — single fixation on the pill answers "are we OK" in <2s; F-pattern scan picks up section headers | Lowest in HTML (pill + headers do the chunking); highest in terminal |
| **"What's at risk?"** | 3 separate CLI invocations (`drift-report`, `list_blocked`, `spec-audit`) — user must merge in their head | Merged markdown risk digest | HTML risk view with severity-sorted list, team-name labels (not bare `node_ref`), drift bucket counts | **HTML risk** — pre-merged + sorted by severity removes the merge step | Working-memory cost of the CLI approach is real: ≥3 outputs × ≥10 items each ≈ violates 7±2 chunks |
| **"What next?"** | `next-leaves` text — fine for an engineer | n/a | HTML delivery-view w/ next legs + theme link + owner | Engineer audience: terminal is fine. Lead audience: HTML wins because the theme link gives context | Lead audiences need *why* before *what* — HTML brief can answer both; CLI cannot |

**Citations (5):**

- Nielsen, J. (April 17 2017, updated from 2006 original 232-user eyetracking study). *F-Shaped Pattern of Reading on the Web: Misunderstood, But Still Relevant (Even on Mobile)*, Nielsen Norman Group — "users first read in a horizontal movement, usually across the upper part of the content area … finally users scan the content's left side in a vertical movement." Implication: put the health pill and `generated_at` top-left; put section headings left-aligned so the F-pattern stem hits them.
- Nielsen, J. (December 3 2006). *Progressive Disclosure*, Nielsen Norman Group — "In practice, designs that go beyond 2 disclosure levels typically have low usability because users often get lost when moving between the levels." Implication: the demo's Summary / Standard / Full LOD toggle is exactly two levels of disclosure beyond default — acceptable. Use a query param (`?detail=`), not localStorage, so URLs are shareable and reproducible.
- Tufte, E. (1983/2001). *The Visual Display of Quantitative Information* — "Above all else show the data … maximize the data-ink ratio … erase non-data ink." Implication: no donut charts for "12 in flight, 3 blocked" — use a stat card or a `<dl>`. Reject chartjunk and decorative SVG.
- GOV.UK Design System — *Tag component* — "Do not use colour alone to convey a status … Use adjectives (descriptive words) and not verbs … Do not make a tag interactive." Implication: status pills carry text labels ("Blocked", "In flight"), are non-interactive, and meet 4.5:1 contrast. Use grey for inactive, red/orange/blue/green semantically.
- Atlassian Statuspage component-status pattern (`status.atlassian.com/api/v2/status.json`) — the "blended status" with values like "All Systems Operational / Partial System Outage / Major Service Outage." Implication: manifold's overall project status should be a single derived label from a small, fixed vocabulary, not a free-text field.

**v1 must-have vs v2 vs avoid (HTML capabilities):**

- **Must-have v1**: semantic color + text status pills (GOV.UK Tag); LOD via `?detail=summary|standard|full` query param; `generated_at` + project label + team-name resolution; deep-linkable URLs; static export (curl the route → save HTML or pipe to `--format md`).
- **v2**: modals / drill-down into per-node pages (we already have node browse); print-stylesheet PDF path; small CSS sparklines for change counts.
- **Avoid v1**: localStorage state (breaks shareability), client-side JS framework, JS-driven layout, dropdowns hiding primary content, color-only encoding, donut charts, animated transitions, "loading" states (everything is server-rendered).

---

## R2 Visual vocabulary

Manifold data is already a graph. Research question: when do humans actually *want* a visual, and what should manifold auto-generate?

| Human question | Source data | Visual | v1 / v2 / don't | Notes |
|---|---|---|---|---|
| "Where are we? (counts)" | `list_targets` rollup | 3–5 stat cards (CSS only: number, label, status color) | **v1** | CSS `display:grid`; no chart library. Tufte data-ink. |
| "Who blocks whom?" | `cross_project_edges` / `blocked_by` | Small flowchart, ≤8 nodes, blocker-subgraph only | **v1 (Option B, see below)** | Mermaid `flowchart LR` rendered server-side to SVG (or md fence) |
| "Spec decomposition" | `parents`, `layer` | Layer tree / nested `<ul>` / swimlane | **v2** | An `<details>`/`<summary>` HTML tree works in v1 without Mermaid |
| "Plan as-is → to-be" | `trajectory_legs` | Numbered leg sequence (ordered list with arrows) | **v1** | Plain HTML/markdown; NOT a Gantt |
| "Company bet map" | `portfolio-report` themes × teams | Extend existing portfolio table (HTML `<table>`) | **v1** (already partly shipped) | Just polish the existing surface |
| "What changed recently?" | `list_changes_since` | Delta list / timeline (ordered list of {when, what, who}) | **v1 — inside the status-brief, not a separate view** | Review finding: PMs need this on first scan |
| "Code vs spec" | `drift-report` buckets | Severity-sorted list grouped by bucket | **v1 — merge into risk-brief later; status-brief shows count + link** | Existing drift HTML stays as deep view |

### Mermaid v1 scope — recommendation: **Option B (blocker subgraph only)** with a hard guard

Mermaid's official config schema (mermaid.js.org/config/schema-docs/config-properties-maxedges.html, current as of v11.15.0) sets `maxEdges` default to **exactly 500** — "Defines the maximum number of edges that can be drawn in a graph." The historic hard-coded ceiling is documented in the mermaid-js GitHub repository: issue #5042 cites the source `if (gk.length < 280) … else throw new Error('Too many edges')` from mermaid v10.6.1, with PR #5086 raising the limit to 500. A real manifold spec graph at portfolio altitude will exceed this immediately. Therefore:

- **Reject Option C** (intent-layer tree) — capability trees explode quickly; even with caps users will hit the wall.
- **Reject "render the whole graph"** — pure hairball; per Tufte, this is non-data ink.
- **Adopt Option B**: render a Mermaid `flowchart LR` containing only the project node, its direct upstream blockers, and any nodes it directly blocks downstream — bounded at 8 nodes server-side, with a fallback message ("subgraph truncated — see /projects/<id>/graph") when exceeded.

**Rendering strategy:**

- **`--format md`**: emit a ```` ```mermaid ```` fenced block; this is what GitHub, GitLab, VS Code, dendron, Typora, and most modern doc tools render natively (Mermaid was added to GitHub Markdown on Feb 14 2022 per GitHub Blog, Martin Woodward & Adam Biagianti, *Include diagrams in your Markdown files with Mermaid*).
- **HTML surface**: server-side SVG via a vendored, ASGI-free mermaid CLI invocation or a pre-rendered SVG cached per node-revision. **No CDN dependency in the product** — the demo CDN is mock-only. If a vendored renderer is too costly for v1, drop Mermaid from the HTML surface and keep the markdown fence (the GitHub-renderable form) only.
- **JSON / MCP surface**: never return Mermaid syntax — return the structured `blocked_by[]` and `blocks[]` arrays. Agents reason over JSON.

### Charts

Stat cards (CSS-only) cover every v1 need. No Chart.js, no D3, no donut. A library is only worth its weight when displaying continuous distributions (latency histograms, burn-down) — none of which v1 needs. Per Tufte and per the manifold "stdlib only" constraint, ship a `<dl class="stats">` and call it done.

### Anti-patterns explicitly rejected

- Full-graph "hairball" Mermaid render — fails at scale, conveys nothing.
- Mermaid as a second source of truth — the SQLite graph is authoritative; Mermaid is a projection.
- Gantt as project management — manifold has no `target_by` dates in v1; faking a time axis would lie.
- Chartjunk donuts with incorrect proportions — "3 of 12 in flight" as a 270° arc is misleading and contributes zero data-ink.
- Color-only status encoding — fails WCAG 1.4.1; GOV.UK explicitly cautions against it.

---

## R3 Architecture & agent parity

```
                        ┌──────────────────────────┐
                        │   SQLite spec graph      │
                        │   (single-writer)        │
                        └────────────┬─────────────┘
                                     │ read-only queries
                                     ▼
                  ┌──────────────────────────────────────┐
                  │  build_status_brief_view(            │
                  │     conn, project_id                 │
                  │  )  →  dict  (the view-model)        │
                  └──────────────────────────────────────┘
                          │            │            │
              ┌───────────┘            │            └───────────┐
              ▼                        ▼                        ▼
       MCP peek_status_brief    GET /projects/<id>/brief   CLI render project
       (structuredContent JSON) (HTML, manifold_web/html)  (--format md|html|json)
              │                        │                        │
              ▼                        ▼                        ▼
          AGENTS / SKILLS         HUMAN BROWSER             CI / PR PASTE
```

This mirrors `drift_report.py` and `portfolio_report.py` today: one query layer, one dict, multiple renderers. The pattern is also exactly StrictDoc's "the web server renders the HTML documents using the same generators that are used by the static HTML export, so the static HTML documentation and the web application interface look identical" — proof from a comparable OSS tool that it scales.

### View-model JSON schema sketch — `status-brief`

```json
{
  "$schema": "manifold/status-brief.v1",
  "project_id": "acme-checkout",
  "project_label": "Acme Checkout",
  "team": "Payments Platform",                  // resolved from registry
  "generated_at": "2026-06-07T18:42:11Z",       // ISO 8601 UTC
  "stale_warning": null,                        // or "data older than 24h"
  "overall": {
    "status": "in_flight",                      // {shipped|in_flight|blocked|at_risk|paused}
    "headline": "On track for 4 of 6 leaves; 1 blocked on auth-svc."
  },
  "shipped":   [ { "node_ref": "...", "label": "...", "shipped_at": "..." } ],
  "in_flight": [ { "node_ref": "...", "label": "...", "owner": "..." } ],
  "blocked":   [ { "node_ref": "...", "label": "...",
                   "blocked_by": [ { "node_ref": "...", "team": "Auth" } ] } ],
  "at_risk":   [ { "node_ref": "...", "label": "...", "reason": "drift:severity-high" } ],
  "changes_since": [                            // last 7 days, capped at 10
    { "when": "2026-06-06T..", "what": "leaf shipped: ...", "who": "..." }
  ],
  "theme_link": {                               // null if no portfolio_links
    "portfolio_id": "checkout-q3",
    "label": "Q3 Checkout Resilience"
  },
  "drift_summary": { "high": 0, "medium": 2, "low": 5,
                      "link": "/projects/acme-checkout/drift" }
}
```

This dict is the **canonical brain** of the brief. HTML, markdown, and JSON renderers all consume it. No renderer derives semantics; they only format.

### Agent parity

- **Agents should NOT scrape HTML.** MCP JSON is canonical. Per the MCP spec, tool results may include `structuredContent` (a JSON value) — `peek_status_brief` returns the view-model dict directly as `structuredContent`, with a serialized JSON `TextContent` block for backwards compatibility (the pattern documented at modelcontextprotocol.io/specification/2025-06-18/server/tools).
- **MCP Apps (SEP-1865, RC 2026-07-28)** opens a future path where the same HTML view could be returned as an embedded sandboxed UI surface inside an MCP host; **do not adopt in v1** — it's RC, not stable, and the JSON-first stance is correct independently.
- **Skill routing for chat**: when a user asks "how's checkout going?", the skill calls `peek_status_brief`, summarizes from the JSON (1–2 sentences from `overall.headline` + `blocked[]` count) and ends with the URL `https://manifold.local/projects/acme-checkout/brief?detail=summary`. Humans get prose + clickable, machines get structured data.

### Module structure

- Reuse `manifold_web/html.py` CSS + base template — do **not** spawn a new module. Add a `brief.html` Jinja-style template (or stdlib `string.Template` if no Jinja dependency) and a small `status_brief.py` builder in `packages/manifold/manifold/`.
- The CSS additions for status pills should be ≤30 lines: 5 semantic classes (`.pill--shipped`, `.pill--in-flight`, `.pill--blocked`, `.pill--at-risk`, `.pill--paused`) following the GOV.UK Tag pattern (uppercase-optional text, 4.5:1 contrast, non-interactive `<span>`).

### Content negotiation

`?format=md|html|json` query param on the route is enough for v1. `Accept` header negotiation is correct REST hygiene but adds parsing complexity and doesn't help humans (browsers always send `Accept: text/html`). **Defer Accept-header negotiation to v2**; revisit if a programmatic consumer asks for it.

### Comparable reference (R0 only)

- StrictDoc's Hotwire architecture is the existence proof for "stdlib-feeling, server-rendered, multi-format export from one model" — manifold should resist the urge to add SPA tooling.
- GitHub Actions Job Summary is the existence proof that markdown-as-report is a first-class human surface, not a degraded fallback.
- Statuspage's `summary.json` is the existence proof for "one JSON endpoint = the entire view-model" — agents and humans both consume from one source of truth.

---

## R4 v1 ship list vs defer

| Priority | Item | Rationale | Effort |
|---|---|---|---|
| **P0** | `build_status_brief_view(conn, project_id) → dict` + golden JSON fixture from test portfolio data (Acme Checkout) | Canonical brain. Everything else depends on this. Golden fixture makes refactoring safe. | **M** |
| **P0** | `GET /projects/<id>/brief` HTML route in `manifold_web` reusing existing CSS | Humans' default surface; closes the web parity gap flagged in red-team. | **S** |
| **P0** | MCP tool `peek_status_brief(project_id)` returning view-model as `structuredContent` | Agent parity; chat skills route through this. | **S** |
| **P0** | `generated_at` (ISO UTC) + project label + team-name resolution (project_id → team via registry) on every render | Review finding: HTML looks authoritative without timestamps; PMs see bare `node_ref` and disengage. | **S** |
| **P0** | Chat skill: "human question → 1-paragraph summary from JSON + shareable URL" | Closes the agent→human handoff loop without scraping HTML. | **S** |
| **P0** | `manifold render project --format md` writing GFM (works in `$GITHUB_STEP_SUMMARY` unchanged) | CI / PR paste path; trivial once builder exists. | **S** |
| **P0** | `stale_warning` field populated when `now - last_drift_run > 24h` | Trust signal; only renders when true. | **S** |
| **P1** | `changes_since[]` populated from `list_changes_since(7d)` inside the brief (capped at 10) | Review finding: PMs need deltas on first scan. Optional `?detail=summary` hides the list; `standard`/`full` shows it. | **S** |
| **P1** | `theme_link` populated from `portfolio_links` when present | Portfolio altitude link-up; brief becomes the entry point to the bet map. | **S** |
| **P1** | `?detail=summary|standard|full` query-param LOD toggle | Per NN/g progressive disclosure (2-disclosure-level limit); cap above summary. | **S** |
| **P2** | `risk-brief` view (separate route, separate builder, **merges** drift buckets + `at_risk[]` + blocked items) | Same architectural pattern; useful but not blocking; review noted "needs team names" — solved by P0 resolution. | **M** |
| **P2** | `delivery-view` HTML (next-leaves + owners + theme) | Engineer/lead split; CLI `next-leaves` already serves engineers. | **M** |
| **P2** | Mermaid `flowchart LR` blocker subgraph (≤8 nodes, server-side SVG with vendored renderer, OR md fence only) | Bounded value; only ship when vendored renderer chosen — no CDN. **Disputed: could also defer to v2 entirely.** | **M** |
| **Defer to v2** | Roadmap HTML (Gantt-like) | No `target_by` in v1 schema; would lie about dates. |
| **Defer to v2** | Full-graph Mermaid / intent-layer tree | Hits `maxEdges=500` limit; per-Tufte non-data ink. |
| **Defer to v2** | PDF export | Static HTML + browser print covers 90% of need; revisit when an exec workflow demands it. |
| **Defer to v2** | `target_by` schema column | Out of scope; cheap alternative is `external_ref` to Jira/Linear where dates already live. |
| **Defer to v2** | `Accept` header content negotiation | `?format=` covers v1; revisit on programmatic-consumer request. |
| **Defer to v2** | React SPA / Chart.js / D3 | Constraint; also not needed per Tufte. |

---

## Disputed items for user decision

| # | Issue | Option A | Option B | Recommended |
|---|---|---|---|---|
| 1 | Mermaid in v1 | Defer all Mermaid to v2 (md-fence only via `--format md`, no HTML rendering) | Ship blocker subgraph (≤8 nodes) as server-side SVG in HTML, md fence in markdown | **B if** a vendored renderer is ≤1 day work; **A otherwise**. Per `maxEdges=500` default (mermaid.js.org/config/schema-docs) and the historic 280-edge cap (issue #5042, `if (gk.length < 280) … else throw new Error('Too many edges')`), anything larger is a trap. |
| 2 | risk-brief vs deltas in status-brief | Merge: status-brief carries `drift_summary` count + `at_risk[]` + `changes_since[]`; no separate risk view in v1 | Separate `/projects/<id>/risk` view in v1 with merged drift/blocked/at-risk lists | **A for v1 (merged), B as P2**. PM review finding says deltas belong in the first scan; engineering teams will still want the dedicated risk view, but not at P0. |
| 3 | Content negotiation | `?format=md\|html\|json` query param (explicit, browser-friendly) | `Accept` header negotiation (REST-correct) | **A**. Browsers always send `Accept: text/html`; explicit `?format=` survives copy-paste of URLs and is unambiguous in logs. |

---

## Optional addenda

**Accessibility minimum bar for internal briefs (1 paragraph).** Internal briefs are still subject to baseline a11y: keyboard navigability (no JS = trivially true), 4.5:1 text contrast (WCAG 1.4.3), do-not-use-color-alone (WCAG 1.4.1) — solved by text labels on every status pill per GOV.UK Tag guidance, plus 1.3.1 (info & relationships) by using `<dl>` for metadata and `<table><th scope="col">` for any tabular data. Per GOV.UK's accessibility statement for its own Design System, the underlying components are fully WCAG 2.2 AA — adopting their HTML patterns is the cheapest way to ship a11y-clean code. No ARIA needed for v1; semantic HTML carries the load.

**Print/PDF path.** Defer. A `@media print` stylesheet (≤20 lines: hide nav, force black text, page-break-inside: avoid on cards) gets exec-ready print output for free; full Selenium-driven PDF (StrictDoc's html2pdf approach) is overkill at v1. Recommendation: ship the print stylesheet in v1 if effort is ≤2 hours; otherwise revisit when someone actually asks.

**Trajectory: HTML plan/apply page vs markdown.** Markdown for v1 — `trajectory_legs` is naturally a numbered list, fits the `--format md` pipeline, and pastes cleanly into a PR. HTML page is a v2 nice-to-have, not a blocker.

---

## References

1. Linear — *How we built Project Updates*. linear.app/now/how-we-built-project-updates
2. Linear Docs — *Initiative and Project updates*. linear.app/docs/initiative-and-project-updates
3. Pabjan, K. (May 9 2022). *Supercharging GitHub Actions with Job Summaries*, GitHub Blog. github.blog/news-insights/product-news/supercharging-github-actions-with-job-summaries/
4. Woodward, M. & Biagianti, A. (Feb 14 2022). *Include diagrams in your Markdown files with Mermaid*, GitHub Blog. github.blog/developer-skills/github/include-diagrams-markdown-files-mermaid/
5. StrictDoc — *Design Document (Traceability)*. strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_25_design-TRACE.html
6. StrictDoc — *User Guide*. strictdoc.readthedocs.io/en/stable/stable/docs/strictdoc_01_user_guide.html
7. Jama Connect — *Working with dashboards*. help.jamasoftware.com/ah/en/analysis---monitoring-your-project/working-with-dashboards.html
8. Polarion ALM — product page. polarion.plm.automation.siemens.com/products/polarion-alm
9. Backstage — *Software Catalog overview*. backstage.io/docs/features/software-catalog/
10. Atlassian Statuspage — *API summary endpoint*. status.atlassian.com/api
11. Atlassian Confluence Data Center — *Status Macro*. confluence.atlassian.com/doc/status-macro-223222355.html
12. Atlassian Confluence Data Center — *Page Properties Report Macro*. confluence.atlassian.com/doc/page-properties-report-macro-186089616.html
13. GOV.UK Design System — *Tag*. design-system.service.gov.uk/components/tag/
14. GOV.UK Design System — *Summary list*. design-system.service.gov.uk/components/summary-list/
15. GOV.UK Design System — *Details (progressive disclosure)*. design-system.service.gov.uk/components/details/
16. Nielsen, J. (Apr 17 2017, updated from 2006). *F-Shaped Pattern of Reading on the Web: Misunderstood, But Still Relevant*, Nielsen Norman Group. nngroup.com/articles/f-shaped-pattern-reading-web-content/
17. Nielsen, J. (Dec 3 2006). *Progressive Disclosure*, Nielsen Norman Group. nngroup.com/articles/progressive-disclosure/
18. Tufte, E. (1983/2001). *The Visual Display of Quantitative Information*. edwardtufte.com/book/the-visual-display-of-quantitative-information/
19. Mermaid — *Config schema (`maxEdges`)*, v11.15.0. mermaid.js.org/config/schema-docs/config-properties-maxedges.html
20. mermaid-js/mermaid — *Issue #5042: Too many edges error* (PR #5086 raised cap from 280 to 500). github.com/mermaid-js/mermaid/issues/5042