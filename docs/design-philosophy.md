---
title: "Claude Code — Management Design Philosophy"
created: 2026-05-30
last_updated: 2026-06-11
---

# Claude Code — Management Design Philosophy

This document captures the overall posture, threat model, per-guard rationale, settings
philosophy, memory/session design, design principles, and open questions behind this
machine's Claude Code setup. It consolidates reasoning that was previously scattered across
earlier audits, plans, and session notes.

**Audience:** the user, future-self on a new machine, or collaborators adopting the same
pattern. All content is employer-agnostic and safe to publish.

---

## 1. Overview — Why Manage Claude This Tightly

The core motivation is straightforward: **Claude Code has real file-write, Bash execution,
and settings-edit capability.** Left entirely unconstrained, any single session that
receives a hostile or confused instruction could, in principle:

- Read credential files and surface them in conversation context
- Edit the very settings and hook files that constrain its behaviour, lifting its own
  restrictions
- Write to shell startup files, PATH-shadowed directories, or package registries, creating
  persistence
- Download and execute arbitrary code via pipe-to-shell patterns
- Execute Claude-authored scripts before the user has reviewed them

The adversary model is **a prompt-injected or rogue Claude instance** — not the user. The
user sits *outside* the trust boundary; the guards exist so that even a compromised or
confused Claude session cannot silently escalate. This is also why certain guards fire on
legitimate-looking requests: the guard cannot distinguish "Claude following a valid
instruction" from "Claude following an injected instruction," so it keeps the human in the
loop for high-risk categories.

The secondary adversary model is **accidents during autonomous sub-agent work**: a
multi-step sub-agent that generates and then immediately executes its own script, or that
recursively modifies the hook layer to unblock itself. The guards prevent this without
requiring the user to audit every intermediate action.

The management posture is therefore **defense-in-depth, not user-discipline**. Removing
the guards would require the user to manually verify every Bash invocation, file write, and
settings edit. That is not scalable. The guards keep the interrupt surface small — only
genuinely high-risk actions reach the user's attention — while low-risk work flows freely.

---

## 2. Security / Threat Model — The Layered Guards

### 2.1 `settings-lock.sh` — Self-Modification Lockout

**What:** Hard-denies any `Write`, `Edit`, or `MultiEdit` to `~/.claude/settings*.json`.
Also denies Bash commands that pair the settings path with write-capable operators
(`>`, `>>`, `tee`, `sed -i`, `mv`, `cp`, `rm`, `truncate`, `sponge`, `dd of=`, `chmod`).

**Why:** `settings.json` holds the permission deny rules and `defaultMode`. If Claude can
edit it, Claude can lift its own restrictions — for example flipping to
`bypassPermissions` mode, or removing deny rules for destructive operations. The only
sound approach is to allow settings changes *only* via a text editor operated by the
user outside Claude. There is no in-session exemption mechanism; the lock is
unconditional.

**Note on dual coverage:** `claude-self-guard.sh` (§2.2) also fires an `ask` prompt on
settings edits. The two work together: `settings-lock` provides the hard deny;
`claude-self-guard` provides the surface-level ask for paths the hard deny might not reach
(e.g., `~/.claude/hooks/*`). As long as `hooks-lock.sh` (the planned companion) is not
yet built, this dual coverage is intentional belt-and-braces.

---

### 2.2 `claude-self-guard.sh` — Enforcement-Layer Ask Prompt

**What:** Fires an `ask` prompt when Claude attempts to write to
`~/.claude/settings.json`, `~/.claude/settings.local.json`, `~/.claude/hooks/*`, or
`~/.claude/bin/*`.

**Why:** `hooks/*` and `bin/*` are the enforcement layer. If Claude can silently edit a
hook script, it can rewrite any guard — including the one that protects it from
self-modification. The ask prompt ensures the user sees and approves any change to the
enforcement apparatus in the same session where it was requested. A prompt-injected Claude
cannot silently disable the rest of the defense layer; the user is always notified.

**Note on `hooks-lock.sh` gap:** `xattr-tagger.sh` explicitly skips the
`~/.claude/hooks/*` path to avoid tagging hook files (the comment defers to a future
`hooks-lock.sh`). Until that hook exists, `claude-self-guard`'s ask-mode is the sole
protection on the hooks directory. This is a known open tension (see §7).

