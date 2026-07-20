# Quality Hooks

**Quality hooks enforce hygiene and tag provenance around commits and file writes — conventional commits, branch protection, compose validation, and authored-file tagging.**

> **Status:** draft — authored, mostly unwired (roadmap, Issue #3).

## The problem

Left unchecked, an agent commits non-conventional messages, commits straight to `main`, leaves a broken compose file behind, or writes files the [guard](guard-hooks) layer can't later tell apart from human-authored ones. Quality hooks catch these at the commit and write boundaries.

## How it works

Two mechanisms, at two lifecycle points:

- **Commit hygiene** (PreToolUse Bash deny) — `conventional-commit` rejects messages that aren't Conventional Commits (parsing every flag/heredoc/`-F` form); `main-branch-guard` denies commit/push/merge while on `main`/`master`. These are guards by *mechanism* but quality by *intent*.
- **Post-write checks & tagging** (PostToolUse) — `docker-compose-validator` runs `compose config` after a compose edit and injects any errors; `xattr-tagger` stamps Claude-authored files with `user.claude.authored`; `install-tagger` stamps freshly-installed `bin` entries.

## Why tag-then-guard

Provenance can't be inferred at deny time, so it's **stamped at write time** (the taggers, PostToolUse) and **enforced later** (`xattr-guard`, PreToolUse). Splitting *mark* from *enforce* across the two phases is what makes "don't execute an un-blessed authored file" possible at all — the taggers here are the write-side of that guard system.

## See also

- [Guard hooks](guard-hooks) — the enforce-side of tagging.
- [Lifecycle](../lifecycle)
