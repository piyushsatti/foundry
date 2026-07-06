---
name: feedback_incremental_walkthroughs
description: "For interactive/procedural guidance, give ONE step at a time and wait — don't dump multi-step walls of text"
metadata: 
  node_type: memory
  last_updated: 2026-05-31
  type: feedback
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

When walking the user through an interactive or multi-step procedure (verification gates, command sequences, file edits), present ONE step at a time and wait for confirmation before giving the next — do not dump the whole sequence in one message.

**Why:** The user executes one step at a time; a multi-step wall causes mistakes — e.g. they pasted a file-edit block into the terminal (running it) instead of opening the file to edit it, because all the steps arrived at once. Their words: "you gave too much text output in one line, lets do things one by one."

**How to apply:** For gates/commands/edits, give the next single step + its pass-criteria, confirm the result, then the next. Big consolidated write-ups are fine for plans/reports reviewed at leisure — not for live walkthroughs. Related: [[feedback_data_quality_proactive]].
