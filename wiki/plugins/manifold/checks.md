# Checks

**Manifold has three checks that answer three different questions — don't mix them up.** One reviews spec history, one reconciles spec against code, one validates graph structure.

> **Status:** stable

## The three checks

| Check | Question | Reads |
|---|---|---|
| **`spec-audit`** | Did we explain our spec changes? | Revision history in the DB only |
| **`drift-report`** | Does the code still match the spec? | Verdicts on realization nodes (+ repo root) |
| **`validate`** | Is the graph well-formed? | Graph rules (cycles, coverage, layers) |

**They never overlap.** `spec-audit` never reads your codebase. `drift-report` never flags "unset change_reason on old revisions" — that's `spec-audit`.

## spec-audit (revision hygiene)

Surfaces spec-graph discipline problems, all from the revision log:

- **Flagged revisions** — `change_reason` of `pivot`, unset, or `other`.
- **Unclarified rationale changes** — `rationale` edited without `clarification` or `correction`.

Every content edit via `update_node` requires an explicit `change_reason`: `correction`, `evolution`, `clarification`, `refactor`, `pivot`, or `other`. Mechanical transitions may auto-set it. `pivot` (formerly misnamed `drift`) means a deliberate intent shift.

## drift-report (spec ↔ code)

Reconciles realization nodes against their evidence. v1 buckets:

- **Violated** — a wired check ran and failed.
- **Unverified** — no verdict mechanism configured; a coverage gap ("we can't tell if code matches").
- **Errored** — the check could not run (broken evidence).
- **Satisfied** — listed in summary counts.

Exits non-zero on any **violated** (unverified alone is a gap, not confirmed drift). It reuses the verdict runner — no parallel check engine. v2 (LLM rationale match) is deferred.

**Not "all clear" just because there are no violations** — treat errored as broken evidence and unverified as unknowns.

## Independent axes

**Status, evidence, and priority are separate — never collapse them.**

| Axis | Term | Means | Does not mean |
|---|---|---|---|
| Work state | `target_status` | planned / in progress / achieved / … in the graph | code is correct |
| Evidence | `verdict_status` / drift bucket | a check is satisfied / violated / errored / missing | roadmap priority is known |
| Ready frontier | `next-leaves` | smallest open, unblocked graph leaves | the most valuable priority |

**`next-leaves` is readiness, not prioritization** — it returns the ready frontier from the graph, not a ranked roadmap. You still decide what matters most. `achieved` is not the same as `satisfied`.

## See also

- [Data model](data-model) — the verdict engine and revision log.
- [Trajectory](trajectory) — evolving the spec safely.
