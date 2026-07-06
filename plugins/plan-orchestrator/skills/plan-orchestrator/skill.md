---
name: plan-orchestrator
description: Decompose complex multi-component features into a contract-driven DAG of phases with explicit stage gates, transparency protocols, and composition with existing skills. Use when you have a clear what+why+metrics+scope but not a clear how, and the work crosses 2+ components. Refuses to run on undersized work; delegates UI/security/code-review/etc. to existing skills via per-phase skill_requirements.
---

<!-- foundry:dependencies:start -->
## Dependencies

Registry: [`manifest.yaml`](../../../../skills/manifest.yaml) · refresh: `python3 scripts/skills_manifest.py sync-docs`

| Kind | Skills | Role |
|------|--------|------|
| **requires** | `progress-tracker` | Must exist in bundle before running |
| **suggests** | `brief`, `subset` | Soft handoff after this skill — suggest, do not auto-chain |
| **dispatches** | `audit`, `hats`, `red-vs-blue`, `grill-with-docs`, `handoff`, `design-taste-frontend` | May invoke via Skill tool or subagent prompt |
| **external** | `brainstorming`, `writing-plans`, `verification-before-completion` | Outside foundry bundle (host plugins) |

**Used by:** `progress-tracker` (suggests)

<!-- foundry:dependencies:end -->

# Plan Orchestrator

## Purpose

You (the architect) coordinate multi-component, multi-day software work via a Directed Acyclic Graph of phases connected by explicit contracts. Your job is **the wiring**: contracts, stage gates, cascade, transparency, traceability. The per-phase work itself is delegated to existing skills (TDD, frontend-design, security-review, code-review, etc.) — composition over reinvention.

Your value is enabling rigorous reasoning at scales where a single agent's context cannot hold everything at once.

## When to use this skill

ALL of the following must hold:
- The user has a clear WHAT, WHY, and MEASURABLE metrics for success
- They don't yet have a clear HOW (architecture, decomposition, contracts)
- The work crosses ≥2 components/services/layers
- Multi-hour or multi-day estimated effort

If any of these is missing, halt with a specific reason. Recommend:
- Missing what/why/metrics → `superpowers:brainstorming`
- Trivial single-file work → `superpowers:writing-plans`

## Precondition checks

Before doing anything else:
- **Architect model:** you should be Opus. Refuse on Haiku; warn (but allow) on Sonnet.
- **Input spec satisfies the Input Contract** (below).
- **Base work-dir** `~/.claude/plan-orchestrator-runs/` exists and is writable.

## Input Contract

The user-provided spec must contain these fields. Missing any → halt and list what's missing:

| Field | Purpose |
|---|---|
| what | concrete description of the work |
| why | motivation that makes the ceremony worth it |
| metrics / success criteria | desk-evaluable, scriptable bars |
| scope & non-goals | what's in; what's explicitly out |
| known constraints | tech / time / integration / compliance |
| existing context pointers | optional — files / docs / prior work |

## Overkill detector

**Primary gate (qualitative):** can the user describe the work in one paragraph and one component? If yes → exit and recommend `superpowers:writing-plans`. The numeric score below cannot override this — one-component work doesn't justify multi-stage ceremony regardless of score.

**Secondary diagnostic (the score is supplementary, not decisive):**

1. Components / services / layers touched? (1 / 2-3 / 4+)
2. Estimated effort? (<2h / half-day / multi-day)
3. New cross-component contracts? (no / yes)
4. Audits needed? (none / one / multi)

```
Q1:  1→0  |  2-3→2  |  4+→4
Q2:  <2h→0  |  half-day→1  |  multi-day→3
Q3:  no→0  |  yes→3
Q4:  none→0  |  one→1  |  multi→2
```

- **≥6** + passes primary gate → proceed
- **3–5** marginal: warn user; proceed only on explicit confirm
- **≤2** overkill: recommend `superpowers:writing-plans` and exit

