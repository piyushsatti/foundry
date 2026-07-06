"""
Bootstrap the manifold schema from schema.sql.

Idempotent: safe to call on an existing DB.  If the DB is at a prior schema
version, _apply_migrations() upgrades it in place before returning.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from manifold import config


SCHEMA_SQL_PATH = Path(__file__).resolve().parent.parent / "schema.sql"

# Idempotent column adds for DBs created before rationale / change_reason shipped.
_LEGACY_COLUMN_ALTERs = (
    "ALTER TABLE nodes ADD COLUMN rationale TEXT",
    "ALTER TABLE nodes ADD COLUMN alternatives_considered TEXT",
    "ALTER TABLE revisions ADD COLUMN change_reason TEXT",
)


def _get_schema_version(conn: sqlite3.Connection):
    """Return the integer schema_version from schema_meta, or None if no row exists."""
    row = conn.execute("SELECT schema_version FROM schema_meta LIMIT 1").fetchone()
    if row is None:
        return None
    return int(row[0])


def _apply_legacy_column_alters(conn: sqlite3.Connection) -> None:
    for stmt in _LEGACY_COLUMN_ALTERs:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError as e:
            if "duplicate column name" not in str(e).lower():
                raise


def _apply_pivot_rename(conn: sqlite3.Connection) -> None:
    """change_reason 'drift' was a misnomer (spec pivot, not intent drift)."""
    conn.execute(
        "UPDATE revisions SET change_reason = 'pivot' WHERE change_reason = 'drift'"
    )


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """Bring any existing DB to the canonical schema (schema_version=1)."""
    current = _get_schema_version(conn)
    if current is None:
        # Fresh DB — bootstrap already wrote the full schema; nothing to migrate.
        return

    _apply_legacy_column_alters(conn)
    _apply_pivot_rename(conn)

    if current != config.SCHEMA_VERSION:
        conn.execute(
            "UPDATE schema_meta SET schema_version = ?, upgraded_at = ?",
            (config.SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
        )


def bootstrap(conn: sqlite3.Connection) -> None:
    """Run the canonical schema.sql against this connection. Seed schema_meta.

    If the DB already exists at a prior schema version, applies migrations
    idempotently to bring it up to the current version.
    """
    sql = SCHEMA_SQL_PATH.read_text(encoding="utf-8")
    conn.executescript(sql)
    existing = conn.execute("SELECT COUNT(*) AS c FROM schema_meta").fetchone()
    if existing["c"] == 0:
        conn.execute(
            "INSERT INTO schema_meta (schema_version, upgraded_at) VALUES (?, ?)",
            (config.SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
        )
    else:
        # Existing DB — run migrations if needed.
        _apply_migrations(conn)
