---
name: reference_worktree_claude_symlink_breaks_sandbox
description: "A git worktree whose `.claude` is a symlink to the main clone breaks the bwrap sandbox — every Bash call dies with `bwrap: Can't create file at <wt>/.claude: Is a directory`; fix = make worktree `.claude` a real dir, not a symlink"
metadata:
  node_type: memory
  last_updated: 2026-06-01
  type: reference
  originSessionId: 8d504945-2e27-41e6-8d26-82040de9f558
---

A git worktree whose `.claude` is a **symlink** to the main clone's `.claude` makes the **bwrap sandbox fail to initialize** — *every* Bash call dies before running with `bwrap: Can't create file at <worktree>/.claude: Is a directory`. During setup bwrap binds a file at the `.claude` path, follows the symlink into the (directory) target, and hits `EISDIR`. `dangerouslyDisableSandbox` and `/sandbox` don't help: global `allowUnsandboxedCommands: false`, and the sandbox is *failing to start*, not disabled. `!` bang-shell also fails — it bypasses PreToolUse hooks but is still bwrap-sandboxed (see [[reference_claude_guard_coverage]]).

Confirmed by isolation on 2026-06-01 (same repo, same global sandbox config): main clone (`.claude` = real dir) runs `echo ok`; a ticket-branch worktree (`.claude` = symlink→dir) errors. It surfaced only then because the global sandbox was re-enabled (`sandbox.enabled: true`) after being off since 2026-05-19, and that worktree was the first worktree session opened under sandbox+symlink. **Affects every worktree** made by the `/worktree` skill — `~/.claude/skills/worktree/helpers.sh` `wt_wire` does `ln -srfn "$main/.claude" "$wt/.claude"`, and `wt_check` (~line 70) *asserts* `.claude` is a symlink (`[ -L ]`), so the doctor passes a broken worktree.

**Fix:** the worktree's `.claude` must be a **real directory** holding a copy of the main clone's `.claude` contents (currently just `settings.local.json`) — never a symlink. The shared brain/memory do NOT travel through `.claude`: they ride `CLAUDE.local.md` `@import` and the `~/.claude/projects/<key>/memory` symlink, so copying loses nothing meaningful. `wt_wire` (create) and `wt_check` (validate) both need patching.

**Why it matters / how to apply:** if Bash is *universally* dead in a worktree session, run `file <worktree>/.claude` first — a symlink is the smoking gun. Replace it with a real dir + copied `settings.local.json`, then start a **fresh** session (the bwrap config is locked at session start; `cd`, `/sandbox`, and `--resume` of the broken session won't recompute it). Related: [[reference_claude_guard_coverage]], [[feedback_diagnose_before_fixing]]. Worktree wiring doctrine lives in `feedback_worktree_workflow` (a project-specific memory store, not this one).