**Always emit a cost estimate with the verdict.** Strong-fit runs typically take 30–60 Opus dispatches + 10–20 Sonnet + ~50 Haiku checks. Rough wall-clock + token cost: twenty-to-one-hundred dollars depending on context sizes (escape dollar signs in skill prose — the Skill tool's positional argument substitution will eat bare `$N`). Tell the user the budget before they commit.

## Work-dir creation

```
~/.claude/plan-orchestrator-runs/<project-slug>/<ISO-timestamp>/
├── spec.md                copy of user input
├── glossary.md            shared vocabulary (Framing writes)
├── dag.md                 phases + contracts manifest (Framing writes)
├── TODO.md                cycle status
├── skill-catalog.md       available skills + audit_triggers (Framing writes)
├── assumptions.md         architect adjudications (Framing writes)
├── contracts/             one file per contract (Framing sketches; Planning fills)
├── phases/                one folder per phase (Planning fills)
├── escalations/           one file per dispatch; architect concatenates
├── learnings.md           Close-out writes
└── run-quality.yaml       Close-out writes
```

---

## ORIENT (every architect cycle)

Architect state lives on disk; memory is rebuilt every cycle. Do NOT trust in-memory state across cycles.

ORIENT has three phases — **read, lint, decide** — and **redirects script output to a file**, never the terminal. Over many cycles, script output in the conversation refills the architect's context with the very state ORIENT was meant to externalize.

```
READ
  1. Read TODO.md frontmatter (current_stage, current_subagent, last_updated)
  2. Read dag.md YAML block (phase statuses, contract versions, edges)
  3. Concatenate per-dispatch files in escalations/ → escalations.md (overwrite)

LINT  (output → <work-dir>/orient-latest.md; architect reads ONLY the summary lines)
  4. Run Structural: scripts/verify-refs.py all (cites + derived-from +
     references + source-form) + verify-dag.py + verify-coverage.py +
     lint-assumptions.py → orient-latest.md (one-line OK/FAIL per check)
  5. Grep escalations.md for "status: open" → count
  6. Grep all assumptions for "status: pending" → count
  7. If spec.md mtime changed since last ORIENT: mark all spec-citing adjudications
     as `stale-spec` and require re-validation before any gate opens

DECIDE
  8. Read orient-latest.md (one screen, not raw script output)
  9. Compute next legal move per stage-gating
  10. Emit terminal one-liner
  11. Only then dispatch or act
```

After any architect mutation to `assumptions.md`, `dag.md`, or any contract: re-run LINT before declaring any gate complete.

Terminal one-liner:
```
[plan-orchestrator] orient: <stage> in progress, <X> open escalations, <Y> pending assumptions. Next: <move>
```

**Why the file redirect:** ORIENT runs every cycle; over 25 cycles the architect's conversation accumulates ~25× the lint output. `orient-latest.md` is overwritten each cycle, so the architect sees one screen of summary instead of dozens of screens of raw output. Detail is one Read away.

---

## Verification toolbox — three classes (parallel, not a ladder)

```
STRUCTURAL — scripts, near-zero cost
  Catches: format errors, dead refs, duplicate IDs, name drift, missing files
  When: every ORIENT cycle; always-on

ALIGNMENT — Haiku, roughly a tenth of a cent per check
  Catches: claim text vs cited source discrepancies
  When: after every architect adjudication; before every stage gate

JUDGMENT — Opus, roughly ten cents to one dollar per check
  Catches: semantic gaps, omissions, cross-edge interactions
  When: cycle boundaries — the Review Pipeline
```

Always catch errors with the cheapest class that can catch them. Don't pay Opus for what a script could find.

---

## The Procedure — five stages

### Stage 1 — Spec validation

1. Copy user-provided spec to `<work-dir>/spec.md`
2. Verify all Input Contract fields present
3. If missing → halt with precise list
4. On pass → update TODO.md (Spec ✓), proceed to Framing

### Stage 2 — Framing (architect)

Every step that has a template MUST open it before writing. Architects under context pressure who write artifacts from intuition produce shapes that downstream verifiers reject (round-3 R3-3). Open the template; fill it.

In order:

1. **Survey project / repo** — existing CLAUDE.md, README, key architectural files
2. **Discover available skills** — write `skill-catalog.md` (each skill: namespace, purpose, stage of use; define `audit_triggers`)
3. **Decompose into phases** — fill `templates/dag-skeleton.md`. **The YAML in the frontmatter is authoritative for `verify-dag.py` and the cascade engine.** Don't put the phases/contracts YAML in a body code block.
4. **Write `glossary.md`** — shared vocabulary, WRITTEN BEFORE any planner runs
5. **Sketch contract skeletons** — one file per contract in `contracts/`, filled from `templates/contract-skeleton.md`
6. **Write `assumptions.md`** — architect adjudications using the structure in `templates/adjudication-entry.md`. Exactly one `source:` form per adjudication; `verify-refs.py source-form` will reject coexistence.
7. **Run Alignment checks** (haiku-claim-check + haiku-coverage-check) on each adjudication
8. **Update `TODO.md`**
9. **Dispatch the Skeptic** (fill `templates/skeptic-prompt.md`)
10. Emit terminal status, halt for Framing gate

**Framing gate:** automatic gate evaluation (below) + user reviews architect adjudications and skeptic findings.

### Stage 3 — Planning (layered dispatch + Review Pipeline)

Planning dispatches happen in **DAG-dependency layers**, not all-at-once. Layer 0 = phases whose `consumes:` is empty. Layer N = phases whose `depends_on` is fully covered by layers 0..N-1. Within a layer, planners run in parallel. Across layers, sequence — a layer-N planner reads the locked contracts produced in layer 0..N-1.

Why not all-at-once: a layer-N planner dispatched before its dependencies have returned reads framing-sketch contracts (v0.1) and re-plans against pre-lock state. Cascade catches this on return, but the cost is wasted dispatches. Layered dispatch avoids the bootstrap waste; the cascade engine still handles late refinements within a layer.

Per planner dispatch:

1. Fill `templates/planner-prompt.md`. Never free-form.
2. Capture each consumed contract's version at dispatch time; pass to planner; planner mirrors as `consumed_versions:` in output. On return, compare to current on-disk versions; re-dispatch any planner whose consumed version was bumped during its run.

**Between planner returns and the Review Pipeline — architect materializes contract version bumps on disk.** Planners promise version bumps in their plans (e.g., "lock C1 to v0.2") but cannot rewrite contract files; that's an architect responsibility (round-3 R3-8). Walk every contract; absorb each planner's promised deltas; bump the YAML `version:` field; set `locked: true`. Skipping this step leaves reviewers chasing phantom contracts.

Then run the **Review Pipeline**:

1. **Structural verifier** (scripts, free)
2. **Alignment checks** (Haiku claim-check + coverage-check on every adjudication)
3. **Edge review** (parallel Opus per producer↔consumer edge) — fill `templates/edge-reviewer-prompt.md`. Edge reviewers MUST also check: does any architect adjudication or dispatch override a spec or contract section without an explicit `revised`-status A-id? (Round-3 R3-6: architect dispatch prompts can launder spec-contradicting directives.)
4. **Assumption sweep** (single Opus) — `templates/assumption-sweep-prompt.md`
5. **Skeptic** (second invocation) — `templates/skeptic-prompt.md`
6. Optional **Synthesis review** (Opus + thinking) if DAG has ≥4 phases or steps 3-5 surfaced cross-edge concerns

Findings flow back to ORIGINAL planners with full planning authority — no edit-applier.

**Parallel dispatch note:** the harness only runs Agent calls in parallel if they appear as multiple tool_use blocks in a single response. Multiple Agent calls across separate responses serialize. To actually parallelize, batch them.

**Before halting at the Planning gate — generate the HTML review.** Run `scripts/make-review.py <work-dir> --stage planning` to produce `<work-dir>/review.html`. This is a single self-contained HTML file the user opens in a browser to review the full state: spec, DAG, contracts, every adjudication (filterable by status), open and resolved escalations, per-phase plans (collapsible), and the four-condition gate evaluation. HTML over Markdown specifically because Implementation is the most expensive stage to redo — the user needs presentation rich enough to actually inspect, not raw artifacts. Tell the user where the file is and (optionally) `open` it for them.

**Planning gate:** automatic gate evaluation + user approves after reviewing `review.html`.

### Stage 4 — Implementation

For each phase, dispatch an implementer (Sonnet, thinking off; Opus if HIGH-COMPLEXITY: ≥5 tasks OR ≥3 contracts OR stage-blocking concerns surfaced).

Each dispatch carries: `subagent-protocol.md` verbatim, `plan.md`, consumed+produced contracts, `skill_requirements` (implementer MUST invoke). Implementer writes `phases/Pn/status.md` after every task. If context approaches 80% → halt with `status: halted, reason: context-budget`; architect dispatches a new instance with the original plan + status.md; resume from `tasks_in_progress`.

Before marking phase complete: run `verify-phase-complete.py Pn` (deterministic, external). Implementer cannot self-declare complete.

**Implementation gate:** automatic gate evaluation + all phases verified complete.

### Stage 5 — Close-out (Audit + Synthesis)

**Audit pass:**
For each audit phase in dag.md:
1. Dispatch the audit skill (`security-review`, `pr-review-toolkit:review-pr`, etc.)
2. Findings → per-dispatch escalation file with `lands_at: <stage>` field
3. Route findings to the indicated stage; mutate there; cascade per field-scoped rule; re-dispatch affected planners/implementers with full authority
4. Re-run audits against new state
5. Loop until clean OR N=3 iterations → halt to user (see "When things go wrong")

**Synthesis (after audit clean):**
1. Draft `learnings.md` (abstract patterns only; no specific names/paths/IDs)
2. Run `run-quality.py` → writes `run-quality.yaml`
3. Propose PR description
4. Invoke `commit-commands:commit-push-pr`
5. Emit final terminal status (green / yellow / red)

**Close-out gate:** audits clean OR remaining findings accepted by user as advisory-with-followup.

---

## Automatic gate evaluation

ALL FOUR must hold for any gate to pass automatically (no user pause):

1. All Structural checks pass (exit 0 from the verifier)
2. All Alignment checks return YES (none NO; UNSURE escalates)
3. Zero blocking escalations open in `escalations.md` (after concatenation in ORIENT)
4. Zero low-confidence + medium-or-higher-risk assumptions in `pending` status

If any fails: architect halts and surfaces to user. Auto-proceed cannot bypass blocking findings.

---

## Architect adjudication structure

See `templates/adjudication-entry.md` for full structure and examples. Required fields:

```yaml
- id: A<N>
  claim: "..."
  rationale: "..."
  confidence: high | medium | low
  risk_if_wrong: "..."
  source:                            # exactly one form
    cite: [{file, anchor}, ...]      # OR
    derived_from: [Ax, Ay]            # OR
    originates_at: <stage>
  affects_artifacts: [paths]
  status: pending | validated | invalidated | revised | wont-fix
  validated_by: -
  validated_at: -
```

Structural scripts verify `source` resolves; Alignment Haiku checks verify claim matches cited content and that affects_artifacts contain the called-for changes.

No memory-based architect text. If you don't have the cited section open, Read it before writing the claim.

---

## Cascade engine

When a contract is mutated:
1. Snapshot old version
2. Run `invalidate.py <contract-id>`: field-level diff; for each consumer phase, if `diff ∩ P.consumes[C]` is non-empty, mark P stale
3. Stage-gating prevents downstream progress until stale phases re-pass

When an adjudication is invalidated:
1. Find artifacts that depended on it (per `affects_artifacts:`)
2. Mark them stale
3. Re-plan / re-implement against the corrected adjudication

**Convergence guarantee — max 3 cascade iterations.** If three rounds of consumer re-dispatch don't quiesce (one consumer's refinement keeps triggering another consumer's restale), halt and surface to user. Options at that point: (a) pin all producer contracts at current versions and force consumers to live with what they have, (b) descope the offending contract field, (c) revisit Framing for that subgraph. Same N=3 bound as audits (parallel discipline, parallel escape hatch).

**Spec mutation handling.** `spec.md` is the root cite source; revising it can silently invalidate every adjudication that cites it. ORIENT checks `spec.md`'s mtime each cycle; if it changed, all adjudications with a `cite:` to `spec.md` are marked `stale-spec` and need re-validation against the new content before any gate opens. The architect cannot revise the spec without paying the re-validation cost.

---

## Subagent dispatch — templates

Every dispatch carries `templates/subagent-protocol.md` verbatim (combined halt-and-escalate + assumption-surfacing).

Judgment-class templates (architect fills slots, never writes scaffolding from scratch):
- `templates/planner-prompt.md` — Planning-stage planners
- `templates/edge-reviewer-prompt.md` — Edge review per edge
- `templates/assumption-sweep-prompt.md` — Assumption sweep
- `templates/skeptic-prompt.md` — Skeptic (Framing-gate and Planning-gate)

Alignment-class dispatch patterns:
- `templates/haiku-claim-check.md`
- `templates/haiku-coverage-check.md`

**Per-dispatch escalation files:** every subagent writes its escalations to its own file at `<work-dir>/escalations/<dispatch-id>.md` (NOT to a shared `escalations.md`). Architect concatenates on each ORIENT. This eliminates parallel-appender numbering coordination — no reserved ranges, no read-before-append, no collisions.

---

## Model and effort allocation

| Dispatch | Model | Thinking |
|---|---|---|
| Architect (you) | Opus | high |
| Phase planner | Opus | medium |
| Edge reviewer | Opus | off |
| Assumption sweep | Opus | medium |
| Skeptic | Opus | high |
| Haiku claim check | Haiku | off |
| Haiku coverage check | Haiku | off |
| Implementer (default) | Sonnet | off |
| Implementer (HIGH-COMPLEXITY) | Opus | off |

**Track in TODO.md:** `opus_dispatches`, `sonnet_dispatches`, `haiku_dispatches`. Warn at 50 Opus per run; hard halt at 100.

**Bash invocations:** every command ends with `; :` or `|| true`. Non-zero exits cancel parallel tool calls in the harness — exit-0 guards prevent collateral damage.

---

## Reviewer scoring culture

> A reviewer that finds zero issues on a complex edge is suspect. A reviewer that finds many is doing its job. **Never penalize a reviewer for finding.**

Reviewers raise issues; they don't fix them. Fixes flow back through original-planner-authority.

---

## When things go wrong (failure-mode branches)

**False-positive Haiku check (NO returned but architect believes Haiku is wrong):**
Override by setting the Alignment finding to `dispute: <reason>` and dispatching a Judgment-class Opus review to adjudicate. If Opus also says NO, the adjudication is wrong (fix it). If Opus says YES, Haiku was wrong; log as a calibration data point in `learnings.md`. Never silently accept a Haiku NO without follow-up — that's how Haiku miscalibration ossifies.

**Partial planner failure (parallel planners return inconsistently):**
Wait for all dispatched planners to return (clean / halted / aborted). Do NOT enter the Review Pipeline with partial returns — its assumptions break. Re-dispatch halted planners with the corrections derived from their escalations; abort and re-dispatch timed-out planners with the same context. If a planner halts twice on the same issue, escalate to user — it's a structural problem, not a planner problem.

**Audit loop hits N=3 iterations without clean:**
Halt to user with the full list of remaining findings classified by `lands_at`. User picks: (a) accept-with-followup (file v2 issues, ship with caveats), (b) descope feature (remove the contributing requirement from spec), (c) one more iteration with a new directive (architect re-dispatches with user's direction). Never silently continue past N=3.

**User rubber-stamping risk (architect dumps 30 adjudications at a gate; user accepts all without reading):**
At gates with >10 adjudications, present a tiered summary:
- **Tier 1 — high-impact decisions** (top 5 by `risk_if_wrong * (1 - confidence)`): user must review individually
- **Tier 2 — medium-impact**: user may batch-accept with a single confirmation
- **Tier 3 — mechanical / restatements**: default-accept unless user opts in to review

This converts blanket rubber-stamping into deliberate batching.

---

## Harness-fit caveats

What this design assumes that Claude Code's harness doesn't always cleanly provide:

- **Per-dispatch model/thinking selection:** Agent tool exposes `model` but not extended-thinking levels per dispatch. The model-allocation table is partly aspirational — if the harness picks differently, work proceeds but cost/quality may shift.
- **Truly-parallel monitoring:** the architect cannot poll dispatched subagents' status while blocked on an Agent call. "Heartbeat" only works between dispatches, not during. Don't design for continuous monitoring.
- **All-or-nothing parallel tool calls:** one tool returning non-zero (or erroring) cancels all parallel tools in the same call. Use exit-0 guards on Bash; dispatch Agents in batches where failures are independently recoverable.
- **Haiku dispatch overhead:** per-call wall-clock cost is non-trivial even for Haiku. 60 Haiku checks doesn't run in 60ms; batch them across cycle boundaries, not all at once.
- **Cross-session state:** the shared learnings library (if/when re-enabled) would be a contention surface across sessions; that's why it's deferred.
- **Skill tool argument substitution eats bare `$N`:** when this skill is invoked with arguments, the Skill tool substitutes positional `$0`, `$1`, etc. in the skill body BEFORE presenting it to the architect. Cost notation like `$0.10` or `$20–$100` in skill prose gets eaten as a path-substitution. Skill prose MUST use worded form ("ten cents", "twenty to one hundred dollars") or escape with backslash. Round-3 R3-0 caught this on the first invocation.

---

## Cross-project learning

**Deferred.** A shared library at `~/.claude/plan-orchestrator-shared-learnings/` was designed earlier but with 0 entries across 2 test runs there's no evidence the pattern reuse helps. For now, `learnings.md` is per-run only. Re-evaluate after ~10 real runs.

---

## Key rules (reference)

- **Composition over reinvention** — delegate to existing skills
- **Stage-gating** — next stage cannot start until current passes its gate
- **Match verification class to error class** — never pay Opus for what a script could catch
- **Adjudication `source:` field required** — exactly one of `cite:` / `derived_from:` / `originates_at:`
- **`affects_artifacts:` required** for any decision propagating to other files
- **Strict assumption resolution before Implementation** — no spike phases
- **Cascade is field-scoped** — internal phase changes don't cascade
- **Heartbeat after every task; verification before completion**
- **ORIENT every cycle** — never trust in-memory state
- **Original-planner-authority on rework** — no edit-applier
- **Architect's own adjudications surface to user** before any planner dispatches
- **Per-dispatch escalation files** — no shared escalations.md write contention
- **Atomic writes on monitored files** — write to `.tmp`, rename; never stream partial state to `status.md` / plan.md / escalation files
- **Cascade and audit both cap at N=3 iterations** — loops surface to user, never silently spin

---

## Anti-patterns

- Inventing audit logic — use existing audit skills
- Letting subagents apply reviewer edits — findings return to original planners
- Vague metrics in the spec — force sharpening at Spec stage
- Code-based exploration to validate assumptions — use spec revision instead
- Skipping stage gates or auto-proceeding past blocking findings — same prohibition
- Treating audit findings as code-only changes — classify by `lands_at` stage
- Self-declared phase completion — verification is deterministic and external
- Carrying state in the architect's head — every cycle starts with ORIENT
- Writing reviewer prompt scaffolding from scratch — fill template slots
- Adjudication without a `source:` field — Structural blocks
- Bash without exit-0 guard
- Skipping `consumed_versions:` in planner output — cascade-timing protection fails silently
- Silently accepting a Haiku NO without follow-up review
- Dumping >10 adjudications at a gate without tiering — invites rubber-stamping
- Streaming partial state to monitored files — write atomically (`.tmp` + rename)
- Spinning the cascade past N=3 iterations — bound exists; honor it
- **Architect dispatch prompts contradicting spec or contract without a prior `revised`-status adjudication** — laundering directives through dispatch language defeats the assumption-surface protocol (round-3 R3-6)
- **Architect writing dag.md / contracts from intuition rather than filling the template** — `verify-dag.py` parses the YAML frontmatter specifically; ad-hoc shapes silently fail verification (R3-3)
- **Promising contract version bumps in plans without materializing on disk** — reviewers chase phantom contracts; architect MUST rewrite contract files between planner returns and review pipeline (R3-8)
