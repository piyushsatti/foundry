---
name: subset
description: Shrink work to the smallest testable vertical slice, define done for that slice, verify end-to-end, then expand. Use when user says take a subset, testable slice, shrink scope, verify end-to-end then expand, or fold it in.
argument-hint: "The larger goal + what to slice from it"
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../../../../skills/manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| **suggests** | `audit` | Soft handoff after this skill — suggest, do not auto-chain |

**Used by:** `brief` (suggests), `plan-orchestrator` (suggests)

<!-- foundry:dependencies:end -->

# Subset

Cut scope to the **smallest slice** that proves the approach works end-to-end. Expand only after the slice passes.

<HARD-GATE>
Do not build the full vision first. Do not bump version or milestone for the slice — **fold it in** to current work unless the user says otherwise.
</HARD-GATE>

## Workflow

### 1. Name the full goal

One paragraph: what the user ultimately wants. This is context, not today's scope.

### 2. Propose the subset

Identify the smallest vertical slice that:

- Touches real code/docs/data (not a throwaway spike unless user agrees)
- Can be verified end-to-end in one session
- De-risks the biggest unknown in the full goal
- Explicitly **excludes** everything else

Present:

```markdown
## Proposed subset

**Slice:** [one sentence]
**Proves:** [what uncertainty this removes]
**Includes:** …
**Excludes (anti-goals):** …
**Done when:** [3–5 concrete checks]
**Expand next (if slice passes):** …
```

Get user approval before building.

### 3. Lock anti-goals

List what you will **not** do in this slice — prevents cost explosion. User can add more.

### 4. Build the slice only

Implement the approved subset. Resist scope creep. If a tangent appears, note it for "expand next" — don't fold it in silently.

### 5. Verify end-to-end

Before calling the slice done:

- Run the actual flow (not unit tests alone)
- Confirm each "done when" check with evidence
- Ask: **Is this a shortcut or a real fix?**

### 6. Report and propose expansion

```markdown
## Subset result

**Status:** pass / fail / partial
**Evidence:** [what was run, what was observed]
**Learned:** …
**Proposed next subset:** …
```

Wait for user direction before expanding.

## Standing rules

- **Fold it in** — absorb into current milestone; no version bump for the slice itself.
- **Anti-goals in agent prompts** — when dispatching subagents for subset work, include explicit non-goals.
- If the slice fails, diagnose before expanding — don't pile on scope.

## Not this skill

- **brief** — sharpen a vague prompt before any work starts
- **audit** — review an artifact; subset is about scope control during implementation
- **brainstorming** — full design exploration for new features
