---
title: Home
category: reference
status: draft
summary: Landing page and index for the foundry wiki.
sources: [README.md, CLAUDE.md]
related: [Glossary, Roadmap, Architecture Overview]
updated: 2026-07-20
---

# foundry wiki

Piyush's agentic-infrastructure monorepo — the durable ideas, architecture, and
vocabulary behind the plugin marketplace and the libraries / MCP servers / apps
that feed it. This wiki is the consolidated home for cross-cutting ideas that
used to be scattered across `docs/`, bundle design sets, and issues.

> **Source model:** these pages are authored in-repo under `wiki/` (folders +
> frontmatter, PR-reviewable) and published to the GitHub wiki as-is.

## Sections

- **[Taxonomy / Glossary](taxonomy/glossary.md)** — the shared vocabulary: what
  the nouns mean and how the verbs relate.
- **[Roadmap](roadmap/roadmap.md)** — what we want to build; parked and shelved ideas.
- **[Architecture](architecture/overview.md)** — decisions, structures, and the
  core architecture of what's been built.
  - [Why bundling](architecture/bundling/why-bundling.md) · [Versioning](architecture/bundling/versioning.md) · [Decisions ledger](architecture/decisions-ledger.md)
  - Systems: [manifold / KAOS](architecture/manifold/overview.md) · [crucible](architecture/crucible.md) · [meditate](architecture/meditate/memory-model.md) · [plan-orchestrator](architecture/plan-orchestrator.md) · [cartographer](architecture/cartographer.md)
- **[What currently exists](reference/what-exists.md)** — the living catalog.
- **[Field notes](field-notes/clipboard-osc52.md)** — investigated Claude Code behavior.
