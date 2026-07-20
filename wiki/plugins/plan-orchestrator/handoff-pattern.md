# Handoff Pattern

**At session end a subagent returns a structured handoff to the orchestrator: what got done with real numbers, where to look, and what was deliberately left undone — with attribution.** Validated against a real chronicler-session transcript.

> **Status:** stable

## Overview

The pattern extends the orchestrator's mandatory output schema with four fields that turn a flat done/fail badge into an actionable story.

| Field | What it carries |
|---|---|
| `narrative_handoff` | Markdown: the short structured message — key wins with concrete numbers |
| `handoff_doc_path` | Optional path to a longer in-repo doc |
| `deliberately_not_done[]` | Negative-space catalog; each item has `reason` + `attributed_to` |
| `where_to_look[]` | Structured pointers: `path` + `description` |

## What a good handoff contains

- **Key wins with concrete numbers**, not vague claims (e.g. "9 → 357 / 650 characters classed").
- **Where to look** — paired file path + what's there + why you'd open it.
- **What's deliberately not done** — each entry attributed `human` or `agent`, with rationale.
- **A hook for human input** — "if there's context I didn't capture, share the path".

## Attribution is evidence of honest operation

**The narrative handoff is the evidence that the agent operated honestly.** An agent that attributes its defers — rather than making unilateral calls — is doing anti-vibe enforcement: "fail loud, ask early" made tangible.

- `attributed_to: human` entries trace explicit human defers (they become `change_reason=evolution` writebacks).
- `attributed_to: agent` entries are surfaced separately, so defensive CYA noise is identifiable.

## Auto-downgrade of vacuous handoffs

**Substance becomes a quality gate at the wire.** If `verdict=achieved` but `narrative_handoff` is empty or under a minimum word count, the verdict auto-downgrades to `needs_review`. Minimum-fields enforcement (at least one win, at least one `where_to_look` entry) catches lazy handoffs before they land.

## See also

- [Plan Orchestrator](overview) — the orchestration skill.
- [Progress tracker](progress-tracker) — cheap in-flight status between handoffs.
