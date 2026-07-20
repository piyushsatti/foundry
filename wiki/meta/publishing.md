# Publishing

**The wiki is authored as a folder tree in `wiki/`, but GitHub's wiki has a flat page namespace — so publishing flattens each page to a unique slug and rewrites every link.** You never hand-name wiki pages; the transform does it.

> **Status:** stable

## The problem

GitHub's wiki serves every page by its basename, ignoring folders. Left as-is, `plugins/manifold/overview.md` and `distribution/overview.md` collide to one `/wiki/overview`, and a nested link like `../lifecycle` 302-redirects to raw. The folder structure that makes the source readable is invisible to the wiki.

## How it works

`scripts/publish_wiki.sh` runs `scripts/flatten_wiki.py`, which:

1. **Slugs each page** — drop the `plugins/` / `harnesses/` wrapper, title-case the rest, join with `-`. So `plugins/manifold/overview.md` → `Manifold-Overview`, unique across the whole wiki.
2. **Rewrites every internal link** to the target's slug, so cross-page navigation resolves on the flat wiki.
3. **Writes the flat pages to the wiki repo root** and pushes.

The source stays folder-structured — and renders natively in the repo tree at `.../tree/main/wiki` — while only the published copy is flat.

## What the reader sees

- **A curated `_Sidebar`** — grouped, human-labeled navigation (GitHub's own flat **Pages** panel still shows below it, but the sidebar is the readable nav). Its links use folder-relative paths in source; the flattener rewrites them to slugs.
- **No frontmatter** — it renders as literal text, so pages carry status in a `> **Status:**` callout instead (see [style](style)).

## Open questions

- A few slugs read long (e.g. `Claude-Code-Hooks-Guard-Hooks`); the slug rule is a small function in `flatten_wiki.py` and can be tuned or special-cased.

## See also

- [Style](style) — the page-header and link conventions.
