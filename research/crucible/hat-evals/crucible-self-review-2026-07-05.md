# Crucible reviews itself — hats panel synthesis (2026-07-05)

**Verification 2 of 2.** The four new agentic-infra hats (prompt-engineer, harness-engineer, skill-designer, eval-engineer) run as a blind parallel panel on the crucible plugin. Synthesis in the main thread (never a panelist [D10]).

## Verdict

**Crucible is well-built, and the panel proved it works by finding its own real defects.** No blockers. The four lenses stayed in-lane, converged on the load-bearing problems, and each credited what's genuinely right. The strongest outcome is not any single finding — it's that a review system, pointed at itself, surfaced structural holes in its own measurement layer and a broken hook. That's the dogfood succeeding.

## Where the hats converged (highest confidence — multiple independent lenses)

1. **The plan-mode hook does not work as designed.** harness-engineer (F1): `additionalContext` on a `PreToolUse` hook reaches the *model, not the user*, so the nudge — authored for the human ("or say no and proceed as-is") — can't reach its recipient; and "never-blocking + user-visible" is structurally unsatisfiable on `PreToolUse` (the only user-facing channel, `permissionDecision`, blocks). skill-designer (F4) independently: even if it fired, it always routes to red-vs-blue, wrong for completeness-shaped plans (migration/schema) that belong to hats+coverage. Two lenses, same conclusion: **the hook needs a rethink** (different event like `UserPromptSubmit`, or a skill-level suggestion instead of a hook).

2. **The evaluation layer doesn't measure what it claims.** eval-engineer, four majors: (F1) benchmark recall saturated at 100% on every config, so it can't answer the tier question it's cited for — yet pins route through it, including a panelist "validated" at sonnet/medium *that was never run*; (F2) the overlap eval *instructs* reviewers "failure_class MUST be one of your declared classes," forcing the out-of-class count toward zero — so "perfect lane discipline" is a **structural artifact, not evidence of distinctness**; (F3) the architect panel had no clean controls, so its "0 FP" is zero-by-construction yet cited for the blue pin; (F4) the skills' evals.json are structure-validated only, never run against a live agent, so a broken skill passes. These are fair, and they land on *my own phase-3 work*.

3. **wardrobe's identity is self-contradictory.** skill-designer (F1) + prompt-engineer (F4): it ships an invocation trigger ("Use when creating, editing, or choosing a hat…") while the body says "Nothing here is invoked directly," and that trigger vocabulary collides with consult/hats — the router could fire a do-nothing reference lib when a review was wanted.

## Other real findings

- **Dispatch collapse (harness F3, major):** hats/red-vs-blue don't declare main-thread-only, but plan-orchestrator may invoke them "via subagent prompt" — and a subagent has no `Task` tool, so the 3–4-way fan-out silently collapses to a single self-review (the exact single-reviewer degradation D1 warns against). No fallback declared.
- **New hats under-surfaced (skill-designer F2, minor):** the four agentic-infra hats are in `wardrobe/SKILL.md` but missing from the `hats` skill's own roster and the README's "10-hat" count — the newest lenses are the least discoverable. *(Self-inflicted this session — fixed, see below.)*
- **effort pins may be inert (harness F2, minor):** `effort:` is a foundry convention (curator.md) but unverified as a Claude Code subagent frontmatter key — if the loader ignores it, the fourth tuple axis is dead metadata.
- **context-bloat (prompt-engineer F1, minor):** bare `[D14]`-style provenance tags and repeated path-fallback boilerplate in the agent payloads — non-task tokens by the files' own doctrine.
- **missing rationalization counter (prompt-engineer F2, minor):** "raise, don't fix" / "do not implement" are bare prohibitions with no counter to the "it's a one-line fix" excuse.
- Minor/nit: `${CLAUDE_PLUGIN_ROOT}` not substituted in body text (harness F4); hook silently no-ops without `jq` (harness F5); hook autoload unverified (harness F6); trigger/units ambiguities (prompt-engineer F3/F5); unowned eval scoring + overlap-judge not anonymized + N=1 overfitting (eval F5–F8).

## What the panel confirmed is RIGHT (credit, per the raise-don't-fix ethos of surfacing the sound too)

- SDO anti-pattern correctly avoided — no skill description leaks its workflow (prompt-engineer).
- "raise, don't fix" enforced *structurally* — agents carry no Edit/Write; no Task tool so panelists can't nest (harness-engineer).
- Blind-parallel topology + main-thread synthesis correct [D10]; missing-agent and missing-lens fallbacks specified (harness-engineer).
- Correct hook *primitive* (a hook, not a skill-to-remember), stated skill boundaries via "Not this skill", good progressive disclosure, no silent auto-chain (skill-designer).
- The benchmark judge *is* config-anonymized; the corpus ground truth *is* falsifiable (eval-engineer).
- The team applied its own evidence (effort avoids `max` per the benchmark) and self-flagged saturation/N=1/deferred work honestly (eval-engineer, prompt-engineer).

## Recommended actions (sorted)

**Fixed already (self-inflicted hygiene):** new hats added to `hats/SKILL.md` roster + README count corrected.

**Your call — substantive, involve design decisions:**
1. **Hook:** rethink the channel (it can't nudge the user on `PreToolUse`) or downgrade to a documented-but-off example. Biggest single defect.
2. **Eval methodology:** (a) make the overlap eval's out-of-class measurable (let reviewers emit any label, or have the judge re-classify); (b) re-run the architect panel with clean controls before citing its FP; (c) stop citing sonnet/medium as "validated" (never ran); (d) label evals.json "spec, not test" or build a live-agent harness. None invalidate the *skills* — they invalidate some *claims about the measurements*.
3. **Dispatch guard:** add "run from main thread; if dispatched as a subagent, review in-thread and say so" to hats/red-vs-blue.
4. **wardrobe identity:** decide reference-only (drop the trigger clauses) vs invocable authoring skill (rewrite the body).
5. Verify `effort` is honored (one A/B), and the smaller prompt/context-bloat items.

All findings have file:line evidence in the four panelist transcripts.
