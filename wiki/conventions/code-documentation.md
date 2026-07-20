---
title: Code Documentation
status: stable
summary: When code gets a comment and when it doesn't — minimal, intent-only, self-documenting; escalate real complexity to the wiki.
sources: []
updated: 2026-07-20
---

# Code Documentation

**Comments rot and add noise, so code carries as few as possible — a comment earns its place only when the code's intent isn't obvious from the code itself.** The default is self-documenting code, not explained code.

> **Status:** stable

## The problem

Over-documented code is worse than under-documented code. Every comment is a second thing to keep true; when it drifts from the code, it misleads. AI-authored code tends to over-explain — a docstring on every function, a paragraph over every loop — which buries the few comments that matter.

## When a comment earns its place

A comment is justified only when the code's **intent** — *what it is trying to do* — isn't obvious. Not what it literally does; the reader can see that.

- A nested `map`/`filter`/`reduce` whose **purpose is clear** needs no comment.
- The same code, where *why* it's shaped that way is non-obvious, gets **one line** of intent.

```python
# no comment — the shape says it
active = [u for u in users if u.enabled]

# one line earned — the shape is non-obvious
# retry newest-first so a flapping job surfaces before stale ones
jobs = sorted(pending, key=lambda j: -j.created_at)[:MAX_RETRIES]
```

## Comments stay short

**A 3–4 line comment is a smell.** It means one of three things:

1. It's genuinely pivotal — rare, and fine.
2. It's badly written — tighten it.
3. That code needs its **own wiki page** — what it does, why it exists, why nothing else works. Escalate there and link to it; don't bury a paragraph in the source.

## Let structure do the documenting

A code piece's **location in the tree, its name, and how it's invoked** should already convey its purpose and importance. If they don't, fix the naming or placement before adding a comment — self-documentation via structure beats prose every time.

## Signature docs: public interface only

Document a function's signature when it sits **outside a modular interface and is called widely** — the public surface others depend on. Functions internal to a feature usually get none; per-function docs everywhere is excessive noise.

## Limits

This assumes good naming and a legible directory structure — minimalism fails on code that isn't self-documenting to begin with. When structure can't carry the meaning (a genuinely subtle algorithm, a hard-won workaround), a comment or a dedicated wiki page is the right tool, not a code smell.

## When to break these rules

Defaults, not laws — add more documentation when the reader genuinely needs it: a published or external API contract, generated code, a teaching example, or a subtle internal algorithm whose intent good naming can't carry. The test is always the reader's understanding, not the rule.

## Open questions

- Language-specific docstring conventions (e.g. Python packages like `manifold`) aren't specified here yet — this page is language-agnostic so far.

## See also

- [Writing](../meta/writing.md) — the wiki-page equivalent, and where escalated code explanations land.
