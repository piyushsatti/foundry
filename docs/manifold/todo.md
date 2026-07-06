# Manifold landscape — master todo & decisions

**Purpose:** Single checklist so chat sessions don't lose state. Update this file when items complete or new decisions land.

**Canonical refs:**
- [`how-to-use.md`](how-to-use.md) — chat-first usage guide
- [`glossary.md`](glossary.md) — proper nouns (code must match)
- [`research/manifold/landscape-2026-06/synthesis.md`](../../research/manifold/landscape-2026-06/synthesis.md) — research source (complete, committed `c30063b`)
- Ephemeral plans (local): `.gitignored/plans/manifold/` — not in git

**Last updated:** 2026-06-07

---

## Status at a glance

| Area | State |
|---|---|
| Landscape research | ✅ Complete, committed |
| Topic A — rename (`spec-audit`, `pivot`) | ✅ Committed (checkpoint) |
| Glossary + coverage audit | ✅ Committed |
| Implementation plan + master todo | ✅ Committed |
| Topic B — stale skill docs | ✅ Done (2026-06-06) |
| Topic C — AGENTS.md compile | ⏸ Deferred (L14) |
| Topic D — Spec Kit import | ⏸ Deferred (L15) |
| Topic E — drift-report v1 | ✅ Shipped (2026-06-06) |
| Topic H — portfolio (Example A) | ✅ Shipped |
| Topic I — cross-project links (Example B) | ✅ Shipped |
| Topics F, G | ❌ Not started |
| Topic J — trajectory (as-is → to-be) | ✅ Shipped v1 (J1–J2) — [`archive/topics/trajectory.md`](../archive/topics/trajectory.md) |
| Human comprehension redesign | 📝 Plan drafted — [`human-comprehension-redesign-plan.md`](human-comprehension-redesign-plan.md) |
| Orchestrator work | ⏸ Separate track — see [`README.md`](README.md) |

---

## Locked decisions (do not re-litigate without new evidence)

| # | Decision | Date | Where recorded |
|---|---|---|---|
| L1 | **Option 1:** split M3 audit vs M4 spec↔code into separate commands | 2026-06-06 | impl plan A.7, glossary |
| L2 | M3 command = `spec-audit` / MCP `spec_audit` | 2026-06-06 | shipped code |
| L3 | M4 command = `drift-report` / MCP `drift_report` — **shipped v1** (Topic E) | 2026-06-06 | impl plan E |
| L4 | `change_reason = pivot` (was misnamed `drift`); bootstrap migration | 2026-06-06 | `schema.py`, glossary |
| L5 | **No deprecation shim** — old M3 `drift-report` removed entirely | 2026-06-06 | user directive |
| L6 | Glossary is canonical — when code/docs disagree, **fix code/docs** | 2026-06-06 | glossary header |
| L7 | Lead with operational nouns; "ADRs that talk to your agent" positioning | 2026-06-06 | synthesis §3 |
| L8 | Interop with Spec Kit in principle, don't compete — **importer deferred (L15)** | 2026-06-06 | synthesis |
| L9 | Out of scope: new SDD CLI, autonomous agent, mem0/Zep memory | 2026-06-06 | impl plan |
| L10 | Palimpsest quarry (`harvest`, `render`, `restructure`) — separate v0.5 track | 2026-06-06 | impl plan |
| L11 | **Product version stays v0.1.0** — no bump until Pi tags for external compatibility | 2026-06-06 | D6 |
| L13 | **D2:** Require explicit `change_reason` on `update_node` — no silent default to `evolution`; mechanical ops (transition, revert, delete) may auto-set | 2026-06-06 | D2 |
| L14 | **Topic C deferred:** no auto AGENTS.md compile — MCP + CLI canonical; hand-curate `CLAUDE.md` / `CODEX.md` until real need | 2026-06-06 | user |
| L15 | **Topic D deferred:** no Spec Kit importer — convenience interop only; no manifold capability gap | 2026-06-06 | user |
| L16 | **Topic E v1:** `drift-report` = verdict rollup on realizations + flag **unverified** (no mechanism) | 2026-06-06 | user |
| L17 | **Topic E v2 (next):** LLM rationale match (`--with-llm` / judge) — build when opportunity allows | 2026-06-06 | user |
| L18 | **One DB, many projects** — cross-team = cross-**project**, not cross-manifold | 2026-06-06 | portfolio design |
| L19 | Portfolio project id **`portfolio`**; theme layer **`theme`** | 2026-06-06 | portfolio design |
| L20 | **Portfolio link** = theme **tracks** team node (`portfolio_links` table) | 2026-06-06 | portfolio design |
| L21 | **Cross-project edge** (`blocks` \| `depends_on`) — not called federation in v1 | 2026-06-06 | portfolio design |
| L22 | Reserve **federation** for Palimpsest-style parent refs — later | 2026-06-06 | portfolio design |
| L23 | **node_ref** = `project_id/node_id` in APIs | 2026-06-06 | portfolio design |
| L24 | CLI **`portfolio-report`** + **`render portfolio --template quarter-roadmap`** | 2026-06-06 | portfolio design |
| L25 | MCP **`list_cross_blocking_chain`** (mirrors `list_blocking_chain`) | 2026-06-06 | naming audit |
| L26 | `portfolio_links.theme_node_id` only; themes in project **`portfolio`** | 2026-06-06 | naming audit |
| L27 | **`render`** scoped: v1 portfolio templates; layer render deferred | 2026-06-06 | naming audit |
| L28 | JSON key **`blocked_by`**: array of `node_ref` | 2026-06-06 | naming audit |
| L29 | Cross-edge CLI deferred — MCP-only v1 | 2026-06-06 | naming audit |
| L30 | MCP **`peers_depends_on`** / **`target_blocks`** = edge write fields | 2026-06-06 | naming audit |
| L31 | **Topic J artifact** = **`trajectory`** (one word); component = **`leg`** | 2026-06-07 | glossary, trajectory design |
| L32 | **Draft action** = **`propose`**: CLI `trajectory propose`, MCP `propose_trajectory` | 2026-06-07 | glossary |
| L33 | **Trust model:** propose never mutates graph; **`accept`** applies legs via existing writes | 2026-06-07 | trajectory design |
| L34 | **`trajectory show`** includes **impact preview** — simulated post-accept state (Terraform plan→apply); real **`next-leaves`** is execution-only, not a trajectory step | 2026-06-07 | trajectory design |

