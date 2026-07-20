# Hooks

**foundry ships a set of hooks that attach to the Claude Code lifecycle to guard, augment, and observe a session.** This page maps them by *class* onto the [lifecycle](../lifecycle) — one document per class, so a reader sees what fires where and why.

> **Status:** draft — most `home/hooks` are authored but currently unwired (see roadmap, Issue #3). The classes below are the organizing plan.

## Classes of hooks

One page per class. Each says: purpose · how it works · why this choice, not another.

| Class | Fires at | Purpose |
|---|---|---|
| **Guard hooks** | PreToolUse, UserPromptSubmit | block dangerous actions (RCE, secret reads, escapes) before they run — see [guardrails](../guardrails/overview) |
| **[Compaction hooks](compaction-hooks)** | PreCompact / PostCompact / SessionStart | preserve durable memory across the compaction boundary |
| **Session hooks** | SessionStart, SessionEnd | inject context on start, clean up on end |
| **Quality hooks** | Stop, PostToolUse | enforce commit hygiene, run checks, tag artifacts at turn boundaries |
| **Logging hooks** | Notification, Stop | append an audit trail of session activity |

## Why a class, not a hook, per page

Hooks in a class share a lifecycle attachment point and a rationale; documenting the class keeps the *why* in one place. A single load-bearing hook (e.g. the pipe-RCE guard) can graduate to its own page when it outgrows its class section — lazy growth.

## Status of the estate

The `home/hooks` set (~33 scripts) is authored but not yet wired into `settings.json`. Wiring, per-hook verdicts, and a test methodology are tracked as Issue #3; the per-class pages here fill in as that work lands.

## See also

- [Lifecycle](../lifecycle) — where each class attaches.
- [Guardrails](../guardrails/overview) — the guard-hook posture.
