# New agentic-infra hats — dry-run distinctness eval (2026-07-05)

**Verification 1 of 2** before dogfooding crucible on foundry. Four new hats (prompt-engineer, harness-engineer, skill-designer, eval-engineer) minted for foundry's own domain. Workflow: `scripts/workflows/hat-evals.js` on the crucible design doc. Judge: opus/high.

## Verdict: PASS — acceptably distinct, no voice collapse

- **Perfect lane discipline** — all four hats produced 0 out-of-class findings (every finding inside its own declared classes).
- **Zero pairwise overlap across all 6 pairs** — including the close-neighbor prompt-engineer ↔ skill-designer (0), which was the distinctness risk. Each hat attacked a different region: prompt-engineer on gate wording, harness-engineer on hook mechanics, skill-designer on namespace/routing, eval-engineer on benchmark rigor.
- **All four beat the no-persona control** — each surfaced ≥1 in-class defect the generic reviewer missed.

## Dogfood highlights (the hats found real issues in crucible's own design)

- **harness-engineer → real hook bug:** the plan-review-nudge hook fires `PreToolUse`/`ExitPlanMode` with `additionalContext`, which reaches the **model, not the user** — so the nudge cannot inform the finalization it targets (event/timing mismatch). Also: no verification the plugin hook autoloads (disclosed silent no-fire path). **Action: revisit the hook before relying on it.**
- **eval-engineer → caught our own weak spots:** (1) the adjudicator gets the strongest pin on reasoning alone while conceded "un-benchmarked" — the most consequential allocation has no falsifiable check; (2) "red must not use max" is generalized from the single non-saturated axis of a corpus the doc itself flags as not-yet-representative. Both are fair hits on my phase-3 conclusions.
- **skill-designer:** wardrobe is declared reference-only yet ships router-visible trigger frontmatter (router could dispatch a dead-end); the hats-vs-audit boundary is never stated.
- **prompt-engineer:** "high-stakes" is an undefined load-bearing term; the worthiness gate gives no operational threshold.

## Note
One near-collision: eval-engineer's non-discriminating-metric finding brushed the control's stale-content note — but eval cleared the bar on its two other unique catches. No hat cut.

---

## Corrected re-run (2026-07-05, after fixing the instrument)

The eval-engineer hat, dogfooded on crucible itself, caught that the FIRST run above used a **rigged instrument**: `hat-evals.js` *instructed* reviewers "failure_class MUST be one of your declared classes," forcing out-of-class toward zero before measurement — so "0 out-of-class / 0 overlap" was partly manufactured. Fixed: reviewers now label naturally, and the **judge independently re-classifies** every finding against all hats' taxonomies with hat names hidden (anonymized to Reviewer-N). Then re-ran the same eval on the same artifact.

**The conclusion held — and now it's honest:**

| Metric | First run (rigged) | Corrected run (judge-classified) |
|---|---|---|
| Out-of-class findings | 0 each (forced by instruction) | **0 each (independently classified — all 15 findings judged in-lane, none reassigned)** |
| Pairwise overlap | 0 across all 6 pairs (instrument blind to it) | **1** (prompt-engineer ↔ skill-designer, on review-skill routing ambiguity — judged *complementary*, different angles) |
| Beats control | all 4 | all 4 |

The corrected instrument **proves it isn't just returning zeros**: it registered a real 1-finding overlap where one genuinely exists — the close-neighbor pair (prompt-engineer/skill-designer) I flagged as the distinctness risk when minting. So the zero out-of-class is now a *measurement*, not an artifact, and the four hats are genuinely distinct.

Bonus: the re-run surfaced more real crucible issues (red-vs-blue collapses to self-review when nested under plan-orchestrator; silent blue-agent failure → false "proceed"; "hats" token overloaded across three referents; wardrobe-as-wrong-primitive). Several were already fixed this session (dispatch guard, wardrobe→reference-only, pin claims); the rest are logged below.

**Still open after the fix pass:** silent blue-failure handling (no retry/timeout/fallback), the "hats" naming overload, and hook autoload verification (needs a live install).
