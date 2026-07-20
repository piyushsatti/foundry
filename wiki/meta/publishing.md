# Publishing

**This wiki is the GitHub wiki repo itself, authored as a folder tree with frontmatter and relative links, published as-is.** GitHub's wiki renderer doesn't honor all of that, and we accept the caveats rather than adding a build step — so writers should know what the reader actually sees.

> **Status:** stable

## Known caveats

The raw markdown is the source of truth; the rendered wiki is a lossy view of it.

- **Frontmatter shows as text.** GitHub's wiki does not strip the YAML block — it renders atop each page. We keep it anyway (it's our metadata and provenance); the reader can ignore the header.
- **Relative `.md` links and nested paths** may not resolve cleanly in the wiki's page namespace. Use [`_Sidebar.md`](../_Sidebar) as the reliable navigation.
- **The folder tree doesn't render as a browsable sidebar.** `_Sidebar.md` is the hand-maintained index that reproduces the structure.

## Why as-is

A transform step (strip frontmatter, rewrite links, flatten) would make the rendered wiki prettier but adds machinery to build and keep correct. We chose the simpler path: author cleanly, accept the rough render, keep the source honest.

## Open questions

- If the render becomes a real obstacle, add a publish transform (the [docs-context-retrieval](../roadmap/docs-context-retrieval) tool or a small script) — deferred until it hurts.

## See also

- [Style](style) — frontmatter and link conventions.
