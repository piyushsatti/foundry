# Worktree recipe & gotchas (manual fallback + reference)

The `/worktree` skill automates all of this — `/worktree add <branch> [base]` creates the worktree and wires brain/memory/`.claude` + per-stack env; `/worktree check` validates or repairs one; `/worktree remove` archives; `/worktree revive` restores; `/worktree reap` finalizes. The mechanics live in `helpers.sh` (`wt_wire`, `wt_check`, `wt_archive`, `wt_revive`, `wt_reap`). This file is the **manual fallback** and the home for the **gotchas** that aren't obvious from the code.

The worktree-first **rules** (always work in a worktree; `<TICKET-ID>[-<slug>]` or `<kebab>` branch names; **always confirm the base branch first**) live in `~/.claude/CLAUDE.md` → "Worktree-First Workflow".

## Layout

Everything for one project lives under a single container dir. The repo's basename equals the
project name; worktrees sit **beside** the repo, never inside it.

```
~/Studio/Developer/projects/<project>/
  <project>/            the git repo
  worktrees/<branch>/   live worktrees
  worktrees/_archive/   archived (locked) worktrees + index.tsv
  artifacts/            shared store: repo and every worktree reach it by relative path
  history/reaped/       reap manifests (residue of finished worktrees)
  research/ notes/ data/
```

| Path | From the repo | From a worktree |
|---|---|---|
| artifacts store | `../artifacts` | `../../artifacts` |
| project container | `..` | `../..` |

A slashed branch (`hotfix/x`) nests one level deeper, so its relative depth gains one `../`.
Nothing depends on that depth being fixed — no path is ever hardcoded into the worktree.

**Why beside, not nested:** a worktree outside the repo cannot dirty the repo's `git status`, so no
`.gitignore` or `info/exclude` entry is needed for it. And because `artifacts/` is a sibling of both
the repo and `worktrees/`, a plain relative path reaches it from either — which is why there are
**no artifacts symlinks any more**.

## Manual create (when the skill isn't available)

Substitute `<project>`, `<branch>`, `<base>`. `P` is the project container dir.

```bash
P=~/Studio/Developer/projects/<project>

git -C "$P/<project>" worktree add "$P/worktrees/<branch>" <branch>
```

For a new branch off a base, confirm `<base>` with the user first, then:

```bash
P=~/Studio/Developer/projects/<project>

git -C "$P/<project>" worktree add -b <branch> "$P/worktrees/<branch>" <base>
```

## Wiring (what `wt_wire` does — replicate manually if needed)

```bash
P=~/Studio/Developer/projects/<project>
WT="$P/worktrees/<branch>"
MAIN="$P/<project>"
CANON=~/.claude/projects/$(printf '%s' "$MAIN" | sed 's#[/._]#-#g')

# 1. Project pair (scaffold empty if absent) — gitignored:
[ -f "$MAIN/CLAUDE.md" ]       || : > "$MAIN/CLAUDE.md"
[ -f "$MAIN/CLAUDE.local.md" ] || : > "$MAIN/CLAUDE.local.md"
: > "$WT/CLAUDE.local.md"   # empty work-unit layer (or seeded from --ticket/--purpose/--handoff)

# 2. Worktree's own claude memory bucket (pure-add; harvested up to parent at reap):
KEY=$(printf '%s' "$WT" | sed 's#[/._]#-#g')   # CC sanitizes '/', '.', and '_' to '-'
mkdir -p ~/.claude/projects/"$KEY"/memory

# 3. .claude as a REAL dir copied from main — NEVER a symlink (see Gotchas):
[ -L "$WT/.claude" ] && rm "$WT/.claude"
mkdir -p "$WT/.claude"
cp -a "$MAIN/.claude/." "$WT/.claude/"

# 4. Artifacts — nothing to do. "$P/artifacts" is already reachable as ../../artifacts.
```

`CANON` is the main clone's project-key dir. Step 3 also gets BUILD-tier sandbox settings from
`wt_wire`: `settings.local.json` gains `sandbox.enabled=true` and `autoAllowBashIfSandboxed=true`.

## Artifacts (`../../artifacts`)

The store lives at `<project>/artifacts`, one level above both the repo and `worktrees/`.

| Concern | How it is handled |
|---|---|
| Reaching it from a worktree | Plain relative path `../../artifacts`. No links, no config. |
| Keeping it out of `git status` | Nothing to keep out — it is outside the worktree entirely. |
| `git worktree move` on archive/revive | Archive stays inside `<project>/`, so the relative path still resolves. |
| Non-default store location | `wt_wire`'s 4th argument overrides the derived path. |

`wt_wire` derives the store as `$(dirname "$MAIN")/artifacts` and only **reports** whether it
exists. `wt_check` walks up from the worktree looking for that same directory and reports
`artifacts: OK` when the relative path resolves, `FAIL` when the store exists but the worktree sits
outside the project tree, and `NA` when there is no store at all.

*(Retired: the symlink farm under `<wt>/artifacts/`, the `/artifacts/` entry appended to the
common-dir `info/exclude`, and the `.gitignored/` collision fallback. The sibling layout makes all
three unnecessary — there is nothing inside the worktree to link or to exclude.)*

