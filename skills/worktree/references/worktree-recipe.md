# Worktree recipe & gotchas (manual fallback + reference)

The `/worktree` skill automates all of this — `/worktree add <branch> [base]` creates the worktree and wires brain/memory/`.claude` + artifacts + serena + per-stack env; `/worktree check` validates or repairs one; `/worktree remove` archives; `/worktree revive` restores; `/worktree reap` finalizes. The mechanics live in `helpers.sh` (`wt_wire`, `wt_check`, `wt_archive`, `wt_revive`, `wt_reap`). This file is the **manual fallback** and the home for the **gotchas** that aren't obvious from the code.

The worktree-first **rules** (always work in a worktree; layout: primary `~/Documents/projects/<repo>/`, worktrees nested in-repo at `<repo>/.worktrees/<branch>/`, shared content `~/Documents/projects/artifacts/<repo>/`; `<TICKET-ID>[-<slug>]` or `<kebab>` branch names; **always confirm the base branch first**) live in `~/.claude/CLAUDE.md` → "Worktree-First Workflow".

## Manual create (when the skill isn't available)

Substitute `<repo>`, `<branch>`, `<base>`:

```bash
# Existing branch (checkout into a worktree):
git -C ~/Documents/projects/<repo> worktree add \
    ~/Documents/projects/<repo>/.worktrees/<branch> <branch>

# New branch from a base (confirm <base> with the user first):
git -C ~/Documents/projects/<repo> worktree add -b <branch> \
    ~/Documents/projects/<repo>/.worktrees/<branch> <base>
```

## Wiring (what `wt_wire` does — replicate manually if needed)

```bash
WT=~/Documents/projects/<repo>/.worktrees/<branch>
MAIN=~/Documents/projects/<repo>
CANON=~/.claude/projects/-home-piyush-Documents-projects-<repo>   # main clone's project-key dir

# 1. Project pair (scaffold empty if absent) — gitignored; native walk-up loads them, no @import:
[ -f "$MAIN/CLAUDE.md" ]       || : > "$MAIN/CLAUDE.md"
[ -f "$MAIN/CLAUDE.local.md" ] || : > "$MAIN/CLAUDE.local.md"
: > "$WT/CLAUDE.local.md"   # empty work-unit layer (or seeded from --ticket/--purpose/--handoff)

# 2. Worktree's own claude memory bucket (pure-add; harvested up to parent at reap — NOT a symlink to main):
KEY=$(printf '%s' "$WT" | sed 's#[/._]#-#g')   # CC sanitizes '/', '.', and '_' → '-'
mkdir -p ~/.claude/projects/"$KEY"/memory        # worktree's OWN empty bucket; curation merges it up later

# 3. .claude as a REAL dir copied from main — NEVER a symlink (see Gotchas → sandbox).
[ -L "$WT/.claude" ] && rm "$WT/.claude"
mkdir -p "$WT/.claude"
cp -a "$MAIN/.claude/." "$WT/.claude/"
# wt_wire also ensures BUILD-tier sandbox settings in the worktree copy:
#   settings.local.json gets sandbox.enabled=true + autoAllowBashIfSandboxed=true

# 4. Artifacts — linked into artifacts/ (not .gitignored/). ABSOLUTE link targets on purpose:
#    portable (BSD/macOS ln has no -r) and they survive `git worktree move` on archive/revive.
mkdir -p "$WT/artifacts"
for d in ~/Documents/projects/artifacts/<repo>/*/; do
    ln -sfn "${d%/}" "$WT/artifacts/$(basename "${d%/}")"
done
# artifacts/ is excluded via the repo's common-dir info/exclude (/artifacts/ entry — repo-wide,
# idempotent). If the repo already tracks an 'artifacts' path, wt_wire falls back to .gitignored/.

# 5. Serena pre-stage (see §Serena pre-stage below)
wt_serena_prestage "$WT" "$MAIN"
```

Verify in a fresh worktree session: native walk-up — `/memory` shows the worktree's `CLAUDE.local.md` plus `<repo>/CLAUDE.md` loaded via parent walk-up (no @import line).

## Serena pre-stage

Each worktree is its own serena project, keyed by the worktree's **basename** (= branch name).
One-worktree-per-branch is the invariant — two worktrees on the same branch would share the same
serena project key and stomp each other's memories. Slashed branch names (e.g. `feature/foo`)
**collapse to the last segment** (`foo`) for the project folder name, because `basename` drops
the path prefix.

On `wt_add` / `wt_wire`, `wt_serena_prestage` runs automatically:

1. If `~/.serena/projects/<branch-name>/` **does not exist** (fresh creation):
   - Creates the dir.
   - Copies `project.yml` from the main clone's serena project (if present) and patches
     `project_name` to the branch name.
   - `memories/` is **not created** — the worktree's serena memories start empty. Parent knowledge
     comes from `~/.serena/memories/global/` (shared tier) + live LSP index. No copy → no drift →
     reap harvest is pure-add.
