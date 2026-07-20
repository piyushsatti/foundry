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

## Progressive disclosure

Reveal detail in layers. Someone skimming the first line of each section should get the whole shape; someone reading deep should find the mechanics. Never front-load a wall of detail the reader can't yet place.

## Nothing is silently swallowed

**Surface what you're unsure of.** If a claim is an assumption, an inference, or unverified, say so — inline (*assumed; not confirmed*) or in an **Open questions** section.

The failure this prevents: murky content that reads as settled, so nobody asks "are we sure this is true?" — until it breaks. Flag it now and it gets resolved later. Silence hides the very things that need review.

## Prose that helps the reader

- **No convoluted paragraphs.** Short sentences. Walk the reader through; don't dump on them.
- **Complex point → example under it.** A concrete example showing what's done and why beats another abstract sentence.
- **Procedures → numbered steps.** If the reader must *do* or *follow* something, break it into step 1, 2, 3 in text. A step diagram is fine too, but numbered text is often clearer.

## Every page ends with

- **Open questions** — assumptions, unverified claims, unresolved decisions. Omit only if there genuinely are none.
- **Appendix / references** — necessary supporting detail and external links, collected here rather than stuffed inline.
- **See also** — related pages.

## On length

Short is a *result* of clarity, not the goal. Cut filler, hedging, and repetition — **never** cut the why, the limits, or a flagged uncertainty to save space. If a page is long because it genuinely covers a lot, that's a signal to **split it** ([organization.md](organization.md)), not to compress it into something unreadable.
