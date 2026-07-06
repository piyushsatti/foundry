# manifold config file — design spec

**Status:** approved design, ready for implementation plan
**Date:** 2026-05-31
**Scope:** additive feature for manifold (v0.4.x). No DB schema change, no migration.

## Motivation

manifold is DB-canonical: the spec lives in one SQLite file, but the *configuration* that points at that file (and tunes a few behaviors) is currently spread across environment variables only — `$MANIFOLD_DB`, `$MANIFOLD_JUDGE_CMD`, `$MANIFOLD_SNAPSHOT_INTERVAL`. In practice a user repeats the DB path in their shell profile, in `.mcp.json`'s `env` block, and in any cron wiring. There is no single place to set it.

This feature adds **one machine-local JSON config file** that consolidates those knobs, while preserving environment variables as the highest-precedence override so nothing breaks for existing users or CI.

## Decisions (locked)

| Decision | Choice | Rationale |
|---|---|---|
| Format | **JSON** | stdlib reads *and* writes it (honors the stdlib-only rule); TOML can't be written by stdlib. |
| Scope | **Consolidate existing knobs only** | YAGNI — `db_path`, `judge_command`, `snapshot_interval`. No new config concepts. |
| Location | **`~/.claude/manifold.json`** (fixed) | Lives next to the *data* (`manifold.db`), not the *code* (skill dir) — survives skill re-copies/updates, stays out of any git tree. Fixed path because the DB path is itself a config value. |
| Precedence | **env var > config file > built-in default** | Env always wins; current users and CI unaffected. |
| Creation | **Explicit `manifold config init`** | Predictable; no silent writes to the user's home directory, no cross-process write races on first run. |
| Command surface | **`path` / `show` / `init` only** | Hand-edit the JSON for changes; `get`/`set` deferred. |
| Secrets | **None** | manifold has no auth today; when it lands, secrets go via env / a `chmod 600` file, never this plaintext config. |

## The config file

- **Path:** `~/.claude/manifold.json`. Overridable via `$MANIFOLD_CONFIG` (an absolute path). The override is also what makes tests hermetic.
- **Format:** JSON object. All three keys optional:

```json
{
  "db_path": "~/.claude/manifold.db",
  "judge_command": "claude --print",
  "snapshot_interval": 3600
}
```

- **Robustness (must-haves):**
  - **Absent file** → empty config; all defaults apply. Behavior is byte-for-byte identical to today.
  - **Malformed JSON** → emit a single warning to stderr (`manifold: ignoring malformed config at <path>: <error>`) and fall back to defaults/env. **Never raise / never crash** because a config file is broken.
  - **`~`** in `db_path` is expanded (`os.path.expanduser`). `judge_command` is **not** expanded by manifold — it is run through the shell (`subprocess.run(..., shell=True)`), which performs its own `~`/`$VAR` expansion at execution time; expanding here too would double-expand. `snapshot_interval` accepts an int or a numeric string, falling back to `3600` on a non-numeric value.
  - **Unknown keys** are ignored (forward-compatible), but `config show` lists them under an "unrecognized" note so typos are visible.
  - The file is **read at most once per process** and cached.

## Resolution semantics (per key)

The principle: **most specific / most runtime-proximate source wins.**

| Setting | 1st (wins) | 2nd | 3rd | Default |
|---|---|---|---|---|
| `db_path` | `$MANIFOLD_DB` | config file `db_path` | — | `~/.claude/manifold.db` |
| `judge_command` | `$MANIFOLD_JUDGE_CMD` | per-project `spec_config.judge_command` | config file `judge_command` | unset (→ `judge_required`) |
| `snapshot_interval` | `$MANIFOLD_SNAPSHOT_INTERVAL` | config file `snapshot_interval` | — | `3600` |

