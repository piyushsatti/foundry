# Compaction Hooks

**When Claude Code compacts context, anything not re-established is lost — so compaction hooks preserve durable memory across that boundary.** They fire around the [lifecycle](../lifecycle)'s compaction phase and on the next session start.

> **Status:** draft

## The problem

Compaction shrinks the running context to fit the window. Whatever mattered but wasn't written somewhere durable — decisions, open threads, injected memory — disappears when the old context is dropped. A session can silently lose the thread mid-task.

## How it works

- **PreCompact** — before compaction, capture what must survive (write it to a durable file, not just context). *Can block*, so it can defer or annotate a compaction.
- **PostCompact / SessionStart** — re-inject the preserved memory into the fresh context.

The load-bearing detail: **SessionStart-on-compact is the durability primitive** — the reliable re-injection point — a finding from [meditate](../../../plugins/meditate/overview). PostCompact alone can't re-establish everything; the start hook is what rehydrates.

## Why this choice, not another

Relying on the model to "remember" across compaction fails — that's the exact thing compaction removes. Writing to a durable file at PreCompact and rehydrating at SessionStart moves the memory out of the volatile context and back in deterministically, instead of hoping it survives.

## Open questions

- Exact division of labor between PostCompact and SessionStart rehydration isn't fully settled here — see meditate's memory-architecture work.

## See also

- [Lifecycle](../lifecycle) — the compaction phase.
- [meditate](../../../plugins/meditate/overview) — the durability primitive.
