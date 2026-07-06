---
name: proactive-data-quality
description: User wants tools to proactively detect and prompt fixes for data quality issues rather than silently working around them
type: feedback
originSessionId: 16e54a8b-a4e0-4ab4-8266-85fa7ff97ecb
last_updated: 2026-04-19
---
Prefer proactive quality enforcement over silent workarounds. When building local tooling, detect and surface problems (duplicate dirs, unnamed items, corrupted data, stale entries) with appropriate severity levels (error/warn/info). It's costlier to have bad info accumulate than to fix things early.

**Why:** User values maintaining A+ quality on their local system of projects, files, folders. Silent degradation (like duplicate project dirs, unnamed sessions piling up) creates confusion later.

**How to apply:** When building any tool that reads/manages local state (project dirs, sessions, configs), include health checks that flag issues and prompt the user to fix them. Don't just handle edge cases silently — surface them.