---

## Open decisions (need answer before/during next work)

| # | Question | Options / notes | Blocks |
|---|---|---|---|
| D1 | **Positioning sentence** — keep "when code diverges" as aspirational until Topic E? | **Locked: factual** — clause ships for projects with verdicts wired (Topic E v1); v2 LLM match deferred (L17) | — |
| D2 | **Default `change_reason=evolution`** on silent `update_node` — force agents to pick a reason? | **Locked: require explicit** on `update_node`; mechanical writes auto-set (relax as needed) | — |
| D3 | **Topic E command shape** — standalone `drift-report` vs `manifold drift code` subcommand? | **Locked: standalone** `drift-report` / MCP `drift_report` (L3) | — |
| D4 | **Topic C output path** — `compile-agents-md` vs …? | **Deferred (L14)** — no auto file; manual host docs | — |
| D5 | **Topic D import name** — `import-speckit` vs …? | **Deferred (L15)** — convenience only, not capability gap | — |
| D6 | **Version bump** — ship rename as v0.1.1, v0.2.0, or patch without tag? | **Locked: stay v0.1.0** — bump only when external users need compatibility | — |
| D7 | **Agent entrypoint** | **Locked:** [`docs/README.md`](README.md) | — |

---

## Immediate work (this sprint)

### Commit batch — rename + glossary (uncommitted)

Working tree has ~25 modified files + 2 new docs. Tests were green (287 manifold + 29 MCP + 102 web) after rename.

- [x] **T0.1** Review diff one more time
- [x] **T0.2** Commit: spec-audit rename, pivot migration, strict change_reason, glossary, todo/plan (`c6c20f8`)
- [ ] **T0.3** ~~Decide version tag (see D6)~~ — **no bump** (L11)
- [x] **T0.4** Re-sync `~/.claude/skills/manifold` copy if using Claude Code install

### Completeness audit follow-up (2026-06-07)

Internal surface-parity audit; fixes tracked below as RT*.

