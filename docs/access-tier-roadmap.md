---
title: Claude Code access-tier roadmap (wants, not-yet-scheduled)
last_updated: 2026-06-11
type: roadmap
status: wishlist — none implemented; capture for evolution
related:
  - 2026-06-11-config-baseline.md
  - design-philosophy.md
---

# Access-tier roadmap

Desired future capabilities/constraints for the Claude Code guard system, captured so they
evolve deliberately rather than ad-hoc. **None of these are implemented yet** — they are wants,
not needs. When one is picked up, move it into a dated plan doc, red/blue review it, and
implement tighten-first like the 2026-06-11 redesign. The live tiers today are INVESTIGATION
(unsandboxed primary clones) and BUILD (sandboxed worktrees) — see the plan + design-philosophy.

---

## W1 — `/mnt/*` is read-only (deny all writes)
**Intent:** Claude may *read* anything under `/mnt/` (network shares, automounts, external disks)
but must never *write/delete/modify* there.

**Why:** `/mnt` mounts are usually shared/production data (NAS, mounted volumes). Reads are safe
for investigation; writes risk clobbering shared state that isn't under version control or review.

**Implementation sketch (both tiers — important, because /mnt writes must be blocked in
unsandboxed INVESTIGATION sessions too, where the sandbox isn't enforcing):**
- BUILD tier (sandboxed): `sandbox.filesystem.denyWrite: ["/mnt"]` — OS-enforced, covers child
  processes. Reads remain allowed (default read policy). Cheap, robust.
- INVESTIGATION tier (unsandboxed): the sandbox doesn't apply, so add a `mnt-write-guard.sh`
  PreToolUse Bash hook (sibling of persistence-bash-guard) that denies write-capable ops
  (`>`/`>>`, `tee`, `cp`/`mv`/`rm`/`install`/`ln`/`truncate`/`dd of=`, `sed -i`, interpreter
  writes) whose target path resolves under `/mnt/`. Reuse the settings-lock operator regex +
  realpath resolution. Pattern fragment belongs in `hooks/patterns.sh` (e.g. `CC_WRITE_OPS`).
- Also consider an `Edit`/`Write` deny rule for `//mnt/**` so the file tools (not just Bash)
  are covered.

**Open questions:** which `/mnt` subpaths (if any) are legitimately writable and need carve-outs;
whether to deny at `/mnt` or per-mount; interaction with `dangerouslyDisableSandbox` escape hatch.

**Quick-win note:** the BUILD-tier half (`denyWrite: ["/mnt"]`) is a one-line, low-risk add
whenever wanted; the INVESTIGATION-tier hook is the real work.

---

## W2 — SSH "read-only, copy-then-read" tier
**Intent:** Claude can *pull data from* a remote host over SSH to inspect it, but cannot run
arbitrary remote commands, cannot mutate the remote, and reads remote data only **after copying
it locally** — i.e. the workflow is: discover → copy to a local scratch dir → read locally.
Never read-in-place by executing on the remote beyond the minimum needed to locate/fetch.

**Why:** Investigation often needs logs/configs/artifacts that live on remote boxes, but a raw
`ssh host <anything>` is full remote code execution. The want is the *read* affordance without
the *execute/write* blast radius, and a forced local-copy boundary so all actual reading happens
on files under local review/audit (and under the existing xattr/tag machinery).

**Implementation sketch (hard — ssh is RCE by nature, so this needs a parsing guard):**
- Allow fetch verbs that pull remote→local only:
  `scp <user@host>:<path> <local>`, `rsync <user@host>:<path> <local>` (and `rsync -avz` read
  direction). DENY the upload direction (`scp <local> host:...`, `rsync <local> host:...`).
- For `ssh host <cmd>`: deny by default. Optionally allow a narrow read-only remote command
  allowlist (`ls`, `find`, `cat`, `tail`, `stat`, `du`, `test -e`) purely to *locate* files
  before copying — enforced by a hook that parses the remote command string and rejects anything
  not in the allowlist (and rejects shell metacharacters `;`/`|`/`&&`/backticks/`$(`).
- Force the copy-then-read boundary: designate a local scratch root (e.g. `~/.claude/ssh-pull/`
  or a per-session `$TMPDIR` subdir); the guard ensures `scp`/`rsync` destinations land there;
  the model reads from there. Tag pulled files (xattr) so they re-gate if executed.
- Deny remote mutation entirely: any `ssh ... 'rm|mv|cp|>|tee|install|systemctl|kill|...'` denied.
- Credentials: must not expose `~/.ssh` keys to a sandboxed/in-process reader — `denyRead`
  `~/.ssh` already set; keep it. SSH agent socket only, no key file reads.

**Open questions / risks:**
- ssh remote-command parsing is the crux — a remote command allowlist is bypassable via
  quoting/env tricks; treat the read-only-remote-command piece as best-effort and lean on
  "deny ssh exec by default, allow only scp/rsync fetch" as the safe core.
- Which hosts? An allowlist of permitted `user@host` targets (config-driven) is probably wanted,
  so Claude can't ssh to arbitrary hosts.
- Should this be its own permission tier toggled per-session, or always-on guards? Likely guards
  + a host allowlist, gated so it only activates when explicitly doing remote investigation.
- Interaction with the network allowlist (ssh is port 22, not the HTTP proxy — sandbox network
  domain allowlist does NOT cover raw ssh/scp; needs the hook layer, not the sandbox).

---

## How to evolve this file
Add new wants as `W3`, `W4`, … with the same shape: intent / why / implementation sketch /
open questions / status. When promoting to implementation, link the dated plan doc here and flip
status. Keep the security framing (rogue-Claude threat model, tighten-first, fail-closed).
