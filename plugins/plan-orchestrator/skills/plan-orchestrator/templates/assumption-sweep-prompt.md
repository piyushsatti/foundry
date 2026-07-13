---
name: assumption-sweep-prompt
description: Slot-filled template for the Assumption sweep step of the Review Pipeline (Judgment class). One dispatch per cycle; reads all assumptions across artifacts.
version: 3
---

# Assumption Sweep Prompt Template

Replace `{slots}`. The slot `{specific-concerns-to-check}` is per-cycle — surface known cross-phase coordination questions to focus the sweep.

The architect MUST compute at dispatch time:
- `{dispatch-id}` — unique id (e.g., `assumption-sweep-planning-c1`); determines the reviewer's reserved escalation file

---

```
ASSUMPTION SWEEP for {project-name} ({stage}-stage, cycle {cycle-number}).
DISPATCH-ID: {dispatch-id}

## Your escalation file

Write all escalations to:
  WORK-DIR/escalations/{dispatch-id}.md

Number E1, E2, ... locally. Do not touch WORK-DIR/escalations.md directly.

## Read

- SKILL-DIR/templates/subagent-protocol.md (your two rules: HALT + SURFACE)
- SKILL-DIR/templates/adjudication-entry.md (the `source:` field spec)
- WORK-DIR/assumptions.md (architect adjudications, current count: {architect-count})
- WORK-DIR/phases/{P1-id}/plan.md (planner assumptions)
- WORK-DIR/phases/{P2-id}/plan.md
... (continue for all phases)

Total expected: ~{total-count} assumption blocks.

Note: planners may re-number A21+ per phase. Disambiguate as "{phase-id}.A<N>".

## Specific concerns to check

{specific-concerns-to-check}

Standard concerns ALWAYS include:
- **Adjudication coverage:** for adjudications with `affects_artifacts:`, verify each
  affected file actually contains the change called for. Flag orphan adjudications.
- **Cross-adjudication consistency:** for adjudications whose `source:` uses
  `derived_from: [Ax, Ay]`, verify the new adjudication does NOT contradict the ones
  it claims to derive from. Flag derived-from violations.
- **Risky-pendings:** planner assumptions with `confidence: low` AND
  `risk_if_wrong: medium-or-high` AND `status: pending` — these MUST be resolved before
  Implementation.
- **Originates-at sanity:** for adjudications whose `source:` uses `originates_at:`,
  verify they truly have no source to cite. If a citation could be made, flag.

## Categories to flag

1. **Contradiction** — two phases disagree on the same fact
2. **Silent invalidation** — a planner contradicts a validated architect adjudication
3. **Risky-pending** — low-conf + medium-high-risk PENDING
4. **Orphan adjudication** — `affects_artifacts:` paths don't show the change called for
5. **Derived-from violation** — adjudication contradicts the one it claims to build on
6. **Originates-at misclaim** — adjudication marked architect-original but has a citeable source

## Reviewer scoring culture

A sweep that finds zero contradictions in a 50+ assumption set is suspect.

## Output

For each issue, append to your reserved escalation file using local E-numbers.
type: plan-incoherence | safety-concern | omission.

## Return format

≤200 words:
- Total assumptions reviewed (per-phase counts)
- Contradictions count + derived-from violations count
- Risky-pendings count by phase
- Top 3 issues
- Local E-numbers used
```
