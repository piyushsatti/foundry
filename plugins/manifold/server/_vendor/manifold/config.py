"""
Configuration for manifold.

Reads environment variables and a machine-local JSON config file, returning
concrete values with sensible defaults.

Resolution order (most specific wins): env var > config file > built-in default.

Config file location: ~/.claude/manifold.json (overridable via $MANIFOLD_CONFIG).
The file is read at most once per process and cached; call _reset_config_cache()
to reset (used in tests).
"""
import json
import os
import sys
from pathlib import Path


SCHEMA_VERSION = 1

MANIFOLD_VERSION = "0.1.0"

_KNOWN_KEYS = {"db_path", "judge_command", "snapshot_interval", "default_idea", "ideas", "schema_version"}

# Module-level cache sentinel; None means "not yet read".
_config_cache: dict | None = None


def _reset_config_cache() -> None:
    """Reset the cached config dict. Called between tests to ensure hermeticity."""
    global _config_cache
    _config_cache = None


def config_path() -> Path:
    """Return the resolved config file path (honouring $MANIFOLD_CONFIG)."""
    override = os.environ.get("MANIFOLD_CONFIG", "").strip()
    if override:
        return Path(override)
    return Path.home() / ".claude" / "manifold.json"


def load_config() -> dict:
    """Read and cache the config file. Fail-soft: returns {} on any problem.

    - Absent file → {} with no warning.
    - Malformed JSON → {} with one stderr warning.
    - Non-object JSON → treated as malformed (emits same warning).
    - Unknown keys are kept in the returned dict so callers can surface them.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    path = config_path()
    if not path.exists():
        _config_cache = {}
        return _config_cache

    try:
        raw = path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"manifold: ignoring malformed config at {path}: {exc}",
            file=sys.stderr,
        )
        _config_cache = {}
        return _config_cache

    if not isinstance(parsed, dict):
        print(
            f"manifold: ignoring malformed config at {path}: expected a JSON object",
            file=sys.stderr,
        )
        _config_cache = {}
        return _config_cache

    _config_cache = parsed
    return _config_cache


def db_path() -> Path:
    """Return the path to the manifold SQLite DB.

    Resolution: $MANIFOLD_DB > config file db_path > ~/.claude/manifold.db
    """
    override = os.environ.get("MANIFOLD_DB", "").strip()
    if override:
        return Path(override)

    cfg = load_config()
    file_val = (cfg.get("db_path") or "").strip()
    if file_val:
        return Path(os.path.expanduser(file_val))

    return Path.home() / ".claude" / "manifold.db"


def default_idea() -> str:
    """Return the configured default idea id (for foundry checkout: foundry)."""
    cfg = load_config()
    val = (cfg.get("default_idea") or "").strip()
    if val:
        return val
    return "foundry"


def idea_db_path(idea_id: str) -> Path | None:
    """Resolve db path for a named idea from config, or None if not configured."""
    cfg = load_config()
    ideas = cfg.get("ideas")
    if not isinstance(ideas, dict):
        return None
    entry = ideas.get(idea_id)
    if not isinstance(entry, dict):
        return None
    raw = (entry.get("db_path") or "").strip()
    if not raw:
        return None
    return Path(os.path.expanduser(raw))


def snapshot_interval_seconds() -> int:
    """Return the snapshot interval in seconds.

    Resolution: $MANIFOLD_SNAPSHOT_INTERVAL > config file snapshot_interval > 3600
    """
    raw = os.environ.get("MANIFOLD_SNAPSHOT_INTERVAL", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            return 3600

    cfg = load_config()
    file_val = cfg.get("snapshot_interval")
    if file_val is not None:
        try:
            return int(file_val)
        except (TypeError, ValueError):
            return 3600

    return 3600


def effective_settings() -> dict:
    """Return each setting's resolved value and source for 'config show'.

    Returns a dict like:
      {
        "db_path":           {"value": Path(...), "source": "env"|"file"|"default"},
        "judge_command":     {"value": "...",      "source": "env"|"file"|"default"},
        "snapshot_interval": {"value": 3600,       "source": "env"|"file"|"default"},
        "unrecognized":      {"key1": val1, ...},  # present only if there are unknown keys
      }

    Note: judge_command here is the machine-global resolution only (env > file > default).
    An individual project's spec_config.judge_command may still override it at validation
    time; that per-project tier is resolved in validate._resolve_judge_command, not here.
    """
    cfg = load_config()
    result: dict = {}

    # --- db_path ---
    env_db = os.environ.get("MANIFOLD_DB", "").strip()
    if env_db:
        result["db_path"] = {"value": Path(env_db), "source": "env"}
    else:
        file_db = (cfg.get("db_path") or "").strip()
        if file_db:
            result["db_path"] = {
                "value": Path(os.path.expanduser(file_db)),
                "source": "file",
            }
        else:
            result["db_path"] = {
                "value": Path.home() / ".claude" / "manifold.db",
                "source": "default",
            }

    # --- judge_command (machine-global only: env > file > default) ---
    env_judge = os.environ.get("MANIFOLD_JUDGE_CMD", "").strip()
    if env_judge:
        result["judge_command"] = {"value": env_judge, "source": "env"}
    else:
        file_judge = (cfg.get("judge_command") or "").strip()
        if file_judge:
            result["judge_command"] = {"value": file_judge, "source": "file"}
        else:
            result["judge_command"] = {"value": "", "source": "default"}

    # --- snapshot_interval ---
    env_snap = os.environ.get("MANIFOLD_SNAPSHOT_INTERVAL", "").strip()
    if env_snap:
        try:
            result["snapshot_interval"] = {"value": int(env_snap), "source": "env"}
        except ValueError:
            result["snapshot_interval"] = {"value": 3600, "source": "default"}
    else:
        file_snap = cfg.get("snapshot_interval")
        if file_snap is not None:
            try:
                result["snapshot_interval"] = {"value": int(file_snap), "source": "file"}
            except (TypeError, ValueError):
                result["snapshot_interval"] = {"value": 3600, "source": "default"}
        else:
            result["snapshot_interval"] = {"value": 3600, "source": "default"}

    # --- unrecognized keys ---
    unknown = {k: v for k, v in cfg.items() if k not in _KNOWN_KEYS}
    if unknown:
        result["unrecognized"] = unknown

    return result


def config_init(path: str | Path, force: bool = False) -> dict:
    """Write a manifold.json seeded from current effective values.

    Args:
        path: Destination file path (the resolved config_path()).
        force: If True, overwrite an existing file; if False, refuse.

    Returns:
        {"ok": True} on success, or {"ok": False, "message": "..."} on refusal.
    """
    p = Path(path)
    if p.exists() and not force:
        return {
            "ok": False,
            "message": f"config already exists at {p} (use --force to overwrite)",
        }

    settings = effective_settings()

    data: dict = {}
    db_val = settings["db_path"]["value"]
    # Store as string; keep ~ form if that's what the user has, otherwise absolute str
    data["db_path"] = str(db_val)

    judge_val = settings["judge_command"]["value"]
    data["judge_command"] = judge_val  # may be ""

    snap_val = settings["snapshot_interval"]["value"]
    data["snapshot_interval"] = snap_val

    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")

    # Invalidate cache so subsequent load_config() in the same process reads the
    # new file (important for test 8's round-trip and for interactive use).
    _reset_config_cache()

    return {"ok": True, "path": str(p)}
