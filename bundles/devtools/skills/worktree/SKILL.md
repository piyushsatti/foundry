---
name: worktree
description: Use when the user says "/worktree", "new worktree", "add a worktree", "check a worktree", "remove/archive a worktree", "revive a worktree", "reap a worktree", or asks for worktree-native setup in any repo.
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../../../../skills/manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| — | — | No manifest dependencies |

<!-- foundry:dependencies:end -->

# /worktree

Source the helpers, then dispatch by the user's intent. ALWAYS source them from **this skill's
base directory** (given as "Base directory for this skill" when the skill is invoked — never a
hardcoded install path; the skill may live in `~/.claude/skills/`, a repo checkout, or elsewhere):

```
source <skill-base-dir>/helpers.sh
```

Works in both bash (3.2+) and zsh, on Linux and macOS.

**Recipe & gotchas:** manual fallback commands + the non-obvious traps (real-dir `.claude`, per-worktree `.venv`, artifacts exclude, serena pre-stage, new-branch-off-remote tracking, editor integration) live in `references/worktree-recipe.md`.

**Confirm-gates (never skip):** (1) the **base branch** — never auto-pick; (2) any **overwrite** of an existing file / differing config — show it and ask; (3) **archive confirm** before `remove`; (4) **reap confirm** (merge-gate + dirty-gate + explicit y/N).

## Modes
- `add [--ticket X] [--purpose Y] [--handoff Z] <branch> [base]` → §Add
- `remove <wt>`              → §Remove (archive)
- `revive <branch>`          → §Revive
- `reap <wt> [--force]`      → §Reap
- `check [name|all]`         → §Check
- `init`                     → §Init
- (bare `/worktree`)         → §Analyze

## Add
1. Resolve `MAIN=$(git -C . worktree list --porcelain | awk '/^worktree /{print $2; exit}')`.
2. If `init` not yet done (no `<repo>/CLAUDE.md` project pair), run §Init first.
3. **Confirm base branch** with the user (gate 1). Then create, wire, and set up env in one call:
   ```
   wt_add [--ticket X] [--purpose Y] [--handoff Z] "$MAIN" <branch> <base>
   ```
   (new branch) or append `0` as a fourth positional arg to check out an existing branch.
   Optional flags seed the worktree's `CLAUDE.local.md` with a context template (ticket / purpose /
   handoff / created date). Omitting all flags writes an empty stub. This is the only correct way
   to create a worktree — never call `git worktree add` directly, as it bypasses wiring and leaves
   the worktree memory-blind.
4. `wt_add` calls `wt_wire`, which runs: brain/memory/.claude wiring → artifacts linking (into
   `artifacts/`) → `wt_serena_prestage` (registers the worktree as its own serena project; serena
   memories start empty — never copied from main; parent knowledge comes from `~/.serena/memories/global/` + live LSP). Then `wt_setup_env` runs automatically.
   **`auto`-weight stacks (python, node) always run unconditionally — never defer them, even in fork
   mode.** `propose` stacks (ros2) print the command for user confirmation. `none` stacks print a note.
5. Report `wt_add` output. Any `FAIL` line from the self-check means wiring is broken — re-run
   `wt_wire <wt> "$MAIN"` and confirm the result.

## Remove (archive)
`remove` archives a worktree so it can be revived later. It does NOT permanently delete anything.

1. **Confirm** with the user before archiving (gate 3).
2. Call `wt_archive "$MAIN" "$WT"`. This:
   - Moves the worktree via `git worktree move` to `<repo>/.worktrees/_archive/<branch>` (uncommitted
     changes are preserved — the directory moves intact).
   - Locks the archive path: `git worktree lock` with reason `"archived <date>"`.
   - De-registers the worktree from serena (`serena_config.yml`) but keeps the serena project folder
     (so memories survive for revive).
   - Appends a row to `_archive/index.tsv` (columns: branch / orig_path / date / ticket).
3. After archiving, the branch still exists and the worktree dir is still registered with git — it is
   simply locked at the archive path. Use `revive` to restore it.

Note: `_archive/index.tsv` lives under `.worktrees/` which is gitignored — it is not clone-durable.
`git worktree list` and the locked directory are the authoritative sources of truth.

