---
name: conduct
description: The ways of working every agent follows during ticketed work: the raise block, code style rule sets, the review checklist, and the transcript convention. Load at the start of any implementation or review task.
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| — | — | No manifest dependencies |

<!-- foundry:dependencies:end -->

# conduct

The ways of working (locked 2026-07-15, ways-of-working experiment). Load at the start of any implementation or review task. Full rationale: the ways-of-working operating model; raw research: piyushsatti/research.

## The raise block

Your ticket lists Proven · Assumed · Unknown and declared files + signatures. If anything you hit contradicts these, or forces work outside declared scope: STOP writing code. Complete read-only checks on the rest of your plan and bundle all contradictions into one raise report: what broke · evidence (file:line, error, output) · smallest options you see. Do not patch around it. Do not pick an option yourself. You resume only on an amended ticket, never on a verbal ok.

Where a failure lives decides what you do: your own PR (gates red, your change broke it): fix in the PR, never file. Epic branch after children merged: new child bug issue, closes before the epic e2e gate. Main: bug ticket always, standalone squash PR, no size exemption. The plan itself: stop and raise. Drive-by ban: broken code your PR did not touch is never fixed silently; file where it lives.

## Code style

- comments: self-documenting code is the default (names, typed signatures, return types, validated models, file placement). Surviving comments are one-line whys. Hard bans: per-function narration blocks, ticket/issue numbers in comments, top-of-file essays. Six-plus lines of needed explanation = review the complexity or move the prose to a real doc the code references.
- contracts: signature first (name, typed parameters, return type, typed models, declared exceptions), implementation only after the contract is complete.
- boundaries: every external call wrapped with explicit exception handling and a useful message (what was called, with what, what was expected); every external payload validated at entry; known failure cases follow a defined procedure written once.
- extraction: co-change test first (a bugfix in A requiring the same edit in B = same knowledge; else coincidence, never extract). Rule of three gates evidence. Extract narrowly, zero speculative parameters. A new conditional for a new caller falsifies the abstraction: re-test, inline back out if it fails.
- logging: getLogger(__name__) at module top; never root logger, print, or per-call loggers; entry point alone configures. Levels: DEBUG dev-only · INFO normal events · WARNING degraded but continuing · ERROR operation failed but app survives · CRITICAL cannot continue. Retries: DEBUG per attempt, INFO on recovery, escalate on budget exhaustion. Placement: boundaries, state transitions, terminal handlers, retry give-ups; never per line. logger.exception() inside except only; either log or raise, never both; one log at the terminal handler. Lazy %-args, stdout only, JSON in prod.

## The review checklist

A review is a checklist execution with evidence, not an opinion. PR-to-epic review passes when: (1) contract: diff matches declared files and implements declared signatures exactly; (2) style: the five rule sets above checked; (3) verification: the ticket's verify plan executed, gates green, output quoted not claimed; (4) raise integrity: zero unresolved raises, divergences recorded in the ticket before merge. Finding format: rule broken · evidence (file:line) · severity. Praise is noise; silence on a passing dimension means it passed.

## The transcript convention

Every agent PR description carries one line: session id · model · effort · link into the transcript store (piyushsatti/transcripts). Never the transcript itself.
