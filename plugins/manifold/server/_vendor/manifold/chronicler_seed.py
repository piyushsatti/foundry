"""Rich Chronicler showcase graph for visualization testing (brief, diagrams, mindmaps).

Fictional but realistic local-first life-logging product spread across a polyrepo:
  - chronicler       — core platform (intent → capabilities → realizations)
  - chronicler-ios   — mobile companion
  - chronicler-sync  — optional E2E sync relay

Use ``seed_chronicler(..., force=True)`` to replace an existing sparse graph.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from . import queries, writes

PROJECT_ID = "chronicler"
PROJECT_LABEL = "Chronicler"
IOS_PROJECT = "chronicler-ios"
IOS_LABEL = "Chronicler iOS"
SYNC_PROJECT = "chronicler-sync"
SYNC_LABEL = "Chronicler Sync"

LAYERS = [
    {"name": "intent", "verdict_default": "human_signoff"},
    {"name": "capabilities", "verdict_default": "human_signoff"},
    {"name": "realizations", "verdict_default": "automated_check"},
]

CHRONICLER_PROJECTS = frozenset({PROJECT_ID, IOS_PROJECT, SYNC_PROJECT})


def purge_chronicler_projects(conn: sqlite3.Connection) -> list[str]:
    """Remove chronicler showcase projects and dependent rows."""
    ids = [
        r["project_id"] for r in conn.execute("SELECT project_id FROM projects")
        if r["project_id"] in CHRONICLER_PROJECTS
    ]
    if not ids:
        return []

    for pid in ids:
        conn.execute("DELETE FROM revisions WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM verdicts WHERE project_id = ?", (pid,))
        conn.execute("DELETE FROM validations WHERE project_id = ?", (pid,))
    conn.execute(
        "DELETE FROM cross_project_edges WHERE src_project_id IN ({}) OR dst_project_id IN ({})".format(
            ",".join("?" * len(ids)), ",".join("?" * len(ids)),
        ),
        ids + ids,
    )
    conn.execute(
        "DELETE FROM portfolio_links WHERE project_id IN ({})".format(
            ",".join("?" * len(ids)),
        ),
        ids,
    )
    for pid in ids:
        conn.execute("DELETE FROM projects WHERE project_id = ?", (pid,))
    return ids


def seed_chronicler(
    conn: sqlite3.Connection,
    *,
    actor: str = "chronicler:seed",
    force: bool = False,
) -> dict:
    """Create or refresh the Chronicler visualization showcase."""
    existing = queries.get_project(conn, PROJECT_ID)
    if existing and not force:
        return summary(conn, status="already_seeded")

    if force or existing:
        purge_chronicler_projects(conn)

    _register_projects(conn)
    _seed_core_graph(conn, actor=actor)
    _seed_ios_graph(conn, actor=actor)
    _seed_sync_graph(conn, actor=actor)
    _wire_cross_edges(conn, actor=actor)

    return summary(conn, status="seeded")


def _register_projects(conn: sqlite3.Connection) -> None:
    for project_id, label in (
        (PROJECT_ID, PROJECT_LABEL),
        (IOS_PROJECT, IOS_LABEL),
        (SYNC_PROJECT, SYNC_LABEL),
    ):
        writes.register_project(
            conn, project_id,
            spec_config={"layers": LAYERS},
            label=label,
        )


def _seed_core_graph(conn: sqlite3.Connection, *, actor: str) -> None:
    pid = PROJECT_ID

    intents = [
        ("I.1", "Local-first life logging", (
            "# Chronicler\n\n"
            "Capture daily life — journal entries, photos, voice, location context — "
            "stored on-device first. Search and reflect without surrendering data to a cloud vendor."
        ), "in_progress"),
        ("I.2", "Privacy by default", (
            "# Privacy\n\n"
            "No account required for core use. Optional encrypted sync is opt-in. "
            "Export always available."
        ), "achieved"),
        ("I.3", "Multi-surface capture", (
            "# Surfaces\n\n"
            "Web PWA, native iOS, voice memos, and import from Apple Photos / Google Takeout."
        ), "in_progress"),
    ]
    for node_id, title, body, status in intents:
        _node(conn, pid, "intent", node_id, title, body=body,
              target_status=status, actor=actor)

    _node(conn, pid, "intent", "I.C1", "Never upload plaintext without consent",
          body="Hard constraint: all cloud paths require explicit user opt-in.",
          kind="constraint", target_status="achieved", actor=actor, parents=["I.2"])
    _node(conn, pid, "intent", "I.C2", "SQLite is canonical store",
          body="On-device SQLite + FTS5; no proprietary binary blob format.",
          kind="constraint", target_status="achieved", actor=actor, parents=["I.1"])

    caps = [
        ("C.1", "Capture pipeline", "Ingest text, markdown, photos, and voice into timeline.", "I.1", "achieved"),
        ("C.2", "Search & recall", "Full-text + semantic search over entries and entities.", "I.1", "in_progress"),
        ("C.3", "Timeline & calendar", "Day/week/month views with mood and tag overlays.", "I.1", "in_progress"),
        ("C.4", "Entity extraction", "People, places, topics from entries (local ML).", "I.1", "planned"),
        ("C.5", "Encrypted sync", "Optional E2E sync between devices via relay.", "I.2", "planned"),
        ("C.6", "Mobile companion", "Native iOS capture, widgets, share extension.", "I.3", "in_progress"),
        ("C.7", "Voice ingestion", "Transcribe voice memos offline; link to timeline.", "I.3", "planned"),
        ("C.8", "Export & portability", "Markdown + JSON export; GDPR-style delete.", "I.2", "achieved"),
        ("C.9", "Weekly review ritual", "Agent-assisted recap and vault health prompts.", "I.1", "planned"),
    ]
    for nid, title, body, parent, status in caps:
        _node(conn, pid, "capabilities", nid, title,
              body=f"# {title}\n\n{body}", parents=[parent],
              target_status=status, actor=actor)

    reals = [
        # Capture (achieved cluster)
        ("R.1.1", "Entry CRUD API", "FastAPI routes for create/read/update entries.", "C.1", "achieved"),
        ("R.1.2", "Photo attachment store", "Local blob dir + thumbnail generation.", "C.1", "achieved"),
        ("R.1.3", "Markdown editor", "TipTap-based editor with autosave.", "C.1", "achieved"),
        ("R.1.4", "Import pipeline", "Apple Photos + Google Takeout batch import.", "C.1", "in_progress"),
        # Search (mixed)
        ("R.2.1", "FTS5 index", "SQLite FTS over title + body + tags.", "C.2", "achieved"),
        ("R.2.2", "Semantic embeddings", "Local embedding model for similarity search.", "C.2", "in_progress"),
        ("R.2.3", "Search UI", "Command palette + filter chips.", "C.2", "planned"),
        ("R.2.4", "Saved searches", "Persist queries as smart collections.", "C.2", "planned"),
        # Timeline
        ("R.3.1", "Day view", "Scrollable day strip with entry cards.", "C.3", "achieved"),
        ("R.3.2", "Calendar heatmap", "Activity density by day.", "C.3", "in_progress"),
        ("R.3.3", "Mood tagging", "Optional mood enum on entries.", "C.3", "planned"),
        # Entity extraction
        ("R.4.1", "NER pipeline", "spaCy + custom gazetteer for people/places.", "C.4", "planned"),
        ("R.4.2", "Entity graph UI", "Browse people ↔ entries relationships.", "C.4", "planned"),
        ("R.4.3", "Topic clustering", "Unsupervised topic labels on monthly batches.", "C.4", "deferred"),
        # Sync (blocked downstream)
        ("R.5.1", "Sync client SDK", "Conflict-free merge for entry deltas.", "C.5", "planned"),
        ("R.5.2", "Device pairing", "QR code + short code pairing flow.", "C.5", "planned"),
        ("R.5.3", "Offline queue", "Retry sync when network returns.", "C.5", "planned"),
        # Mobile (cross-repo)
        ("R.6.1", "Share extension spec", "Contract for iOS share → chronicler ingest.", "C.6", "achieved"),
        ("R.6.2", "Widget designs", "Quick-capture widget + today summary.", "C.6", "in_progress"),
        # Voice
        ("R.7.1", "Whisper local", "On-device transcription for voice memos.", "C.7", "planned"),
        ("R.7.2", "Voice → entry linker", "Attach transcript to timeline entry.", "C.7", "planned"),
        # Export
        ("R.8.1", "Markdown export", "Zip of entries as .md files.", "C.8", "achieved"),
        ("R.8.2", "JSON archive", "Full-fidelity export for migration.", "C.8", "achieved"),
        # Weekly review
        ("R.9.1", "Review prompt templates", "Structured questions for weekly ritual.", "C.9", "planned"),
        ("R.9.2", "Vault doctor integration", "PARA health check hooks.", "C.9", "planned"),
    ]
    for nid, title, body, parent, status in reals:
        _node(conn, pid, "realizations", nid, title,
              body=f"# {title}\n\n{body}", parents=[parent],
              target_status=status, actor=actor)


def _seed_ios_graph(conn: sqlite3.Connection, *, actor: str) -> None:
    pid = IOS_PROJECT

    _node(conn, pid, "intent", "I.1", "Native iOS companion",
          body="# iOS\n\nSwiftUI app: capture, browse timeline, widgets.",
          target_status="in_progress", actor=actor)

    caps = [
        ("C.1", "Share extension", "Receive URLs, text, images from other apps.", "I.1", "in_progress"),
        ("C.2", "Timeline reader", "Read-only timeline with offline cache.", "I.1", "planned"),
        ("C.3", "Push notifications", "Reminders for journaling ritual.", "I.1", "planned"),
        ("C.4", "Widgets", "Today summary + quick capture.", "I.1", "in_progress"),
    ]
    for nid, title, body, parent, status in caps:
        _node(conn, pid, "capabilities", nid, title,
              body=f"# {title}\n\n{body}", parents=[parent],
              target_status=status, actor=actor)

    reals = [
        ("R.1", "Share extension v1", "UIKit share sheet → chronicler API.", "C.1", "in_progress"),
        ("R.2", "Core Data cache", "Offline read model synced from main app.", "C.2", "planned"),
        ("R.3", "APNs registration", "Device token + notification categories.", "C.3", "planned"),
        ("R.4", "WidgetKit bundle", "Small + medium widgets.", "C.4", "in_progress"),
        ("R.5", "App Store pipeline", "TestFlight + release automation.", "C.1", "planned"),
    ]
    for nid, title, body, parent, status in reals:
        _node(conn, pid, "realizations", nid, title,
              body=f"# {title}\n\n{body}", parents=[parent],
              target_status=status, actor=actor)


def _seed_sync_graph(conn: sqlite3.Connection, *, actor: str) -> None:
    pid = SYNC_PROJECT

    _node(conn, pid, "intent", "I.1", "Optional sync relay",
          body="# Sync relay\n\nMinimal E2E encrypted blob relay — zero knowledge of plaintext.",
          target_status="planned", actor=actor)

    caps = [
        ("C.1", "Relay API", "Store encrypted blobs; no decryption server-side.", "I.1", "planned"),
        ("C.2", "Pairing service", "Short-lived pairing tokens.", "I.1", "planned"),
    ]
    for nid, title, body, parent, status in caps:
        _node(conn, pid, "capabilities", nid, title,
              body=f"# {title}\n\n{body}", parents=[parent],
              target_status=status, actor=actor)

    reals = [
        ("R.1", "Rust relay server", "Axum + S3-compatible blob store.", "C.1", "planned"),
        ("R.2", "Rate limiting", "Per-device upload quotas.", "C.1", "planned"),
        ("R.3", "Pairing endpoint", "POST /pair with QR payload.", "C.2", "planned"),
    ]
    for nid, title, body, parent, status in reals:
        _node(conn, pid, "realizations", nid, title,
              body=f"# {title}\n\n{body}", parents=[parent],
              target_status=status, actor=actor)


def _wire_cross_edges(conn: sqlite3.Connection, *, actor: str) -> None:
    """Cross-project blockers for blocker diagram testing."""
    edges = [
        (PROJECT_ID, "R.5.1", SYNC_PROJECT, "R.1", "blocks"),
        (PROJECT_ID, "R.5.2", SYNC_PROJECT, "R.3", "blocks"),
        (PROJECT_ID, "R.6.2", IOS_PROJECT, "R.4", "blocks"),
        (IOS_PROJECT, "R.1", PROJECT_ID, "R.6.1", "blocks"),
        (IOS_PROJECT, "R.3", PROJECT_ID, "R.5.3", "blocks"),
    ]
    existing = queries.list_cross_edges(conn)
    existing_keys = {
        (e["src_project_id"], e["src_node_id"], e["dst_project_id"], e["dst_node_id"])
        for e in existing
    }
    for src_p, src_n, dst_p, dst_n, rel in edges:
        key = (src_p, src_n, dst_p, dst_n)
        if key in existing_keys:
            continue
        writes.create_cross_edge(conn, src_p, src_n, dst_p, dst_n, rel, actor=actor)


def _node(
    conn: sqlite3.Connection,
    project_id: str,
    layer: str,
    node_id: str,
    title: str,
    *,
    body: str,
    actor: str,
    parents: Optional[list[str]] = None,
    target_status: str = "planned",
    kind: str = "spec",
) -> None:
    if queries.get_node(conn, project_id, node_id) is not None:
        return
    writes.create_node(
        conn, project_id, layer, node_id, title,
        body=body, kind=kind, parents=parents or [],
        target_status=target_status, actor=actor,
    )


def demo_urls(*, host: str = "127.0.0.1", port: int = 7779) -> dict[str, str]:
    base = f"http://{host}:{port}"
    pid = PROJECT_ID
    return {
        "home": f"{base}/",
        "project": f"{base}/projects/{pid}",
        "brief": f"{base}/projects/{pid}/brief",
        "mindmap": f"{base}/projects/{pid}/mindmap?focus=I.1",
        "mindmap_search": f"{base}/projects/{pid}/mindmap?focus=C.2",
        "diagram_decomposition": f"{base}/projects/{pid}/views/decomposition?focus=I.1",
        "diagram_blockers_sync": f"{base}/projects/{pid}/views/blockers?focus=R.5.1",
        "diagram_blockers_ios": f"{base}/projects/{pid}/views/blockers?focus=R.6.2",
        "drift": f"{base}/projects/{pid}/drift-report",
        "ios": f"{base}/projects/{IOS_PROJECT}",
        "sync": f"{base}/projects/{SYNC_PROJECT}",
    }


def summary(conn: sqlite3.Connection, *, status: str,
            host: str = "127.0.0.1", port: int = 7779) -> dict:
    counts = {
        pid: _node_count(conn, pid)
        for pid in (PROJECT_ID, IOS_PROJECT, SYNC_PROJECT)
    }
    return {
        "status": status,
        "main_project": PROJECT_ID,
        "projects": list(CHRONICLER_PROJECTS),
        "node_counts": counts,
        "total_nodes": sum(counts.values()),
        "urls": demo_urls(host=host, port=port),
        "visualization_focus": {
            "brief": PROJECT_ID,
            "mindmap_root": "I.1",
            "blockers_sync": "R.5.1",
            "blockers_ios": "R.6.2",
            "decomposition": "C.2",
        },
    }


def _node_count(conn: sqlite3.Connection, project_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM nodes WHERE project_id = ? AND deleted_at IS NULL",
        (project_id,),
    ).fetchone()
    return int(row["n"]) if row else 0
