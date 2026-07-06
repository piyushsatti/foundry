---
name: promoting-memory-to-docs
description: "When promoting a memory entry to a documentation file, capture the active-use framing in the doc and cross-link from any consumer so the surfacing memory provided is not lost"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: db5e5856-1b33-4caf-857f-fe95b00bbfb3
last_updated: 2026-05-22
---

When a memory entry is promoted to a documentation file (because its content is reference material rather than a recurring behavior rule), the move is not just a copy-paste of the raw content. The doc must:

1. **Capture the active-use framing** — include why the content was promoted, how it should surface, and what task/decision it's expected to inform. Without this, the doc reads like inert reference material instead of guidance that needs to fire at a specific moment.
2. **Cross-link from any consumer** — find the task, journal entry, or other doc that'll naturally consume the content, and add a pointer to the new doc there. Memory entries surface automatically via the memory loader; docs only surface if something points at them.

**Why:** Memory entries are auto-loaded each session and shape behavior passively. Docs are inert until someone reads them. Promoting memory → doc without these two steps loses the "this should fire when X happens" property the memory was providing. Concrete example from 2026-05-22: the Claude Code permission pipe-limitation memory was promoted to `~/Documents/notes/infrastructure/claude/permission-pipe-limitation.md`, but only worked as a replacement because (a) the doc itself carries a "before touching deny rules, read this" framing and (b) the open `dev-machine-problems.md` "Review auto-mode / permission settings" entry was edited to cross-link the doc. Without those two steps, the next permission audit would have written the same dead `Bash(curl * | sh*)` deny rule the memory was preventing.

**How to apply:** When proposing to promote a memory to docs, before deleting the memory:

1. Write the doc with an explicit "why this is here / when to read this" section near the top
2. Identify the consumer (the task list, journal entry, audit checklist, related doc) that'll naturally hit this content
3. Cross-link from the consumer back to the doc — phrase the link so it acts as a behavior cue ("before doing X, read Y") not just a passive reference
4. Only then delete the memory and prune `MEMORY.md`

If no consumer exists, the content might not be a clean memory-to-doc candidate — either it's still a behavior rule (keep as memory) or it's truly orphan reference (consider whether it should exist at all).
