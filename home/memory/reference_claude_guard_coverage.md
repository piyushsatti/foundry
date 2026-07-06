---
name: reference_claude_guard_coverage
description: "Claude Code PreToolUse hooks guard only the agent's Bash tool calls — the `!` bang-shell bypasses them, and the bwrap sandbox may not actually be active (verify); the deny-hook layer is often the SOLE runtime control"
metadata:
  node_type: memory
  last_updated: 2026-06-01
  type: reference
  originSessionId: f634cf24-4437-480e-b3c1-49acaf5b21d0
---

Claude Code's PreToolUse hooks fire on the **agent's Bash tool calls** — that is the guarded attack surface (a prompt-injected/rogue Claude can only act via tool calls). Two things are NOT covered, both verified empirically on 2026-06-01:

1. **The `!` bang-shell bypasses PreToolUse hooks.** A command the user types as `!docker run …` runs in the user's own shell, not through the tool layer, so no hook fires (observed: `!docker run -v /:/host alpine true` ran and pulled the image, while the *same* command via Claude's Bash tool was denied by `docker-escape-guard`). This is correct for the rogue-Claude threat model — the user is the trust authority and can edit the hooks anyway — but it means hook coverage is the agent's surface, not the human's.

2. **Don't assume the bwrap sandbox is active — verify.** The Bash tool ran **un-sandboxed**: `Seccomp: 0`, host mount namespace (`mnt:[4026531832]`), parent process `claude` (not `bwrap`), despite `autoAllowBashIfSandboxed: true` and `bwrap` installed. Docker (root daemon, via the `docker` group) and host files were fully reachable. So the sandbox gave **zero** runtime confinement and the **PreToolUse deny-hook layer was the sole control** (e.g. `docker-escape-guard.sh` is the only thing stopping a `docker run -v /:/host` host-root escape). **This is by design:** the user deliberately disables the sandbox for these (trusted) session types, so the deny-hook layer is the *intended* sole control — not an accidental gap.

**Why it matters / how to apply:** when reasoning about what actually protects the host, count only the *live* layers. The bwrap sandbox may be **deliberately disabled** for a session type (as here — a user choice), in which case the deny-hooks are the *intended* sole control and must be treated as load-bearing. Don't assume the sandbox is a live control either way — verify: `grep Seccomp /proc/self/status` (expect non-zero for seccomp), check for a `bwrap` parent (`cat /proc/$PPID/comm`), compare `/proc/self/ns/mnt` to a private ns. **Crucially, also read `~/.claude/settings.local.json`:** on 2026-06-01 the concrete cause was a local `sandbox.enabled:false` (+`autoAllowBashIfSandboxed:false`) that, as a scalar, **overrides** global `settings.json`'s `sandbox.enabled:true`. **Update 2026-06-01:** resolved by re-enabling the sandbox globally — the `sandbox.enabled:false` override was removed from `~/.claude/settings.local.json`, so global `sandbox.enabled:true` governs all session types. To keep non-project work (the Obsidian vault) functional, `sandbox.filesystem.allowWrite` is extended to known-good paths (`~/Documents/notes`, `/tmp`) alongside `~/Documents/projects`/`~/.claude`. Lesson: when a sandboxed session can't write where it expects, the `allowWrite` list is the first thing to check. If it's not live, the deny-hooks are doing all the work — design and audit guards on that basis. Related: [[feedback_diagnose_before_fixing]], [[feedback_data_quality_proactive]].
