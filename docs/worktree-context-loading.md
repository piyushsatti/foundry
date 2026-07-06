---
title: "Claude Code context loading across git worktrees — memory shares, CLAUDE.md doesn't"
applies_to: Claude Code v2.1.x (verified 2.1.141, 2026-05-22)
created: 2026-05-22
last_updated: 2026-05-22
keywords: [claude-code, worktree, claude-md, memory, context-loading, project-slot]
related:
  - "../home/hooks/claude-files-guard.sh"
  - "clipboard-model.md"
---

# Why this doc exists

If you're working in a git worktree and notice that your **memory** is available but your **project CLAUDE.md** is not, this is by design — Claude Code resolves the two file types differently for worktree sessions. The asymmetry isn't documented officially as far as I can tell; this doc captures the empirical behavior so future sessions don't have to re-investigate.

# The behavior, in a table

For a Claude session started in `~/Documents/projects/.worktrees/<repo>/<branch>/`:

| File loaded? | Path resolved | Notes |
|---|---|---|
| Global `~/.claude/CLAUDE.md` | Always loaded | Independent of cwd / project |
| Project `~/.claude/projects/<main-checkout-hash>/CLAUDE.md` | **NOT loaded** | Strict per-hash — the worktree has its own slot, which is empty by default |
| Project `~/.claude/projects/<worktree-hash>/CLAUDE.md` | Loaded if present | But starts empty when the worktree is created |
| Project `~/.claude/projects/<main-checkout-hash>/memory/*.md` | **Loaded** | Worktree → main-checkout mapping happens for memory |

So memory routes worktree → main-project automatically, but CLAUDE.md is strictly resolved by the working directory's escaped-path hash. Each worktree is an island for CLAUDE.md.

# Slot naming convention

The `~/.claude/projects/` slot for a given working directory is the cwd with `/` → `-` and a leading `-` prepended. For example:

| Working directory | Slot directory |
|---|---|
| `/home/<user>/Documents/projects/my-project` | `-home-<user>-Documents-projects-my-project` |
| `/home/<user>/Documents/projects/.worktrees/my-project/feature-x` | `-home-<user>-Documents-projects--worktrees-my-project-feature-x` |

Each is independent. Writing CLAUDE.md to one does not affect the other.

# How this was verified

Run a fresh Claude session in a worktree, ask whether a project CLAUDE.md is loaded:

```bash
cd /home/<user>/Documents/projects/.worktrees/my-project/feature-x
claude
# In the session:
# > Do you see a CLAUDE.md for this project loaded? Show me the first line.
```

The session reports something like: *"No — I only see your global `~/.claude/CLAUDE.md` and the project memory index (MEMORY.md). No project-level CLAUDE.md from the project repo is loaded."*

Repeat from the main checkout (`~/Documents/projects/my-project`) for the sanity-check — that session sees the project CLAUDE.md (confirming the slot is correctly populated, just not shared).

# Implications for a one-CLAUDE.md-per-project workflow

If you want a single source-of-truth CLAUDE.md that's visible from every worktree of a given project, three patterns exist; the decision between them is **deferred** as of 2026-05-22 (attempted the repo-commit pattern, reverted before commit to think more carefully):

**Pattern A: Per-slot copy (manual)**
Copy or symlink the CLAUDE.md into each worktree's slot when the worktree is created. Lowest infrastructure but easy to forget.

**Pattern B: Artifacts directory + symlinks**
Keep the canonical CLAUDE.md in a non-repo directory (e.g. `~/Documents/projects/artifacts/<repo>/CLAUDE.md`), then symlink each worktree's slot to it:

```bash
ln -s ~/Documents/projects/artifacts/<repo>/CLAUDE.md \
      ~/.claude/projects/-home-<user>-Documents-projects--worktrees-<repo>-<branch>/CLAUDE.md
```

One source of truth, no per-slot copies to keep in sync. But the `claude-files-guard.sh` hook currently blocks the canonical write because it treats anything under `~/Documents/projects/` as repo-adjacent. The hook would need to be relaxed for this pattern to work cleanly inside Claude.

**Pattern C: Setup script on worktree creation**
Wrap `git worktree add` in a script that also creates the worktree's slot and symlinks the canonical CLAUDE.md into it. Eliminates the manual step; survives across `git worktree remove` / re-create cycles.

**Pattern D (committed repo-root CLAUDE.md, the `/init` canonical) — attempted and reverted 2026-05-22**
The simplest pattern is to commit `<repo>/CLAUDE.md` directly. Git distributes the file across worktrees (any worktree on a branch that includes the commit sees the file). Trade-off: the file is team-visible, so it must only contain content appropriate to share — usually fine for project-shape docs, but a deliberate decision. **Note:** verification requires the file to be COMMITTED first — uncommitted files in the main repo's working tree don't appear in worktrees on different branches. Reverted before committing to defer the team-visibility decision.

# Decision framework

When you come back to pick a pattern, walk this rubric:

**Q1: Is the project CLAUDE.md content team-shareable?**

The content of your current `~/.claude/projects/<hash>/CLAUDE.md` is project shape (architecture, key paths, conventions, build commands). Read it. Ask: *"Would a teammate cloning this repo benefit from this file? Does it contain anything I'd be uncomfortable with them seeing?"*

- **Yes, team-shareable, no personal content** → Pattern D. Zero ongoing cost, distributes via git, teammates benefit.
- **No, contains personal preferences or work-in-progress thinking** → Q2.
- **Mixed (some team-worthy, some personal)** → Split: team-worthy content → Pattern D (committed); personal content → global `~/.claude/CLAUDE.md` or per-project `CLAUDE.local.md`.

