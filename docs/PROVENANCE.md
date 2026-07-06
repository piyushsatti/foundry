# Provenance — where each component came from

Consolidated 2026-07-04. No single machine was current for everything, so each
component is the latest copy pulled from whichever of Mac / pslap / psdev had it.
Recency was determined by **content (md5) + mtime**, never by any machine's
self-description (a file that called itself "source of truth" was, in one case,
the stale one).

| Component | Latest source | Why |
|-----------|---------------|-----|
| `CLAUDE.md` | **psdev** live (Jul 3) | Superset — pslap's content + a `scrutineer` section. |
| `statusline-command.sh` | pslap/psdev (Jun, 8.9 KB) | Mac's was a stale 2.8 KB April copy. |
| `skills/worktree/` | **pslap LIVE** (8.1 KB SKILL + ~30 KB helpers) | The overlay copy that called itself canonical was a stale 2.7 KB stub. |
| `skills/apply-curation/` | pslap overlay | Only copy. |
| `hooks/` (31 + `lib/`) | pslap overlay | Full latest guard suite; Mac had 14 stale/subset. |
| `commands/onboard,confluence-doc,jira-ticket,primer` | pslap | Newest; Mac's `onboard` was the old April version. |
| `commands/os-doctor,weekly-review` | **Mac** (Jun 7 / Jun 12) | Recent Mac-only work — exists nowhere else. |
| `agents/scrutineer.md` | psdev | Only copy. |
| `plugins/meditate/` | pslap overlay | `v1.2.1` dev source (installed/cached was 1.1.1). Re-versioned to `0.1.0` on import (intentional monorepo reset; content was identical to pslap v1.2.1). 2026-07-05 P0/P1 repair pass reconciled it — authority docs vendored into `plugins/meditate/docs/`, macOS portability + manifest contract fixed. Version stays `0.1.0` (do not bump without Piyush's go-ahead). |
| `memory/` (26) · `statuslines/` (4) · `bin/bless` | pslap overlay | Only copies. |
| `docs/` (7) · `infra/` (MANIFEST + capture/apply) | pslap overlay | Latest authored infra notes/tooling. |
| `plugins/crucible/` | authored in-repo (2026-07-05) | Lens × stance adversarial + panel review system. Phases 1–2 shipped as sibling skills (`skills/wardrobe`, `skills/consult`, `skills/hats`, `skills/red-vs-blue`) + `home/agents/` stance agents; phase 4 (this pass) folded them into `plugins/crucible/` — `skills/`, `agents/`, and a vendored copy of `docs/adversarial-review-methodology.md` (a one-line pointer stub is left at the old repo-root path). Interim `skills/` and `home/agents/` locations are decommissioned (moved, not duplicated). Re-versioned at `0.1.0` — initial authorship, not a bump. |

**Later merged in:** the 10 authored ai-foundry skills (manifold, present,
plan-orchestrator, os-doctor, progress-tracker, brief, audit, subset, hats,
red-vs-blue) were consolidated into this repo when ai-foundry was folded into
foundry — they now live under `plugins/` and `skills/`, not a separate repo.

## Full evidence trail
The by-machine originals, dated snapshots, and the raw md5 divergence matrix were
kept in a local staging area outside this repo (not committed). This repo is the
curated result, not the evidence.
