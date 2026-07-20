# Hooks

**foundry ships a set of hooks that attach to the Claude Code lifecycle to guard, augment, and observe a session.** This page maps them by *class* onto the [lifecycle](../lifecycle) — one document per class, so a reader sees what fires where and why.

> **Status:** draft — most `home/hooks` are authored but currently unwired (see roadmap, Issue #3). The classes below are the organizing plan.

## Classes of hooks

One page per class. Each says: purpose · how it works · why this choice, not another.

| Class | Fires at | Purpose |
|---|---|---|
| **[Guard hooks](guard-hooks)** | PreToolUse | block dangerous actions — RCE, secret reads, escapes — before they run (16 hooks) |
| **[Session hooks](session-hooks)** | SessionStart | inject durable memory, scope, and pending work into a fresh session (5) |
| **[Quality hooks](quality-hooks)** | PreToolUse + PostToolUse | commit hygiene, compose validation, authored-file tagging |
| **[Logging hooks](logging-hooks)** | Pre/PostToolUse + Stop | append a redacted audit trail |
| **[Compaction hooks](compaction-hooks)** | PreCompact / PostCompact | preserve memory across compaction (none wired yet; `memory-durability` is the intended one) |

## Why a class, not a hook, per page

Hooks in a class share a lifecycle attachment point and a rationale; documenting the class keeps the *why* in one place. A single load-bearing hook (e.g. the pipe-RCE guard) can graduate to its own page when it outgrows its class section — lazy growth.

## Status of the estate

The `home/hooks` set (~33 scripts) is authored but not yet wired into `settings.json`. Wiring, per-hook verdicts, and a test methodology are tracked as Issue #3; the per-class pages here fill in as that work lands.

A handful of files are **helpers, not event hooks**: `stats.sh` (the shared `deny_hook`/sandbox library), `patterns.sh` (install-path regex), `lib/memkey.sh` (memory-index functions), `stats-report.sh` (a manual CLI), and `auto-open-html.json` (a paste-ready config snippet).

## See also

- [Lifecycle](../lifecycle) — where each class attaches.
- [Guardrails](../guardrails/overview) — the guard-hook posture.
