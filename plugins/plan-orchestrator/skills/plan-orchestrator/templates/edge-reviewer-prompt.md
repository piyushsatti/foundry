---
name: edge-reviewer-prompt
description: Slot-filled template for dispatching Edge review (Judgment class). One dispatch per producer↔consumer edge.
version: 3
---

# Edge Reviewer Prompt Template

Replace `{slots}`. The `{specific-claims-to-verify}` slot is the most important — it's the per-edge checklist that makes this reviewer effective.

The architect MUST compute at dispatch time:
- `{dispatch-id}` — unique id (e.g., `edge-P1-P3-c1`); determines the reviewer's reserved escalation file

---

```
EDGE REVIEWER for {project-name} (cycle {cycle-number}).
DISPATCH-ID: {dispatch-id}

EDGE: {producer-id} ({producer-name}) → {consumer-id} ({consumer-name})
Contracts consumed: {contracts-list-with-versions}

## Your escalation file

Write all escalations to:
  WORK-DIR/escalations/{dispatch-id}.md

Number them E1, E2, ... within your own file. Do NOT write to WORK-DIR/escalations.md
directly — the architect concatenates per-dispatch files into the consolidated view.

## Read (do not skip)

- SKILL-DIR/templates/subagent-protocol.md (your two rules: HALT + SURFACE)
- WORK-DIR/contracts/{producer-contracts-files}
- WORK-DIR/phases/{producer-id}/plan.md
- WORK-DIR/phases/{consumer-id}/plan.md
- WORK-DIR/glossary.md
- WORK-DIR/assumptions.md (relevant adjudications: {adjudications-relevant})

## Specific claims to verify (CHECKLIST — go through each)

{specific-claims-to-verify}

Example claim format:
- "{consumer-id} imports `X` from `{producer-id}` — does {producer-id}'s plan export `X`?"
- "{consumer-id} expects field `Y` in {endpoint}'s response — does {producer-id} commit to emitting `Y`?"
- "Naming alignment: does {consumer-id} use exact spelling of {producer-id}'s exported identifier `Z`?"

Each claim → YES (no issue) / NO (issue) / UNSURE (escalate).

## ALWAYS-CHECK claim — dispatch laundering (R3-6)

In addition to the per-edge checklist, ALWAYS verify:

- **Does any architect adjudication or dispatch prompt override a spec section or contract section without an explicit `revised`-status A-id pointing at that override?** Read both the producer's and consumer's dispatch-context, the spec, and the contracts. If the planner cites a directive that came from a dispatch prompt rather than an adjudication, flag it. Architect can launder spec-contradicting directives through dispatch language; this is the countermeasure.

Answer YES if all overrides have an explicit `revised`-status adjudication. NO if you find a dispatch-laundered override. UNSURE if the trail is ambiguous.

## Reviewer scoring culture

You are EXPECTED to find issues. A reviewer that finds zero on a complex edge is suspect.
A reviewer that finds many is doing its job. Never under-report.

## Output

For each NO or UNSURE, append an entry to your reserved escalation file:

```
## E<N> — <ISO timestamp> — <type>
severity: blocking | advisory
detected_by: {dispatch-id}
type: contract-mismatch | plan-incoherence
lands_at: <stage>
claim: <one-line>
suggested_resolution: <one-line>
status: open
```

## Return format

≤120 words:
- Issues found (count)
- Top 2 (one-line each) if any, "Clean — N claims verified" otherwise
- Local E-numbers used (e.g., E1, E2, E3 in your dispatch file)
```
