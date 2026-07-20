---
title: Organization
status: stable
summary: How the wiki is structured — the folder tree is the index.
sources: []
updated: 2026-07-20
---

# Organization

**The folder tree IS the index.** Reading `wiki/` tells you what exists — the domains, features, and ideas. There is no separate "what lives where" page; the layout answers that.

## Rules

- **Group by domain.** A domain is a top-level folder (`distribution/`, `manifold/`). Mechanisms are *files* inside it (`distribution/bundling.md`), never top-level folders of their own.
- **Subject-scoped.** Everything about a subject — including its decisions and tradeoffs — lives in that subject's folder. Nothing subject-specific sits at root.
- **Grow lazily.** Start topics as `.md` files in a domain folder. Only pre-create structure you're filling now.
- **Root stays minimal.** Only genuinely cross-cutting pages (e.g. `glossary.md`) and `meta/` live at root.

## Split a file vs. make a subfolder

| Situation | Do this |
|-----------|---------|
| One page is getting long (> ~2 min read) | Split into a sibling `.md` in the same domain folder |
| A single topic has grown to several pages | Promote that file to its own subfolder (`manifold.md` → `manifold/`) |
| Anything else | Leave it as one file |

Promote only when a topic outgrows one page. Don't build empty scaffolding ahead of content.
