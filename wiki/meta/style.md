# Style

**Mechanics for every page.** How content should *read* lives in [writing](writing); this covers *format*.

> **Status:** stable

## Page header

**No YAML frontmatter** — GitHub's wiki renders it as literal text atop the page. A page opens with three things:

1. **`# Title`** — one H1, the page's name.
2. **One BLUF sentence** — what the page is.
3. **A status callout** — `> **Status:** stable`, using one of:

| Status | Meaning |
|---|---|
| `draft` | being written |
| `stable` | reviewed, subject settled |
| `parked` | deliberately deferred; may resume |
| `shelved` | paused, no plan to resume |
| `archived` | superseded; kept for history |

Provenance — the sources a page consolidates — goes in the page's **Appendix / references**, not a metadata block.

## Headings

**A heading promises a section — deliver one.** Put at least a paragraph (usually several) under every *prose* heading. A prose heading with a single line beneath it, or one stacked directly under another, is over-sectioning: it fragments ideas that belong together and renders as a jagged, hard-to-read list. **The rendered page is the artifact, not the source symbols.**

- **One H1**, matching the title.
- **~2–4 body headings on a short page**, not one per idea. The closing sections (Open questions, References, See also) are page furniture — heading-labelled lists by design, and the one exception to the paragraph rule. They don't count against the budget.
- **One line to say? It's not a section.** Fold it into prose, or make it a **list item**, a **table** row, or a **bold lead-in** (`**Term** — the one line`).
- **Descriptive headings:** a noun phrase ("How bundling works") or a task ("Publish to the release branch"). Standard arc names (How it works, Limits, Open questions) are fine; the rule targets vague catch-alls like "Other" or "Misc".
- **H3 is the floor.** Reaching for an H4 usually means the page holds two topics — split into a sibling page ([organization](organization)) rather than nesting deeper. A default; see *When to break these rules*.

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

- **Code:** fenced blocks always carry a language tag. Examples usually render as a fenced block — [writing](writing) covers *when* to add one.
- **Links:** relative, and **without the `.md` extension** — a `.md` link resolves to raw file content, not the rendered wiki page. Within a long page, `#anchor` links to its own headings. External URLs collect in References/Appendix, not inline.
- **Callouts:** a blockquote with a bold lead-in — `> **Note** — …`, `> **Warning** — …`. Do **not** use `> [!NOTE]` GitHub-alert syntax; it does not render on the wiki.
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

- [Writing](writing) — how a page reads.
- [Organization](organization) — where a page lives.
- [Publishing](publishing) — how the wiki renders once published.
