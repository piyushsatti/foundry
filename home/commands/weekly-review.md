---
name: weekly-review
description: Run the Sunday morning weekly review ritual for the LifeOS vault. Five steps, ~20 minutes, os-doctor + inbox + status pass.
user_invocable: true
---

# Weekly Review

The Sunday morning ritual that keeps the vault honest. Documented in `~/LifeOS/04-Archive/projects/vault-cleanup/04-weekly-review.md`. Total time ~20 min.

## Anti-pattern guard

This is **not** a project worksession. If draining the inbox surfaces a 2-hour task, the task gets *placed* (into a project file or calendar block), not *done* in the review. The review's job is to keep the vault honest, not to advance the work.

## Steps — execute in order, one at a time, with Pi's involvement

### Step 1 — OS doctor (2 min)
Invoke the `os-doctor` skill. After the report writes, surface the top 3 issues to Pi. Wait for acknowledgment before moving on.

### Step 2 — Drain `00-Inbox/` (5–10 min)
List every file in `~/LifeOS/00-Inbox/` (root only — skip `apple-notes-raw/`). For each file, ask Pi for the fate:
- **place** — move to its real PARA home (specify destination)
- **absorb** — content is already captured elsewhere; archive the original to `~/LifeOS/04-Archive/inbox/YYYY-MM/`
- **leave** — still active capture, keep in inbox
- **archive** — move to `~/LifeOS/04-Archive/inbox/YYYY-MM/` without absorbing

Use AskUserQuestion with a multi-select list of files for batch decisions when possible. Never delete — Pi's standing rule. Move to archive instead.

### Step 3 — Re-status projects (5 min)
For each `_PROJECT.md` in `~/LifeOS/01-Projects/*/`, surface its current `status` and `updated` field. Ask Pi:
- Is the status still right? (`active` / `scoping` / `parked` / `paused` / `closed`)
- If `active`: confirm count is ≤ 3
- If `closed`: confirm move to `~/LifeOS/04-Archive/projects/<name>/`

Update the `updated` field on any project Pi confirms is still accurate or whose status changed.

### Step 4 — Tend areas (2 min)
Open `~/LifeOS/02-Areas/_AREAS.md`. Ask Pi which areas were tended this week. For each, update the `last_tended` field in that area's `_AREA.md`.

### Step 5 — Update START-HERE.md (3 min)
Ask Pi for the coming week's top priorities. Update `~/LifeOS/START-HERE.md` "Right now" section accordingly.

## Don't

- Don't batch-decide for Pi. He sees each file/project individually so the judgment stays his.
- Don't delete anything.
- Don't extend a step beyond its budget. If something needs more time, it becomes a project, not a review item.
- Don't run this in a session where Pi is tired or context is heavy. Propose pausing instead.
