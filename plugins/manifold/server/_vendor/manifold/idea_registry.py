"""Per-idea manifold databases — one SQLite file per product idea.

Chronicler, Hailey, and Foundry are separate ideas with separate spec graphs.
Portfolio rollup is optional and lives in its own DB when needed (not seeded here).
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from . import queries, writes
from . import foundry_seed
from . import chronicler_seed

CLAUDE_DIR = Path.home() / ".claude"


@dataclass(frozen=True)
class IdeaSpec:
    idea_id: str
    project_id: str
    label: str
    db_filename: str
    description: str

    @property
    def default_db_path(self) -> Path:
        return CLAUDE_DIR / self.db_filename


IDEAS: dict[str, IdeaSpec] = {
    "foundry": IdeaSpec(
        idea_id="foundry",
        project_id="ai-foundry",
        label="AI Foundry",
        db_filename="foundry.db",
        description="Manifold tooling monorepo (skills, MCP, web, core library).",
    ),
    "chronicler": IdeaSpec(
        idea_id="chronicler",
        project_id="chronicler",
        label="Chronicler",
        db_filename="chronicler.db",
        description="Local-first life logging product.",
    ),
    "hailey": IdeaSpec(
        idea_id="hailey",
        project_id="hailey",
        label="Hailey",
        db_filename="hailey.db",
        description="Separate product idea — seed intent only; flesh out in-repo.",
    ),
}

DEFAULT_IDEA = "foundry"

PRODUCT_LAYERS = [
    {"name": "intent", "verdict_default": "human_signoff"},
    {"name": "capabilities", "verdict_default": "human_signoff"},
    {"name": "realizations", "verdict_default": "automated_check"},
]


def list_ideas() -> list[IdeaSpec]:
    return list(IDEAS.values())


def get_idea(idea_id: str) -> IdeaSpec:
    spec = IDEAS.get(idea_id)
    if spec is None:
        known = ", ".join(sorted(IDEAS))
        raise KeyError(f"Unknown idea {idea_id!r} (known: {known})")
    return spec


def ideas_config_map() -> dict[str, dict[str, str]]:
    """Serialize idea → db_path + project_id for manifold.json."""
    return {
        spec.idea_id: {
            "db_path": f"~/.claude/{spec.db_filename}",
            "project_id": spec.project_id,
            "label": spec.label,
        }
        for spec in IDEAS.values()
    }


def seed_product_idea(
    conn: sqlite3.Connection,
    spec: IdeaSpec,
    *,
    actor: str = "manifold:init-ideas",
) -> dict:
    """Minimal 3-layer graph for a standalone product idea."""
    if queries.get_project(conn, spec.project_id) is not None:
        return _product_summary(conn, spec)

    writes.register_project(
        conn,
        spec.project_id,
        spec_config={"layers": PRODUCT_LAYERS},
        label=spec.label,
    )

    intent_body = _intent_body(spec)
    writes.create_node(
        conn, spec.project_id, "intent", "I.1", spec.label,
        body=intent_body,
        target_status="in_progress",
        actor=actor,
    )

    writes.create_node(
        conn, spec.project_id, "capabilities", "C.1", "MVP",
        body=f"# MVP\n\nFirst shippable slice of {spec.label}.",
        parents=["I.1"],
        target_status="planned",
        actor=actor,
    )

    writes.create_node(
        conn, spec.project_id, "realizations", "R.1", "Initial codebase",
        body=f"# Initial codebase\n\n{spec.description}",
        parents=["C.1"],
        target_status="planned",
        actor=actor,
    )

    return _product_summary(conn, spec)


def _intent_body(spec: IdeaSpec) -> str:
    if spec.idea_id == "chronicler":
        return (
            "# Chronicler\n\n"
            "Local-first life logging — capture, reflect, and search personal history "
            "without surrendering data to a cloud vendor."
        )
    if spec.idea_id == "hailey":
        return (
            "# Hailey\n\n"
            "Product idea (details TBD). Use this graph for intent → capabilities → "
            "realizations as the idea crystallizes."
        )
    return f"# {spec.label}\n\n{spec.description}"


def _product_summary(conn: sqlite3.Connection, spec: IdeaSpec) -> dict:
    pid = spec.project_id
    count = conn.execute(
        "SELECT COUNT(*) AS n FROM nodes WHERE project_id = ? AND deleted_at IS NULL",
        (pid,),
    ).fetchone()["n"]
    return {
        "idea_id": spec.idea_id,
        "project_id": pid,
        "project_label": spec.label,
        "db_path": str(spec.default_db_path),
        "node_count": count,
        "status": "seeded" if count else "empty",
    }


def seed_foundry_idea(
    conn: sqlite3.Connection,
    *,
    repo_root: Path,
    actor: str = "foundry:init",
    purge: bool = True,
) -> dict:
    """Seed ai-foundry dogfood graph without portfolio theme layer."""
    if purge:
        foundry_seed.purge_all_projects(conn)
    result = foundry_seed.seed_ai_foundry(
        conn, repo_root=repo_root, actor=actor, include_portfolio=False,
    )
    result["idea_id"] = "foundry"
    result["db_path"] = str(IDEAS["foundry"].default_db_path)
    result["status"] = "seeded"
    return result


SeedFn = Callable[..., dict]

_SEEDERS: dict[str, SeedFn] = {
    "foundry": lambda conn, **kw: seed_foundry_idea(conn, **kw),
    "chronicler": lambda conn, **kw: chronicler_seed.seed_chronicler(
        conn, actor=kw.get("actor", "manifold:init-ideas"), force=kw.get("force", False),
    ),
    "hailey": lambda conn, **kw: seed_product_idea(conn, IDEAS["hailey"], **kw),
}


def init_idea_db(
    idea_id: str,
    db_path: Path,
    *,
    repo_root: Optional[Path] = None,
    actor: str = "manifold:init-ideas",
    purge_foundry: bool = True,
) -> dict:
    """Create or refresh one idea's SQLite file."""
    from . import db, schema

    spec = get_idea(idea_id)
    db_path = Path(db_path).expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = db.connect(db_path)
    try:
        schema.bootstrap(conn)
        seeder = _SEEDERS[idea_id]
        if idea_id == "foundry":
            if repo_root is None:
                repo_root = Path(__file__).resolve().parents[3]
            result = seeder(conn, repo_root=repo_root, actor=actor, purge=purge_foundry)
        else:
            result = seeder(conn, actor=actor)
        conn.commit()
    finally:
        conn.close()

    result["db_path"] = str(db_path)
    return result


