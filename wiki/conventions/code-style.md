---
title: Code Style
status: stable
summary: A baseline for naming and shape (constants, private functions, interface validation) that each repo adapts on adoption.
sources: []
updated: 2026-07-20
---

# Code Style

**Consistent naming and shape within a file make code scannable — but the specific choices are opinionated and language-bound, so this is a baseline each repo tailors, not a global mandate.** Consistency within a repo matters more than any single rule.

> **Status:** stable — a baseline to adapt per repo.

## The problem

Inconsistent style within a file — mixed naming, no signal for which functions are public — makes code hard to scan and reason about. But one fixed global standard fights language idioms and team taste, so a rigid central rulebook would be wrong as often as right.

## Approach

Keep a **small central baseline**. Each repo adopts it, tailors it to its language and norms, and then applies it consistently. The win is consistency *within* a repo, not agreement across all of them.

## Baseline conventions

| Convention | Default |
|---|---|
| Constants | `UPPER_SNAKE_CASE` |
| Internal / private functions | prefix with `_` |
| Public-interface functions | validate parameters at the boundary |
| Naming | one scheme per file; names convey purpose (see [code-documentation.md](code-documentation.md)) |

Names doing their job *is* documentation — structure and naming carry intent so comments don't have to.

## Per-repo customization

These are defaults, not law. On adopting the tooling in a repo, **tailor them to the language and record the repo's choices** (in that repo's `CLAUDE.md` or a `CONTRIBUTING`). The central baseline is a skeleton.

## When to break these rules

Follow the language's own idioms when they conflict — Python privates use `_`, but Go signals visibility by capitalization; Python constants are `UPPER_SNAKE`, Go uses `MixedCaps`. Consistency-within-repo beats the central default every time.

## Open questions

- No per-language tables yet (Python, JS, …). Add them as repos formalize their choices.

## See also

- [Code documentation](code-documentation.md) — when code earns a comment.
