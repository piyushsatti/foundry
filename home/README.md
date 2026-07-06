# home — personal `~/.claude` kit

The Claude Code configuration I sync across machines, versioned here so it's
reviewable and portable. This is the **generic, you-owned** layer; anything
machine-bound or work-sensitive stays out (see the fence below).

## Layout

| Path | What it is |
|------|-----------|
| `CLAUDE.md` | Global workflow discipline — rules that apply to every project (generic only; no employer/project/language specifics) |
| `settings/` | Per-machine settings variants + the wired template. **Not yet merged** — see [`settings/NOTES.md`](settings/NOTES.md) |
| `hooks/` | 32 guard/logging/nudge hooks (secret-scan, sandbox guards, conventional-commit, audit trail, …) + `lib/` |
| `commands/` | Slash commands (`primer`, …) |
| `agents/` | User-level subagents (`scrutineer` — research-rigor auditor) |
| `bin/` | Helper executables (`bless`) |
| `memory/` | Recalled facts/references (`MEMORY.md` index + `feedback_*` / `reference_*`) — generic, portable memories only |
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
