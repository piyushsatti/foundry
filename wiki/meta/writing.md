---
title: Writing
status: stable
summary: How a page reads — tell the story of why something exists and how it works, disclose detail in layers, and hide nothing.
sources: []
updated: 2026-07-20
---

# Writing

**A page tells a simple story: what problem exists, how it's solved, how the solution works, and where it doesn't.** A reader should finish knowing not just *what* we built but *why* — and should be able to stop at any depth with a coherent picture.

> **Status:** stable

## The arc every page follows

1. **The problem / the why.** Open with the problem or question this page answers. A reader who stops here still knows why the page exists.
2. **The approach.** What we do about it, in a sentence or two.
3. **How it works.** The mechanism, disclosed progressively — simplest framing first, detail layered after.
4. **Where it doesn't work.** Limits, tradeoffs, failure modes, stated plainly. A solution with no stated cost is under-explained.

Small pages compress these into a few sentences; big ones give each its own section. The *order* holds either way: **why before how, how before caveats.**

## Page types carry extra obligations

The arc fits every page, but the type adds a rule:

- **Architecture / design pages** — **state the alternatives you rejected, and why.** "We use X, not Y or Z, because…". A decision with no visible discarded options reads as unconsidered; the *why-not* is as load-bearing as the *why*. Put it beside the approach or in an **Alternatives considered** section.
- **Reference / catalog / glossary** — definitions and tables over narrative; the arc compresses to a line.
- **Field notes** — problem observed → mechanism → fix.

(Documenting *code* is a separate discipline — see [conventions](../conventions/code-documentation.md), not this guide.)

## Progressive disclosure

Reveal detail in layers. Someone skimming the first line of each section should get the whole shape; someone reading deep should find the mechanics. Avoid front-loading a wall of detail the reader can't yet place.

## Nothing is silently swallowed

**Surface what you're unsure of.** If a claim is an assumption, an inference, or unverified, say so — inline (*assumed; not confirmed*) or in an **Open questions** section.

The failure this prevents: murky content that reads as settled, so nobody asks "are we sure this is true?" — until it breaks. Flag it now and it gets resolved later. Silence hides the very things that need review.

## Prose that helps the reader

- **No convoluted paragraphs.** Short sentences. Walk the reader through; don't dump on them.
- **Complex point → example under it.** A concrete example showing what's done and why beats another abstract sentence.
- **Procedures → numbered steps.** If the reader must *do* or *follow* something, break it into step 1, 2, 3 in text. A step diagram is fine too, but numbered text is often clearer.

## Minimize jargon

Where a human will read it, use **as little jargon as possible** — plain words first. Technical precision rarely requires technical vocabulary.

When a term is unavoidable, **don't gloss it inline term-by-term** — that clutters the body. Collect the vocabulary once, at the end: point to where it's defined (the [glossary](../glossary.md), or the `sources` the page was drawn from). One place for the curious reader, a clean body for everyone else.

## Self-contained

**A doc stands on its own.** Explain the what and the why in the page itself; a reader should never need an external ticket to understand it.

Load-bearing references to issues/tickets *outside the repo's scope* — or a page written as a changelog of ticket #123 — are a **smell**: the repository should be a complete document in itself. Same-repo issue links are fine as *supplementary pointers*, never as the substance.

## Every page ends with

- **Open questions** — assumptions, unverified claims, unresolved decisions. Omit only if there genuinely are none.
- **Appendix / references** — necessary supporting detail and external links, collected here rather than stuffed inline.
- **See also** — related pages.

## On length

Short is a *result* of clarity, not the goal. Cut filler, hedging, and repetition — but don't cut the why, the limits, or a flagged uncertainty to save space. If a page is long because it genuinely covers a lot, that's usually a signal to **split it** ([organization.md](organization.md)) — though not always; see below.

## When to bend these rules

These are defaults, not laws — the goal is a page the reader can follow. Break a rule when following it would hurt that, **deliberately, not lazily**.

- A **pure reference or index** page (glossary, catalog) legitimately skips the arc — it's definitions and tables.
- A tiny page collapses the whole arc into a sentence.
- Don't split a page just to hit a length target: a genuinely interlinked, complex topic can be one long page. **A topic shattered into fragments nobody reads is worse than a long page someone does.**
