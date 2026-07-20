---
title: Organization
status: stable
summary: How the wiki is structured — the folder tree is the index, grouped by domain, decomposed as it grows.
sources: []
updated: 2026-07-20
---

# Organization

**The folder tree IS the index.** Reading `wiki/` tells you what exists — the domains, features, and ideas. There is no separate "what lives where" page; the layout answers that. So the structure has to stay legible.

> **Status:** stable

## Rules

- **Group by domain.** A domain is a top-level folder (`distribution/`, `manifold/`). Mechanisms are *files* inside it (`distribution/bundling.md`), never top-level folders of their own. *Why:* the top level should read as a list of what foundry is, not a pile of every sub-topic.
- **Subject-scoped.** Everything about a subject — including its decisions and tradeoffs — lives in that subject's folder. Nothing subject-specific sits at root. *Why:* you find everything about X by opening `X/`, not by hunting.
- **Grow lazily.** Start topics as `.md` files in a domain folder. Only create structure you're filling now. *Why:* empty scaffolding lies about what exists.
- **Root stays minimal.** Only genuinely cross-cutting pages (e.g. `glossary.md`) and `meta/` live at root.

## Complexity is a signal to decompose

The rule behind the rules — it recurs everywhere. When something gets too big, produce a **coarse view + focused parts**; never cram, and never silently drop.

| When this gets too big | Don't | Do |
|---|---|---|
| A page (2+ topics, wants an H4) | nest deeper / cram | split into a sibling `.md` |
| A domain (many pages) | one giant folder | promote a topic to its own subfolder |
| A diagram (> ~8 nodes) | shrink the font | coarse view + per-section diagrams ([style.md](style.md)) |
| A paragraph | convolute it | break into steps or add an example ([writing.md](writing.md)) |

Promote only when a topic outgrows its current home. Don't build ahead of content.
