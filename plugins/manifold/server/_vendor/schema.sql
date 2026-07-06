-- manifold canonical schema (v1.0).
-- Tables defined here; indexes in the section below.
-- Schema version is tracked in schema_meta; current version: 1.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    schema_version INTEGER NOT NULL,
    upgraded_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    project_id        TEXT PRIMARY KEY,
    label             TEXT,
    spec_config       TEXT NOT NULL,
    created_at        TEXT NOT NULL,
    archived_at       TEXT,
    last_revision_id  INTEGER
);

CREATE TABLE IF NOT EXISTS nodes (
    project_id            TEXT NOT NULL,
    node_id               TEXT NOT NULL,
    layer                 TEXT NOT NULL,
    title                 TEXT,
    kind                  TEXT NOT NULL DEFAULT 'spec',
    realized_by_external  TEXT,
    body                  TEXT NOT NULL DEFAULT '',
    contract              TEXT,
    delegate_to           TEXT,
    applies_to            TEXT,
    target_status         TEXT,
    target_shape          TEXT,
    target_rationale_ref  TEXT,
    target_achieved_when  TEXT,
    target_achieved_at    TEXT,
    target_superseded_by  TEXT,
    verdict_mechanism     TEXT,
    verdict_check         TEXT,
    verdict_assertion     TEXT,
    verdict_judge_prompt  TEXT,
    verdict_status        TEXT,
    verdict_evidence_ref  TEXT,
    verdict_evidence_hash TEXT,
    verdict_last_checked  TEXT,
    rationale             TEXT,                       -- anti-drift
    alternatives_considered TEXT,                     -- anti-drift
    current_revision_id   INTEGER,
    last_modified_at      TEXT NOT NULL,
    deleted_at            TEXT,
    PRIMARY KEY (project_id, node_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS node_edges (
    project_id   TEXT NOT NULL,
    src_node_id  TEXT NOT NULL,
    dst_node_id  TEXT NOT NULL,
    edge_kind    TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    PRIMARY KEY (project_id, src_node_id, dst_node_id, edge_kind),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS revisions (
    revision_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       TEXT NOT NULL,
    node_id          TEXT NOT NULL,
    ts               TEXT NOT NULL,
    change_type      TEXT NOT NULL,
    prev_revision_id INTEGER,
    snapshot         TEXT NOT NULL,
    change_summary   TEXT,
    change_reason    TEXT,                            -- anti-drift
    batch_id         TEXT,
    source           TEXT NOT NULL,
    actor            TEXT NOT NULL,
    git_sha          TEXT,
    note             TEXT
);

CREATE TABLE IF NOT EXISTS validations (
    validation_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id        TEXT NOT NULL,
    started_at        TEXT NOT NULL,
    finished_at       TEXT,
    status            TEXT NOT NULL,
    nodes_total       INTEGER,
    issues_total      INTEGER,
    verdicts_run      INTEGER NOT NULL DEFAULT 0,
    targets_run       INTEGER NOT NULL DEFAULT 0,
    framework_version TEXT
);

CREATE TABLE IF NOT EXISTS verdicts (
    verdict_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    validation_id   INTEGER NOT NULL,
    project_id      TEXT NOT NULL,
    node_id         TEXT NOT NULL,
    mechanism       TEXT NOT NULL,
    status          TEXT NOT NULL,
    source          TEXT NOT NULL,
    evidence_ref    TEXT,
    evidence_hash   TEXT,
    FOREIGN KEY (validation_id) REFERENCES validations(validation_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    project_id  TEXT,
    event_type  TEXT NOT NULL,
    detail      TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_links (
    theme_node_id  TEXT NOT NULL,
    project_id     TEXT NOT NULL,
    node_id        TEXT NOT NULL,
    created_at     TEXT NOT NULL,
    PRIMARY KEY (theme_node_id, project_id, node_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cross_project_edges (
    src_project_id  TEXT NOT NULL,
    src_node_id     TEXT NOT NULL,
    dst_project_id  TEXT NOT NULL,
    dst_node_id     TEXT NOT NULL,
    edge_kind       TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    PRIMARY KEY (src_project_id, src_node_id, dst_project_id, dst_node_id, edge_kind),
    FOREIGN KEY (src_project_id) REFERENCES projects(project_id) ON DELETE CASCADE,
    FOREIGN KEY (dst_project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS nodes_layer ON nodes(project_id, layer);
CREATE INDEX IF NOT EXISTS nodes_target_status ON nodes(project_id, target_status);
CREATE INDEX IF NOT EXISTS nodes_target_status_global ON nodes(target_status, last_modified_at DESC);
CREATE INDEX IF NOT EXISTS nodes_verdict_status ON nodes(project_id, verdict_status);
CREATE INDEX IF NOT EXISTS nodes_realized_by_external ON nodes(realized_by_external) WHERE realized_by_external IS NOT NULL;
CREATE INDEX IF NOT EXISTS nodes_deleted ON nodes(project_id, deleted_at) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS edges_dst ON node_edges(project_id, dst_node_id, edge_kind);
CREATE INDEX IF NOT EXISTS edges_src ON node_edges(project_id, src_node_id, edge_kind);

CREATE INDEX IF NOT EXISTS revisions_node_ts ON revisions(project_id, node_id, ts DESC);
CREATE INDEX IF NOT EXISTS revisions_chain ON revisions(prev_revision_id);
CREATE INDEX IF NOT EXISTS revisions_global_ts ON revisions(project_id, ts DESC);
CREATE INDEX IF NOT EXISTS revisions_change_type ON revisions(change_type);
CREATE INDEX IF NOT EXISTS revisions_git_sha ON revisions(git_sha) WHERE git_sha IS NOT NULL;
CREATE INDEX IF NOT EXISTS revisions_batch ON revisions(batch_id) WHERE batch_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS verdicts_node ON verdicts(project_id, node_id, validation_id DESC);
CREATE INDEX IF NOT EXISTS verdicts_validation ON verdicts(validation_id);

CREATE INDEX IF NOT EXISTS events_project_ts ON events(project_id, ts DESC);
CREATE INDEX IF NOT EXISTS events_type ON events(event_type, ts DESC);

CREATE INDEX IF NOT EXISTS portfolio_links_theme
    ON portfolio_links(theme_node_id);
CREATE INDEX IF NOT EXISTS portfolio_links_target
    ON portfolio_links(project_id, node_id);

CREATE INDEX IF NOT EXISTS cross_edges_dst
    ON cross_project_edges(dst_project_id, dst_node_id, edge_kind);
CREATE INDEX IF NOT EXISTS cross_edges_src
    ON cross_project_edges(src_project_id, src_node_id, edge_kind);

CREATE TABLE IF NOT EXISTS trajectories (
    trajectory_id   TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    status          TEXT NOT NULL,
    target_brief    TEXT NOT NULL,
    scope_json      TEXT,
    proposed_by     TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    resolved_at     TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS trajectory_legs (
    leg_id               TEXT PRIMARY KEY,
    trajectory_id        TEXT NOT NULL,
    seq                  INTEGER NOT NULL,
    leg_kind             TEXT NOT NULL,
    node_ref             TEXT,
    payload_json         TEXT NOT NULL,
    status               TEXT NOT NULL,
    applied_revision_id  INTEGER,
    FOREIGN KEY (trajectory_id) REFERENCES trajectories(trajectory_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS trajectories_project
    ON trajectories(project_id, created_at DESC);
CREATE INDEX IF NOT EXISTS trajectory_legs_traj
    ON trajectory_legs(trajectory_id, seq);
