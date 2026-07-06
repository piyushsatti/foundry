---
name: Diagnose before making changes
description: When debugging or proposing fixes, verify assumptions with evidence (logs, traces, real reproductions) before writing fix code
type: feedback
originSessionId: 71d61fb2-216c-43f3-9696-d78a78447a90
last_updated: 2026-05-06
---
When debugging or proposing fixes, verify assumptions with evidence before writing fix code.

**Why:** During the 2026-05-06 statusline bug session, I jumped to multi-scenario fix proposals based on a theory about `.model.id` being stale. The user pushed back: "if you are making any assumptions, make sure to diagnose before making changes." A diagnostic log added afterward proved my theory was wrong — `.model.id` was already correct and live. The "bug" was a transient state captured at the wrong moment, not a code bug. Acting on the assumption would have produced unnecessary code complexity.

**How to apply:** When the user reports a bug or unexpected behavior, before proposing fixes:
1. Write a diagnostic step that captures the actual runtime values (file dump, log block, print statement)
2. Have the user reproduce the bug with diagnostics in place
3. Read the diagnostic output
4. Only then propose a fix — and only one, the one the evidence supports

If a plan would benefit from a diagnostic step before the fix step, structure the plan as diagnose-first with a follow-up fix plan after evidence is in hand. Avoid presenting "Scenarios A/B/C with conditional fixes" — that's a tell that I'm guessing.
