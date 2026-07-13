"""
SQLite connection helpers for manifold.

Every connection enables WAL mode, foreign keys, and a dict-like row factory.
"""
import sqlite3
from pathlib import Path
from typing import Optional


def connect(path=None, *, check_same_thread: bool = True) -> sqlite3.Connection:
    """Open a manifold-flavored connection to the SQLite DB at `path`.

    `path` may be a Path, a str path, ":memory:", or None (uses config.db_path()).
    Creates the parent directory if needed. Enables WAL, foreign keys, and Row
    row factory.

    Set `check_same_thread=False` when sharing one connection across threads
    (e.g., from the web server's ThreadingHTTPServer). Safe with WAL mode +
    SQLite's internal locking.
    """
    from manifold import config
    if path is None:
        path = config.db_path()
    if isinstance(path, str):
        # Special-case the in-memory DB string; don't try to mkdir on it.
        if path != ":memory:":
            path = Path(path)
    if isinstance(path, Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_target = str(path)
    else:
        sqlite_target = path  # ":memory:" or any sqlite3-recognized URI
    conn = sqlite3.connect(sqlite_target, timeout=30.0, isolation_level=None,
                            check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn
