---
name: haiku-coverage-check
description: Alignment-class dispatch pattern — verifies an adjudication's intended change has actually landed in each affected artifact. Architect dispatches via Agent tool with model=haiku.
version: 1
---

# Haiku Coverage Check — Dispatch Pattern

For each adjudication with an `affects_artifacts:` field, dispatch ONE Haiku agent per affected artifact. Asks: "does this file contain the change the adjudication called for?"

This is the companion to `haiku-claim-check.md`. Claim-check verifies the adjudication's text against its source; coverage-check verifies the adjudication's *consequence* has propagated to the files it should affect.

## When to dispatch

- After making mechanical edits in response to an adjudication
- Sweep all adjudications with `affects_artifacts` before any stage gate closes

## Dispatch payload (Agent tool, `model: "haiku"`, no thinking)

```
You are an Alignment-class checker for a plan-orchestrator project.

ADJUDICATION:
  id:    <adjudication-id>
  claim: <claim text>
  intended change: <one-line summary of what should be different in the affected file>

AFFECTED ARTIFACT:
  path: <relative file path>

CURRENT CONTENT (relevant section, post-edit):
<paste the file content or the affected section>

QUESTION:
Does the artifact contain the change the adjudication called for?
That is, has the decision actually been propagated into this file?

ANSWER (exactly one of YES / NO / UNSURE):
  YES — change is reflected.
  NO  — change is NOT reflected, or the file contradicts the adjudication. (One-line reason.)
  UNSURE — ambiguous; needs human or Opus review. (One-line reason.)

Respond with one word followed by a colon and a one-line reason (if NO or UNSURE).
```

## Interpreting the result

| Response | Action |
|---|---|
| YES | This artifact reflects the adjudication. |
| NO | **Block the gate.** Architect must edit the artifact to match. The adjudication has not landed. |
| UNSURE | Escalate to user or Opus. |

## What this catches

The exact pattern that surfaced in the first test-bed run (cycle-2 closure):
- Adjudication A51 said "hex parity = odd-r everywhere."
- P1.A28 said odd-r ✓
- P3.A25 said **even rows are offset right** (= even-r) ✗
- L2 cycle-2 reviewer said "clean — pointy-top + offset-r" but didn't check parity
- Architect's own L0 precision check caught it manually
  → A Haiku-coverage-check against `phases/P3/plan.md` would have said NO immediately.

Also catches:
- Adjudication says "drop the fallback clause"; file still has "or implements equivalent"
- Adjudication says "rename X to Y"; file still has X
- Adjudication says "add field Z"; file doesn't mention Z

## Cost guard

Typical: 20 adjudications × ~2 affected artifacts each = ~40 Haiku calls per Alignment sweep. <$0.05.

## Relationship to `verify-coverage.py`

`verify-coverage.py` (Structural class) checks **mtime** — was the file modified after the adjudication's timestamp? That catches "file never touched."

`haiku-coverage-check.md` (Alignment class) checks **content** — does the file's current state actually contain the change? That catches "file touched but in a way that doesn't match the adjudication's intent."

Both are necessary. Run Structural first (free), then Alignment on whatever passes Structural.