def init_all_ideas(
    *,
    repo_root: Optional[Path] = None,
    actor: str = "manifold:init-ideas",
    ideas: Optional[list[str]] = None,
) -> dict:
    """Initialize every registered idea DB under ~/.claude/."""
    selected = ideas or list(IDEAS)
    results = []
    for idea_id in selected:
        spec = get_idea(idea_id)
        results.append(
            init_idea_db(idea_id, spec.default_db_path, repo_root=repo_root, actor=actor)
        )
    config_result = write_ideas_config(default_idea=DEFAULT_IDEA)
    return {"ideas": results, "config": config_result}


def write_ideas_config(
    *,
    default_idea: str = DEFAULT_IDEA,
    force: bool = False,
) -> dict:
    """Write ~/.claude/manifold.json with per-idea db paths."""
    from . import config

    spec = get_idea(default_idea)
    path = config.config_path()

    if path.exists() and not force:
        cfg = config.load_config()
        if cfg.get("ideas"):
            return {
                "ok": True,
                "path": str(path),
                "action": "kept_existing",
                "message": "Config already has ideas registry (use --force to rewrite).",
            }

    data: dict = {
        "schema_version": 1,
        "db_path": f"~/.claude/{spec.db_filename}",
        "default_idea": default_idea,
        "ideas": ideas_config_map(),
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")

    config._reset_config_cache()
    return {"ok": True, "path": str(path), "action": "written", "default_idea": default_idea}


def resolve_idea_db(idea_id: str) -> Path:
    """Return db path for an idea (config file > built-in default)."""
    from . import config

    spec = get_idea(idea_id)
    cfg = config.load_config()
    ideas = cfg.get("ideas") or {}
    entry = ideas.get(idea_id) or {}
    raw = (entry.get("db_path") or "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return spec.default_db_path.resolve()
