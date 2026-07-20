---
title: Style
status: stable
summary: Format mechanics — frontmatter, headings, diagrams, and formatting conventions.
sources: []
updated: 2026-07-20
---

# Style

**Mechanics for every page.** How content should *read* lives in [writing.md](writing.md); this covers *format*.

> **Status:** stable

## Frontmatter

Every page opens with exactly this set. The `> **Status:**` callout below the H1 mirrors the `status` value.

```yaml
---
title: Page Title
status: draft        # see the table below
summary: One line saying what this page is.
sources:             # in-repo paths this page consolidates; [] if none
  - path/to/source.md
updated: 2026-07-20   # YYYY-MM-DD
---
```

| `status` | Meaning | Enter when |
|---|---|---|
| `draft` | being written | on creation |
| `stable` | reviewed, and its subject is settled | after a review pass |
| `parked` | deliberately deferred; may resume | work paused, intent to return |
| `shelved` | paused, no plan to resume | idea captured, not scheduled |
| `archived` | superseded; kept for history | replaced by a newer page |

- **`sources`** — in-repo paths (design notes, transcripts, prior docs) whose content this page consolidates. Not external URLs (those go in References), not code the page merely mentions. Empty is `sources: []`.
- **`updated`** — bump by hand on any substantive content change, not typo fixes.

## Headings

**A heading promises a section — deliver one.** Put at least a paragraph (usually several) under every *prose* heading. A prose heading with a single line beneath it, or one stacked directly under another, is over-sectioning: it fragments ideas that belong together and renders as a jagged, hard-to-read list. **The rendered page is the artifact, not the source symbols.**

- **One H1**, matching `title`.
- **~2–4 body headings on a short page**, not one per idea. The closing sections (Open questions, References, See also) are page furniture — heading-labelled lists by design, and the one exception to the paragraph rule. They don't count against the budget.
- **One line to say? It's not a section.** Fold it into prose, or make it a **list item**, a **table** row, or a **bold lead-in** (`**Term** — the one line`).
- **Descriptive headings:** a noun phrase ("How bundling works") or a task ("Publish to the release branch"). Standard arc names (How it works, Limits, Open questions) are fine; the rule targets vague catch-alls like "Other" or "Misc".
- **H3 is the floor.** Reaching for an H4 usually means the page holds two topics — split into a sibling page ([organization.md](organization.md)) rather than nesting deeper. A default; see *When to break these rules*.

## Diagrams

**Mermaid only** — plain text, diffs cleanly, GitHub renders it natively. No images-of-diagrams.

- **Shape carries meaning:** rectangle = step/state, rounded = start/end, diamond = decision. Stay consistent within a page.
- **Prefer two channels — avoid color as the only signal.** Pair color with a label or shape, so the diagram survives greyscale and colorblind readers.
- **Color is theme-aware by default.** Prefer Mermaid's default theme; it adapts to GitHub's light and dark modes. Add custom color only when it *carries meaning*.
- **Renders well:** muted blues, teals, greys. **Avoid:** low-contrast on white *or* black (pale yellow, light grey); red+green as the only distinction; saturated fills that wash out labels.

### Too big? Decompose, don't shrink

Target **≤ ~8 nodes**. Past that, you're showing too much at once. Draw one **coarse diagram** of the top-level pieces, then give each piece its own section with its own focused diagram.

For example, a 12-node build-and-release flow becomes one coarse diagram — `bundles → build → plugins → release → marketplace` (5 nodes) — and then a focused diagram inside the *Build* section that expands the `build` node alone.

## Formatting

- **Code:** fenced blocks always carry a language tag. Examples usually render as a fenced block — [writing.md](writing.md) covers *when* to add one.
- **Links:** relative (`../distribution/overview.md`); to repo source, a repo-relative path; within a long page, `#anchor` links to its own headings. External URLs collect in References/Appendix, not inline.
- **Callouts:** a blockquote with a bold lead-in — `> **Note** — …`, `> **Warning** — …`. Do **not** use `> [!NOTE]` GitHub-alert syntax; it does not render on the published wiki.
- **Tables:** for parallel rows sharing 2–4 attributes; a list for anything else. A too-wide table is a decompose signal like any other.
- **Images:** prefer Mermaid and prose; use a raster image only for what can't be drawn (e.g. a UI screenshot). Every image needs alt text.
- **Line wrapping:** one sentence per line (or semantic line breaks) so diffs stay readable.
- **Link text** describes its destination — never a bare "here" or "this".

## When to break these rules

Prefer these patterns; they're not absolute. Optimize for the reader.

- **Headings:** if a complex, tightly interlinked topic genuinely reads better whole — with H4s — than as several thin pages, keep it whole. The H3 guidance flags *likely* over-stuffing, not every case.
- **Diagram size:** an inherently connected system may need a denser diagram than ~8 nodes. If decomposing it loses the very relationships that matter, don't.
- Break a rule on purpose, and note why if it isn't obvious.

## References

- [Headings — Technical Writing Essentials (BCcampus)](https://pressbooks.bccampus.ca/technicalwriting/chapter/headings/)
- [Headings and titles — Google developer documentation style guide](https://developers.google.com/style/headings)

## See also

- [Writing](writing.md) — how a page reads.
- [Organization](organization.md) — where a page lives.
- [Publishing](publishing.md) — how the wiki renders once published.