---

### 2.3 `xattr-tagger.sh` + `xattr-guard.sh` — Write-Then-Execute Gate

**What (two-part lifecycle):**
1. `xattr-tagger.sh` (PostToolUse, async): stamps every Claude-written file with a
   `user.claude.authored` extended attribute immediately after it is written.
2. `xattr-guard.sh` (PreToolUse Bash, sync): before any Bash command runs, checks whether
   referenced files carry that xattr and whether the command is in a danger category —
   interpreter exec (`bash <path>`, `python <path>`, etc.), `cp` without an
   xattr-preserving flag, or output redirect to a script-extension or
   `~/.local/bin`-class target. If both conditions hold, the command is denied with a
   message directing the user to `bless` the file.

**Bless:** `~/.claude/bin/bless <path>` is a small binary the user runs in their own
terminal (not via Claude) to remove the tag after review, unblocking subsequent execution.

**Why:** An agentic Claude can generate a script and immediately try to run it — closing
the human-review loop entirely. The xattr tag interrupts that loop at the execution point
rather than the write point (which is already audited). A generated script that the user
has not read is semantically untrusted, even if the session that wrote it was behaving
correctly — it could have been steered by an earlier prompt injection. The bless mechanism
restores execution capability only via a user action that necessarily implies review.

**Exemption (2026-05-30):** `bash -n <file>` (parse-only syntax check) was added as an
explicit exemption because it does not execute the file; denying it was pure friction.
The exemption is narrow: only `bash/sh/zsh/ksh/dash -n` (POSIX no-execute parse), not
full interpreter exec or other flags.

---

### 2.4 `bash-cred-read-guard.sh` — Credential Read Blocking

**What:** Hard-denies Bash commands that reference known credential storage paths
(`.ssh/`, `.gnupg/`, `.aws/`, `.docker/`, `.kube/`, `.netrc`, `.pgpass`,
`.git-credentials`, browser profile storage, etc.) or that invoke credential-emitting CLI
tools (`gh auth token`, `aws configure get`, `op read`, `bw get`, `pass show`, etc.).

**Why:** Claude's sandbox `denyRead` rules cover some of this, but the rules operate at
the filesystem level and can be bypassed by indirect access patterns (e.g., `cat`,
`head`, `jq`). This hook closes the Bash read-side gap that `sensitive-file-guard.sh`
(Write/Edit only) and `secret-scanner.sh` (content pattern match) leave open. Credentials
that flow into Claude's conversation context are effectively exfiltrated — they appear in
session transcripts, can be echoed back, and may leak across subagent boundaries. The
pattern is deliberately broad on false positives (they prompt the user) because false
negatives (missed credential reads) are the failure mode with real cost.

---

### 2.5 `pipe-rce-guard.sh` — Pipe-to-Shell / Process Substitution RCE Blocking

**What:** Hard-denies Bash commands matching canonical download-then-execute patterns:
pipe-to-shell (`curl … | bash`), process substitution (`bash <(curl …)`), and command
substitution into interpreter (`bash -c "$(curl …)"`). Covers optional `sudo`/`nohup`/`env`
wrappers before the shell name.

**Why:** Claude Code's permission system splits compound commands on shell operators
(`|`, `&&`, `;`, `||`) before matching. Any deny rule that *contains* a pipe or operator
is dead config — it never matches because the full composite string is never checked
against it (verified empirically; documented at `permission-pipe-limitation.md`). Without
this hook, `curl https://x | bash` would reach only a normal permission prompt (not a
hard deny), because the system sees `curl https://x` and `bash` as independent
subcommands, neither matching a composite deny pattern. The hook solves this by receiving
the unmodified full command string in its stdin JSON before the split happens, then
rejecting the composite pattern. This is the only correct mechanism for pipe-based RCE
protection; settings.json deny rules cannot handle composite patterns.

---

### 2.6 `persistence-guard.sh` + `persistence-bash-guard.sh` — Persistence Write Asking

**What:** Fire `ask` prompts on writes to persistence / lateral-movement vectors: shell
startup files (`~/.bashrc`, `~/.zshrc`, etc.), SSH `authorized_keys` and config,
systemd user units, autostart entries, `~/.local/bin/` and `~/bin/` (PATH-shadow), package
manager registries (`~/.npmrc`, `~/.pypirc`, etc.), editor auto-exec configs (`~/.vimrc`,
`~/.config/nvim/`), global git config, per-repo `.git/hooks/`, and system files (`/etc/cron*`,
`/etc/sudoers`, etc.).