- [x] **RT1** Enforce `change_reason` enum in writes + MCP schema (H2)
- [x] **RT2** Fix repo doc tool counts 38 MCP / 17 CLI (H3)
- [x] **RT3** spec-audit: exclude `created` from unset flood; flag invalid enum (M2 partial)
- [x] **RT4** MCP/web `tests/__init__.py` for discover (M4)
- [x] **RT5** `cli.py` `__main__` guard for `python3 -m manifold.cli` (M6)
- [x] **RT6** Re-sync installed skill (H1) — same as T0.4
- [x] **RT7** Guard `create_cross_edge`: reject self-edge + archived endpoints (M1)
- [x] **RT8** `next-leaves` print exclusion reason (L4) — CLI `--verbose`, MCP `include_excluded`
- [x] **RT9** drift-report: distinguish check errored vs violated (M3)
- [x] **RT10** MCP/web tests for portfolio + cross-project tools (M5)

### Cross-tech dogfood follow-up (2026-06-07)

Testbeds: `obs-fastapi`, `obs-express`, `obs-gin` in `~/.claude/manifold.db`.

- [x] **RT11** `propose_trajectory` validates transition legality at propose time (was deferred to peek)
- [x] **RT12** Document verdict/status independence in SKILL.md + `references/verdicts.md`
- [x] **RT13** Verdict-quality guidance (grep anchoring, curl liveness, branch coupling) in `references/verdicts.md`
- [x] **RT14** Trajectory leg payload worked examples + partial-accept nuance in `references/trajectory.md`
- [x] **RT15** `peek_node_full` null fields for existing node — repro + fix (obs-fastapi R.1)
- [x] **RT16** `next-leaves --verbose` VERDICT column: wire cached drift results or rename column
- [x] **RT17** Note in `references/rituals.md`: spec-audit can't fail under MCP-only writes (by design)
- [x] **RT18** Trajectory abandon/delete surface for dead drafts
- [x] **RT19** Headless MCP stdio invocation docs in `references/user-guide.md`

### Cross-tech dogfood round 2 (2026-06-07)

Fixture: `obs-fastapi` only.

- [x] **R2-1** Spec-audit failure paths (pivot + unclarified via library writes)
- [x] **R2-2** Portfolio `T.obs` + cross-block `obs-fastapi/R.2` ← `obs-express/R.2`
- [x] **R2-3** Trajectory full accept (`tr-f0912065` → `accepted`)
- [x] **R2-4** `human_signoff` + `llm_judge` exercised (`--all-layers` required)
- [x] **R2-5** Doc: layer scope, LLM judge setup, `judge_required` → violated (`verdicts.md`)

### Topic B — Docs + naming ✅ (2026-06-06)

- [x] **T1.1** `architecture.md`
- [x] **T1.2** `user-guide.md`
- [x] **T1.3** `why-manifold.md`
- [x] **T1.4** `changelog.md` — v0.1.0 ongoing entry (2026-06-06 landscape work under same version)
- [x] **T1.5** `SKILL.md`
- [x] **T1.6** `schema.sql` header — schema_version 1 (checkpoint)
- [x] **T1.7** `packages/manifold/README.md`
- [x] **T1.8** D1 aspirational + footnote
- [x] **T1.9** D2 documented in user-guide
- [x] **T1.10** intent-broker, three lineages, Spec Kit interop in why-manifold

---

## Skill iteration

- [x] **S0** Phase 0 — close the loop
  - [x] **S0.1** Commit docs reorg (`801268a`)
  - [x] **S0.2** Re-sync installed skill (`~/.claude/skills/manifold`)
  - [x] **S0.3** Fix eval #2 — split spec-audit vs drift-report
  - [x] **S0.4** Add cross-blockers eval
  - [x] **S0.5** Promote skill-iteration-plan.md + index links
  - [x] **S0.6** Eval runner script + verify evals pass
- [x] **S1** Phase 1 — skill v0.1.1 consumption hardening (routing, writeback, manifest)
- [x] **S2** Phase 2 — Topic E v1.5 verdict bootstrap + drift ritual
- [x] **S3** Phase 3 — Topic J trajectory (3P product + 3S skill)
- [x] **S4** Phase 4 — dispatch-orchestrator boundary

---

## Roadmap work (Topics C–G)

### Topic C — AGENTS.md compile ⏸ **deferred (L14)**

Research suggested graph → slim AGENTS.md. **Skipped for now:** another file surface to keep in sync; MCP + CLI + skill are enough. Users who want session bootstrap copy intent into host files (`CLAUDE.md`, `CODEX.md`, `AGENTS.md`) by hand. Revisit when a concrete non-MCP workflow appears.

- [ ] ~~T2.1–T2.4~~ — cancelled until need

### Topic D — Spec Kit import ⏸ **deferred (L15)**

Convenience import only — manifold already authors graphs, imports v0.2 trees, and runs MCP/CLI. Nothing Spec Kit provides is missing from core product. Revisit if Spec Kit becomes part of your workflow.

- [ ] ~~T3.1–T3.5~~ — cancelled until need

### Topic E — Spec↔code drift (real M4) ✅ v1 shipped (2026-06-06)

Design: [`archive/topics/drift-report-design.md`](../archive/topics/drift-report-design.md)  
Plan: [`archive/topics/drift-report-plan.md`](../archive/topics/drift-report-plan.md)

- [x] **T4.1** **D3** — standalone `drift-report` (L3)
- [x] **T4.2** Inputs — project + `project_root` / `--repo`
- [x] **T4.3** Checks — **v1 (L16):** violated + unverified realizations; **v2 (L17):** LLM rationale match
- [x] **T4.4** Output — terminal + `--format md`
- [ ] **T4.5** M3 link (finding → `change_reason`) — deferred post-v1
- [x] **T4.6** Implement `drift-report` CLI + MCP + HTTP
- [x] **T4.7** Update positioning copy — aspirational → factual

### Topic H — Portfolio / company themes (Example A) ✅

Design: [`archive/topics/portfolio-cross-project.md`](../archive/topics/portfolio-cross-project.md)

- [x] **H1** Schema `portfolio_links`
- [x] **H2** Writes `link_portfolio` / `unlink_portfolio`
- [x] **H3–H4** Queries `portfolio_report`, `list_portfolio_links`
- [x] **H5** Tests
- [x] **H6–H8** CLI `portfolio-report`, MCP, HTTP `/reports/portfolio`
- [x] **H9–H10** `render portfolio --template quarter-roadmap`
- [x] **H11** Test fixture: Q3 Reliability example

### Topic I — Cross-project links (Example B) ✅

Same design/plan as Topic H.

- [x] **I1** Schema `cross_project_edges`
- [x] **I2–I3** Writes + validation
- [x] **I4–I6** Queries + `is_cross_blocked`
- [x] **I7** `next_leaves` respects cross blockers
- [x] **I8** `portfolio_report` `blocked_by` key
- [x] **I9–I11** MCP + integration tests (product → AI block); CLI cross-edges deferred (L29)

### Topic H+I docs

- [x] **D1** Glossary portfolio + cross-project sections
- [x] **D2** `skills/manifold/references/business-model.md`
- [x] **D3** `architecture.md` — schema tables, query rows, MCP 38 tools
- [x] **D4** `user-guide.md` — portfolio-report + cross-edge examples
- [x] **D5** Topic F stub → [`orchestrator-contract.md`](orchestrator-contract.md)
- [x] **D6** Topics H/I marked shipped in local impl plan

### Topic F — Intent-broker + orchestrator

- [x] **T5.1** Orchestrator contract stub → [`orchestrator-contract.md`](orchestrator-contract.md) (expand in orchestrator skill)
- [ ] **T5.2** Agents write `transition_target`, verdicts via MCP
- [ ] **T5.3** Parallel worktrees share `$MANIFOLD_DB`
- [ ] **T5.4** Fold into future `skills/orchestrator/` (separate from manifold core)

### Topic G — ReqIF + baselines

- [ ] **T6.1** Immutable baselines design
- [ ] **T6.2** ReqIF export (enterprise on-ramp)
- [ ] **T6.3** Lower priority until solo-dev + agent path solid

### Topic J — Trajectory ✅ v1 shipped (J1–J2)

Design + nouns locked L31–L34: [`archive/topics/trajectory.md`](../archive/topics/trajectory.md)

