# plan-orchestrator

A Claude Code skill for decomposing complex, multi-component, multi-day software work into a contract-driven DAG of phases with explicit stage gates, transparency protocols, and composition with existing skills.

The skill turns ambitious work into rigorous, auditable execution at scales where a single agent's context cannot hold everything at once. The architect (Opus) coordinates phase planners, edge reviewers, a skeptic, audit skills, and implementers — each with strict halt-and-escalate and assumption-surfacing rules.

---

## When to invoke

Invoke the skill (`/plan-orchestrator`) when ALL of these hold:

- You have a clear **what**, **why**, and **measurable metrics**
- You don't yet have a clear **how** (architecture, decomposition, contracts)
- The work crosses **two or more components** / services / layers
- Estimated effort is **multi-hour or multi-day**

If any of these is missing, the skill refuses early and recommends:
- Missing what/why/metrics → `superpowers:brainstorming`
- Trivial single-file work → `superpowers:writing-plans`

There is a primary qualitative gate at invocation: *can the user describe the work in one paragraph and one component?* If yes, the skill exits and recommends `writing-plans`. This is non-negotiable; the numeric overkill score cannot override it.

## Cost

Typical strong-fit run: 30–60 Opus dispatches + 10–20 Sonnet + ~50 Haiku checks. Rough wall-clock + token cost: twenty to one hundred dollars depending on context sizes. The skill emits this estimate at invocation; you decline before any dispatch happens.

## How to use

### Step 1 — write the spec

Author a spec covering these fields. Missing any → skill halts with a precise list.

| Field | Purpose |
|---|---|
| `what` | Concrete description of the work |
| `why` | Motivation that makes the ceremony worth it |
| `metrics` | Desk-evaluable, scriptable success bars |
| `scope` / `non-goals` | What's in; what's explicitly out |
| `constraints` | Tech / time / integration / compliance |
| `existing context` | Optional — files / docs / prior work |

See `test-beds/tasklog/spec.md` for the smallest concrete example. See `test-beds/hex-wars/spec.md` and `test-beds/habit-tracker/spec.md` for larger examples spanning frontend + backend.

### Step 2 — invoke

In Claude Code:

```
/plan-orchestrator <path-to-spec.md>
```

The skill body is presented to Opus, which becomes the architect. The architect:

1. Validates the spec against the Input Contract
2. Runs the overkill detector (refuses if undersized)
3. Creates a work-dir at `~/.claude/plan-orchestrator-runs/<project>/<ISO-timestamp>/`
4. Walks the five stages, halting at user gates

### Step 3 — be present at gates

Stage gates are the user's leverage. Four conditions must hold for any gate to auto-pass:

1. All Structural checks pass (scripts return clean)
2. All Alignment checks return YES (Haiku claim-check agrees with cited content)
3. Zero blocking escalations open in `escalations.md`
4. Zero low-confidence + medium-or-higher-risk assumptions in `pending` status

If any fails, the architect halts and surfaces to you. Auto-proceed cannot bypass blocking findings.

## The five stages

1. **Spec validation** — fields present? overkill check passes?
2. **Framing** (architect) — glossary, DAG, contract skeletons, architect adjudications, skeptic dispatch
3. **Planning** (parallel planners by DAG layer + Review Pipeline) — phase plans, edge reviewers, assumption sweep, skeptic round 2
4. **Implementation** — per-phase implementers invoking the phase's `skill_requirements` (TDD, etc.)
5. **Close-out** — audit skills, sanitized learnings, PR

Detailed mechanics live in `skill.md`. Why each piece exists lives in `design-notes.md` (72 design decisions across 4 iterations).

## What you get

After a successful run, the work-dir contains:

```
<work-dir>/
├── spec.md                  immutable, your original input
├── glossary.md              shared vocabulary
├── dag.md                   phases + contracts manifest (YAML authoritative)
├── assumptions.md           every architect adjudication, source-cited
├── contracts/               one file per contract; version-tracked, locked
├── phases/<id>/plan.md      one detailed plan per phase
├── escalations/             per-dispatch escalation files
├── escalations.md           architect's concatenated view
├── orient-latest.md         most recent ORIENT cycle's lint summary
├── learnings.md             sanitized abstract patterns
├── run-quality.yaml         post-run quality scorecard
└── TODO.md                  cycle status + dispatch counters
```

The work-dir is your audit trail. Even if the run halts halfway, every architect decision is traceable to a `source:` field (cite / derived_from / originates_at).

### The HTML review

Before the Planning gate halts for your approval, the architect runs `scripts/make-review.py` to generate `<work-dir>/review.html` — a single self-contained HTML page (no external assets, no JS deps) you open in a browser to review the full state at once:

- The four-condition gate evaluation, pass/fail per condition
- The spec (rendered markdown)
- The DAG: phases with status pills, contracts with version + lock status
- Every adjudication, filterable by status (pending / validated / revised / invalidated / wont-fix)
- Every escalation, filterable by status (open / resolved), with severity + lands-at columns
- Per-phase plans, collapsible (click to expand)
- Glossary

