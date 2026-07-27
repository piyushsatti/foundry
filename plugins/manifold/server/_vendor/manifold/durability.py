"""
Durability for manifold.

- snapshot(): VACUUM INTO sibling file with ISO timestamp suffix.
- dump(): NDJSON of every table to a file. Lossless.
- restore(): Rebuild a DB from a dump.
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from manifold import db, schema


TABLES = ("schema_meta", "projects", "nodes", "node_edges", "revisions",
          "validations", "verdicts", "events", "portfolio_links",
          "cross_project_edges")


def snapshot(db_path: Path) -> Path:
    """Create a VACUUM INTO snapshot. Returns the snapshot path."""
    db_path = Path(db_path)
    ts = datetime.now(timezone.utc).isoformat().replace(":", "-")
    out = db_path.parent / f"{db_path.name}.snapshot-{ts}"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("VACUUM INTO ?", (str(out),))
    finally:
        conn.close()
    return out


def dump(conn: sqlite3.Connection, out_path: Path) -> None:
    """Write NDJSON of every table. First line is a header record."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        header = {
            "manifold_dump_version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "tables": list(TABLES),
        }
        f.write(json.dumps(header) + "\n")
        for table in TABLES:
            rows = conn.execute(f"SELECT * FROM {table}").fetchall()
            for r in rows:
                f.write(json.dumps({"table": table, "row": dict(r)}) + "\n")
    tmp.replace(out_path)


def restore(dump_path: Path, target_db: Path) -> None:
    """Rebuild a DB from an NDJSON dump. target_db must not exist."""
    dump_path = Path(dump_path)
    target_db = Path(target_db)
    if target_db.exists():
        raise FileExistsError(f"{target_db} already exists; refusing to overwrite")
    conn = db.connect(target_db)
    try:
        schema.bootstrap(conn)
        # Clear the auto-seeded schema_meta row so the dump's row(s) load cleanly
        conn.execute("DELETE FROM schema_meta")
        lines = dump_path.read_text(encoding="utf-8").splitlines()
        for line in lines[1:]:
            if not line.strip():
                continue
            entry = json.loads(line)
            table = entry["table"]
            row = entry["row"]
            cols = list(row.keys())
            placeholders = ", ".join("?" * len(cols))
            col_list = ", ".join(cols)
            conn.execute(
                f"INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({placeholders})",
                [row[c] for c in cols],
            )
    finally:
        conn.close()