- [x] **J1** Schema + manual legs + impact preview engine
- [x] **J2** MCP + CLI + HTTP (`propose`, `show`, `accept`)
- [ ] **J3** Web plan/apply inbox (minimal HTML show page shipped; full inbox deferred)
- [ ] **J4** LLM-assisted `propose_trajectory`
- [ ] **J5** T4.5 drift finding → leg
- [ ] **J6** `restructure` leg kinds (Palimpsest quarry)

### Topic K — Human output ✅ shipped (K1–K13)

Research: [`research/manifold/human-output-2026-06/synthesis.md`](../../research/manifold/human-output-2026-06/synthesis.md). Architecture: [`human-presentation.md`](human-presentation.md). Skill: [`../../skills/present/SKILL.md`](../../skills/present/SKILL.md).

**Diagrams / mindmaps (P0 day 1)**

- [x] **K8** `build_diagram_view()` + `build_mindmap_view()` + golden fixture
- [x] **K9** MCP `peek_diagram` + `peek_mindmap`
- [x] **K10** HTML `/projects/<id>/diagram` + `/mindmap` + `/views/<view_id>` (server SVG; Mermaid export in `<details>`)
- [x] **K11** `presentation_format.py` Mermaid + markdown formatters (export path)
- [x] **K12** `present` skill stub + manifest entry
- [x] **K13** View registry (`presentation_views.json`) + `list_presentation_views` MCP + content negotiation (`Accept` / `?format=json`)

**Status brief (shipped)**

- [x] **K1** `build_status_brief_view()` + golden JSON fixture
- [x] **K2** `GET /projects/<id>/brief` HTML route (`manifold_web`)
- [x] **K3** MCP `peek_status_brief` → structured JSON
- [x] **K4** `generated_at`, project label, team-name resolution on every render
- [x] **K5** `manifold render project --template status-brief --format md` (CI / `$GITHUB_STEP_SUMMARY`)
- [x] **K6** Chat skill: 1-paragraph summary from JSON + shareable URL
- [x] **K7** `stale_warning` when validation &gt; 24h old

Defer: full timeline/Gantt, full-graph Mermaid, separate risk-brief route, PDF.

**Next: visualization verification + UI pass** (use the Chronicler showcase fixture)

- [x] **K14** Verification pass — seed `chronicler`, smoke brief/mindmap/blockers/decomposition URLs + `test_chronicler_seed` before UI work
- [x] **K15** Web UI polish — typography, layout, viz-nav, cards, dynamic SVG sizing (fixture: `chronicler_seed.py`)

### Human comprehension redesign 📝 plan drafted (2026-06-15)

Plan: [`human-comprehension-redesign-plan.md`](human-comprehension-redesign-plan.md). This is the next documentation and validation layer on top of shipped Topic K human output.

- [x] **HC0** Research/outcomes plan doc with evidence links, stakeholder matrix, phases, and claim caveats
- [x] **HC1** Terminology and IA pass — human terms vs API terms, first-run path, readiness/evidence caveats
- [ ] **HC2** Status brief audit — ensure `generated_at`, stale warning, drift caveats, deltas, and one-builder parity
- [ ] **HC3** Risk/verification view — make violated/errored/unverified/satisfied and status/verdict mismatches impossible to miss
- [ ] **HC4** Delivery view — ready frontier work with exclusion reasons, blockers, verdict context, and no priority overclaim
- [ ] **HC5** Trajectory human preview — reviewable `propose → show → accept` with mutation boundary and partial-accept caveat
- [ ] **HC7** Skill routing/evals — reject all-clear, priority, compliance, and mutation-boundary overclaims
- [ ] **HC8** Dogfood/UX validation — first-five-minutes tasks, time-to-answer, wrong-answer rate, confidence updates
- [ ] **HC6** Traceability projection — audit-friendly exports and explicit non-compliance-ready caveats; do after HC7/HC8 unless a concrete reviewer need appears

---

## Glossary maintenance

- [x] **T7.1** Re-run coverage audit (2026-06-06 post Topic E) — see glossary §Coverage audit
- [x] **T7.2** Document `delegate_to`, `applies_to`, `contract`, `target_shape`, `target_achieved_when`, `target_rationale_ref`
- [x] **T7.3** Palimpsest quarry nouns in glossary (planned, not shipped — L10)

---

## Explicitly deferred / out of scope

