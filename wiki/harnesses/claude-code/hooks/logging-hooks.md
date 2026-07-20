# Logging Hooks

**Logging hooks write the audit trail — a redacted JSONL of tool events and a rotating session-summary log — so session activity is reviewable after the fact, not only by re-reading transcripts.**

> **Status:** draft — authored, mostly unwired (roadmap, Issue #3).

## The problem

Guards block the worst actions in the moment, but a human overseeing a fleet still needs to see what happened — who ran what, which files changed, when. Without a durable trail, review means scrolling transcripts, which doesn't scale.

## How it works

- **`audit-log`** — writes JSONL of Bash/Write/Edit/MultiEdit events with credential redaction and per-file sha256 + byte count. It is the one hook attached to two phases at once: **PreToolUse** (the intent) and **PostToolUse** (the result), branching on whether a `tool_response` is present.
- **`session-log`** — appends a deduplicated summary line (cwd, branch, last commit) to `session-log.md` at **Stop**, rotating at 2000 lines.

## Why append-only and redacted

An audit trail is only useful if it's trustworthy and safe. **Append-only** so it can't be quietly rewritten; **redacted** so the log itself never becomes the secret leak it's meant to help catch.

## Open questions

- No hook uses `SessionEnd`; `session-log` approximates it with `Stop` plus dedup (Stop fires on every turn stop, not true session end). A real `SessionEnd` hook would be cleaner.

## See also

- [Lifecycle](../lifecycle) · [Guardrails](../guardrails/overview)
