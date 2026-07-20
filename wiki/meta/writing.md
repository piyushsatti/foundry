# Writing

**A page tells a simple story: what problem exists, how it's solved, how the solution works, and where it doesn't.** A reader should finish knowing not just *what* we built but *why* — and should be able to stop at any depth with a coherent picture.

> **Status:** stable

## The arc every page follows

1. **The problem / the why.** Open with the problem or question this page answers. A reader who stops here still knows why the page exists.
2. **The approach.** What we do about it, in a sentence or two.
3. **How it works.** The mechanism, disclosed progressively — simplest framing first, detail layered after.
4. **Where it doesn't work.** Limits, tradeoffs, failure modes, stated plainly. A solution with no stated cost is under-explained.

The arc is the *logic*, not a required heading list. Sectioning scales with size: a small page folds the arc into a few sentences; a big one gives each step its own heading. Either way the order holds — **why before how, how before caveats.**

## Page types carry extra obligations

- **Architecture / design pages** — **state the alternatives you rejected, and why.** The *why-not* is as load-bearing as the *why*. Make it count:
  - *Thin (avoid):* "We use SQLite, not Postgres."
  - *Load-bearing (prefer):* "We use SQLite, not Postgres or a hosted DB, because each idea is a single-user, single-file project — one small DB you can copy, diff, and delete. Postgres adds a server dependency for zero multi-user benefit."
  - The test: could the reader reconstruct why the rejected option was tempting *and* what killed it? If not, it's decoration.
- **Reference / catalog / glossary** — definitions and tables over narrative; the arc compresses to a line.
- **Field notes** — problem observed → mechanism → fix.

(Documenting *code* is a separate discipline — see [conventions/code-documentation.md](../conventions/code-documentation).)

## Progressive disclosure

Reveal detail in layers. Lead each section with a sentence that stands alone, then add the mechanics below it:

- *Front-loaded (avoid):* "The build script walks `bundles/`, resolves each `plugin.json`, copies `server/` while rewriting `${CLAUDE_PLUGIN_ROOT}`, then writes to `plugins/`."
- *Layered (prefer):* "The build script materializes each bundle into `plugins/`. **How:** it walks `bundles/`, resolves each `plugin.json`, and rewrites `${CLAUDE_PLUGIN_ROOT}` as it copies."

A reader who stops at the first sentence still knows what the script does.

## Nothing is silently swallowed

**Surface what you're unsure of.** If a claim is an assumption, an inference, or unverified, say so — inline (*assumed; not confirmed*) or in an **Open questions** section.

The failure this prevents: murky content that reads as settled, so nobody asks "are we sure this is true?" — until it breaks. Flag it now and it gets resolved later. Silence hides the very things that need review.

## Prose that helps the reader

- **No convoluted paragraphs.** Short sentences. Walk the reader through; don't dump on them.
- **Complex point → example under it.** A concrete example showing what's done and why beats another abstract sentence. (This whole page is the rule in practice.)
- **Procedures → numbered steps.** If the reader must *do* or *follow* something, break it into step 1, 2, 3 in text. A step diagram is fine too, but numbered text is often clearer.

## Minimize jargon

Where a human will read it, use **as little jargon as possible** — plain words first. Technical precision rarely requires technical vocabulary.

When a term is unavoidable, don't gloss it inline term-by-term. Collect the vocabulary once — a **Terms** pointer in the closing section, linking to the [glossary](../glossary) or the page's `sources`. One place for the curious reader, a clean body for everyone else.

## Self-contained

**A doc stands on its own.** Explain the what and the why in the page itself; a reader should never need an external ticket to understand it.

Load-bearing references to issues/tickets *outside the repo's scope* — or a page written as a changelog of ticket #123 — are a **smell**: the repository should be a complete document in itself. Same-repo issue links are fine as *supplementary pointers*, never as the substance.

## Every page ends with

Non-tiny pages close with these, in order. They are heading-labelled lists — the deliberate exception to style.md's "paragraph under every heading", and they don't count against its heading budget.

- **Open questions** — assumptions, unverified claims, unresolved decisions. Omit if there genuinely are none.
- **Appendix / references** — supporting detail, external links, and any **Terms** pointer. Omit if none.
- **See also** — related pages. Omit if none.

A genuinely tiny page folds even these into its prose.

## On length

Short is a *result* of clarity, not the goal. Cut filler, hedging, and repetition — but don't cut the why, the limits, or a flagged uncertainty to save space. If a page is long because it genuinely covers a lot, that's usually a signal to **split it** ([organization.md](organization)) — though not always; see below.

## When to break these rules

These are defaults, not laws — the goal is a page the reader can follow. Break a rule when following it would hurt that, **deliberately, not lazily**.

- A **pure reference or index** page (glossary, catalog) legitimately skips the arc — it's definitions and tables.
- A tiny page collapses the whole arc into a sentence.
- Don't split a page just to hit a length target: a genuinely interlinked, complex topic can be one long page. **A topic shattered into fragments nobody reads is worse than a long page someone does.**

## See also

- [Style](style) — format mechanics.
- [Organization](organization) — where a page lives.
- [Page template](page-template) — the copy-me skeleton.