| Item | Why |
|---|---|
| Build competing SDD CLI | Research locked — interop instead |
| Autonomous agent in manifold | Orchestrator is separate skill |
| mem0/Zep conversational memory | Different problem |
| `harvest` / `render` / `restructure` | Palimpsest quarry |
| Full orchestrator implementation | Separate track — design doc not written |
| **Trajectory** (as-is → to-be) | ✅ J1–J2 shipped; J3+ deferred |
| **Verdict bootstrap** (wire realizations for drift-report) | Topic E v1.5 — not implemented |
| **Orchestrator writeback contract** (idempotency, fencing, structured verdicts) | Topic F v1.1 — not implemented |
| **Drift finding → spec update** (T4.5) | Overlaps Topic J v2 — not implemented |

---

## Separate track: orchestrator

See [`README.md`](README.md) orchestrator section + [`archive/orchestrator-2026-05/`](archive/orchestrator-2026-05/).

Not part of landscape Topics A–G but still pending in repo:

1. Write `docs/orchestrator-design.md` (from synthesis HTML)
2. Write manifold v0.1.1 plan (verdict failure data, fencing tokens, idempotency keys)
3. Ship manifold v0.1.1
4. Write orchestrator Phase 1 plan
5. Ship orchestrator Phase 1

**Note:** Landscape rename may overlap with parts of old "manifold v0.1.1 plan" — reconcile orchestrator contract docs when relevant.

---

## Session handoff one-liner

**If resuming cold:** read [`../README.md`](../README.md) → [`how-to-use.md`](how-to-use.md) → glossary → [`todo.md`](todo.md). **Shipped:** landscape A–H+I+J v1 (trajectory); Topic K human output (K1–K13).

---

## Changelog

| Date | Change |
|---|---|
| 2026-06-06 | D2 locked: explicit change_reason required on update_node |
| 2026-06-06 | L15: Topic D (Spec Kit import) deferred — convenience interop only |
| 2026-06-06 | D6 locked: no version bump on rename |
| 2026-06-06 | D7: SESSION-HANDOFF slimmed; May orchestrator archive preserved |
| 2026-06-07 | Docs reorg: `docs/README.md` entrypoint; archive/ taxonomy |
| 2026-06-07 | Removed `SESSION-HANDOFF.md` (redirect stub; entrypoint is README) |
| 2026-06-07 | Topic J: **trajectory** / **propose** / **leg** locked (L31–L33) |
| 2026-06-07 | L34: **impact preview** on `trajectory show` (plan before apply) |
| 2026-06-07 | Completeness audit follow-up RT1–RT5 (enum, docs, spec-audit, test discover, cli guard) |
| 2026-06-07 | L11/D6 reaffirmed: product version **v0.1.0** (reverted erroneous 1.0.0 drift) |
| 2026-06-07 | RT7–RT8: cross-edge guards + next-leaves exclusion reasons |
| 2026-06-07 | RT9–RT10: drift errored bucket + MCP/web portfolio tests |
| 2026-06-07 | Manifold docs → `docs/manifold/`; added [`how-to-use.md`](how-to-use.md) |
| 2026-06-07 | Skill iteration plan (Phases 0–5 complete) |
| 2026-06-07 | Skill iteration Phase 0+1: evals, runner, routing, manifest, rsync (S0, S1) |
| 2026-06-07 | Skill iteration Phase 2: verdicts.md, drift ritual, eval #6 (S2) |
| 2026-06-07 | Skill iteration Phase 3: trajectory J1–J2, trajectory.md, eval #7, 41 MCP tools (S3) |
| 2026-06-07 | Skill iteration Phase 4: orchestrator-contract dispatch boundary (S4) |
| 2026-06-07 | Cross-tech dogfood RT15–RT19: peek verdict block, STORED/COMPUTED columns, reject trajectory |
| 2026-06-07 | Topic K human-output research complete → [`human-output-2026-06/synthesis.md`](../../research/manifold/human-output-2026-06/synthesis.md); K1–K7 tracked |
| 2026-06-15 | Human comprehension redesign plan drafted → [`human-comprehension-redesign-plan.md`](human-comprehension-redesign-plan.md) |
| 2026-06-16 | HC1 terminology and IA pass: human/API crosswalk, new-user path, readiness/evidence caveats |
