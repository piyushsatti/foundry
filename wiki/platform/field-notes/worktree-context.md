---
title: Worktree Context Loading
status: stable
summary: Claude Code shares memory across git worktrees but resolves CLAUDE.md strictly per-directory.
sources:
  - docs/worktree-context-loading.md
updated: 2026-07-20
---

# Worktree Context Loading

**Claude Code shares memory across git worktrees but resolves CLAUDE.md strictly by the working directory's path hash — so a worktree sees your memory but not the project CLAUDE.md.**

> **Status:** stable

## The asymmetry

For a session started in a worktree (`.worktrees/<repo>/<branch>/`):

| Context | Loaded in worktree? | Why |
|---|---|---|
| Global `~/.claude/CLAUDE.md` | Always | Independent of cwd |
| Project CLAUDE.md (main-checkout slot) | **No** | Resolved strictly per path-hash; worktree has its own empty slot |
| Project CLAUDE.md (worktree slot) | Only if present | Starts empty at worktree creation |
| Project `memory/*.md` | **Yes** | Memory routes worktree → main-checkout automatically |

**Memory maps worktree → main project; CLAUDE.md does not.** Each worktree is an island for CLAUDE.md. Memories added from a worktree land in the main-checkout's memory dir — usually what you want.

## Slot naming

The `~/.claude/projects/` slot is the cwd with `/` → `-` and a leading `-`:

| Working directory | Slot |
|---|---|
| `…/projects/my-project` | `-home-…-projects-my-project` |
| `…/projects/.worktrees/my-project/feature-x` | `-home-…-projects--worktrees-my-project-feature-x` |

Writing CLAUDE.md to one slot does not affect the other.

## Single-source CLAUDE.md: four patterns

To make one CLAUDE.md visible from every worktree of a repo. **Pattern decision is deferred** — pick per project via the questions below.

| Pattern | How | Per-worktree cost | Main risk |
|---|---|---|---|
| **A — per-slot copy** | `cp`/symlink into each slot manually | 1 cp | Forgetting it; silent drift |
| **B — artifacts + symlinks** | Canonical file outside repo, symlink each slot to it | 1 symlink | Needs the `claude-files-guard` hook relaxed |
| **C — worktree wrapper** | Script wraps `git worktree add` to make slot + symlink | Zero | Script breaks; worktrees made without it. Inherits B's hook tweak |
| **D — committed repo CLAUDE.md** | Commit `<repo>/CLAUDE.md`; git distributes it | Zero | File is team-visible — must hold no personal content |

**Choosing:** Is the content team-shareable? Yes → **D**. No → how often do you make worktrees? Rarely → **A**; frequently → **B** (hook tweak now) or **C** (tooling once).

## Two verification traps

- **Cross-worktree visibility needs a commit.** Uncommitted files in the main working tree are *not* visible from worktrees on other branches. To test Pattern D, commit to a branch and check from a worktree on it — don't confuse "loads from cwd" (known yes) with "distributes across worktrees".
- **The hook blocks Pattern B.** `claude-files-guard.sh` denies `*/CLAUDE.md` writes outside its allowlist by path-match, without checking whether the target is in a real git tree — so it blocks a canonical `artifacts/<repo>/CLAUDE.md`. Fix: walk up for `.git` before blocking.
