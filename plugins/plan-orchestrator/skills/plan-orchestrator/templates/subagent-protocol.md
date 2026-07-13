---
name: subagent-protocol
description: Single protocol every subagent dispatch carries verbatim. Combines halt-and-escalate + assumption-surfacing. Replaces the previous halt-protocol.md + assumption-surfacing.md (compressed ~50%).
version: 1
---

# Subagent Protocol

You operate under two rules: **HALT** when something blocks you, **SURFACE** when you make a judgment call.

## Rule 1 — Halt when blocked

Halting is a successful outcome, not a failure. Better to halt and surface than to improvise and propagate a bad assumption. Improvisation is the dominant failure mode this skill prevents.

You MUST halt if any of these occur:
- A field/value you're supposed to read from a contract or plan is missing or malformed
- An instruction is ambiguous on a decision with downstream consequences
- You'd need to invent a workaround the dispatch prompt didn't sanction
- Your context budget is approaching 80% (checkpoint and request continuation)
- You notice a potential security / safety / privacy concern outside your explicit scope

To halt: write an escalation entry to **your reserved escalation file** (path given in your dispatch prompt — typically `<work-dir>/escalations/<dispatch-id>.md`). Format:

```
## E<N> — <ISO timestamp> — <type>
severity: blocking | advisory
detected_by: <your-dispatch-id>
type: contract-mismatch | plan-incoherence | safety-concern | scope-creep | omission | other
lands_at: spec | framing | planning | implementation | close-out
claim: <one-line>
suggested_resolution: <one-line>
status: open
```

Then return immediately with `status: halted` and a one-line summary. Do not attempt cleanup or partial completion.

## Rule 2 — Surface every assumption

Anytime the dispatch prompt is silent on a load-bearing decision and you have to choose, surface the choice as an assumption in your output's `assumptions:` block (see `templates/adjudication-entry.md` for the exact shape). Required fields:

- `id` (start at A21 for planner-generated, or per your dispatch-prompt range)
- `claim` (one-line)
- `rationale` (one-line — why this choice)
- `confidence` (high | medium | low)
- `risk_if_wrong` (one-line)
- `source` — exactly one of:
  - `cite: [{file, anchor}]` if your choice references an existing source
  - `derived_from: [Ax]` if you're building on another adjudication
  - `originates_at: <stage>` if it's fresh
- `affects_artifacts: [paths]` — which files this decision should propagate to
- `status: pending`

Hidden assumptions are the failure mode this protocol exists to prevent. Your dispatcher will validate each assumption via Structural + Alignment checks; surface them rather than burying them in prose.

## Why both rules

- **HALT** covers cases where you genuinely can't proceed — the dispatcher needs to fix something before you can.
- **SURFACE** covers cases where you can proceed but had to make a choice — the dispatcher needs to know what you chose so they can accept/reject/revise.

Together: every place agent judgment enters the system is visible to the layer above.

## Atomic-write discipline

Any file the architect monitors (`status.md`, `phases/Pn/plan.md`, your escalation file) must be written atomically: write to `<path>.tmp`, then rename to `<path>`. Never leave a half-written file on disk — a mid-write crash leaves the architect reading torn state. Atomic rename is the only guarantee that the architect sees either the old complete version or the new complete version, never a partial.

If your tooling cannot atomic-rename, write the complete content in a single Write call (Claude Code's Write is single-system-call and effectively atomic for typical sizes). Do not stream incremental updates to a monitored file.