**Q2: How often do you create new worktrees in this repo?**

- **Rarely (few times a year)** → Pattern A is fine. The manual copy step is low-friction relative to other worktree-setup chores.
- **Frequently (multiple per month, e.g. one per ticket)** → Q3.

**Q3: Do you want the hook tweak now, or a setup script later?**

- **Hook tweak now** → Pattern B. Edit the hook to walk for `.git` before blocking, then symlink each worktree slot to `~/Documents/projects/artifacts/<repo>/CLAUDE.md`.
- **Invest in tooling once** → Pattern C. Write a `git worktree add` wrapper (bash, ~50 lines) that also creates the slot dir and the symlink. Pattern C inherits from Pattern B (still need the canonical file in `artifacts/`), so the hook tweak from B is still required.

## Cost / risk summary

| Pattern | Per-worktree cost | Ongoing maintenance | Risk |
|---|---|---|---|
| A — per-slot copy | 1 cp at worktree creation | Drift between worktree copies if you edit one but not others | Forgetting the cp; silent drift |
| B — artifacts + symlinks | 1 symlink at worktree creation | Hook tweak weakens (slightly) the personal-leak safety net | Hook change made wrong; orphan symlinks if artifacts moves |
| C — worktree wrapper script | Zero (script handles it) | Script becomes personal infrastructure to maintain | Script breaks on edge cases; new worktrees created without it |
| D — committed in repo | Zero (git handles it) | Project CLAUDE.md tracked in git history like any code file | File leaks personal content; team disagrees with what's documented there |

# Verification gotcha: testing cross-worktree visibility requires a commit

A subtle trap (hit on 2026-05-22): when verifying whether a worktree session can see a project CLAUDE.md, **uncommitted files in the main repo's working tree are not visible from worktrees on different branches**. Git worktrees each have their own working tree on disk; an untracked file in one isn't magically visible in another.

This means: to verify Pattern D actually works *before* committing to main, you must commit somewhere. Two safe paths:

**Option 1: Commit to a feature branch, verify from a worktree on that branch**
1. In the main checkout: `git checkout -b try-claude-md` then create the CLAUDE.md and commit
2. Create a worktree on the same branch (or one branched from it): `git worktree add ../.worktrees/<repo>/try-claude-md try-claude-md`
3. In that worktree: `claude` → ask "do you see a project CLAUDE.md?"
4. If it works, merge `try-claude-md` to main. If not, the worktree's `.git` link will be cleaned up by `git worktree remove`.

**Option 2: Just test in the main checkout where the file lives**
This tests "does Claude Code load CLAUDE.md from cwd / project root?" — which we already know is YES (hierarchical loading is well-documented). It does NOT test cross-worktree distribution. Don't confuse these two questions.

The 2026-05-22 attempted-and-reverted experiment hit this trap: the file was placed in the main checkout's working tree (untracked), then verified from a worktree on a different branch, which couldn't see the untracked file. The test failure looked like Pattern D doesn't work, but actually the methodology was wrong — the file wasn't propagated by git because it wasn't committed.

# Hook interaction

`~/.claude/hooks/claude-files-guard.sh` blocks Write/Edit/MultiEdit to:

- `*/CLAUDE.md` outside of `~/.claude/*` and `~/Documents/claude/*`
- `*/memory/*.md` outside the same allowlist
- `*/.claude/*` outside the same allowlist

The intent is to prevent CLAUDE.md / memory files from getting committed into project git repos. The hook is **over-conservative** for the `artifacts+symlinks` pattern because it pattern-matches the file path without checking whether the file would actually land inside a git working tree. As a result, paths like `~/Documents/projects/artifacts/<repo>/CLAUDE.md` are blocked even though `artifacts/` is not a git repo.

**Possible hook fix (if Pattern B is chosen):** walk up the target path looking for a `.git` directory or file. Only block if the file would land inside an actual git working tree. This unblocks Pattern B while preserving the original safety intent.

**Possible hook fix (if Pattern D is chosen):** remove the `*/CLAUDE.md` pattern from the deny list entirely, since committed repo-root CLAUDE.md is the canonical team-context artifact. Memory and `.claude/**` blocks would remain (no team-share convention for those). This was attempted on 2026-05-22 and reverted pending the team-visibility decision.

The hook implementation is in `~/.claude/hooks/claude-files-guard.sh` and `~/.claude/hooks/claude-files-bash-guard.sh` (the bash mirror for cp/mv/ln/install vectors).

# Memory behavior contrast (for reference)

In the same worktree session, the memory index DOES load. Verified by the session reporting access to `MEMORY.md` even though it lives at `~/.claude/projects/<main-checkout-hash>/memory/MEMORY.md`, not at the worktree's slot. So if you've been adding memories from inside a worktree, they go to the main-checkout's memory directory — which is usually what you want.

If you ever need a worktree-local memory (rare), you'd write it to `~/.claude/projects/<worktree-hash>/memory/` explicitly. There's currently no clean way to express this through the slash commands.

# Provenance

Verified 2026-05-22 during a memory audit + CLAUDE.md hook investigation. Two sessions were run side-by-side: one in the main checkout, one in a feature-branch worktree, both asked the same question about loaded CLAUDE.md. The asymmetry between memory loading (works across worktrees) and CLAUDE.md loading (per-hash isolation) was the key finding.

This doc lives in `infrastructure/claude/` because the behavior is portable Claude Code knowledge that applies to any machine and any project.