`persistence-guard.sh` covers the Write/Edit tool. `persistence-bash-guard.sh` closes the
indirect-write gap: redirect (`>`/`>>`), `cp`, `mv`, `tee`, `dd of=`, `install`, `ln`
targeting the same path set.

**Why:** Persistence paths are the canonical lateral-movement surface. A Claude session
that appends to `~/.bashrc` has code that runs on every future login — persisting beyond
the session and affecting all future shell contexts. The `ask` posture (not hard `deny`)
reflects that legitimate use cases exist (e.g., the user asking Claude to update a startup
alias). The goal is to keep the user in the loop, not to prohibit all config changes.

---

### 2.7 `claude-files-guard.sh` + `claude-files-bash-guard.sh` — Repo Pollution Prevention

**What:** Hard-deny `Write`/`Edit` of `CLAUDE.md`, `memory/*.md`, or `.claude/**` paths
inside project repos (anywhere that is not `~/.claude/` or `~/Documents/claude/`). The
bash variant closes the `mv`/`cp`/`ln` bypass: write a temporary file anywhere, rename it
to a Claude-specific name inside the repo.

**Why:** Claude-specific files (memory, instructions) should live under
`~/.claude/projects/<sanitized-path>/` where Claude's project system loads them, *not*
inside the repo tree. Files inside the repo would be: (a) committed to git and pushed to
the remote, potentially exposing internal context to teammates or a public remote; (b)
loaded in ways that conflict with the project system's path-based isolation; (c) hard to
clean up across branches and worktrees. The guard enforces the correct location in the
deny message rather than silently allowing a misplacement.

---

### 2.8 `sensitive-file-guard.sh` + `secret-scanner.sh` — Content-Level Protection

**`sensitive-file-guard.sh`:** Denies writes to files whose name matches sensitive
patterns (`.pem`, `.key`, `.p12`, `.pfx`, `.crt`, `credentials*`, `secrets*`).

**`secret-scanner.sh`:** Scans the content of Write/Edit/Bash commands for known
credential patterns (Anthropic/OpenAI/AWS/GitHub/Slack keys, private key PEM blocks,
database connection URIs with embedded passwords). Fires on match.

**Why:** Belt-and-braces for secrets that are present in content rather than path. The
primary defense is credential-path blocking (§2.4); these two handle the remaining surface
where a secret appears in a file being written (not read) or in an inline Bash command.

---

## 3. Settings Philosophy

### 3.1 Sandbox

The bubblewrap (`bwrap`) sandbox is enabled (`sandbox.enabled: true`). It provides a
second containment layer for the Bash tool — restricting filesystem write access to
declared allowed paths, enforcing `denyRead` on credential paths, and running Bash with
limited capabilities.

**Known limitation:** the sandbox uses Linux user namespaces (via `bwrap`), which requires
an AppArmor profile exception on Ubuntu 24.04 (see `infrastructure/system/apparmor-bwrap-userns.md`
for the fix). Without that profile, `bwrap` fails to create a loopback interface and every
Bash call dies.

