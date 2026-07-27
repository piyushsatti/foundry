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

**Layout:** worktrees live BESIDE the repo at `<project>/worktrees/<branch>`, with `<project>/artifacts` shared by the repo and every worktree via plain relative path (`../../artifacts`), archives at `<project>/worktrees/_archive/<branch>`, and reap manifests at `<project>/history/reaped/`.

**Recipe & gotchas:** manual fallback commands + the non-obvious traps (real-dir `.claude`, repo-CLAUDE.md walk-up gap, per-worktree `.venv`, new-branch-off-remote tracking, editor integration) live in `references/worktree-recipe.md`.

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
4. `wt_add` calls `wt_wire`, which runs: brain/memory/.claude wiring → artifacts reachability
   report (nothing is linked or created — `<project>/artifacts` is already a relative path away).
   Then `wt_setup_env` runs automatically.
   **`auto`-weight stacks (python, node) always run unconditionally — never defer them, even in fork
   mode.** `propose` stacks (ros2) print the command for user confirmation. `none` stacks print a note.
5. Report `wt_add` output. Any `FAIL` line from the self-check means wiring is broken — re-run
   `wt_wire <wt> "$MAIN"` and confirm the result.

## Remove (archive)
`remove` archives a worktree so it can be revived later. It does NOT permanently delete anything.

1. **Confirm** with the user before archiving (gate 3).
2. Call `wt_archive "$MAIN" "$WT"`. This:
   - Moves the worktree via `git worktree move` to `<project>/worktrees/_archive/<branch>` (uncommitted
     changes are preserved — the directory moves intact).
   - Locks the archive path: `git worktree lock` with reason `"archived <date>"`.
   - Appends a row to `_archive/index.tsv` (columns: branch / orig_path / date / ticket).
3. After archiving, the branch still exists and the worktree dir is still registered with git — it is
   simply locked at the archive path. Use `revive` to restore it.

Note: `_archive/index.tsv` lives outside the repo, so it is not clone-durable.
`git worktree list` and the locked directory are the authoritative sources of truth.

## Revive
Restore an archived worktree to active development.

1. Call `wt_revive "$MAIN" "<branch>"`. This:
   - Unlocks the archive path, then moves the worktree via `git worktree move` back to
     `<project>/worktrees/<branch>`.
   - Removes the branch row from `_archive/index.tsv`.
2. The worktree is fully active again — no re-wiring needed (the `.claude` dir and own memory bucket
   are already inside the moved directory, and artifacts stay reachable by relative path).

## Reap
`reap` finalizes a **done** worktree: gates it, writes a promotion manifest, and permanently
deletes the worktree. Use when the branch is merged and the work is complete.

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
  repo / ticket / date) followed by a `candidates:` list — one entry per harvested memory from the
  worktree's claude bucket (`~/.claude/projects/<wt-key>/memory/`). Each entry carries
  `id / store / source / type / body / collision / proposed: {}`, with `store` always `claude`
  (curator fills `proposed`; no `base` field). Prints
  `"reap: promotion pending (memory-curator not yet built)"`. **No memory is auto-merged** — the
  manifest is the input contract for the future `memory-curator` agent.
- Copies the manifest to `<project>/history/reaped/<branch>.reap-manifest.md` (preserved outside the
  worktree before deletion).
- Calls `wt_remove` (deletes the worktree dir + per-wt key dir).

Branch deletion is left to `commit-commands:clean_gone`.

Call: `wt_reap "$MAIN" "$WT" [--force]`

## Check
For each target worktree (one, or all from `git worktree list`):
`wt_check <wt> "$(canonical_dir <wt>)"` and print the lines.
Lines reported: `brain` / `bridge` / `nest` / `memory` / `settings` / `artifacts` / `branch` /
`remote` / `env`. `nest` asserts the worktree sits under `<project>/worktrees/`; `artifacts` asserts
`<project>/artifacts` is reachable from the worktree by relative path (`NA` if there is no store).
If any `FAIL`, offer to repair: re-run `wt_wire` for that worktree (gate 2 applies to any clobber).

## Init
Ensure the project is worktree-native:
- Project pair present: `<repo>/CLAUDE.md` + `<repo>/CLAUDE.local.md` (both gitignored real files; `wt_wire` scaffolds empty stubs if absent).
- **Known gap:** with worktrees beside the repo, native CLAUDE.md walk-up from `<project>/worktrees/<branch>/` reaches `<project>/CLAUDE.md` → `~/.claude/CLAUDE.md` but NOT `<repo>/CLAUDE.md` (the repo dir is not an ancestor). The `bridge:` check still forbids an `@import`. Resolving this is a pending design call — see `references/worktree-recipe.md` → Gotchas.
- Global ignores present in `~/.gitignore_global`: `**/CLAUDE.md`, `**/CLAUDE.local.md`, `.remember/`. The worktree dir itself needs no ignore — it lives outside the repo.
- Report what's missing; create only the safe, confirmed pieces.

## Analyze (bare /worktree)
Detect context and PROPOSE one mode, then confirm:
- cwd is a worktree → suggest `check`.
- cwd is the main clone, project not wired → suggest `init`.
- otherwise → ask whether to `add`.
Never act before the user confirms the proposed mode.