HTML over raw Markdown specifically because Implementation is the expensive stage to redo — you need presentation rich enough to actually inspect dozens of adjudications and edge findings without losing your place.

You can also run it manually at any time:

```bash
python3 ~/.claude/skills/plan-orchestrator/scripts/make-review.py <work-dir> --stage planning
python3 ~/.claude/skills/plan-orchestrator/scripts/make-review.py <work-dir> --stage planning --open  # macOS: open in browser
```

## Test beds — example spec shapes

The repo ships three test-bed specs you can read for shape:

- `test-beds/hex-wars/spec.md` — a turn-based hex-grid game (frontend + backend + shared types). The first test bed; surfaced the original design.
- `test-beds/habit-tracker/spec.md` — Python + TypeScript multi-component with concurrent CLI/web writes. The second test bed; produced round-2 design refinements.
- `test-beds/tasklog/spec.md` — minimal async/event-driven (single-writer producer, two independent consumers, schema evolution). The third test bed; specifically engineered to stress cascade-timing + spec-version pinning.

Each has a `<work-dir>` under `~/.claude/plan-orchestrator-runs/` if you ran it (these are not in the repo — runs are user state).

## Skill package contents

```
plan-orchestrator/
├── skill.md                       the skill body Claude reads at invocation
├── design-notes.md                72 decisions across 4 iterations
├── README.md                      this file
├── templates/
│   ├── subagent-protocol.md       HALT + SURFACE — pasted into every dispatch
│   ├── adjudication-entry.md      the `source:` field spec; cite/derived_from/originates_at
│   ├── escalation-entry.md        the per-dispatch escalation file format
│   ├── dag-skeleton.md            authoritative dag.md shape
│   ├── contract-skeleton.md       per-contract template
│   ├── phase-plan-skeleton.md     per-phase plan template
│   ├── planner-prompt.md          slot-filled planner dispatch
│   ├── edge-reviewer-prompt.md    slot-filled edge reviewer dispatch
│   ├── assumption-sweep-prompt.md slot-filled assumption sweep dispatch
│   ├── skeptic-prompt.md          slot-filled skeptic dispatch (Framing + Planning gates)
│   ├── haiku-claim-check.md       Alignment-class claim verification
│   └── haiku-coverage-check.md    Alignment-class coverage verification
├── scripts/                       Structural-class verifiers (Python 3, stdlib only)
│   ├── verify-refs.py             cites / derived-from / references / source-form
│   ├── verify-dag.py              YAML/prose consistency on dag.md
│   ├── verify-coverage.py         affects_artifacts paths exist + mtime sane
│   ├── lint-assumptions.py        adjudication format compliance
│   ├── detect-duplicate-ids.py    A/E id collisions
│   ├── name-drift.py              terminology drift between glossary and artifacts
│   └── run-quality.py             post-run quality scorecard
└── test-beds/
    ├── hex-wars/spec.md
    ├── habit-tracker/spec.md
    └── tasklog/spec.md
```

## Key design decisions to know about

- **ORIENT every cycle.** Architect state lives on disk; in-memory is never trusted. Re-read TODO.md, dag.md, escalations, assumptions on each cycle. Survives compaction.
- **Verification toolbox — three classes, parallel.** Structural (scripts, near-zero cost), Alignment (Haiku, tenths of a cent), Judgment (Opus, dollars). Catch each error with the cheapest class that can catch it.
- **Per-dispatch escalation files.** Each subagent writes to its own file under `escalations/`. No append collisions. Architect concatenates on ORIENT.
- **Reviewer-raises-don't-fix.** Reviewers find issues; original planners apply fixes with full planning authority. No edit-applier drift.
- **Cascade is field-scoped, N=3 bounded.** Mutating a contract field only restales consumers whose `consumes:` slice intersects the diff. Cascade caps at 3 iterations before halting to user.
- **Spec-version pinning.** ORIENT detects `spec.md` mtime changes; spec-citing adjudications get marked `stale-spec` and need re-validation.
- **Composition over reinvention.** Each phase declares `skill_requirements:` and the implementer MUST invoke them — TDD, frontend-design, security-review, etc. The skill orchestrates; it doesn't reinvent.

## When NOT to use

- Single-component work (use `writing-plans`)
- Spec is still vague (use `brainstorming`)
- You won't be present at gates — the skill assumes a human-in-the-loop adjudicator
- Budget is hard-constrained below ~$20

## Iteration history

- **Iteration 1:** initial design, tested on `hex-wars` test-bed (round 1)
- **Iteration 2:** decisions 42–50, tested on `habit-tracker` (round 2). Surfaced cascade-timing protection (`consumed_versions`), reserved-range numbering, etc.
- **Iteration 3:** decisions 51–64. External Opus reviewer audit produced 8 consolidations (collapsed source-field, per-dispatch escalation files, etc.). Plus round-2 refinements.
- **Iteration 4:** decisions 65–72. Tested on `tasklog` (round 3). Surfaced architect-materialization gap, dispatch-laundering of spec overrides, layered dispatch within DAG dependencies, and the source-form structural check.

See `design-notes.md` for full rationale on each decision.
