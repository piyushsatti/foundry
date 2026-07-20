# Libraries

**Some things we build are reused across plugins but aren't shipped as a plugin themselves — a shared markdown tool two plugins call, a common skill, a helper package.** They need a home that isn't `plugins/`; this is it.

> **Status:** draft — no shared library documented yet; this page states where one will go.

## What belongs here

A capability lives in `libraries/` when it is **used by more than one plugin and isn't a shipped plugin on its own**. It maps to the [`library`](../glossary) noun and to the repo's `library/` (shared skills/agents) and shared `packages/`.

## The rule that keeps it clean

- **Subject-owned parts stay with their subject.** manifold's engine library and web app document *within* [`plugins/manifold/`](../plugins/manifold/overview) — you still find everything about manifold in one place. Only **cross-plugin** shared things live here.
- **A capability moves here when a second plugin needs it** — the Rule of Three, same as code promotion (see [distribution/bundling.md](../distribution/bundling)). A day-one shared library is indirection with no reuse yet.

## Limits

Empty until a real cross-plugin capability exists — lazy growth, no scaffolding ahead of content.

## See also

- [Distribution / bundling](../distribution/bundling) — the Rule of Three.
- [Glossary](../glossary) — the `library` noun.
