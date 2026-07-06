# Orchestrator Synthesis Addendum — Subagent Handoff Pattern

> Companion to `orchestrator-synthesis-2026-05-24.html`. Captures one substantive design extension surfaced after the synthesis was finalized.
>
> **Authoritative for v0.1 design alongside the synthesis HTML.** When you write the orchestrator design doc, include this.

## Why this addendum exists

After the orchestrator synthesis HTML was written, Pi pointed me at a real chronicler-session transcript where the wrapping-up agent produced a structured **handoff to the orchestrator** at session end. The pattern is genuinely useful and fills a gap the synthesis hadn't named. The synthesis HTML is dated and stays as-is; this addendum is where the extension lands.

## The pattern (from the chronicler agent's actual output)

At session end the agent produced **two artifacts**:

### 1. A short structured handoff MESSAGE

Bullet-pointed summary delivered directly to the orchestrating session / user. Shape:

- **Branch state** — commit SHA, test pass count, commits ahead of main, merge-readiness assessment
- **Key wins** with concrete numbers ("9 → 357 / 650 characters classed") — NOT vague claims
- **Where to look** — paired list: file path + what's there + why you'd open it
- **What's deliberately not done** — explicit attribution ("Pi's call — don't reopen without discussion"), with the rationale
- **Hook for human input** — "if there's context I didn't capture, share the path"

### 2. A longer handoff DOC committed to the repo

`docs/agent-handoff-YYYY-MM-DD.md` (281 lines in the chronicler case). Shape:

- DB access patterns, snapshot discipline
- CLI catalog with known gotchas
- Data-shape pitfalls
- Authorized vs frozen zones in the codebase
- Collaboration preferences (how the human likes to work)
- Open menu of next actions

Plus: the session transcript path + session id, so future debugging can dive from summary to detail when summary isn't enough.

## How this extends the orchestrator v0.1 output schema

The mandatory structured output schema (from systems engineer perspective in the synthesis) gets four new fields:

```jsonc
{
  // EXISTING fields from synthesis §6 ("Fail loud, ask early" enforcement)
  "verdict":              "achieved" | "failed" | "blocked" | "needs_review",
  "evidence":             [string],
  "assumptions_made":     [string],
  "unresolved_questions": [string],
  "change_reason":        "correction" | "evolution" | "clarification"
                        | "refactor" | "drift" | "other",

  // NEW from this addendum
  "narrative_handoff":    string,         // markdown; the short structured message
  "handoff_doc_path":     string | null,  // optional path to longer doc (in-repo)
  "deliberately_not_done": [              // negative-space catalog WITH attribution
    {
      "item":          string,
      "reason":        string,
      "attributed_to": "human" | "agent"
    }
  ],
  "where_to_look": [                      // structured pointer list
    {
      "path":        string,
      "description": string
    }
  ]
}
```

## Where this surfaces in the design

| Existing piece (from synthesis) | What the handoff adds |
|---|---|
| **Cockpit DONE panel** — was just a leaf id + pass/fail badge | Each completed leaf is expandable inline to show its full `narrative_handoff` — the actual wins, gaps, pointers. "What got done since last visit" becomes substantive. |
| **`change_reason=drift` field** — single-word enum | Gets its rationale from `deliberately_not_done[]` entries with `attributed_to=agent`. Drift becomes prose with attribution, not just a tag. |
| **Schema-enforced auto-downgrade** — was just on `assumptions_made` | Extends: if `verdict=achieved` AND (`narrative_handoff` is empty OR under N words) → auto-downgrade to `needs_review`. Vacuous handoffs caught at the wire. |
| **SRE's session transcript log stream (B)** | Every handoff carries the transcript path + session id explicitly. The orchestrator persists this in the `job_phases` table. Future debugging path is clean. |
| **Manifold's `change_reason` writeback** | `deliberately_not_done[]` entries with `attributed_to=human` become individual `change_reason=evolution` writebacks with the rationale in the change_summary. Pi's explicit defers get traced. |

## Pros / cons (full discipline applied)

**Pros**
1. **Real-world validated.** The chronicler agent produced a genuinely useful handoff with concrete numbers, file paths, explicit attribution. Not a hypothetical pattern.
2. **Fills a substantive gap.** Without it, the cockpit's DONE panel is flat (id + status). With it, each row is a story you can act on.
3. **Makes "fail loud, ask early" tangible.** The chronicler agent did not make unilateral decisions — they attributed defers to Pi. The narrative handoff is the *evidence* that the agent operated honestly. Anti-vibe enforcement.
4. **Composable with auto-downgrade.** Substance of the handoff becomes a quality gate. Lazy agents get auto-flagged.
5. **Cheap to add.** Four new schema fields + one cockpit widget. No new infrastructure.

**Cons**
1. **Adds prose-quality requirements.** Agents differ; some handoffs will be vacuous. Mitigation: minimum-fields-required enforcement (must have at least one win, at least one where_to_look entry).
2. **More tokens per leaf.** Each leaf produces a richer artifact. ~500-1500 extra tokens. At Pi's scale, ~$0.05-0.20/leaf extra — clearly worth it.
3. **Risk of CYA noise.** Defensive agents writing handoffs full of caveats. Mitigation: `deliberately_not_done` requires `attributed_to`; "agent" choices are surfaced separately from "human" choices on the cockpit, so noise is identifiable.

Cons are tractable. **Decision: adopt as P0 for orchestrator v0.1 substrate.**

## Implementation notes for the design doc (next session)

When writing `docs/orchestrator-design.md`, fold this into the substrate:

1. **Schema section** — include the four new fields in the mandatory output schema. Don't section them off; they're peers of `verdict`, `evidence`, etc.
2. **Auto-downgrade rules section** — add the vacuous-handoff rule alongside the assumptions-made rule.
3. **Cockpit section** — DONE panel widget that expands to show `narrative_handoff` rendered as markdown. Drill-down to `handoff_doc_path` if present.
4. **Writeback section** — `deliberately_not_done[]` with `attributed_to=human` entries trigger individual `manifold update-node` calls with `change_reason=evolution` and the rationale captured.
5. **Transcript reference section** — persist session_transcript_path + session_id in the `job_phases` table at session end. Surface in cockpit drill-down.
