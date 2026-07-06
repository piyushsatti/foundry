# Claude Code — Portable Configuration Overlay

A portable capture of the Claude Code personal setup: hooks, commands, skills, statusline,
`CLAUDE.md`, settings template, and carried memory. Deploys to a fresh `~/.claude/` on any
machine.

## Architecture: Capture ↔ Apply

```
capture-claude.sh  ←→  MANIFEST  ←→  post-install-claude.sh
  live ~/.claude/        maps           overlay → ~/.claude/
  → overlay              files          + slug remap for memory
```

Re-run `capture-claude.sh` any time the live setup changes, then review the Phase 2
checklist (employer/work-ref taint) before committing.

## File Structure

```
claude/
  capture-claude.sh          # Live ~/.claude/ → overlay (re-runnable)
  post-install-claude.sh     # Overlay → new machine (DRAFT — VM-tested first)
  MANIFEST                   # What's carried / excluded / templated
  README.md                  # This file
  CLAUDE.md                  # Global Claude workflow rules (carried verbatim)
  settings.template.json     # settings.json with /home/<user> → $HOME
  statusline-command.sh      # Statusline script (absolute path rendered at apply time)
  hooks/                     # All hook scripts (*.sh)
  commands/                  # Custom slash commands (*.md + subdirs)
  statuslines/               # Statusline variant scripts
  bin/
    bless                    # xattr-bless helper
  skills/
    worktree/                # Worktree skill (SKILL.md + helpers.sh + tests)
  memory/
    *.md                     # Portable memory files (carried from source machine)
    .source-slug             # Origin machine's project slug (used for remap on apply)
  templates/                 # CLAUDE.md templates for new projects
```

## What's Portable

| Item | How carried | Notes |
|------|-------------|-------|
| `hooks/` | As-is (`cp --preserve=xattr`) | xattr-tagged; plain cp trips guard |
| `commands/` | As-is | Custom slash commands |
| `statusline-command.sh` | As-is | Path rendered at apply via `~/.claude/` |
| `statuslines/` | As-is | Statusline variants |
| `bin/bless` | As-is | xattr-bless helper |
| `skills/` | As-is | Custom skill definitions |
| `CLAUDE.md` | As-is | Global workflow rules |
| `settings.json` | **Templated** | `$HOME` substituted at apply time |
| `memory/*.md` | Carried + **slug remapped** | See Slug Remap below |

## Settings Templating

`capture-claude.sh` writes `settings.template.json` by replacing every occurrence of
`/home/<user>` with `$HOME` in the live `settings.json`.

`post-install-claude.sh` renders the template back to `~/.claude/settings.json` by
substituting `$HOME` with the target machine's actual `$HOME`.

**What's templated:**
- `sandbox.filesystem.allowWrite` / `denyRead` paths
- `permissions.additionalDirectories` paths
- Any other absolute `$HOME`-rooted paths in the hooks section

**What's NOT in the template** (no live absolute paths remaining):
- Hook `command` entries use `~/.claude/hooks/...` tilde-relative form — they resolve
  correctly on any machine without substitution.
- `statusLine.command` uses `~/.claude/statusline-command.sh` — same.

## Slug Remap (Memory — Decision A)

Claude Code derives a project slug from an absolute directory path by replacing every
`/` with `-` (the path starts with `/`, so the slug starts with `-`).

```
/home/<user>  →  -home-<user>       (verified against ~/.claude/projects/ on source)
/home/alice   →  -home-alice        (example on a new machine)
```

**Capture:** `capture-claude.sh` derives the source slug (`echo "$HOME" | sed 's|/|-|g'`),
copies `~/.claude/projects/<source-slug>/memory/*.md` → `infrastructure/claude/memory/`,
and records the slug in `memory/.source-slug`.

**Apply:** `post-install-claude.sh` derives the TARGET slug the same way, reads
`.source-slug` to know the origin, and installs the memory files at
`~/.claude/projects/<target-slug>/memory/`. If source and target slugs differ (different
username on the new machine), this is logged as a remap warning.

## Excluded Secrets and Ephemeral State

The following are intentionally NEVER committed:

| Item | Reason |
|------|--------|
| `.credentials.json` | OAuth credentials — SECRET |
| `audit.jsonl`, `*.jsonl` | Conversation transcripts |
| `audit.log` | Ephemeral log |
| `cache/`, `image-cache/`, `paste-cache/` | Regenerable |
| `telemetry/` | Telemetry state |
| `tasks/`, `agents/`, `sessions/` | Session-specific state |
| `shell-snapshots/`, `daemon*` | Ephemeral process state |
| `projects/*/` (except `memory/`) | All project-level state except portable memory |
| `settings.local.json` | Machine-local overrides |

## Employer-Clean Seam

⚠️ **CLAUDE.md and `settings.template.json` may still contain employer/work references.**

Specifically:
- `CLAUDE.md` may contain your work email, employer name, and workflow conventions
  tied to employer tooling (Jira, Confluence, worktree naming conventions)
- `memory/*.md` may contain employer project names, domain knowledge, or internal references
- `settings.template.json` may contain employer-specific permission rules (AWS, Jira MCP)

**This is fine for copying between your own machines.** The content is carried verbatim
and works correctly for personal use.

**Must scrub before any PUBLIC push** (e.g. making this repo public or sharing with others):
1. Replace any work email or employer name with generic placeholders in CLAUDE.md
2. Strip employer/project-name references from CLAUDE.md and memory/*.md
3. Review settings.template.json deny rules for employer-specific tool names
4. Audit skills/ and commands/ for any employer-specific content

The deferred scrub list is tracked in `memory/workflow_pending_cleanup.md`.

## Phase 2 Checklist (after re-running capture-claude.sh)

After `capture-claude.sh` refreshes the overlay, verify before committing:

1. **settings.template.json**: confirm no hardcoded `/home/<user>` paths leaked through:
   ```bash
   grep -n 'home/<user>' infrastructure/claude/settings.template.json
   ```
   Expect no output.

2. **CLAUDE.md**: skim for new employer/work references added since last capture.
   Run the verify clean check (substitute your own taint terms):
   ```bash
   grep -rniE 'your-employer|work-email|project-name' infrastructure/claude/
   ```

3. **memory/*.md**: review any newly-captured memory files for content you want to exclude.

## Capture ↔ Apply Quick Reference

```bash
# Capture live → overlay (run from anywhere):
bash ~/Documents/notes/infrastructure/claude/capture-claude.sh

# Apply overlay → new machine (DRAFT — syntax-checked; VM-test before using):
bash ~/Documents/notes/infrastructure/claude/post-install-claude.sh
```

## Manual / Secret Steps (documented, not captured)

- **Claude Code auth**: Re-authenticate on the new machine via `claude auth`.
- **MCP server credentials**: Re-configure Atlassian MCP credentials (`~/.claude/.credentials.json`)
  on the new machine — never committed.
- **`settings.local.json`**: Machine-local overrides (not captured). Re-create if needed.
