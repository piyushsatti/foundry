# Guard Hooks

**Guard hooks block dangerous actions at PreToolUse, before they run — the defense-in-depth layer that treats Claude as a potentially rogue or prompt-injected actor.** They are the largest class: 16 of the estate.

> **Status:** draft — authored, mostly unwired (roadmap, Issue #3).

## The problem

A single Bash or Write can exfiltrate a credential, escape a container, or corrupt the enforcement layer itself — and a prompt-injected session will try. Permission rules can't catch it: they can't express composite-command patterns (a pipe splits the matcher — see [permission pipe](../guardrails/permission-pipe)). Guards intercept at PreToolUse, where they see the full command, and deny or ask before it executes.

## What they protect

Each guard attaches at PreToolUse (Bash / Write / Edit), inspects the tool input, and fails closed. Grouped by what they defend:

- **Secrets & credentials** — `bash-cred-read-guard` (reads of `.ssh`/`.aws`/token CLIs), `secret-scanner` (secret material in writes/commands), `sensitive-file-guard` (`*.pem`, `*.key`, `*credentials*`).
- **Container & host escape** — `docker-escape-guard` ("Gate 0": `--privileged`, host namespaces, `docker.sock` mounts), `pipe-rce-guard` (`curl … | sh`, `bash <(…)`), `unsandboxed-install-guard` (re-denies local installs when unsandboxed).
- **Persistence & lateral movement** — `persistence-guard`, `persistence-bash-guard` (rc files, ssh keys, git hooks, systemd, PATH), `cwd-drift-guard` (bare leading `cd`).
- **The enforcement layer** — `settings-lock`, `claude-self-guard` (Claude editing its own settings/hooks/bin).
- **Claude's own files** — `claude-files-guard` and `claude-files-bash-guard` (the latter closes the `cp`/`mv` rename bypass), `ai-artifact-guard`, `xattr-guard` (gates authored files until blessed).
- **Source of truth** — `test-file-guard` (tests aren't edited unless asked).

## Why deny at PreToolUse, not permissions

Deny-beats-allow, and the hook sees the whole command where a permission matcher sees only fragments. That's what makes pipe-to-shell and rename bypasses catchable at all — the guardrails posture in one sentence.

## Open questions

- `settings-lock` and `claude-self-guard` overlap: `settings-lock`'s header says it's "intentionally disabled" per `claude-self-guard`, yet it still carries active deny logic — possibly mid-migration; worth an audit when wiring.
- `xattr-guard` depends on the [quality](quality-hooks) taggers having stamped files first — the two form one system spanning Pre- and PostToolUse.

## See also

- [Guardrails](../guardrails/overview) · [Permission pipe](../guardrails/permission-pipe) · [Lifecycle](../lifecycle)