**Docker socket tension:** the bwrap sandbox strips supplementary groups when entering the
user namespace, so the `docker` group GID is dropped even if the user holds it on the
host. This means `docker.*` commands from inside the sandbox cannot reach the unix socket.
This is a separate problem from permission rules and cannot be fixed by adjusting guards
(see §7, open question #3).

### 3.2 Permission Precedence — Deny Beats Allow

The permission engine evaluates `deny` rules before `allow` rules, regardless of
specificity. This is a documented behaviour, not a nuance. Consequences:

- An `allow: Bash(rm -rf ~/.tmux/plugins/*)` rule cannot carve an exception from
  `deny: Bash(rm -rf:*)` — the deny fires first and wins.
- Narrowing a deny requires *editing the deny*, not adding an allow.
- Adding an allow rule is always additive and cannot regress a sibling deny.

This asymmetry governs all permission design decisions: additive allow changes are safe;
deny changes require explicit coverage proofs.

**Implication for the pipe-RCE case:** A deny rule written as `Bash(curl * | sh*)` is
dead config — it never matches because the engine sees `curl ...` and `sh` as independent
subcommands, neither of which matches the composite pattern. With `curl` and `bash` each
individually allowed, `curl | bash` slips through to a permission prompt, not a hard deny.
Composite pipe/operator patterns must be handled in PreToolUse hooks that check the
unmodified command string before splitting (see §2.5).

### 3.3 Deny > Allow > Prompt Architecture

The rule stack from most to least permissive:

1. **Explicit deny (settings.json):** hard-refuse; no user prompt.
2. **Hook hard-deny (`deny_hook`):** hard-refuse with explanation.
3. **Hook ask (`ask` permissionDecision):** surface to user, await approval.
4. **Explicit allow (settings.json):** run without prompting.
5. **`autoAllowBashIfSandboxed: true`:** when the sandbox is enabled, Bash commands not
   matching any deny/allow rule run without a per-call prompt; the sandbox is the
   containment layer.
6. **Default tool allow/deny from Claude Code itself.**

The target signal-to-noise ratio: every surviving prompt should be meaningful (user needs
to make a real decision). Guards that fire on safe, routine actions train the operator to
reflexively approve and erode trust in the load-bearing denies. Removing ergonomic
over-blocks *strengthens* the security posture by reducing approval fatigue.

### 3.4 Global vs. Local Settings Split

The hierarchy from lowest to highest precedence: global (`~/.claude/settings.json`) →
project-local (`.claude/settings.json`) → machine-local (`settings.local.json`) → CLI
args → Managed.

Design rule: **all portable policy lives in global.** Permissions, hooks wiring,
plugin flags, theme, effort level, output style — all global. Machine-local
(`settings.local.json`) holds only machine-specific overrides (absolute path adjustments,
experimental flags) and is kept minimal or empty. The split means a fresh machine that
installs global `settings.json` from the notes vault gets the full policy immediately,
with only the path-specific fields needing post-install parameterisation.

**Staleness hazard:** `/config` slash commands and `/model`, `/effort`, `/tui`, `/voice`,
`/focus` all write to global `~/.claude/settings.json`. The file can drift silently from
the notes-vault copy without a capture/apply loop. This is tracked as an open question
(§7).

### 3.5 Auto-Mode and defaultMode

`defaultMode` in `settings.json` controls whether Claude operates in auto or ask mode by
default. Auto mode reduces per-action prompts; ask mode maximises human oversight but
becomes unusable at scale. The current posture uses selective auto-mode with guards as the
real control surface: the model is free to run routine operations without per-action
prompts, and guards intercept only the high-risk categories.

---

## 4. Memory / Sessions / Portability

### 4.1 Memory Model

Global memory files live at `~/.claude/projects/-home-<user>/memory/*.md`. They carry
YAML frontmatter with `name`, `description`, `type`, and `originSessionId`. Claude Code
loads them at session start; the harness computes a staleness warning from internal mtime.

Per-project memory lives at `~/.claude/projects/<sanitized-path>/memory/`. Claude derives
the project key from the working directory path — a machine-keyed slug that changes on
username or path change. This means project memories are not portable by default across
machines with different `$HOME` or username.

The target convention is `last_updated: YYYY-MM-DD` in YAML frontmatter, used for conflict
resolution: when two facts conflict, prefer the file with the newer `last_updated`. Without
this field, staleness detection relies on the harness's internal clock approximation.

### 4.2 Session Transcript Storage and Portability

Session transcripts are JSONL files under `~/.claude/projects/<slug>/`.
They are **not portable by design** — large (hundreds of MB), machine-keyed, and primarily
useful for `--resume` and Rewind within the same machine. The authored content *inside*
sessions (plans, diffs, memory updates) should be promoted to the notes vault or project
repos as it is produced; relying on transcripts as a knowledge store creates a
loss-on-machine-change risk.

**Session naming:** using `/name <description>` within a session makes transcripts
findable. Sessions without names are indexed only by UUID.

### 4.3 The Portability North Star

The goal is that a fresh machine (or Docker development container) running
`post-install.sh` from the notes vault arrives at a fully functional Claude Code setup
with identical guards and policy. This requires:

1. All authored portable files (`~/.claude/hooks/`, `CLAUDE.md`, `settings.json` policy
   fields, `commands/`, `skills/`, `bin/bless`, `statusline-command.sh`) to live
   canonically in `infrastructure/claude/` in the notes vault.
2. Machine-specific fields in `settings.json` (absolute paths in
   `permissions.additionalDirectories`, `statusLine.command`, `sandbox.filesystem.*`)
   templated as `${HOME}/...` placeholders, filled at install time.
3. A `capture.sh` script that syncs live `~/.claude/` authored files to the vault,
   surfacing drift.
4. A `verify-sync.sh` that exits non-zero if vault and live differ — runnable on demand
   and as a session-start hook.

This is the **carry-across-machines north star**. As of 2026-05-30 it is partially
implemented: the vault holds copies of most hooks and commands, but they are drifting from
live (no capture loop exists yet) and `CLAUDE.md` is not in the vault. The portability
work is open (see §7).

---

## 5. Design Principles

The following principles recur across the setup and are worth stating explicitly as they
are easy to violate during one-off configuration sessions.

1. **Deny beats allow, unconditionally.** No allow can override a deny. Design new
   permissions around this: if you want a narrower restriction, edit the deny, don't add
   an allow on top.

2. **Guards are defense-in-depth, not user-discipline.** The controls exist so the user
   does not have to manually audit every action. A guard that fires only when the user
   "forgets" to watch is not a guard — it is a reminder, and reminders fail under load.
   Guards must work even when the user is not watching.

3. **Every surviving prompt must be meaningful.** Guards that fire on routine safe
   operations train reflexive approval and destroy the signal value of real prompts.
   Ergonomic over-blocks should be removed; load-bearing controls should be kept. The
   distinction is: does blocking this action provide genuine security value as written, or
   does it merely inconvenience legitimate work?

4. **Review every diff before committing.** Claude is not authorised to commit unless
   explicitly asked. This applies even when working in sub-agents on feature branches.
   Convention: conventional commit format (`feat:/fix:/chore:/docs:/refactor:/test:`),
   no co-author trailers.

5. **Sonnet for sub-agents; lean main thread.** Dispatch sub-agents with Sonnet by
   default. Reserve the main orchestrating thread (and advisor reviews) for Opus. Heavy
   file exploration and bulk edits belong in sub-agents — their context churn stays out
   of the main thread.

6. **Prefer hooks for composite patterns; deny rules for simple prefix patterns.** The
   permission engine cannot handle pipeline composition (`cmd1 | cmd2`), operator chaining
   (`cmd1 && cmd2`), or argument-position reasoning. Anything requiring those capabilities
   must live in a PreToolUse hook, not a settings.json deny rule. See
   `permission-pipe-limitation.md`.

7. **The enforcement layer is immutable from within a session.** `settings.json`,
   `hooks/*`, and `bin/*` cannot be modified by Claude in the same session that might
   benefit from their relaxation. This is the root principle behind settings-lock and
   claude-self-guard. Any change to the enforcement layer must be made by the user,
   outside Claude, with deliberate intent.

8. **Secrets never enter context.** Credentials should not be read by Bash tools, written
   into files Claude edits, or appear in Claude-authored script content. They are
   categorically out of scope for Claude operations. If a workflow requires credentials,
   the user handles that step manually and relays only non-secret results to Claude.

9. **Worktree-first for non-trivial work.** Feature work happens in dedicated worktrees,
   never in the main checkout. The main clone stays clean on the default branch. This
   prevents session-scope contamination and makes rolling back straighforward.

---

## 6. The Audit and Telemetry Layer

`audit-log.sh` writes a JSONL record of every Bash/Write/Edit/MultiEdit event (both
PreToolUse and PostToolUse) to `~/.claude/audit.jsonl`. The log includes command text with
common credential shapes redacted before writing. File writes are logged with SHA-256 hash
and byte count post-write.

The audit log currently has **forever retention** with no rotation policy. This is flagged
as an open question (§7, #8).

`stats.sh` is a shared library sourced by ~12 hooks to record per-hook invocation counts
in `hook-stats.jsonl`. Useful for identifying which guards are firing most frequently and
tuning ergonomic over-blocks.

---

## 7. Open Questions / Unresolved Tensions

These are the design questions still open as of 2026-06-01, in priority order.

1. **`hooks-lock.sh` not yet built.** `claude-self-guard.sh` currently provides ask-mode
   protection on `~/.claude/hooks/*`, but it is not a hard deny. The tagger explicitly
   skips hooks/ pending a dedicated `hooks-lock.sh`. Until it exists, a session where the
   user approves a hook edit has no secondary check. The `workflow_pending_cleanup.md`
   entry from 2026-05-01 tracked this. Design question: should it be a hard deny (no
   in-session hook edits ever) or ask-with-explanation (current pattern, user approves)?

2. **`rm -rf` blanket deny vs. path-scoped narrowing.** `Bash(rm -rf:*)` and its spelling
   variants are a blanket deny with no path scope — they block legitimate scratch-dir and
   plugin-reinstall cleanups as well as dangerous targets. Three options were analysed in
   Appendix 26: (A) leave as-is; (B) replace with a path-anchored deny set covering
   dangerous targets (known gap: `cd /dangerous && rm -rf .` evades string matching);
   (C) treat as non-issue and run cleanups manually. The chaining gap in Option B means
   B is not a security-neutral change — it trades hard-deny coverage for ergonomics.
   Decision pending.

3. **Docker socket / bwrap group stripping.** The bwrap sandbox strips supplementary
   groups on entering the user namespace, removing the `docker` GID. Every `docker`
   command from inside the Bash tool fails with socket permission denied. Options: (a)
   sandbox exception preserving the GID; (b) add the socket to the sandbox allow-list and
   relax socket permissions; (c) `docker context` over TCP/SSH instead of unix socket; (d)
   accept and use paste-relay for docker commands. Options (a) and (b) give every Claude
   Bash call effective root on the host via volume mounts — a genuine host-security
   tradeoff, not just friction. Decision pending.

4. **CLAUDE.md cross-worktree strategy — Pattern A/B/C/D.** Claude's hierarchical
   CLAUDE.md loading is strict per filesystem path; worktree sessions do not automatically
   load the main checkout's CLAUDE.md. Four patterns were validated (see
   `worktree-context-loading.md`): (A) per-worktree copy; (B) artifacts-dir symlinks;
   (C) setup-script wiring; (D) committed repo-root file. Pattern D requires a
   team-visibility decision (is this file appropriate for teammates to see?). Decision
   pending; current state is per-slot copy with no automation.

5. **Ask-mode vs. hard-deny calibration for `claude-self-guard`.** The hook fires an
   `ask` prompt (not a hard deny) for hooks-dir and bin-dir edits. In a session where the
   user explicitly asks Claude to update a hook, approving the prompt is correct behaviour.
   But the ask prompt could also be approved reflexively or by a confused user. Should
   hooks-dir edits be hard-denied (unconditionally user-terminal-only, matching
   settings-lock) or remain ask-mode? Tension: hard deny is safer but removes a valid
   workflow; ask-mode is more usable but relies on the user not approving carelessly.

6. **Audit log retention / unbounded growth.** `audit.jsonl` has forever retention. On an
   active machine this file grows without bound. No rotation, truncation, or archival
   strategy has been defined. Practical concern: log is useful for debugging/auditing;
   wholesale deletion loses history. Options: size-based rotation; time-based rotation;
   compression + archive; keep but add a session-start size warning.

7. **Docker lifecycle command prompting revisit.** A three-tier decision was made
   deliberately on a prior date: narrow allowlist for inspect/log commands, lifecycle verbs
   (`up`, `restart`, `build`, `pull`, `start`, `stop`) still prompt. The rationale at the
   time was that lifecycle verbs should be visible in the audit log and require conscious
   approval. This decision is open for revisit as the workflow evolves — but it is a
   *deliberate* prior decision, not a gap.

8. **Project memory portability under machine-keyed paths.** Claude derives the project
   slug from the working directory path. A machine with a different username or `$HOME`
   path creates a different slug, making old memories invisible. Three strategies: commit
   `memory/` inside project repos (travels with repo, team-visible if pushed); commit
   to the notes vault under a stable key with a restore script; leave out of scope and
   treat memories as machine-local. No decision made.

9. **Memory `last_updated:` convention adoption.** A `last_updated: YYYY-MM-DD` frontmatter
   field was proposed as the standard for memory files, enabling model-readable conflict
   resolution. Six existing files can be backfilled with filesystem mtime as an
   approximation. Convention adoption and backfill pending user approval; the harness's
   own "N days old" warning remains the fallback until this lands.

10. **Settings live-vs-vault drift and source-of-truth model.** `~/.claude/settings.json`
    (live) and `infrastructure/claude/settings-template.json` (vault) diverge silently
    after every `/config`, `/model`, or `/effort` session command. No capture loop exists.
    The live file is 610 lines; the vault template is 340 lines and significantly stale.
    Decision: which direction is canonical (live-to-vault via `capture.sh`, or
    vault-to-live via `post-install.sh`)? Related: four fields in `settings.json` embed
    absolute paths that must be parameterised before the file can be committed to a public
    vault.

11. **`autoAllow` safety is transitively staked on an ask-only hook layer (surfaced by
    Gate 0, 2026-06-01).** With `autoAllowBashIfSandboxed: true` (§3.3 rule 5, §3.5), any
    Bash command not matching an explicit deny/allow runs without a prompt — so the *only*
    thing re-gating dangerous-but-unlisted commands (the docker container-escape flags
    closed at Gate 0 via `docker-escape-guard.sh`, plus `pipe-rce-guard.sh` and the other
    high-risk categories) is the PreToolUse **hook layer**. The hooks are the real control
    surface here, not `settings.json`. But that layer is itself protected only by
    `claude-self-guard.sh` in **ask mode**, not a hard deny — `hooks-lock.sh` still does not
    exist (see #1, #5). Residual: a prompt-injected/rogue session that gets a single hook
    edit *approved* could neutralise the very guard that makes `autoAllow` safe, after which
    `autoAllow` would silently run the now-unguarded command. This introduces no new gap so
    much as it **raises the priority of #1 and #5** — before Gate 0 they were abstract; now
    they are the sole backstop for a live auto-run posture. Until `hooks-lock.sh` lands
    (hard-deny on `hooks/*` and `bin/*`), the load-bearing assumption is operator
    discipline: never approve a hook/bin edit you did not originate. Decision pending;
    tracked with #1/#5.

---

## 8. Workflow-Tiered Access (2026-06-11)

### Two-tier model

The guard system now operates in two named tiers aligned to the two real workflows:

**INVESTIGATION tier** (unsandboxed primary clones): the working mode for debugging,
reading logs, inspecting APIs, exploring other branches. Loosens interpreter one-liners,
network reads, and cloud/k8s/container read CLIs — the friction that impeded investigation
work. Keeps hard denies on writes, installs, and persistence (cheap to enforce there;
investigation sessions don't need them).

**BUILD tier** (sandboxed worktrees): the working mode for implementing, running, and
shipping. Loosens project-local installs (tagged so they can't silently run unsandboxed
later) and waives the bless gate for Claude-authored scripts within the sandbox (tag kept
for the unsandboxed re-run check). Keeps the sandbox network allowlist as the egress
filter.

### The hard constraint: deny beats allow, so tier-dependent rules live in hooks

`deny` always wins regardless of specificity — a worktree's `settings.local.json` cannot
relax a global deny. Anything that must differ by tier therefore lives in hook scripts that
branch on `is_sandboxed()` rather than in settings rules. `is_sandboxed()` (in `stats.sh`)
walks up from `$CLAUDE_PROJECT_DIR` to the nearest `.claude/settings.local.json` and reads
`sandbox.enabled`. It is **fail-closed**: absent file, parse error, missing `jq`, or any
ambiguity → treat as unsandboxed (strict tier). Hooks run outside bwrap, so this detection
is feasible and reliable.

### Keystone rule: sandbox allowWrite must never include hooks/bin/settings

The sandbox's `filesystem.allowWrite` must never include `~/.claude/hooks/`, `~/.claude/bin/`,
or `~/.claude/settings*.json`. Hooks run *outside* the sandbox (PreToolUse fires before the
command spawns), so sandboxed code has no hook watching writes inside hooks/. A single
allowed interpreter one-liner writing to a hook file would silently disable a guard for all
future commands. The allowWrite list is narrowed to writable data paths only (projects/,
plans/, tasks/, audit.jsonl, etc.); the enforcement layer is immutable from within any
session.
