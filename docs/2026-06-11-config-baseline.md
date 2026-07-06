---
title: Claude Code config baseline — pre-redesign snapshot
last_updated: 2026-06-11
type: reference
related:
  - design-philosophy.md
---

# Claude Code config baseline (captured 2026-06-11)

The "before" photograph taken immediately prior to the **workflow-tiered access redesign**.
Recorded so future audits can measure drift.
Source: live read of `~/.claude/settings.json`, `~/.claude/settings.local.json`, and
`~/.claude/hooks/` on 2026-06-11.

## settings.json (`~/.claude/settings.json`, 621 lines)
- Top-level: `model: opusplan`, `advisorModel: opus`, `outputStyle: Explanatory`,
  `effortLevel: high`, `cleanupPeriodDays: 3650`, `respectGitignore: false`,
  `attribution.commit/pr: ""` (no Co-Authored-By), `enableWorkflows: false`,
  `skipAutoPermissionPrompt: true`, `useAutoModeDuringPlan: true`.
- Permission rule counts: **132 allow / 147 deny / 24 ask**. `defaultMode: default`.
  `additionalDirectories: ["~/.claude/hooks"]`.
- **allow** highlights: read tools, WebSearch/WebFetch, context7 MCP; many read-only Bash
  verbs (git read subcmds, ls/cat-family, jq, linters, `uv pip list/show/freeze/tree`,
  `npm list/info/ls`, `docker ps/images/logs/inspect`, `docker compose config/ps/logs`,
  `docker (compose )?exec * airflow`, `aws sts/s3 ls/ecr|ecs describe/logs *`, `ros2 *` read,
  `setfattr -n` + `getfattr`, `gsettings/dconf`, `ps aux *`).
- **deny** groups: destructive-file (`rm -rf|-fr|-r -f|--recursive|-Rf`, `shred`, `dd`, `mkfs`,
  `find * -delete|-exec rm|mv|chmod|chown|sh|bash|-fprint*|-fls`); git-destructive (force-push x4,
  `reset --hard`, `clean -fd|-df|-f`, `checkout -- .|.`, `filter-branch|filter-repo`,
  `update-ref -d`, `rebase`, `pull --rebase`, remote add/set-url/remove/rm/rename); priv-esc
  (`sudo`, `su`, `su -`, `pkexec`, `chmod 777|0777`, `chown`, `eval`); publishes (`npm/cargo/uv
  publish`, `twine upload`); **interpreter-inline** (`bash -c`, `sh -c`, `zsh/dash/ksh -c`,
  `pwsh -c|-Command`, `python[3] -c`, `node -e`, `perl -e`, `ruby -e` — both `*` and `:*`);
  **package installs** (`uv add|pip install|pip uninstall|tool install|tool uninstall|uvx`,
  `pip[3] install`, `pipx install|run|inject`, `pipenv install|update|sync`, `poetry
  add|install|update`, `npm install|i|add|ci`, `pnpm add|install|i`, `yarn add|install`,
  `cargo install|add`, `gem install`, `brew install|upgrade`, `go install|get`,
  `apt|apt-get|aptitude|snap|flatpak|dnf|yum install`, `pre-commit install`); docker-destructive
  (`system prune`, `volume rm`, `rmi -f`, `image rm|rmi|prune`); xattr/bless bypass (`setfattr
  -x|--remove`, `bless`/`*/bless`); 10 Atlassian MCP write tools.
- **ask** (24): all `gh pr/issue/release` mutations, `gh api * --method|-X POST/PUT/PATCH/DELETE`,
  and `git commit:*`.
- Inline PreToolUse Bash deny for `psql` + `DROP TABLE|DATABASE|SCHEMA|INDEX | TRUNCATE`.

### sandbox block (in settings.json)
- `enabled: true`, `autoAllowBashIfSandboxed: true`, `allowUnsandboxedCommands: false`.
- `network.allowedDomains` (6): github.com, api.github.com, pypi.org, files.pythonhosted.org,
  registry.npmjs.org, index.crates.io. `allowLocalBinding: true`.
- `filesystem.allowWrite`: `~/.claude` (**whole tree — includes hooks/bin/settings**),
  a work project path (**NONEXISTENT, F13**), `~/Documents/notes`,
  `~/Documents/projects`, `/tmp`.
- `filesystem.denyRead`: `~/.ssh`, `~/.aws/credentials`, `~/.gnupg`.

## settings.local.json (`~/.claude/settings.local.json`)
```json
{ "outputStyle": "default", "sandbox": { "enabled": false, "autoAllowBashIfSandboxed": false } }
```
This scalar **disables the sandbox globally** (overrides settings.json `enabled:true`) — the
regression that put every session in the strictest tier. Primary clones' own
`settings.local.json` also set `enabled:false`; ~5 worktrees re-enable it. Net: unsandboxed
nearly everywhere.

## Hooks (`~/.claude/hooks/`) — inventory at baseline
Dir perms: `drwxrwxr-x piyush piyush` (**group-writable, F4**). `~/.claude/bin/` same.
Settings files: `lsattr` shows `--------------e-------` (**not immutable** — no `i` flag).

