---
name: os-doctor
description: Run a read-only health check on the LifeOS vault. Outputs a dated report and surfaces top issues.
user_invocable: true
---

# OS Doctor

Invoke the `os-doctor` skill to audit `~/LifeOS`. The skill is read-only — it never modifies the vault. It writes a single report to `~/LifeOS/02-Areas/tool-stack/os-doctor-YYYY-MM-DD.md`.

## What to do

1. Use the Skill tool to invoke `os-doctor`. Follow its instructions exactly.
2. After the report is written, surface to Pi:
   - Path to the report
   - Top 3 most-urgent issues
   - Total violation count
3. Do NOT propose execution of fixes. The weekly review ritual handles that. If Pi explicitly asks to fix something, treat that as a fresh request.

## Don't

- Don't summarize the full report inline — Pi can read the file.
- Don't write to anything except the report file.
- Don't audit `00-Inbox/apple-notes-raw/` (that has its own processing project).