2. If the project dir **already exists** (revive case): skips creation entirely and re-registers
   as-is — the worktree's own memories are preserved exactly as left before archiving (they were
   never copied from main in the first place).
3. Always registers the worktree's absolute path in `~/.serena/serena_config.yml` under `projects:`
   (idempotent — no duplicate insertion).

`wt_check` reports a `serena: OK` line when the absolute path is found in `serena_config.yml`,
or `serena: NA` when it is absent (not a FAIL — serena is optional).

On archive (`wt_archive`): de-registered from `serena_config.yml` but project folder kept.
On revive (`wt_revive`): re-registered; memories preserved (no copy).
On reap (`wt_reap`): de-registered AND project folder purged (`wt_serena_deregister --purge`).

## Artifacts (`artifacts/`)

Wired artifacts are linked into `<wt>/artifacts/` (not `.gitignored/`). The destination directory
is excluded via the repo's **common-dir** `info/exclude` (entry `/artifacts/`), which means:

- The exclusion is **repo-wide** — it covers all worktrees and the main clone of that repo without
  any per-worktree setup.
- It is **not committed** — safe to use even if other repos track a real `artifacts/` path.
- `wt_wire` adds the entry idempotently (checks for `*/artifacts/*` before appending).

Collision probe: if the repo already tracks a path named `artifacts` (`git ls-files --error-unmatch
artifacts` exits 0), `wt_wire` emits a warning and links into `.gitignored/` instead. The
`.gitignored/` path must then be excluded manually (see Gotchas below).

## Archive / Revive

`wt_archive` and `wt_revive` implement reversible suspension of a worktree using native git mechanics.

### Archive (`wt_archive <main> <wt>`)
- Moves the worktree to `<repo>/.worktrees/_archive/<branch>` via `git worktree move` (git tracks
  the new location; uncommitted changes are preserved — the directory moves intact).
- Locks the archive path: `git worktree lock <path> --reason "archived <date>"`. This prevents
  `git worktree prune` from silently removing it.
- De-registers the worktree from `serena_config.yml` (keeps the project folder for revive).
- Appends a row to `<repo>/.worktrees/_archive/index.tsv` (columns: branch / orig_path / date /
  ticket). Header is written on first use.

`index.tsv` lives under `.worktrees/` (gitignored) — it is **not clone-durable**. The source of
truth is `git worktree list` plus the presence of the locked directory.

### Revive (`wt_revive <main> <branch>`)
- Unlocks the archive path, then moves it back to `<repo>/.worktrees/<branch>` via `git worktree move`.
- Re-registers with serena (calls `wt_serena_prestage`); because the project dir already exists,
  it is registered as-is — the worktree's own serena memories persist through the archive
  (they were never copied from main, so nothing to restore).
- Removes the branch row from `index.tsv`.
- No re-wiring needed — the `.claude` dir, own memory bucket, and artifacts links are already inside
  the moved directory.

## Reap

`wt_reap <main> <wt> [--force]` finalizes a done worktree. Use after a branch is merged.

### Gates (evaluated in order)
| Gate | Behavior without `--force` | With `--force` |
|---|---|---|
| Merge | Branch must be in `git branch --merged <trunk>` | Skipped (warn printed) |
| Dirty | `git status --porcelain` must be empty | Skipped (warn printed) |
| Confirm | Interactive `[y/N]` prompt | Skipped (also skipped if `WT_ASSUME_YES=1`) |

`<trunk>` = the main clone's currently checked-out branch — detected via `git rev-parse --abbrev-ref
HEAD` on the main clone, not hardcoded. Works for `master`, `main`, or any custom trunk name.

On merge-gate failure, `git diff --stat <trunk>...<branch>` is printed before refusing.

### Sequence (after gates pass)
1. `wt_reap_promote` writes `<wt>/.reap-manifest.md`:
   - YAML frontmatter: worktree / branch / repo / ticket / date.
   - `candidates:` list — one entry per harvested memory from **both** stores:
     serena (`~/.serena/projects/<branch>/memories/`) and claude
     (`~/.claude/projects/<wt-key>/memory/`). Each entry: `id / store / source / type /
     body / collision / proposed: {}`. `collision` is the path of a same-named file in
     the parent store if one exists, or `none`. `proposed` starts empty — the
     `memory-curator` agent fills it. There is no `base` field.
   - Ticket is read from `WT_TICKET` env var, or parsed from `CLAUDE.local.md`
     (`Ticket:` line) as a fallback.
   - Prints `"reap: promotion pending (memory-curator not yet built)"`. **No memory is
     auto-merged** — the manifest is the input contract for the future `memory-curator` agent.
2. Manifest is copied to `<repo>/.worktrees/_reaped/<branch>.reap-manifest.md` (preserves it
   outside the worktree before deletion).
3. `wt_remove` deletes the worktree dir and per-wt key dir.
4. `wt_serena_deregister --purge` removes the serena config entry AND deletes the serena project
   folder (unlike archive, which keeps the folder).

Branch deletion is left to `commit-commands:clean_gone`.

## Gotchas

- **`.claude` MUST be a real directory, NOT a symlink.** A symlinked `.claude` → main makes the bwrap sandbox fail to initialize (`bwrap: Can't create file at <wt>/.claude: Is a directory`) → *all* Bash in the worktree is blocked. `wt_wire` copies main's `.claude` contents into a real dir; `wt_check` flags a symlink as FAIL. (Root-caused 2026-06-01; full write-up in `~/Documents/notes/journal/dev-machine-problems.md`.) The shared brain/memory do **not** ride `.claude` — they use `CLAUDE.local.md` + the worktree's own memory bucket (see §Wiring step 2).