| script | size | mtime | role |
|---|---|---|---|
| settings-lock.sh | 1837 | 2026-05-22 | deny edits to settings*.json. **Has a Bash branch but is NOT wired to the Bash matcher (F1)** |
| secret-scanner.sh | 2118 | 2026-04-08 | deny secrets in writes/commands |
| sensitive-file-guard.sh | 608 | 2026-05-19 | deny pem/key/credentials writes; **line 8 `exit 0` waves through `*/.claude/hooks/*` (F2)** |
| claude-files-guard.sh | 2320 | 2026-05-22 | deny CLAUDE.md/memory/.claude writes in repos |
| claude-files-bash-guard.sh | 3212 | 2026-05-22 | deny cp/mv/ln/install landing Claude-named files in repos (allows `~/.claude/*`) |
| ai-artifact-guard.sh | 1168 | 2026-04-08 | deny docs/superpowers writes |
| persistence-guard.sh | 3512 | 2026-05-20 | ask on Write to dotfiles/systemd/~/.local/bin/etc |
| persistence-bash-guard.sh | 5560 | 2026-05-20 | ask on Bash writes to persistence paths |
| claude-self-guard.sh | 1304 | 2026-05-20 | ask on writes to ~/.claude settings/hooks/bin |
| pipe-rce-guard.sh | 2722 | 2026-05-20 | deny curl|bash / pipe-to-shell |
| docker-escape-guard.sh | 20883 | 2026-05-31 | deny container-escape docker flags (`-rw-rw-r--`, run via `bash <path>`) |
| bash-cred-read-guard.sh | 4099 | 2026-05-20 | deny reads of .ssh/.aws/.kube/gh-token/keyring (wired on Bash) |
| xattr-guard.sh | 3701 | 2026-05-30 | deny exec/cp/redirect of `user.claude.authored`-tagged files (wired on Bash); exempts `bash -n` |
| xattr-tagger.sh | 1118 | 2026-05-19 | PostToolUse: tag Claude-written files; **skips hooks/ & bin/ (F3)** |
| main-branch-guard.sh | 601 | 2026-04-08 | deny commit/push/merge on main/master |
| conventional-commit.sh | 1350 | 2026-04-08 | deny non-conventional commit msgs; **breaks on `-F`/bare `--amend`/heredoc** |
| docker-compose-validator.sh | 612 | 2026-04-08 | PostToolUse compose lint (context inject) |
| audit-log.sh | 4933 | 2026-05-20 | append JSONL audit (async) |
| stats.sh | 1253 | 2026-05-29 | shared helper (deny_hook/log_stat/project_dir); **11 hooks source it; its absence silently disables them (F5)** |
| pending-cleanup-check.sh | 780 | 2026-05-29 | SessionStart context |
| project-bootstrap-check.sh | 2112 | 2026-06-01 | SessionStart context |
| scope-context.sh | 1328 | 2026-04-23 | SessionStart context |
| session-log.sh | 852 | 2026-04-08 | Stop log (async) |
| ~/.claude/bin/bless | 1409 | 2026-05-19 | user-only TTY helper to clear the authored xattr |

### Hook wiring (settings.json `hooks`)
- **PreToolUse Write|Edit|MultiEdit:** settings-lock → secret-scanner → sensitive-file-guard →
  claude-files-guard → ai-artifact-guard → persistence-guard → claude-self-guard → audit-log(async).
- **PreToolUse Bash:** secret-scanner → pipe-rce-guard → docker-escape-guard → bash-cred-read-guard
  → persistence-bash-guard → claude-files-bash-guard → xattr-guard → audit-log(async) →
  main-branch-guard → conventional-commit → inline psql-DDL deny. **(settings-lock absent here = F1.)**
- **PostToolUse Write|Edit|MultiEdit:** ruff format → ruff check (context) → docker-compose-validator
  → xattr-tagger → audit-log(async). **PostToolUse Bash:** audit-log(async).
- **SessionStart:** pending-cleanup-check, project-bootstrap-check, name reminder, scope-context.
  **Stop:** session-log. **PreCompact/PostCompact:** prompt + reminders.

## Known gaps at baseline (carried into the redesign as "tighten-first")
- **F1** settings-lock not wired to the Bash matcher → Bash redirect/cp can rewrite settings*.json.
- **F2** sensitive-file-guard line-8 bypass for `*/.claude/hooks/*` (no content scan of hook edits).
- **F3** xattr-tagger skips hooks/ & bin/ (an overwritten hook gets no tag → never re-gated).
- **F4** hooks/ & bin/ are group-writable.
- **F5** stats.sh is a silent single point of failure for 11 hooks.
- **F13** a nonexistent work project path in sandbox allowWrite.
- Sandbox `allowWrite` includes the entire `~/.claude` tree (hooks are writable from inside the
  sandbox, where no hook can see in-process writes) — the keystone risk the redesign closes first.

## Provenance
Rationale: [`design-philosophy.md`](design-philosophy.md).
