---
name: brief
description: Turn a vague or underspecified prompt into a sharp, approved brief before any work starts. Use when the request is unclear, ambiguous, too broad, or the user asks to sharpen, clarify, unpack, or refine the prompt before starting.
argument-hint: "The vague request as the user stated it"
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| **suggests** | `subset`, `audit`, `hats`, `red-vs-blue` | Soft handoff after this skill — suggest, do not auto-chain |
| **external** | `brainstorming`, `writing-plans` | Outside foundry bundle (host plugins) |

**Used by:** `plan-orchestrator` (suggests)

<!-- foundry:dependencies:end -->

# Brief

The user's prompt isn't ready for work yet. Interview until it's sharp, write a brief, get approval — **then** stop and hand off to execution (or another skill).

<HARD-GATE>
Do NOT write code, edit files, create plans, dispatch subagents, or invoke implementation skills until the user approves the brief.
</HARD-GATE>

## When to use

- Request is vague, hand-wavy, or one-liner for something large
- Multiple interpretations exist
- Success criteria are missing
- Scope is unbounded
- User says "help me think this through", "I'm not sure what I want", or "sharpen this"

## When NOT to use

- User already gave a clear spec → proceed or use **subset** / **writing-plans**
- User wants to stress-test an existing plan against domain docs → **grill-with-docs**
- User wants full feature design with approaches and design doc → **brainstorming**

## Process

### 1. Restate (may be wrong)

```markdown
## My read of your request

[1–3 sentences — best guess at intent]

**What I might be getting wrong:** …
```

### 2. Interview — one question at a time

Ask until these are unambiguous (skip what's already clear):

| Field | Question territory |
|-------|-------------------|
| Goal | What outcome do you want? |
| Why now | What triggered this? |
| Success | How will we know it worked? |
| Scope | What's in? |
| Anti-goals | What's explicitly out? |
| Constraints | Time, tech, must-not-break |
| Audience | Who uses or reads the result? |
| Preference | Any strong opinions or past decisions to honor? |

If a question can be answered by reading the repo, read first — don't ask what files contain.

Keep going until **you could hand this to a stranger** and they'd know what to do.

User's standing preference: **prompt again and again until you know exactly.**

### 3. Write the brief

```markdown
# Brief: [title]

## Goal
[One clear sentence]

## Context
[Why this matters, what exists today]

## Success criteria
- [ ] …
- [ ] …

## Scope
**In:** …
**Out (anti-goals):** …

## Constraints
- …

## Open questions resolved
| Question | Answer |
|----------|--------|
| …        | …      |

## Suggested next step
[Which skill or action after approval — e.g. subset, writing-plans, audit, go]
```

### 4. Get approval

Ask: **"Does this brief match your intent? Edit anything, or say go."**

Only after explicit approval (go / lgtm / approved / yes) may work begin.

## After approval

Stop the brief skill. Suggest the appropriate next skill based on the brief:

- Large unclear how → **brainstorming** or **writing-plans**
- Clear but too big → **subset**
- Plan exists, needs review → **audit**, **hats**, or **red-vs-blue**
- Clear and small → execute directly

Do not auto-chain — tell the user what you'd invoke and wait if they want control.
