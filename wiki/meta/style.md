---
title: Style
status: stable
summary: Format mechanics — frontmatter, headings, and how to draw (and decompose) diagrams.
sources: []
updated: 2026-07-20
---

# Style

**Mechanics for every page.** How content should *read* lives in [writing.md](writing.md); this covers *format*.

> **Status:** stable

## Frontmatter

Every page opens with exactly this set:

```yaml
---
title: Page Title
status: draft        # draft | stable | shelved | parked | archived
summary: One line saying what this page is.
sources:             # in-repo paths this page consolidates (provenance)
  - path/to/source.md
updated: 2026-07-20   # YYYY-MM-DD
---
```

## Headings

- **One H1**, matching `title`.
- **H2/H3 for structure** — aim for ~2–4 headings on a short page, not one per idea.

**A heading promises a section — deliver one.** Put at least a full paragraph (usually several) under every heading. A heading with a single line beneath it, or one stacked directly under another, is the tell-tale sign of over-sectioning: it fragments ideas that belong together and renders as a jagged, hard-to-read list. **The rendered page is the artifact, not the source symbols** — write for how it looks, not how it's marked up.

**One line to say? It's not a section.** Fold it into surrounding prose, or represent it as what it actually is — a **list item**, a **table** row, or a **bold lead-in** (`**Term** — the one line`). "Many short items" is a list, not a stack of headings.

**Make headings descriptive:** a noun phrase ("How bundling works") or a task ("Publish to the release branch") that tells the reader what they'll learn or do — not a bare label.

**Why stop at H3:** reaching for an H4 usually means the page is holding two topics — split into a sibling page ([organization.md](organization.md)) rather than nesting deeper. A symptom check, not an arbitrary cap (see *When to break these rules*).

## Diagrams

**Mermaid only** — plain text, diffs cleanly, GitHub renders it natively. No images-of-diagrams.

### Keep them small — and what to do when you can't

Target **≤ ~8 nodes**. Past that, the problem isn't the diagram — it's that you're showing too much at once. Don't shrink it. **Decompose it:**

1. Draw one **coarse diagram** of the top-level pieces (≤ ~8 nodes).
2. Give each piece its own section, with its own focused diagram if it needs one.

Same rule as prose: complexity is a signal to break down, never to cram ([organization.md](organization.md)).

### Visual conventions

- **Shape carries meaning:** rectangle = step/state, rounded = start/end, diamond = decision. Stay consistent within a page.
- **Prefer two channels — avoid color as the only signal.** Pair color with a label or shape, so the diagram survives greyscale and colorblind readers.
- **Color is theme-aware by default.** Prefer Mermaid's default theme; it adapts to GitHub's light and dark modes. Add custom color only when it *carries meaning*.
- **Renders well:** muted blues, teals, greys — legible on both light and dark backgrounds.
- **Avoid:** anything low-contrast on white *or* black (pale yellow, light-grey text); red+green as the only distinction (colorblind-hostile); saturated fills that wash out labels.

### Procedures

A left-to-right or top-down numbered flow works — but if numbered *text* is clearer, use that instead ([writing.md](writing.md)).

## Examples

A sufficiently complex point carries a concrete example right under it — often a fenced block. Show, don't only assert.

## Other

- Fenced code blocks always carry a language tag.
- Links relative (`../distribution/overview.md`).
- Status callouts and notes go in blockquotes (`> **Status:** …`).
- Filenames kebab-case, in the subject's folder.

## When to break these rules

Prefer these patterns; they're not absolute. Optimize for the reader.

- **Headings:** if a complex, tightly interlinked topic genuinely reads better whole — with H4s — than as several thin pages, keep it whole. The H3 guidance flags *likely* over-stuffing, not every case.
- **Diagram size:** an inherently connected system may need a denser diagram than ~8 nodes. If decomposing it loses the very relationships that matter, don't.
- Break a rule on purpose, and note why if it isn't obvious.

## References

- [Headings — Technical Writing Essentials (BCcampus)](https://pressbooks.bccampus.ca/technicalwriting/chapter/headings/)
- [Headings and titles — Google developer documentation style guide](https://developers.google.com/style/headings)
