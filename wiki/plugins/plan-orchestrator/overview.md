# Plan Orchestrator

**A skill that decomposes multi-component work into a Directed Acyclic Graph of phases wired by explicit contracts, with stage gates and transparency protocols.** The architect owns the wiring; per-phase work is delegated to existing skills.

> **Status:** stable

## Overview

**The skill is a context-sharding engine that uses contracts as the cut lines.** A phase's working set is its plan plus the contracts it reads plus a minimal repo slice; if that exceeds the per-agent budget, the phase must split. Contracts are the throttle, and the architect's value is enabling rigorous reasoning at scales one agent's context can't hold.

**Invoke only when** you have a clear WHAT + WHY + measurable METRICS but no clear HOW, and the work crosses ≥2 components over multi-hour effort. Missing what/why/metrics → `brainstorming`; trivial single-file work → `writing-plans`.

## The five stages

Work passes through named stages; each has a gate the next stage cannot start until it passes.

| Stage | What happens |
|---|---|
| **Spec** | Validate the input contract; halt on missing fields |
| **Framing** | Architect writes DAG, glossary, skill-catalog, contract skeletons, own adjudications |
| **Planning** | Parallel planners produce phase plans; the Review Pipeline runs |
| **Implementation** | Implementers write code per plan; completion is verified externally |
| **Close-out** | Audit pass (security-review, code-review, …) then synthesis + learnings |

```mermaid
graph LR
  A[Spec] --> B[Framing]
  B --> C[Planning]
  C --> D[Implementation]
  D --> E[Close-out]
```

## Input contract + overkill detector

**The spec must carry six fields** — what, why, metrics/success criteria, scope & non-goals, known constraints, and optional context pointers. Any missing → halt with a precise list.

**The overkill detector refuses undersized work.** The primary gate is qualitative: if the work fits one paragraph and one component, exit and recommend `writing-plans` — no numeric score can override that. A supplementary 0–12 score (components, effort, new contracts, audits) then sorts marginal cases. Every verdict ships a cost estimate: roughly twenty to one hundred dollars per run.

## Three-class verification

**Match the verification class to the error class** — never pay Opus for what a script can catch.

| Class | Tool / cost | Catches |
|---|---|---|
| **Structural** | scripts, ~free | format errors, dead refs, duplicate IDs, name drift |
| **Alignment** | Haiku, ~a tenth of a cent | claim text vs cited source discrepancies |
| **Judgment** | Opus, ~ten cents to a dollar | semantic gaps, omissions, cross-edge interactions |

These fire in parallel at different points, not as a ladder. Alongside them the **Skeptic** (Opus, high thinking) is dispatched at the Framing and Planning gates to find *omissions* — things that should be in the work-dir but aren't — directly attacking the architect-blindspot gap.

## The automatic gate

**A gate passes without a user pause only when all four hold:**

1. All Structural checks pass
2. All Alignment checks return YES (UNSURE escalates)
3. Zero blocking escalations open
4. Zero low-confidence + medium-or-higher-risk assumptions still pending

Any failure halts to the user. Auto-proceeding past blocking findings is forbidden.

## Harness-fit caveats

The design assumes knobs the Claude Code harness doesn't cleanly give:

- **Per-dispatch thinking level is not exposed** — the Agent tool sets `model` but thinking is session-level; the allocation table is partly aspirational.
- **Parallel tool calls are all-or-nothing** — one non-zero exit cancels the sibling dispatches. Guard every Bash with `; :` or `|| true`.
- **`$N` substitution hazard** — the Skill tool eats bare `$0`, `$20` as positional args, so cost prose must be worded ("twenty to one hundred dollars"), not `$`-notated.
- **No live monitoring** — the architect can't poll subagents mid-dispatch; heartbeats only land between dispatches.

## See also

- [Progress tracker](progress-tracker) — the cheap ORIENT-cycle status store.
- [Handoff pattern](handoff-pattern) — the subagent→orchestrator handoff schema.
