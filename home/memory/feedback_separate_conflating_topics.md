---
name: feedback-separate-conflating-topics
description: "when two related-but-distinct topics are in play, stop and ask to separate them — don't reason about both at once"
metadata: 
  node_type: memory
  type: feedback
  last_updated: 2026-06-20
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

When a session has two topics that are related but distinct (and easy to conflate), STOP and raise it to the user — propose splitting into separate conversations, or tackling them one at a time. Do not try to reason about both simultaneously.

**Why:** Holding both at once produced abstract, wrong, conflated answers for hours. Concretely: "windows scramble/restore after sleep" (a window-management problem) vs "why does locking send the display to sleep at all" (a display-power problem) share a trigger (display blanks after lock) but have totally different root causes and fixes. Reasoning about both together muddied every answer until the user forced a hard separation — then the correct answer landed immediately.

**How to apply:** At the first sign two threads are tangling, name both explicitly and ask: "These are two separate problems — want to split them or take them one at a time?" Then purge the other from working focus and answer only the active one. Cleaner isolation = correct, concrete answers. Related: [[feedback-diagnose-before-fixing]].
