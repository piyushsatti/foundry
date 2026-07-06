---
name: feedback_workflow_schema_placement
description: "In multi-agent workflows, don't force a StructuredOutput schema on a heavy file-writing stage — schema only the small verdict stages"
metadata:
  node_type: memory
  last_updated: 2026-05-31
  type: feedback
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

When orchestrating a Workflow, attach a `schema:` only to agents whose OUTPUT *is* the deliverable — a verdict, a classification, a short structured result. Do NOT put a schema on a heavy GENERATIVE stage whose real deliverable is a written file: the agent does its file work, treats "I wrote the file" as done, and skips the mandatory StructuredOutput call (even after the harness nudges it), so the workflow drops the item.

**Why:** On 2026-05-31 a revise→re-review workflow lost 3 of 4 Opus revisers — each "completed without calling StructuredOutput (after 2 in-conversation nudges)" and wrote *nothing* to disk. The one that complied had no special trait; the schema-after-heavy-work pattern is just fragile. The re-run with NO schema on the revise stage — free-text return, the file as the deliverable, the output path reconstructed deterministically from the item — succeeded 3/3.

**How to apply:** For a file-writing stage, omit the schema, have the agent return a short free-text pointer, and reconstruct any path you need downstream (e.g. the v2 file path) deterministically from the item rather than parsing the reply. Keep schemas on the small verdict/review stages where the structured output *is* the work. Reinforce with prompt ordering: "write the file first; do not end your turn until the Write tool has succeeded." Schemas are a capture mechanism, not a work mechanism. Related: [[feedback_diagnose_before_fixing]].