## Revive
Restore an archived worktree to active development.

1. Call `wt_revive "$MAIN" "<branch>"`. This:
   - Unlocks the archive path, then moves the worktree via `git worktree move` back to
     `<repo>/.worktrees/<branch>`.
   - Re-registers the worktree in serena (calls `wt_serena_prestage`). Because the serena project
     folder already exists, it is registered as-is — serena memories stay the worktree's own
     (never copied from main; the folder simply persisted through the archive).
   - Removes the branch row from `_archive/index.tsv`.
2. The worktree is fully active again — no re-wiring needed (the `.claude` dir, own memory bucket, and
   artifacts links are already in place inside the moved directory).

## Reap
`reap` finalizes a **done** worktree: gates it, writes a promotion manifest, and permanently
deletes the worktree and its serena project. Use when the branch is merged and the work is complete.

Gates (in order — all must pass, or use `--force` to override each):
1. **Merge gate**: branch must appear in `git branch --merged <trunk>` where `<trunk>` is the main
   clone's currently checked-out branch (detected, not hardcoded — works for `master`, `main`, etc.).
   On failure, shows `git diff --stat <trunk>...<branch>` and refuses.
2. **Dirty gate**: worktree must have no uncommitted changes (`git status --porcelain` is empty).
   On failure, prints a message and refuses.
3. **Confirm prompt**: interactive `[y/N]` asking "ticket merged + work finalized?". Skip with
   `--force` or `WT_ASSUME_YES=1`.

Then:
- Calls `wt_reap_promote`: writes `<wt>/.reap-manifest.md` with YAML frontmatter (worktree / branch /
  repo / ticket / date) followed by a `candidates:` list — one entry per harvested memory from
  **both** stores (serena `~/.serena/projects/<branch>/memories/` and claude
  `~/.claude/projects/<wt-key>/memory/`). Each entry carries `id / store / source / type / body /
  collision / proposed: {}` (curator fills `proposed`; no `base` field). Prints
  `"reap: promotion pending (memory-curator not yet built)"`. **No memory is auto-merged** — the
  manifest is the input contract for the future `memory-curator` agent.
- Copies the manifest to `<repo>/.worktrees/_reaped/<branch>.reap-manifest.md` (preserved outside the
  worktree before deletion).
- Calls `wt_remove` (deletes the worktree dir + per-wt key dir).
- Calls `wt_serena_deregister --purge` (removes the wt from serena_config.yml AND deletes the serena
  project folder — unlike archive which keeps the folder).

Branch deletion is left to `commit-commands:clean_gone`.

Call: `wt_reap "$MAIN" "$WT" [--force]`

## Check
For each target worktree (one, or all from `git worktree list`):
`wt_check <wt> "$(canonical_dir <wt>)"` and print the lines.
Lines reported: `brain` / `bridge` / `nest` / `memory` / `settings` / `artifacts` / `branch` /
`remote` / `env` / `serena` (new — whether the worktree's absolute path is registered in
`~/.serena/serena_config.yml`).
If any `FAIL`, offer to repair: re-run `wt_wire` for that worktree (gate 2 applies to any clobber).

## Init
Ensure the project is worktree-native:
- Project pair present: `<repo>/CLAUDE.md` + `<repo>/CLAUDE.local.md` (both gitignored real files; `wt_wire` scaffolds empty stubs if absent). Native CLAUDE.md walk-up from `<repo>/.worktrees/<branch>/` loads `<repo>/CLAUDE.md` → `~/Documents/projects/CLAUDE.md` → `~/.claude/CLAUDE.md` automatically — no @import bridge needed.
- Global ignores present in `~/.gitignore_global`: `**/CLAUDE.md`, `**/CLAUDE.local.md`, `.serena/`, `.worktrees/`, `.remember/`. (Trailing-slash / symlink-match restriction is RETIRED — these are real in-tree files/dirs, not symlinks.)
- Report what's missing; create only the safe, confirmed pieces.

## Analyze (bare /worktree)
Detect context and PROPOSE one mode, then confirm:
- cwd is a worktree → suggest `check`.
- cwd is the main clone, project not wired → suggest `init`.
- otherwise → ask whether to `add`.
Never act before the user confirms the proposed mode.
