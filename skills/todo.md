# Foundry skills — master todo

**Purpose:** Track skill authorship and registry work across sessions. Update when items complete or new decisions land.

**Canonical refs:**
- [`README.md`](README.md) — authored vs draft vs vendored
- [`manifest.yaml`](manifest.yaml) — allowlist + dependency graph
- [`../scripts/skills_manifest.py`](../scripts/skills_manifest.py) — validate, sync-docs, deps queries
- Ephemeral plans (local): `.gitignored/plans/trigger-vocabulary-2026-06-07.md`

**Last updated:** 2026-07-05

---

## Status at a glance

| Area | State |
|---|---|
| Repo layout (`skills/` + `vendor/skills/`) | ✅ Done |
| `manifest.yaml` + dependency graph | ✅ Done |
| `skills_manifest.py` (validate, sync-docs, deps) | ✅ Done |
| `sync-skills.sh` (multi-host + repo copies) | ✅ Installed 2026-06-07 |
| Trigger vocabulary map | ✅ Done (local: `.gitignored/plans/trigger-vocabulary-2026-06-07.md`) |
| Tier 1 draft skills (5) | 📋 Draft — review queue |
| Shipped authored skills | ✅ manifold, plan-orchestrator, os-doctor, progress-tracker, present |

---

## Open items

### Review queue — CLEARED 2026-07-05

All shipped after conformance tests passed (evidence: `research/crucible/test-approval-2026-07-05.md`). Pi delegated approval: test → if they work, ship.

- [x] **hats** — rewritten on research basis, wardrobe-sourced lenses; A3 panel passed → shipped
- [x] **red-vs-blue** — rewritten (blue-adjudicates-red bug fixed), worthiness gate + lens param; A4+A5 passed → shipped
- [x] **worktree** — macOS-portable, tests 92/0, installed on Mac; A1 passed → shipped
- [x] **wardrobe** — 10 v1 hats + HATS.md contract → shipped
- [x] **consult** — single-lens brainstorm partner; A2 passed → shipped
- [ ] ~~**brief**~~ / ~~**audit**~~ / ~~**subset**~~ — parked (Pi: can live without for now; revisit on demand)

**crucible phases 1–4 DONE** (2026-07-05) — packaged at `plugins/crucible/`; benchmark + hat-evals run (`research/crucible/`); pins retained. Open follow-ups: adjudicator benchmark (un-benchmarked role), harder corpus v2, non-security overlap fixture. Design: `.gitignored/plans/crucible-plugin-design.md`.

### Future (not blocking)

- [x] Multi-host skill sync — `scripts/sync-skills.sh --host cursor|codex|claude|all`
- [x] Repo skill copies — `scripts/sync-skills.sh --repo` → `.agents/skills/` + `.cursor/skills/`
- [ ] Toolbox install scripts — rsync from foundry to hosts via sibling `toolbox` repo
- [ ] **crucible plugin** — lens × stance review system (hat library + consult + stance agents + worthiness gate); design: `.gitignored/plans/crucible-plugin-design.md` (2026-07-05)

### After reviews ship

- [ ] Re-run `python3 scripts/skills_manifest.py sync-docs && validate`
- [ ] Update this file — move reviewed skills out of queue

---

## Locked decisions

| # | Decision | Date |
|---|---|---|
| S1 | Foundry repo is source of truth for authored skills | 2026-06-07 |
| S2 | Vendored skills live in `vendor/skills/` — do not edit in place | 2026-06-07 |
| S3 | ~~Model routing agnostic — ask user which model per dispatch~~ — superseded by S7 | 2026-06-07 |
| S4 | Tier 1 skill names: `brief`, `audit`, `hats`, `red-vs-blue`, `subset` | 2026-06-07 |
| S5 | `vault-doctor` renamed → `os-doctor` | 2026-06-07 |
| S6 | Host install is explicit-only — no auto-sync, no nagging in chat | 2026-06-07 |
| S7 | Review skills default to the session model (override on request); hats + red-vs-blue design decisions must cite `docs/adversarial-review-methodology.md` | 2026-07-05 |
