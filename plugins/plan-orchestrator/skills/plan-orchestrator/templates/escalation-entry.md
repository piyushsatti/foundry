# Escalation Entry Format

Every entry written to a subagent's reserved escalation file at `<work-dir>/escalations/<dispatch-id>.md` uses this exact header. The architect concatenates per-dispatch files into `<work-dir>/escalations.md` on each ORIENT. Format is consumed by `verify-dag.py`, `run-quality.py`, and the architect's ORIENT step.

```
## E<N> — <ISO timestamp> — <type-slug>
severity: blocking | advisory
detected_by: <dispatch-id>
source: <file or phase id>
type: contract-mismatch | yaml-prose-mismatch | missing-input | plan-incoherence | safety-concern | scope-creep | omission | plan-defense | other
lands_at: spec | framing | planning | implementation | close-out
blocks: <list of phases/ops that cannot proceed>
claim: <one-line description>
suggested_resolution: <one-line best guess>
status: open | acknowledged | resolved | wont-fix
resolved_by: -
resolved_at: -
```

## Rules

- Append-only inside your own dispatch file by the author; subagents never mutate entries written by others
- **Exception — architect-on-close:** the architect (and only the architect) MAY mutate the `status:`, `resolved_by:`, and `resolved_at:` fields of an existing entry when closing it. This is so the simple-grep gate-evaluation can read effective status without walking `resolved_by:` chains across dispatch files (round-3 R3-5). The original `claim:` and `suggested_resolution:` MUST NOT be edited — those are audit history.
- The `lands_at` field drives where re-work happens — classifies the escalation against the five stages (spec | framing | planning | implementation | close-out)
- Contract resolutions cascade field-scoped: when a contract is mutated, only consumers whose `consumes:` slice intersects the changed fields get marked stale
