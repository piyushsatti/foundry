---
phase: P<n>
name: <slug>
generated_by: <planner-instance-id>
generated_at: <ISO timestamp>
consumes:
  C<n>: [<field>, ...]
produces:
  C<n>: <version>
skill_requirements: [<list>]

assumptions:
  - id: A<n>
    claim: <one-line>
    rationale: <one-line>
    confidence: high | medium | low
    risk_if_wrong: <one-line>
    status: pending
    validated_by: -
    validated_at: -
---

# Phase P<n> — <Name>

## Goal

<One paragraph stating what this phase accomplishes within the larger DAG.>

## Tasks

### T1 — <task name>
- inputs: <files / contracts read>
- output: <file / artifact produced>
- skill invoked: <skill name, if applicable>
- estimated files touched: <n>
- notes: <specifics, edge cases this task handles>

### T2 — <task name>
- inputs: <...>
- output: <...>

## Dependencies

This phase consumes `<C1>`, `<C2>`. If those change in fields we read, this phase becomes stale per the cascade rule (decision 7).

## Verification

The following must pass for this phase to be marked complete (run by `verify-phase-complete.py`):

- [ ] All declared tasks present in `tasks_completed` in `status.md`
- [ ] Declared artifacts exist at their paths
- [ ] Declared tests pass: `<test command>`
