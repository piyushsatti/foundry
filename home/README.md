# home — authored Claude Code tooling

Tooling I **built** for my Claude Code setup — hooks, commands, statuslines,
subagents, helper bins — versioned because they are developed artifacts.

**Live personal state is deliberately NOT here.** `~/.claude/CLAUDE.md` (global
rules) and `~/.claude/settings.json` drift by design per machine/preference;
mirroring them in a repo produces stale copies, so the live files are the only
truth (evicted 2026-07-12). Machine-bound or work-sensitive content stays out
(see the fence below).

## Layout

| Path | What it is |
|------|-----------|
| `hooks/` | 32 guard/logging/nudge hooks (secret-scan, sandbox guards, conventional-commit, audit trail, …) + `lib/` |
| `commands/` | Slash commands (`primer`, …) |
| `agents/` | User-level subagents (`scrutineer` — research-rigor auditor, `warden` — ways-of-working scope gate) |
| `bin/` | Helper executables (`bless`) |
| `statuslines/` | Statusline scripts + `statusline-command.sh` dispatcher |

## The fence — what does NOT live here

Machine-bound and work-sensitive content (real hostnames, employer detail,
internal infra, private project names, per-host paths) belongs in the
gitignored `local/` store, **not** in this kit. `CLAUDE.md` and `memory/` here
are deliberately kept generic so this can be published. Some memory files link
to `[[...]]` targets that live only in the local store — those dead links are
expected for a public reader.

## Install

These are **reference copies** — don't blindly symlink them into `~/.claude`.
`settings/` in particular is unmerged (per-machine variants side by side); pick
or hand-merge per the NOTES before wiring anything live.
