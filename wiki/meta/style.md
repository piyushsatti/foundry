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
- **H2/H3 for structure.**

**Why stop at H3:** reaching for an H4 usually means the page is holding two topics. That's a signal to split into a sibling page ([organization.md](organization.md)), not to nest deeper. The limit is a symptom check, not an arbitrary cap.

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