Note the judge ordering: a **per-project** setting (stored in the DB's `spec_config`) is more specific than the **machine-global** config file, so it sits *above* the file but *below* the per-run env var. This extends the existing two-tier resolution in `validate._resolve_judge_command` with a third tier.

## CLI surface

A new `config` subcommand group in `manifold/cli.py`:

- **`manifold config path`**
  Prints the resolved config file path (honoring `$MANIFOLD_CONFIG`) and whether it currently exists. Exit 0.

- **`manifold config show`**
  Prints each effective setting, its resolved value, and **its source** (`env` / `file` / `default`). This is the "why is my DB pointing there?" diagnostic. It reports the *machine-global* resolution; for `judge_command` it notes that an individual project may still override it via its `spec_config.judge_command` (that per-project tier is resolved at validation time, not here). Also lists any unrecognized keys found in the file. Exit 0.

  Example:
  ```
  db_path           /Users/me/.claude/manifold.db        (default)
  judge_command     claude --print                       (file)
  snapshot_interval 3600                                 (default)
  config path       /Users/me/.claude/manifold.json      (exists)
  ```

- **`manifold config init [--force]`**
  Writes a `manifold.json` at the resolved path, **seeded from the current effective values** (so whatever you have in env right now becomes the file's starting point). Pretty-printed, stable key order. **Refuses to overwrite** an existing file unless `--force`; without it, prints `config already exists at <path> (use --force to overwrite)` and exits non-zero. Creates `~/.claude/` if missing.

## Code changes (file-by-file)

- **`manifold/config.py`**
  - Add `config_path() -> Path` (resolve `$MANIFOLD_CONFIG` else `~/.claude/manifold.json`).
  - Add `load_config() -> dict` — cached read, fail-soft on missing/malformed, returns `{}` on any problem.
  - Update `db_path()` and `snapshot_interval_seconds()` to consult the file as the middle tier.
  - Add a resolver that returns each setting's `(value, source)` for `config show`.
  - Update the module docstring — it no longer promises "No file I/O."

- **`manifold/validate.py`**
  - `_resolve_judge_command(spec_config, env)` gains the config-file value as the 3rd fallback (after env and per-project `spec_config.judge_command`).

- **`manifold/cli.py`**
  - Register the `config` subparser with `path` / `show` / `init` (+ `--force` on `init`).

- **`tests/test_config.py`** — extend (see Testing).

- **`USER.md`** — new "Configuration" section documenting the file, precedence, and the three commands. Brief note in **`ARCHITECTURE.md`** that config resolution is env > file > default.

## Testing (enumerated)

All tests point `$MANIFOLD_CONFIG` at a temp file for hermeticity.

1. **Absent file** → `db_path()` returns the default; `load_config()` returns `{}`.
2. **File sets `db_path`** → `db_path()` returns it (with `~` expanded).
3. **Env beats file** → with both `$MANIFOLD_DB` and a file `db_path`, env wins.
4. **File beats default** → file `snapshot_interval` used when env unset.
5. **Malformed JSON** → no exception; defaults returned; one stderr warning.
6. **Unknown key** → ignored by resolvers; surfaced by `config show`.
7. **Judge precedence** → env > `spec_config.judge_command` > file > unset (4 cases).
8. **`config init`** writes a file seeded from effective values; round-trips through `load_config()`.
9. **`config init` clobber-refusal** → second run without `--force` exits non-zero and leaves the file unchanged; `--force` overwrites.
10. **`config show` source attribution** → reports `env` / `file` / `default` correctly for a mixed setup.

## Back-compat & non-goals

- **Zero breakage:** purely additive. Env-var users and no-config users get behavior identical to today. No DB schema change, no migration step.
- **Out of scope (deferred):** named DB profiles; `config get` / `config set`; secrets/passwords + auth; folding `$MANIFOLD_PIDFILE` and `$MANIFOLD_STRICT_CONCURRENCY` into the file (they stay env-only — per-invocation server flags, not machine config); TOML; auto-creation on first run.
