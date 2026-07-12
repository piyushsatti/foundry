-- progress-tracker schema (SQLite)
--
-- One DB per machine at ~/.claude/progress.db. Multi-project, multi-phase,
-- multi-dispatch. Append-only events table provides audit history.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS projects (
    project_id   TEXT PRIMARY KEY,
    label        TEXT,                  -- human-friendly name (defaults to project_id)
    work_dir     TEXT,                  -- absolute path if known
    started_at   TEXT NOT NULL,         -- ISO-8601 UTC
    last_update  TEXT NOT NULL          -- bumped on any event under this project
);

CREATE TABLE IF NOT EXISTS phases (
    project_id   TEXT NOT NULL,
    phase_id     TEXT NOT NULL,
    name         TEXT,
    PRIMARY KEY (project_id, phase_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dispatches (
    dispatch_id  TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL,
    phase_id     TEXT NOT NULL,
    role         TEXT,                  -- planner | implementer | reviewer | skeptic | audit | other
    agent_model  TEXT,                  -- opus | sonnet | haiku | other
    status       TEXT NOT NULL,         -- PENDING | IN_PROGRESS | BLOCKED | DONE | HALTED
    started_at   TEXT NOT NULL,
    last_update  TEXT NOT NULL,
    blocker      TEXT,                  -- one-line if BLOCKED
    halt_reason  TEXT,                  -- one-line if HALTED
    FOREIGN KEY (project_id, phase_id) REFERENCES phases(project_id, phase_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_dispatches_project_phase ON dispatches(project_id, phase_id);
CREATE INDEX IF NOT EXISTS idx_dispatches_status ON dispatches(status);

CREATE TABLE IF NOT EXISTS todo_items (
    dispatch_id  TEXT NOT NULL,
    item_idx     INTEGER NOT NULL,
    description  TEXT NOT NULL,
    state        TEXT NOT NULL,         -- pending | in_progress | done
    updated_at   TEXT NOT NULL,
    PRIMARY KEY (dispatch_id, item_idx),
    FOREIGN KEY (dispatch_id) REFERENCES dispatches(dispatch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    event_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts           TEXT NOT NULL,
    project_id   TEXT,
    phase_id     TEXT,
    dispatch_id  TEXT,
    event_type   TEXT NOT NULL,         -- init | start | done | block | halt | finish | note
    detail       TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts DESC);
CREATE INDEX IF NOT EXISTS idx_events_dispatch ON events(dispatch_id);
