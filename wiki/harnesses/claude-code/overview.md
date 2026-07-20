# Claude Code

**Claude Code is the harness foundry builds on and hardens — so we keep our own annotated understanding of it: its lifecycle, the hooks we design for it, how we guard it, and its quirks.** We link to the official docs but hold our own version, because our hooks and processors need a shared map to point at ("this acts *here*").

> **Status:** stable

## What a harness is

A **harness** is the runtime that runs the agent. Claude Code is one; others could come later, which is why this lives under `harnesses/`. Everything about the Claude Code harness lives here.

## What's here

- **[Lifecycle](lifecycle)** — the ordered events a session moves through, and the canonical diagram every hook points at.
- **[Hooks](hooks/overview)** — the hook estate: the classes of hooks we've built and where each fires.
- **[Guardrails](guardrails/overview)** — the security / hardening posture.
- **[Field notes](field-notes/clipboard-osc52)** — investigated Claude Code behavior.

## Our stance vs the official docs

The official [Claude Code hooks reference](https://code.claude.com/docs/en/hooks) is the source of truth for *what events exist*. Our pages add what it doesn't: *which of those we hook, why, and how they compose* — annotated onto one shared lifecycle so a reader can see where every foundry hook acts.

## See also

- [Lifecycle](lifecycle) · [Hooks](hooks/overview)
