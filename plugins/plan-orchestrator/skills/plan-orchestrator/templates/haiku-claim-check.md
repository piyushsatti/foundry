---
name: haiku-claim-check
description: Alignment-class dispatch pattern — verifies an adjudication's claim text against its cited source. Architect dispatches via Agent tool with model=haiku. Cheap, single-shot Q-and-A.
version: 1
---

# Haiku Claim Check — Dispatch Pattern

For each adjudication with a `cites:` field, dispatch ONE Haiku agent per cite. Single-shot Q-and-A; no extended thinking; typically <2k input tokens per call.

## When to dispatch

- Immediately after writing or updating any adjudication that has `cites:`
- Sweep all adjudications before any stage gate closes

## Dispatch payload (Agent tool, `model: "haiku"`, no thinking)

```
You are an Alignment-class checker for a plan-orchestrator project.

ADJUDICATION:
  id:    <adjudication-id>
  claim: <claim text from the adjudication>

CITED SOURCE:
  file:   <cited file path>
  anchor: <cited anchor>

CITED SECTION CONTENT:
<paste the section content from the cited file — the heading line plus
its body up to the next heading>

QUESTION:
Do the claim and the cited section agree on load-bearing facts —
counts, names, structural details, signatures, enumerations?

ANSWER (exactly one of YES / NO / UNSURE):
  YES — claim and source agree.
  NO  — claim and source disagree on a load-bearing fact. (One-line reason.)
  UNSURE — ambiguous; needs human or Opus review. (One-line reason.)

Respond with one word followed by a colon and a one-line reason (if NO or UNSURE).
```

## Interpreting the result

| Response | Action |
|---|---|
| YES | This cite is verified. If all cites for this adjudication return YES → adjudication may proceed to `validated`. |
| NO | **Block the gate.** Either the claim text is wrong (architect re-reads source and fixes claim) or the source is wrong (architect must update source first). |
| UNSURE | Escalate. Either user adjudication, or upgrade to Opus assumption-sweep review. |

## What this catches

The exact pattern that surfaced in the first test-bed run:
- Architect claim A42 said "8 values"; cited contract section had 9.
  → A Haiku-claim-check would have said NO immediately, before A42 propagated into 4 downstream findings.

Also catches:
- Architect mis-counting / mis-naming an item from a list
- Architect citing a stale snapshot of content that's since changed
- Architect citing a section that doesn't actually say what the claim says

## Cost guard

Typical: 20 adjudications × ~3 cites each = ~60 Haiku calls per Alignment sweep.
At Haiku's per-token rates this is < $0.10 per sweep — cheaper than a single Opus L2 edge-reviewer dispatch.

## Implementation hint

Architect-as-dispatcher pseudocode:

```
for adj in assumptions where adj.cites is non-empty:
    for cite in adj.cites:
        section_content = read(cite.file, around=cite.anchor)
        result = dispatch_agent(
            model="haiku",
            prompt=fill_template(adj.claim, cite.file, cite.anchor, section_content)
        )
        if result == "NO": block_gate(adj.id, cite, reason=result.reason)
        elif result == "UNSURE": escalate(adj.id, cite, reason=result.reason)
```
