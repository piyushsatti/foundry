---
title: Organization
status: stable
summary: How the wiki is structured — the folder tree is the index, grouped by domain, decomposed as it grows.
sources: []
updated: 2026-07-20
---

# Organization

**The folder tree IS the index.** Reading the tree tells you what exists — the domains, features, and ideas. There is no separate "what lives where" page; the layout answers that. So the structure has to stay legible.

> **Status:** stable

This page covers *where a page lives*. The rest of the rulebook: [style.md](style.md) = how a page is formatted · [writing.md](writing.md) = how it reads · [page-template.md](page-template.md) = the copy-me skeleton.

## Domain vs subject

A **subject** is any topic the wiki documents. A **domain** is a *top-level* subject — a folder at the root (`plugins/`, `distribution/`). A subject can nest: `manifold` is a domain; `manifold/trajectory` is a subject within it. "The subject's folder" means wherever that subject lives, root-level or nested.

## Rules

- **Group by domain.** Mechanisms are usually *files* inside a domain (`distribution/bundling.md`) rather than top-level folders of their own. *Why:* the top level should read as a list of what foundry is, not a pile of every sub-topic.
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

## When to break these rules

The rules favor a legible tree; they're defaults, not laws.

- A mechanism can earn its **own top-level folder** if it's big or central enough that burying it as a file would hide it.
- A complex, interlinked system may be clearer as **one long page or a deeper subtree** than as many fragments. Splitting past the point of readability — pages nobody stitches back together — defeats the purpose.
- **When "split" and "keep whole" both fire:** keep it whole if a reader must hold both topics in mind at once to understand either; otherwise split.
- Decompose to help the reader, not to satisfy a count.

## See also

- [Style](style.md) · [Writing](writing.md) · [Page template](page-template.md)