- **Slashes in branch names are fine** (e.g. `hotfix/x`). Artifacts links use **absolute** targets, so nesting depth is irrelevant — no hardcoded `../../../../`, no no-slashes constraint. Proven by the live `hotfix/session-processing-exif` worktree. *(The old "no slashes" rule and the old relative `ln -srn` links are both retired — BSD/macOS ln has no `-r`, and relative links broke on archive moves.)*
  Note: slashed names collapse to the last segment as the serena project key (`basename` behavior).

- **`.worktrees/` is ignored globally** (`~/.gitignore_global`), so a nested worktree never dirties the main clone's `git status`. No per-clone or per-branch setup needed for the worktree dir itself.

- **`artifacts/` excluded via common-dir `info/exclude`.** `wt_wire` appends `/artifacts/` to
  `$(git rev-parse --git-common-dir)/info/exclude` (idempotent). This covers all worktrees of that
  repo — no per-worktree setup needed. If the repo tracks a real `artifacts` path, `wt_wire` falls
  back to `.gitignored/` (see §Artifacts above); in that case exclude `.gitignored/` manually:
  ```bash
  printf '/.gitignored\n' >> "$(git -C <repo> rev-parse --git-common-dir)/info/exclude"
  ```

- **New-branch-off-remote tracking trap.** `worktree add -b <branch> <path> origin/main` auto-sets the new branch to track `origin/main`. Correct it on first push with `git push -u origin <branch>` so it tracks its own remote branch (and a bare `git pull` doesn't pull main).

- **Empty `artifacts/`.** On a clone where `artifacts/<repo>/` is empty (fresh remote), the symlink loop is a no-op — skip it. rsync artifacts over only if a worktree needs the vendor SDKs / work-order docs.

- **Per-worktree `.venv`.** `.venv` is gitignored and does NOT carry into a new worktree, so linters / type-checkers / imports / tests fail until one exists. After creating a worktree: `uv venv && uv pip install -e ".[dev]"` (uv hardlinks from cache, ~1s). Don't share/symlink `.venv` across worktrees — it breaks per-branch isolation.

- **Docker-created dirs block `git worktree remove` (issue #1).** Airflow and other Docker
  services run without `--user`, so `dashboard-data/`, `logs/`, and `dags/` end up owned by
  `nobody` or `root` inside the worktree. `git worktree remove --force` cannot delete them.
  Use `wt_remove <main> <wt>` instead — it detects non-user-owned paths and prints the exact
  `sudo rm -rf` + `git worktree prune` recovery commands. True root fix (out of skill scope):
  add `user: "${UID}:${GID}"` to your project's docker-compose services.

- **Dead NAS mount bricks the bwrap sandbox (issue #5 — Linux only).** A hard-mounted NAS share
  (e.g. `/mnt/shared-data`) that goes offline causes `stat` to hang. bwrap then fails to
  bind-mount it and ALL sandboxed Bash dies with `remount ... No such device`. Run
  `wt_preflight_mounts` before any sandbox-dependent worktree ops — it probes each `/mnt/*`
  with a 3-second timeout and reports which shares are stale. On a stale-mount warning:
  either `sudo umount -l <path>` (lazy unmount) to clear the dead share, or use
  `dangerouslyDisableSandbox: true` for git commands in that session.
  On macOS `wt_preflight_mounts` no-ops cleanly (seatbelt sandbox, no bwrap, no `/proc/mounts`).
  (Cross-ref: `workflow-remote-vs-onprem-data` memory — "a dead NAS mount wedges bwrap".)

## Cleanup

After a PR merges: use `/worktree reap <wt>` — it gate-checks (merge + dirty + confirm), writes a
promotion manifest to `_reaped/<branch>.reap-manifest.md`, removes the worktree dir, and purges its
serena project. Then `commit-commands:clean_gone` handles branch deletion. If Docker-owned dirs
block removal, `wt_remove` prints the exact `sudo rm -rf` + `prune` recovery — see Gotchas above.

For temporary suspension (branch parked, not done): use `/worktree remove <wt>` to archive, then
`/worktree revive <branch>` to restore.

## Editor integration

- **VS Code** 1.103+: Command Palette → `Git: Create Worktree`, `Git: Open Worktree in New Window`, `Git: Delete Worktree`.
- **Neovim**: `git-worktree.nvim` + Telescope (config at `~/.config/nvim/lua/plugins/worktree.lua`).
