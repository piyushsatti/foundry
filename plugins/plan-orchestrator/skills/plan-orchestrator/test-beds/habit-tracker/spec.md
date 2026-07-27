---
name: habit-tracker
created: 2026-05-18
purpose: Round-2 test bed for the plan-orchestrator skill — exercises a problem class deliberately different from hex-wars
---

# Habit Tracker — Round-2 Test-Bed Spec

This is the user-provided spec the plan-orchestrator skill is invoked against. Designed to differ from hex-wars on: domain (data tracking vs game), concurrency model (real concurrent CLI+web writes vs hot-seat), persistence (SQLite vs JSON files), language stack (Python+TypeScript vs all-TypeScript), and computational pattern (aggregation/insights vs validation).

## What

A personal habit-tracking application with three components:

- **Backend** (Python + FastAPI + SQLite): owns the data model, provides REST API, runs the reminder scheduler
- **CLI** (Python, same package as backend): quick local commands (`ht log <habit>`, `ht streak`, `ht report`); talks to the SQLite DB directly (no HTTP)
- **Web dashboard** (React + Vite + TypeScript): habit management UI, streaks dashboard, completion charts; talks to backend via REST
- **Shared schema** (manually-kept consistent): TypeScript types for frontend; Python pydantic models for backend

User defines habits (daily/weekly/N-times-per-week frequency); logs completions; views streaks, completion rates, and week-over-week trends.

## Why

Round-2 test bed for plan-orchestrator. Chosen because:

- **Different problem class than hex-wars** — no game state, no turn semantics, no inter-player coordination; instead has data aggregation, concurrent writes, and cross-language schema maintenance
- **Real concurrency surface** — CLI and web can both write to SQLite simultaneously. WAL mode + locking discipline matters. Different failure mode than hex-wars's serialized hot-seat.
- **Cross-language schema** — the habit/log schema lives in two places (TS + pydantic). Naming drift between them is exactly what the new `name-drift.py` Structural check should catch.
- **Aggregation correctness** — streak calculations, completion rate windows, week-over-week deltas. Verification has real semantic content beyond "does the schema match."
- **Scheduler component** — adds a fourth phase (reminder scheduler). Tests how the skill handles cron-like internal services.

## Success criteria (metrics)

Each must be desk-evaluable or scriptable:

1. **Functional correctness** — All unit + integration tests pass; ≥40 tests covering: habit CRUD, log entry CRUD, streak math, completion-rate windows, scheduler tick behavior, concurrent-write scenarios.
2. **CLI latency** — `ht log <habit>` completes in <100ms (cold-cache, simple log entry, on local SQLite).
3. **Web dashboard load** — Dashboard renders 100 habits with 1 year of daily-grain history in <1.5s on Chrome (cold cache).
4. **Insights correctness** — Streak calculations (`current_streak`, `longest_streak`) and completion-rate windows (7/30/90 day) exactly match 30 hand-validated test fixtures.
5. **Concurrent write safety** — Run a 30-second scenario where the CLI writes a log entry every 100ms while the web dashboard polls `/api/habits/:id/logs` every 200ms; assert no corrupted reads, no missed writes, no DB lock errors.
6. **Reminder scheduler accuracy** — Configure habit with 09:00 daily reminder; advance simulated time across 7 days; assert exactly 7 reminder events logged with timestamps within ±1s of 09:00 local.
7. **Audit cleanliness** — `code-review:code-review` returns 0 blocking; basic input-validation pass (CLI args sanitized, web inputs validated server-side).

## Scope (in)

- **Habits** — name (1-64 chars, regex-validated), frequency (daily / weekly / N-times-per-week), optional reminder time (HH:MM)
- **Log entries** — timestamp (ISO), habit_id, optional notes (≤500 chars)
- **Insights** — current_streak, longest_streak, completion_rate (7/30/90 day windows), week-over-week trend (+/- vs prior week)
- **CLI commands**: `ht add`, `ht list`, `ht log`, `ht streak`, `ht report`, `ht edit`, `ht delete`
- **Web UI**: habit list, add/edit habit form, log entry button, streaks dashboard, completion chart (last 90 days)
- **Reminder scheduler** — internal cron-like loop; emits structured log lines like `{event: 'reminder', habit_id, scheduled_for}` to stdout (does NOT integrate with macOS/Linux notification APIs)
- **Single-user** — no auth, no multi-tenancy

## Non-goals (explicit)

- Network sync / multi-device — local SQLite only
- Mobile app (no React Native, no iOS, no Android)
- Real OS notifications via macOS / Linux APIs
- Multi-user / sharing / public profiles
- AI-generated habit recommendations or "nudges"
- Cloud sync (no Postgres, no S3, no Firebase)
- Authentication / OAuth / login UI
- Export to external formats (CSV/PDF) — deferred to v2

## Constraints

- **Languages:**
  - Backend + CLI: Python 3.11+ (FastAPI, sqlite3 stdlib or sqlalchemy, pydantic)
  - Frontend: TypeScript + React + Vite
  - Shared schema: TypeScript types (`.d.ts`) for frontend; pydantic models for backend. Architect responsible for keeping them consistent.
- **Persistence:** SQLite in WAL mode for concurrent reader/writer. Single DB file. Default location `~/.local/share/habit-tracker/habits.db`, override via env var `HABIT_TRACKER_DB`.
- **Backend listens on** 127.0.0.1:8200 (localhost only; no CORS middleware; frontend uses Vite dev proxy).
- **CLI talks to the DB directly** (does NOT go through the HTTP API). This means both CLI and backend HTTP write to the same DB and rely on SQLite's locking.
- **Reminder scheduler** is a background task inside the FastAPI process (e.g., `asyncio.create_task` or `APScheduler`).
- **Code budget:** 2000-4500 LOC total across components + tests.

## Known context pointers

- SQLite WAL mode: `PRAGMA journal_mode=WAL;` at DB open
- pydantic + TypeScript schema parity: maintain by hand in v1; add codegen in v2
- FastAPI + scheduler: `asyncio.create_task(scheduler_loop())` at startup event
- React + Vite: standard scaffold with TanStack Query for API state

## Output location

When the skill runs against this spec, the implementation should land at:
```
~/Desktop/habit-tracker-testbed/
```

The skill's work-dir will be at:
```
~/.claude/plan-orchestrator-runs/habit-tracker/<timestamp>/
```