## Archive / Revive

`wt_archive` and `wt_revive` implement reversible suspension of a worktree using native git mechanics.

### Archive (`wt_archive <main> <wt>`)
- Moves the worktree to `<project>/worktrees/_archive/<branch>` via `git worktree move` (git tracks
  the new location; uncommitted changes are preserved — the directory moves intact).
- Locks the archive path: `git worktree lock <path> --reason "archived <date>"`. This prevents
  `git worktree prune` from silently removing it.
- Appends a row to `<project>/worktrees/_archive/index.tsv` (columns: branch / orig_path / date /
  ticket). Header is written on first use.

`_archive` sits **under the worktrees root**, not beside it, so every git-registered worktree — live
or parked — stays in one subtree and `<project>/` keeps only the dirs the layout defines.

`index.tsv` is **not clone-durable**. The source of truth is `git worktree list` plus the presence
of the locked directory.

### Revive (`wt_revive <main> <branch>`)
- Unlocks the archive path, then moves it back to `<project>/worktrees/<branch>` via `git worktree move`.
- Removes the branch row from `index.tsv`.
- No re-wiring needed — the `.claude` dir and own memory bucket are already inside the moved
  directory, and artifacts were never wired in the first place.

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
   - `candidates:` list — one entry per harvested memory from the worktree's claude bucket
     (`~/.claude/projects/<wt-key>/memory/`). Each entry: `id / store / source / type / body /
     collision / proposed: {}`. `store` is always `claude`. `collision` is the path of a same-named
     file in the parent store if one exists, or `none`. `proposed` starts empty — the
     `memory-curator` agent fills it. There is no `base` field.
   - Ticket is read from `WT_TICKET`, or parsed from `CLAUDE.local.md` (`Ticket:` line) as a fallback.
   - Prints `"reap: promotion pending (memory-curator not yet built)"`. **No memory is
     auto-merged** — the manifest is the input contract for the future `memory-curator` agent.
2. Manifest is copied to `<project>/history/reaped/<branch>.reap-manifest.md` — reaped manifests are
   residue of finished work, so they land in `history/`, not under the live `worktrees/` root.
3. `wt_remove` deletes the worktree dir and per-wt key dir.

Branch deletion is left to `commit-commands:clean_gone`.

## Gotchas

- **`.claude` MUST be a real directory, NOT a symlink.** A symlinked `.claude` → main makes the bwrap sandbox fail to initialize (`bwrap: Can't create file at <wt>/.claude: Is a directory`) → *all* Bash in the worktree is blocked. `wt_wire` copies main's `.claude` contents into a real dir; `wt_check` flags a symlink as FAIL. (Root-caused 2026-06-01.) The shared brain/memory do **not** ride `.claude` — they use `CLAUDE.local.md` + the worktree's own memory bucket (see §Wiring step 2).

- **Repo-level `CLAUDE.md` is NOT loaded inside a worktree (open design gap).** Native CLAUDE.md walk-up climbs the worktree's ancestors: `<project>/worktrees/<branch>` → `<project>/worktrees` → `<project>` → and up. The repo dir `<project>/<project>/` is **not** on that path, so `<repo>/CLAUDE.md` never loads. Walk-up does still reach `<project>/CLAUDE.md` and `~/.claude/CLAUDE.md`. The nested layout used to make this work for free; the sibling layout breaks it. `wt_check`'s `bridge:` line still FAILs on an `@import`, so the two available fixes — put project context at `<project>/CLAUDE.md`, or re-introduce an `@import` bridge and relax `bridge:` — are a **pending design call**, not something `wt_wire` decides.

- **Slashes in branch names are fine** (e.g. `hotfix/x`). Nothing stores a path relative to the worktree, so the extra nesting level is irrelevant. *(The old "no slashes" rule died with the relative `ln -srn` artifact links.)*

- **Worktrees never dirty the repo.** They live outside it, so no `.gitignore` or `info/exclude` entry is needed for the worktree dir. *(The old global `/.worktrees/` ignore only still matters for repos not yet migrated off the nested layout.)*

- **New-branch-off-remote tracking trap.** `worktree add -b <branch> <path> origin/main` auto-sets the new branch to track `origin/main`. Correct it on first push with `git push -u origin <branch>` so it tracks its own remote branch (and a bare `git pull` doesn't pull main).

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
promotion manifest to `<project>/history/reaped/<branch>.reap-manifest.md`, and removes the worktree
dir. Then `commit-commands:clean_gone` handles branch deletion. If Docker-owned dirs block removal,
`wt_remove` prints the exact `sudo rm -rf` + `prune` recovery — see Gotchas above.

For temporary suspension (branch parked, not done): use `/worktree remove <wt>` to archive, then
`/worktree revive <branch>` to restore.

## Editor integration

- **VS Code** 1.103+: Command Palette → `Git: Create Worktree`, `Git: Open Worktree in New Window`, `Git: Delete Worktree`.
- **Neovim**: `git-worktree.nvim` + Telescope (config at `~/.config/nvim/lua/plugins/worktree.lua`).
