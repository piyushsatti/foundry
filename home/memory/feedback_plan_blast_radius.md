---
name: plan-blast-radius
description: "Every plan file must include a brief blast-radius (what artifacts a change touches, at what scope)"
metadata: 
  node_type: memory
  last_updated: 2026-06-22
  type: feedback
  originSessionId: cae4cbcd-9e0e-4716-80a6-fc9382b83919
---

When presenting a plan file, always include a brief **blast radius**: at a high level, what artifacts the change impacts and at what scope — e.g. local Claude settings, global Claude settings, one DAG, one module, a repo, user-global config. Place it near the top (right after the Context section). A small table (Artifact | Scope | Impact) plus a one-line "not touched" works well; also note reversibility.

**Why:** the user reviews every diff and wants to gauge the surface area of a change before approving it — what's the highest scope affected, and what is explicitly safe/untouched. Without this, a plan reads as a list of steps with no sense of how far the consequences reach.

**How to apply:** add a "Blast radius" section to every plan written to the plan file. Lead with the highest-scope artifact. Distinguish global vs project-local vs single-file. Call out what is NOT touched (no code / no settings.json / no hooks / no repo files). Note that it's reversible and how. Complements the durable-plan-doc discipline in [[plan-redblue-then-implement]].
