# Contract-DAG Skill — Design Notes

Running log of decisions made during brainstorming. Read this file first to resume the design conversation across context-window resets.

Brainstorming started: 2026-05-17
Author: Piyush Satti

---

## Source material

User-provided retrospective: "Contract-Driven Multi-Agent Development: A Session Retrospective."

Summary: a single user prompt was decomposed across ~25 subagent invocations into a working, tested, security-audited refactor. Structured as a DAG of four phases, three interface contracts, halt-and-escalate protocol. Tiered Opus (planning/review/audit) + Sonnet (implementation). Reviewer-between-planning-and-execution caught 11 blocking inter-phase mismatches. n=1 success.

The retrospective listed gaps the framework didn't yet handle (single-reviewer SPOF, edit-applier drift, long-phase supervision, security as afterthought, sensitive planning artifacts, untyped contracts, untested escalation protocol, no persistent learning, architect blindspot, cost asymmetry on small work).

Goal: design the **base-class** skill — a general contract-DAG framework, shape-agnostic. Derived skills (user-story, bugfix, refactor, perf-sec) come later.

---

## Decisions captured

### 1. Trigger (topic 1)
- **Explicit invocation only.** Skill never auto-fires.
- User invokes when they have: clear *what*, strong *why*, defined *metrics/success criteria*, but no clear *how*.

### 2. Input contract (topic 4a)
Skill requires structured user input satisfying these fields:

| Field | Required | Purpose |
|---|---|---|
| What | yes | Concrete thing to build/fix/change |
| Why | yes | Justifies ceremony, informs tradeoffs |
| Success criteria / metrics | yes | Defines "done"; lets auditor verify |
| Scope & non-goals | yes | Bounds phases; defines what's *not* a divergence |
| Known constraints | yes | Tech, time, integration, compliance |
| Existing context pointers | optional | Files/docs/prior work — saves rediscovery tokens |

- Accepts any artifact type (user story, bug report, PRD, RFC, refactor brief) as long as the field set is present.
- If fields missing → skill halts with a precise missing-fields list, recommends `superpowers:brainstorming` to elicit them.
- Skill **does not duplicate** brainstorming elicitation.

### 3. Scope: base class (topic 4b)
- v1 is the general framework, **shape-agnostic**.
- Derived skills (user-story-specific, bugfix-specific, etc.) layer on top later.
- One general DAG-building strategy; reviewer step catches bad shapes.

### 4. Context budget (topic 2 — cross-cutting constraint)
- Per-agent target: **≤180k working tokens** (70% of 256k window).
- Implications:
  1. **Contracts are the throttle.** A phase's working set = phase plan + relevant contracts + minimal repo slice. If that exceeds budget, the phase must be split.
  2. **Single-Opus reviewer doesn't scale** to large projects — need sharded reviewers or field-level (interface-only) review.
  3. **Architect state must live on disk.** Main thread can be compacted without catastrophe; re-reads `dag.md` to re-orient.
- Reframing: the skill is fundamentally a **context-sharding engine that uses contracts as the cut lines.**

### 5. Directory layout (topic 3)

```
<work-dir>/
├── spec.md              user input
├── glossary.md          shared vocabulary (written FIRST, before any planner runs)
├── dag.md               manifest: nodes, edges, status, escalation refs
├── contracts/
│   └── C1-<name>.md
├── phases/
│   └── P1-<name>/
│       ├── plan.md
│       ├── status.md    heartbeat + checkpoints
│       └── review.md
├── cross-review.md      cross-phase reviewer output
├── audits/              created only when audits run
│   └── A1-security.md
├── escalations.md       single append-only log
└── learnings.md         written at completion, sanitized
```

### 6. Where work-dir lives (topic 10 partial)
- **Outside the repo:** `~/.claude/plan-orchestrator-runs/<project>/<timestamp>/`
- Pointer file inside repo: `.contract-dag-ref` (path + timestamp)
- Rationale: zero leak risk by default; archives every run for cross-project learning; survives branch switches and fresh clones; architect compaction recovery is just re-reading `dag.md`.

### 7. Cascade rule (topic 6 partial)
- **Option (b): contract-scoped field-level invalidation.**
- When a contract is mutated:
  - Compute field-level diff between `C_old` and `C_new`
  - For each consumer phase P: if `diff ∩ P.consumes[C]` is non-empty, mark P stale
  - Stale phases require re-planning + re-review against the new contract
- Internal-only changes to a phase (that don't touch contracts) do not cascade.
- **The invalidation rule is a script, not an LLM call.** Deterministic; saves tokens; enforceable.

### 8. Contract format (topic 5)
Sectioned markdown with YAML frontmatter. Each `##` heading is a "field" with a stable anchor (slug). Consumers declare which fields they read.

```markdown
---
id: C1
name: config-loader-interface
producer: P1
consumers:
  P3: [signature.load_config, behaviour.cache_invalidation]
  P4: [signature.load_config]
status: locked
version: 1.2
---

# C1 — Config Loader Interface

## signature.load_config
- input: `path: Path`
- output: `Config`
- raises: `ConfigError`

## behaviour.cache_invalidation
- Cached after first load
- `reload_config()` invalidates

## non_goals
- Async loading
```

### 9. Escalation semantics
- **Blocking rule:** unresolved escalation on N blocks all descendants(N) from starting.
- **Cascade rule (b):** mutation to a contract field invalidates only consumers that read that field. Internal phase changes don't cascade.

### 10. `dag.md` format (topic 6)
- **Option (c) — hybrid, YAML authoritative.** YAML frontmatter (or fenced YAML block) is the source of truth for the invalidation script. Prose below is for humans.
- If YAML and prose disagree → escalation raised (type: `yaml-prose-mismatch`). YAML does NOT silently win.
- YAML must encode: phases (id, name, produces, consumes-with-fields, status, depends_on, escalation refs); contracts (producer, version, locked status).
- Viewer / visualizer (topic 13) renders from YAML directly.

### 11. Escalation entry format (topic 6)
Every entry in `escalations.md` has this structured header:

```
## E<N> — <ISO timestamp> — <type-slug>
- severity: blocking | advisory
- detected_by: <agent-id or script-name>
- source: <file or phase id>
- type: contract-mismatch | yaml-prose-mismatch | missing-input |
        plan-incoherence | safety-concern | scope-creep | other
- blocks: <list of phases/ops that can't proceed until resolved>
- claim: <one-line description>
- suggested_resolution: <one-line best guess>
- status: open | acknowledged | resolved | wont-fix
- resolved_by: -
- resolved_at: -
```

Resolutions append a new entry rather than mutating the original (keeps audit history).

### 12. `verify-dag.sh` discipline (topic 6)
- **Option (b) — architect auto-runs** after any subagent that touched `dag.md` returns.
- Script is deterministic: parses YAML, parses prose markers, compares structural claims, exits non-zero on mismatch.
- Hook-enforced (option c) deferred to a future iteration — user not yet using hooks.

### 13. Halt-and-escalate boilerplate (topic 11 partial)
- Lives in: `~/.claude/skills/plan-orchestrator/templates/halt-protocol.md`
- Included **verbatim** in every subagent dispatch (planners, reviewers, implementers, auditors).
- Three jobs: (1) grant explicit permission to halt, (2) name specific triggers (blocking + advisory), (3) reframe halting as success.
- This is the *behavioral* half of the escalation protocol; the file/format is the *mechanical* half.

### 14. Assumption-Surfacing Protocol (topic 7b)
- Non-blocking counterpart to halt-and-escalate. Subagents proceed but explicitly surface choices they made.
- Format: structured `assumptions[]` block in artifact frontmatter or dedicated section.
- Fields: `id`, `claim`, `rationale`, `confidence` (high/med/low), `risk_if_wrong`, `status` (pending/validated/invalidated/revised), `validated_by`, `validated_at`.
- **Cascade extension:** invalidating an assumption marks downstream work stale (same machinery as contract-field cascade, decision 7).
- **Architect's own assumptions surface to USER.** Skill blocks any planner dispatch until user has validated the architect's reading of the spec. This is the structural fix for the architect-blindspot gap.
- Lives in: `~/.claude/skills/plan-orchestrator/templates/assumption-surfacing.md`
- Together with halt-protocol (decision 13), forms the **transparency protocols** — every place agent judgment enters the system is made visible.

### 15. Validation routing (topic 7b)
- **Option (a): strict synchronous.** Architect validates EVERY subagent's return (assumptions + output) before next dispatch.
- Rationale: prevents wrong-assumption propagation; matches the base-class skill's rigorous philosophy.
- Cost: more architect cycles. Mitigated because most assumptions are `confidence:high × risk:low` → quick ack. Only `confidence:low × risk:high` requires real adjudication.
- Derived skills (future) may relax to risk-tiered routing using the confidence × risk matrix.
- Validators may **delegate verification** to a small subagent (e.g., "read the repo and confirm assumption A2") rather than personally checking — keeps the validation flow scalable.

### 16. Layered review pipeline (topic 7)
Four layers, each with bounded scope:

| Layer | Type | What it sees | Cost |
|---|---|---|---|
| L1 — Deterministic scripts | `verify-dag.sh`, `validate-contracts.sh`, `check-consumption.sh`, `lint-assumptions.sh` | Specific files | ~0 tokens |
| L2 — Edge reviewers (parallel Opus) | One per producer→consumer edge: contract + consumer's plan slice | Bounded context per edge | ~30k tokens × N edges |
| L3 — Assumption auditor (single Opus) | All `assumptions[]` across work-dir | All assumptions only | ~40k tokens |
| L4 — Synthesizer (optional Opus) | Findings from L2 + L3 | Findings only, not full plans | ~50k tokens, only when triggered |

L4 triggers when: ≥4 phases, OR L2/L3 surfaced cross-edge concerns, OR architect requests it.

**Findings flow back to ORIGINAL planners**, not to a separate edit-applier. Closes the edit-applier-drift gap from the retrospective.

### 17. Review cycle trigger (topic 7)
- **Option (c): hybrid.**
- **L1 is event-triggered** — runs immediately on any artifact mutation (free, deterministic).
- **L2–L4 are checkpoint-triggered** — after initial planning, after each phase completion, before audits.
- **Off-checkpoint deep review is forced** when L1 fails or a new escalation is opened.

### 18. Long-running phase protocol (topic 8)
Four mechanisms:

1. **Heartbeat:** Implementer writes `<work-dir>/phases/Pn/status.md` after every task. Frontmatter tracks `tasks_planned / tasks_completed / tasks_in_progress / tasks_remaining / context_utilization / last_heartbeat`. Stale `last_heartbeat` relative to elapsed time = silent-death escalation.
2. **Continuation:** Implementer detects context approaching 80% → updates status.md → returns `status: halted, reason: context-budget`. Architect dispatches a NEW implementer with original plan + status.md + protocols. New instance resumes from `tasks_in_progress`.
3. **Completion verification:** `verify-phase-complete.sh Pn` is deterministic, external. For each task in `tasks_planned`: checks task in `tasks_completed`, declared artifact exists, declared tests pass. Implementer cannot self-declare phase complete.
4. **Architect-as-supervisor (no dedicated supervisor subagent for v1).** After every implementer return, architect reads status.md, compares against plan, checks heartbeat freshness, runs verification before accepting `status: complete`.

### 19. Chunking threshold (topic 8)
- **Option (c): hybrid.** Phases sized for logical coherence first.
- **Split if** plan estimates `>5 tasks` OR `>10 file edits`.
- Thresholds are starting values; tune after a few real runs.
- Continuation protocol (decision 18.2) handles surprises that exceed the threshold at runtime.

### 20. Tier-gating rule (cross-cutting)
Work tiers (top to bottom):

```
T0 — Spec (user input)
T1 — Architect's framing: DAG, glossary, contract skeletons, architect's assumptions
T2 — Detailed plans: phase plans, full contract bodies, planner assumptions
T3 — Implementation: code, tests, status.md, implementer assumptions
T4 — Audits: security, perf, completeness
T5 — Synthesis: learnings, sanitized planning, archive
```

**Rule:** Tier N+1 cannot begin until Tier N **passes its validation gate.**

Gate criteria (all required):
- All L1 deterministic scripts pass
- L2–L4 review pipeline approved at that tier
- Every assumption at that tier has `status: validated` or `revised` (no `pending`)
- Zero open blocking escalations affecting that tier

**Cascade exception:** Tier N may be reopened by problems surfaced in Tier N+M. Reopening Tier N marks all descendants stale per the existing cascade rule (decision 7). This is waterfall with feedback loops, not strict waterfall.

Strengthens cascade rule: cascade is reactive; tier-gating is preventive.

### 21. TODO.md + terminal status (cross-cutting)
Single-page user-facing state view at `<work-dir>/TODO.md`. Architect updates on every state change.

Required sections:
- Frontmatter: `work_dir`, `current_tier`, `current_subagent`, `last_updated`
- **Current state** block: active work, blocked-on, open escalations count, pending assumption count
- **Tier progress** checklist (T0–T5)
- **Recent activity** (last ~5 events with timestamps)

Architect emits a one-line terminal summary at every cycle:
```
[contract-dag] T<n> active (<phase>). <X> blocking | <Y> advisory | <Z> pending validation. See TODO.md
```

Purpose: user traceability without diving into multiple files. Also serves as the entry point for the future viewer/visualizer (topic 13).

### 22. Resolution of low-confidence assumptions before T3
A `confidence:low` + `risk_if_wrong:medium-or-high` assumption cannot enter T3 with `status:pending`. Each such assumption MUST be resolved by ONE of:

- **spec-tightened** — assumption becomes a precise, desk-evaluable requirement in `spec.md` (with a measurable bar)
- **scope-reduced** — feature descoped until the assumption becomes high-confidence
- **deferred** — explicit "future work" with rationale and external tracker reference

**Spike phases / exploratory code are NOT supported.** If information needed to plan can't be obtained from docs, vendor benchmarks, prior art, or product judgment, the spec is revised. The framework does not write throwaway code to discover requirements.

Rationale:
- The skill is invoked when the user has a clear *what + why + metrics*. Vague metrics mean the spec needs more work, not that the framework should accommodate uncertainty with code.
- Throwaway code violates the "every artifact is intentional" principle.
- Forcing resolution at T1 keeps the rigor symmetric across all tiers.

### 23. Audit feedback flow (closes the loop for topic 9)
When an audit phase (T4) surfaces findings, each finding is classified by **tier of origin** and lands at that tier. Escalation entry format gains a new field:

```
- lands_at: T0 | T1 | T2 | T3
```

Routing:

| Finding type | lands_at | Behaviour |
|---|---|---|
| Pure implementation bug | T3 | Re-implement specific code |
| Implementer wrong implicit choice | T3 | Revise assumption + fix code |
| Plan-level design flaw | T2 | Re-dispatch planner; cascade marks implementation stale |
| Contract design flaw | T1 | Mutate contract; cascade marks all consumers stale |
| Cross-phase interaction issue | T1 | Mutate contract between them |
| Spec-level issue | T0 | User decision required |

The cascade rule (decision 7) + tier-gating (decision 20) do the rest. No new machinery required.

After re-work, the audit phase re-runs against the new state. Loop until clean OR N iterations (default 3) → escalate to user.

### 24. Architect blindspot mitigation final (topic 11) — REVISED
Four mechanisms in v1:
- Decision 14 — architect surfaces its own assumptions to user
- Decision 20 — tier-gating
- Decision 21 — TODO.md + terminal visibility
- **Skeptic subagent (in v1)** — addresses the omission gap directly

**Skeptic invocation:**
- **When:** end of T1 (before user gate), end of T2 (before T3 begins)
- **Input:** whole work-dir (read-only) + `skill-catalog.md` + `spec.md`
- **Prompt:** *"Find things that should be in the work-dir but aren't. Don't validate what's there — look for omissions: missing phases, unaddressed spec requirements, missing audit triggers, untested error paths, lack of observability/logging considerations."*
- **Output:** advisory escalations of type `omission` appended to `escalations.md`
- **Cost:** ~30k tokens per invocation; bounded scope (single Opus)

Rationale: the first three nets validate **explicit assertions**. The skeptic checks for **what's missing** — directly attacking the architect-blindspot gap that motivated this skill (security wasn't planned for in the retrospective; user supplied it from outside).

Skeptic findings are advisory by default; user reviews and decides per-entry whether each is real or out-of-scope.

### 25. `learnings.md` sanitization (topic 10)
Written at T5 with strict rules:
- ONLY abstract patterns — no specific names, paths, IDs, secrets
- Each entry: pattern statement + abstract context + caveats
- User MUST review `learnings.md` before any cross-project export
- Sanitized entries optionally copied to `~/.claude/plan-orchestrator-shared-learnings/patterns.md`
- L1 script `sanitize-learnings.sh` flags: absolute paths, common PII shapes, identifier leaks; user resolves before export

### 26. Cross-project learning (topic 12)
Shared library at `~/.claude/plan-orchestrator-shared-learnings/`:

```
├── patterns.md          append-only; tagged by problem_class
├── anti-patterns.md     things that didn't work
└── meta.md              counts, vintage, source-run-ids
```

Entry format:
```yaml
---
id: L1
problem_class: [refactor, data-extraction]
source_run: 2026-05-18T13:00Z
confidence: medium
---

## L1 — Materialized views cheaper than expected for derived state
Pattern: For derived state with <1k rows updated on event commit, a materialized
view is faster and simpler than full event replay at query time.

Caveats: validated at ~2k rows total; behaviour at >10k unknown.
```

**Promotion (at T5):**
- Architect drafts `learnings.md` for the current run
- For each entry, architect proposes: *"export to shared library? y/n"*
- User explicitly opts in per-entry; default: no
- Only opt-in entries land in `patterns.md`
- Cross-project library is **never auto-populated** — always user-approved

**Filter (at T1):**
- Architect lists `problem_class` tags for the current project from the spec
- Tag-based intersection: pull library entries whose `problem_class` has ≥1 overlap with current project tags
- Cap: top 10 by recency if more than 10 match
- Surface in `assumptions.md` as: *"Based on L1 (from <source_run>), I'm considering X. Validate or invalidate."*

**Conflicts:**
- When two pulled entries contradict, both surfaced to user as a disjunctive assumption
- User resolves which applies (or neither)
- Never auto-resolved

**Audit / maintenance:**
- `meta.md` tracks: entry count, oldest entry, source-run-ids
- User can manually delete entries; skill never auto-deletes in v1
- Pattern decay / expiry deferred to v2 (only matters at library scale)

Architect never silently applies a learned pattern. Always surfaces for user validation.

### 27. Viewer / visualizer (topic 13)
**Deferred to v2.** v1 ships file-based observability only.

`dag.md` YAML and `TODO.md` frontmatter are structured enough that a future tool (Python TUI, web viewer, Obsidian plugin) can parse them. No v1 commitment to render anything.

### 28. Skill catalog format (topic 14 leftover)
`<work-dir>/skill-catalog.md` is written by the architect at T1.

```yaml
---
generated: <timestamp>
work_dir: <path>
---

## Available skills

| Skill | Namespace | Purpose | Use at tier |
|---|---|---|---|
| writing-plans | superpowers | T2 phase plans | T2 |
| test-driven-development | superpowers | test-first impl | T3 |
| frontend-design | frontend-design | UI generation | T2/T3 UI phases |
| security-review | (root) | security audit | T4 |
| review-pr | pr-review-toolkit | code review | T4 |
| commit-push-pr | commit-commands | git landing | T5 |

## Missing relevant skills

| Need | Workaround |
|---|---|
| perf-review | manual T4 review |
| a11y-review | descope or manual T4 review |

## Audit triggers

audit_triggers:
  security-review:
    spec_keywords: [auth, oauth, password, secret, PII, token, session]
    file_patterns: [auth/*, security/*]
    always_for: [authentication, authorization]
  pr-review-toolkit:review-pr:
    always_for: [any T3 phase]
```

### 29. Overkill detector (topic 15)
At invocation, the skill asks four quick questions and scores:

| Q | Choices | Score |
|---|---|---|
| Components touched | 1 / 2-3 / 4+ | 0 / 2 / 4 |
| Effort | <2h / half-day / multi-day | 0 / 1 / 3 |
| New cross-component contracts | no / yes | 0 / 3 |
| Audits needed | none / one / multi | 0 / 1 / 2 |

Total 0–12. Thresholds:
- **≥6** — strong fit, proceed
- **3–5** — marginal, warn user, recommend `superpowers:writing-plans` as lighter alternative; proceed only on explicit confirm
- **≤2** — overkill, recommend `superpowers:writing-plans` and exit

Numbers are starting values; tune after real runs.

### 30. Architect compaction recovery / ORIENT step
Every architect cycle starts with an explicit ORIENT step. State lives on disk; architect memory is rebuilt every cycle.

**ORIENT protocol:**
1. Read `TODO.md` frontmatter (`current_tier`, `current_subagent`, `last_updated`)
2. Read `dag.md` YAML block (phase statuses, contract versions, edges)
3. Grep `escalations.md` for `status: open`
4. Grep `assumptions` across artifacts for `status: pending`
5. Compute the next legal move per tier-gating (decision 20)
6. Only then dispatch / act

Terminal status at cycle start:
```
[contract-dag] orient: T<n> in progress, <X> open escalations, <Y> pending assumptions. Next: <move>
```

**Effect:** architect compaction becomes survivable. If the previous architect thread was compacted, the new architect re-orients from files without knowing the difference. The architect is **stateless across cycles** — all state lives on disk.

Closes the explicit retrospective gap on architect compaction recovery.

### 31. Continuity of planning authority (closes edit-applier-drift gap)
"Original planner" means **continuity of authority**, not literal subagent instance reuse (which Claude Code doesn't provide anyway).

When reviewer findings require plan revision:
- Dispatch a planner subagent with **full planning authority**
- **Inputs:** original plan + reviewer findings + relevant contracts + relevant assumptions (validated AND pending)
- **Dispatch prompt explicitly states:**
  > *"You have planning authority. You may:*
  > *— Accept the findings and revise the plan, OR*
  > *— Argue back (escalation type: `plan-defense`) with rationale.*
  > *You may NOT act as an edit-applier or find-and-replace tool. If you believe the reviewer is wrong on a specific finding, halt and surface the disagreement via escalation."*

Rationale: the retrospective's edit-applier-drift gap came from a separate subagent applying reviewer edits to plans it didn't write. The fix is **role continuity**, not instance reuse. The new instance has the same authority as the original — including the right to argue.

Closes the edit-applier-drift gap.

### 32. Model and effort allocation per dispatch type
Two dimensions per dispatch: **model** (Opus / Sonnet / Haiku) and **extended thinking** (off / medium / high). Principle: hard reasoning where consequences are expensive; cheap execution where the plan is explicit.

| Dispatch type | Model | Thinking | Rationale |
|---|---|---|---|
| Architect framing (T1) | Opus | high | broad context; cascade implications |
| Phase planner (T2) | Opus | medium | per-phase judgment |
| L1 deterministic scripts | (no LLM) | — | free |
| L2 edge reviewer | Opus | off | bounded local scope |
| L3 assumption auditor | Opus | medium | subtle cross-artifact patterns |
| L4 synthesizer | Opus | high | most context-stressed step |
| Skeptic | Opus | high | omissions are the hardest to spot |
| T3 implementer | Sonnet | off | mechanical execution per explicit plan |
| T3 continuation | Sonnet | off | resume mechanical execution |
| Audit phase dispatch | (inherits) | (inherits) | audit skill decides own model |
| T5 synthesis writer | Sonnet | off | mechanical + light judgment |
| Verifier (delegated checks) | Haiku | off | small bounded reads |

**Override triggers:**

| Trigger | Adjustment |
|---|---|
| Phase HIGH-COMPLEXITY (≥5 tasks OR ≥3 contracts touched OR tier-blocking concerns) | Implementer Sonnet → Opus |
| Project overkill score ≥10 (very large) | L2 reviewer → Opus + high thinking |
| Project overkill score 6-7 (marginal) | L2 thinking off; L3 → Sonnet + medium thinking |

**Cost guardrail:**

Architect tracks cumulative dispatches in `TODO.md` frontmatter:
```yaml
opus_dispatches: <count>
sonnet_dispatches: <count>
haiku_dispatches: <count>
```

Thresholds (defaults; configurable):
- Warn user at **50 Opus dispatches** per run
- Hard halt at **100 Opus dispatches** — architect requires explicit user override

Terminal one-liner can include cumulative dispatch count when over warning threshold.

### 33. Automated post-run quality assessment
At T5, the architect runs a deterministic `run-quality.sh` script that reads the work-dir and produces an objective quality report.

**Two evaluation surfaces:**

| Surface | What it measures | How |
|---|---|---|
| **Output** | Did the built project meet its spec? | project's test suite + audit skills + per-metric verification scripts |
| **Process** | Did the skill execute its protocols cleanly? | `run-quality.sh` reads work-dir artifacts |

**`run-quality.sh` output (`<work-dir>/run-quality.yaml`):**

```yaml
run_id: <timestamp>
overall: green | yellow | red

hard_checks:                      # any failure → RED
  tier_violations: 0              # must be 0
  final_blocking_escalations: 0   # must be 0
  unresolved_assumptions: 0       # must be 0

soft_checks:                      # warning thresholds
  cascades_triggered: <n>         # informational
  phases_redone: <n>              # warn at >3
  context_budget_halts: <n>       # warn at >2 per phase

audit_findings_by_lands_at:
  T0: <n>  T1: <n>  T2: <n>  T3: <n>

skeptic_findings:
  total: <n>
  validated_as_real: <n>          # true-positive rate
  false_positives: <n>

dispatches:                       # from decision 32 guardrail
  opus: <n>  sonnet: <n>  haiku: <n>

token_cost:
  actual: <count>
  predicted: <count>
  ratio: <x>                      # warn at >1.5x, red at >3x
```

**Verdict matrix:**

| output tests | output audits | process | verdict |
|---|---|---|---|
| ✓ | ✓ | green | SATISFACTORY — ship |
| ✓ | ✓ | yellow | functional success, friction → tune defaults |
| ✓ | ✗ | — | audit gap; investigate |
| ✗ | — | green | clean process, bad output → skill bug |
| ✗ | — | red | skill itself broken |

Both surfaces must be ✓ AND process green/yellow for the skill to be considered fit for purpose. The harness is **test-bed-independent** — applies to any run.

---

# Naming consolidation and verification additions (added after first test-bed reflection)

These supersede earlier numbered conventions (T0–T5, L1–L4) which proved opaque or overloaded in practice. The earlier decisions remain in this file for traceability; new naming below is canonical going forward.

### 34. Procedural stage names (supersedes T0–T5)

The skill's procedure has six stages, named — not numbered:

| Stage | What | Gate criteria |
|---|---|---|
| **Spec** | User provides spec; validate input contract | All input-contract fields present |
| **Framing** | Architect decomposes: DAG, glossary, skill-catalog, contract skeletons, own assumptions | User validates architect's assumptions; all Structural + Alignment checks pass |
| **Planning** | Parallel planners produce detailed phase plans | All planner assumptions validated; review pipeline clean |
| **Implementation** | Implementers write code per plan | All phases pass completion verification |
| **Audit** | Audit phases dispatched (security-review, code-review, …) | All audits clean OR remaining findings explicitly accepted |
| **Synthesis** | Learnings, PR description, sanitization | (terminal) |

"Tier-gating" → **stage-gating**. Stage names referenced explicitly; no T-numbers.

### 35. Verification toolbox — three classes, parallel (supersedes L0–L5 layering)

```
STRUCTURAL CHECKS
  Cost:    $0 per check (deterministic script)
  Catches: format errors, dead refs, duplicate IDs, name drift, missing files
  When:    Every architect cycle; always-on (free)

ALIGNMENT CHECKS
  Cost:    ~$0.001 per check (Haiku, small bounded prompt)
  Catches: claim-text vs cited-source discrepancies
  When:    After every architect adjudication; before every stage gate

JUDGMENT CHECKS
  Cost:    $0.10–$1.00 per check (Opus, sometimes with thinking)
  Catches: semantic gaps, cross-edge interactions, omissions
  When:    Cycle boundaries (post-batch); these are the Review Pipeline
```

Toolbox, not a ladder. Different classes fire at different points. Each error class should be caught by the cheapest class that can catch it.

### 36. Review pipeline step names (supersedes L1–L4 of decision 16)

Four named steps. Each is a step in a procedure, not a "layer":

| Step | What | Class | Model |
|---|---|---|---|
| **Lint** | Run all Structural scripts | Structural | (no LLM) |
| **Edge review** | Per-producer↔consumer-pair semantic review | Judgment | Opus |
| **Assumption sweep** | Read all assumptions; flag contradictions, silent invalidations, risky-pendings | Judgment | Opus |
| **Synthesis review** | Cross-finding meta-review (conditional) | Judgment | Opus + thinking |

Plus the **Skeptic** (separate; runs alongside the pipeline, finds omissions).

### 37. Alignment-class checkers

Two Haiku checkers, single-shot Q-and-A with bounded inputs:

**`haiku-claim-check.py`** — for each adjudication entry with `cites: [<file:anchor>]`, dispatch one Haiku per cite:
```
Adjudication says: <claim>
Cited section: <text near anchor>
Do they agree on load-bearing facts? Answer: YES / NO / UNSURE — one-line reason.
```
NO → block gate. UNSURE → escalate to architect or Opus.

**`haiku-coverage-check.py`** — for each adjudication with `affects_artifacts: [<paths>]`, dispatch one Haiku per path:
```
Adjudication called for: <change>
Current state of <path>: <relevant excerpt>
Does the file contain the change called for? Answer: YES / NO / UNSURE.
```
NO → adjudication not landed; block gate.

### 38. Judgment-class prompt templates

Reviewer prompts at Judgment class were ad hoc in the first test-bed run; ~80% scaffolding, ~20% per-dispatch variation. Templates fill the scaffolding once; architect fills slots, not free-form prose.

Templates in `templates/`:

- `planner-prompt.md` — slots: `{phase-id}`, `{contracts-to-read}`, `{skill-requirements}`, `{architect-adjudications-relevant}`, `{omission-directives}`
- `edge-reviewer-prompt.md` — slots: `{producer}`, `{consumer}`, `{contracts-consumed}`, `{specific-claims-to-verify}`
- `assumption-sweep-prompt.md` — slots: `{assumption-blocks-to-read}`, `{known-contradictions}`, `{specific-concerns}`
- `skeptic-prompt.md` — slots: `{stage-context}`, `{adjudications-to-walk}`, `{omission-categories}`

Templates make prompts auditable cycle-to-cycle and reduce architect prompt-writing variance.

### 39. Architect adjudication structure

Each adjudication entry now requires two new fields:

```yaml
- id: A<N>
  claim: "<one-line>"
  rationale: "<one-line>"
  confidence: high | medium | low
  risk_if_wrong: "<one-line>"
  cites:                        # NEW — required for any factual claim
    - file: <path>
      anchor: <slug-of-heading>
  affects_artifacts:            # NEW — required for any decision propagating to other files
    - <path>
  status: pending | validated | invalidated | revised
  validated_by: -
  validated_at: -
```

Without `cites`, adjudication cannot be Alignment-checked. Without `affects_artifacts`, no downstream coverage check. Structural scripts auto-verify both fields' paths/anchors exist; Alignment checkers auto-verify content.

### 40. Reviewer scoring culture

The framework explicitly treats issue-raising as the desired behavior:

> A reviewer that finds zero issues on a complex edge is suspect — likely missed something. A reviewer that finds many issues is doing its job. **Never penalize a reviewer for finding.**

Folded into the existing halt-protocol and assumption-surfacing clauses; reviewer dispatch templates state this explicitly in slot copy. Complement: reviewers raise; they don't fix. Fixes flow through the original-planner-authority rule (decision 31).

### 41. (Reserved) — User's L0–L5 ideology

User has noted a separate L0–L5 ideology distinct from procedural stages — about *how to think about a project*, not *what stages a project passes through*. To be defined and added as its own named concept (not "Layers," not "Tiers," not "Stages"). Reserved as a placeholder until the user describes it.

---

## Lessons from the first test-bed run (hex-wars)

The framework's first end-to-end exercise produced these design lessons. Each suggests a concrete change above:

**Architect-text-vs-artifact drift is the dominant failure mode.** One architect text error (A42 said "8 values"; locked contract had 9) cascaded into 4 downstream findings. Architects working from memory are unreliable; decision 39's `cites:` field forces read-back.

**One small error has disproportionate downstream cost.** The A42 error produced E60, E68, E72, plus planner hedging. Cost scales with the number of subagents that read the text. This is why Alignment-class checks (decision 37) earn their place.

**Reviewer value scales with checklist specificity.** The Lint step caught real issues every cycle. The Edge-review step missed parity even though that was the relevant check — because the prompt said "verify hex orientation" not "verify parity choice (odd-r vs even-r)." Templates (decision 38) must include explicit field-level checklists.

**Parallel-tool harness fail-fast.** A non-zero exit from one Bash command cancelled 7 parallel agent dispatches. All Bash invocations in skill procedure must use exit-0 guards (`; :` or `|| true`).

**Numbering collisions across parallel reviewers.** Parallel reviewers each read `escalations.md` at dispatch time, so each used the same "next free" E-number. Reviewer prompts now require an "read escalations.md and pick first unused number > N" step before any append.

**Architect-as-monitor mode emerged dynamically.** User explicitly switched from synchronous-dispatch to background-dispatch + monitor mid-run. Procedure variant to be formalized: architect can dispatch all Judgment-class checks as background agents, then orient on each completion.

**Mechanical-fix vs replanner-cycle.** After Edge-review found small text/rename issues, architect-edit-then-Alignment-recheck was cheaper than re-dispatching planners. Heuristic: if findings are single-line edits or name renames, architect edits; if they require restructuring, re-dispatch planner with full authority.

**Architect debt accumulates if allowed.** Mid-run I deferred fixing A42 ("I'll patch later"). Principle now: every adjudication must pass Alignment-class check before its associated stage gate closes. No bookkeeping debt across gate boundaries.

**Convergence is real but multi-cycle.** Cycle 1: 33 findings / 19 blocking. Cycle 2: 15 findings / 6 blocking. Architect mechanical fixes + Alignment recheck: 0 blocking. Three rounds of review for a 4-phase multi-day project. Typical run probably needs 2–3 cycles of Edge review.

**The framework converges because the user intervenes at critical points.** Without "don't stop at the Planning gate" and "tighten architect discipline" interventions, the framework would have produced subtly broken software that "passed" all checks. The framework is a tool for the user, not a replacement.

---

# Round-2 lessons (habit-tracker test bed)

Two end-to-end test-bed runs (hex-wars + habit-tracker) surfaced patterns. Below: findings consolidated, then new decisions 42-50 that fold them back into the skill design.

## Round-2 findings catalog

**Failures of the framework that need design fixes:**

- **R2-13/14 — Cascade-timing failure (dominant pattern, 5+ edge-review findings traced to it):** producer-can-refine-its-contract-during-Planning combined with parallel-planner-reads-at-dispatch-time = consumers freeze on pre-mutation snapshot. Every edge review caught a flavor of "consumer doesn't know producer's contract evolved while they were drafting."
- **R2-15 — Auto-proceed past blocking findings was architect discipline failure:** I treated "auto-proceed" too liberally and skipped past 11 blocking findings at end of Planning. The skill text isn't strong enough on gate semantics — even the architect who knows the design drifted.
- **R2-9 — Cross-adjudication citation missing:** Planners genuinely want to cite other adjudications ("this builds on A19"), but `cites:` expects file:anchor. No mechanism for cross-adjudication relationships.
- **R2-10 — Slug ambiguity:** Anchor matching has no canonical rule. `command.add` vs `command-add` vs `commandadd` produced inconsistent results.
- **R2-8 — Numbering collision across parallel appenders returns:** Planners read escalations.md at dispatch time and each picked the same "next free" number. Same class as round-1's reviewer collision; not yet solved.
- **R2-2 — `cites: []` workaround is ugly:** Architect-original decisions have nothing to cite; current design forces ugly empty-array marker. Needs proper field.
- **R2-11 — Coverage check silently passes on pending:** `verify-coverage.py` only runs against `validated` adjudications. Pending adjudications with broken `affects_artifacts:` slip through.

**Architect-as-script bugs (lessons about dogfooding):**

- **R2-1 — `verify-cites.py` regex bug, architect self-found by dogfooding the script:** confirmed value of running architect's own scripts on architect's own writes.

**Validations of the existing design (these worked):**

- **R2-3** — 5 real cite errors in adjudications, caught by the fixed script. Structural class earns its keep.
- **R2-4** — Structural caught everything cheaply at Framing stage. Cost-effective layer ordering works.
- **R2-5** — Alignment Haiku correctly flagged a conflated adjudication (UNSURE on A11). Alignment adds value beyond Structural.
- **R2-6** — Skeptic found 12 omissions cheaper layers couldn't catch. Skeptic remains essential complement.
- **R2-7** — P5 planner caught architect's dag-misstatement (missing C4). Planners verify architect manifests; not passive consumers.

**Emergent patterns to encode:**

- **R2-12** — Planners verify dag.md against their needs. Positive emergent behavior. Should be codified, not relied on as luck.

---

## Decisions 42-50

### 42. Cascade-timing protection — `consumed_versions:` field
Resolves R2-13 / R2-14. The dominant failure mode of round-2.

At planner dispatch time, architect captures the version of every contract the planner will consume. Versions are written into the dispatch prompt. Planner output's frontmatter mirrors them in a `consumed_versions:` block. On planner return, architect compares against current on-disk versions; if any consumed contract has bumped versions in the interim, planner output is marked stale and re-dispatched.

```yaml
# In planner output frontmatter
consumed_versions:
  C1: "0.2"
  C2: "0.1.3"
```

Closes the gap where producers refine their own contracts during parallel Planning and consumers don't notice.

### 43. Auto-proceed semantics — strict
Resolves R2-15.

"Auto-proceed" means ALL of:
1. All Structural checks pass (exit 0)
2. All Alignment checks return YES (none NO; UNSURE escalates)
3. ZERO blocking escalations open in escalations.md
4. ZERO low-confidence + medium-or-higher-risk assumptions in `pending` status (per decision 22)

Failure of any condition → architect HALTS and surfaces to user. Auto-proceed cannot bypass blocking findings.

Skill text updates:
- Replace "auto-proceed" with "automatic-gate-evaluation"
- Add explicit anti-pattern: "auto-proceeding past blocking findings is forbidden"
- Each gate description in skill.md must call out the four-condition check

### 44. Cross-adjudication citation — `derived_from:` field
Resolves R2-9.

New optional field:

```yaml
- id: A21
  claim: "..."
  cites: [...]                  # factual claim against file:anchor sources
  derived_from: [A19, A11]      # this adjudication builds on other adjudications
```

- `cites:` keeps its meaning
- `derived_from:` lists adjudication IDs this builds on
- NEW Structural script `verify-derived-from.py` checks each referenced ID exists
- Optional Alignment check: "does A21 contradict A19?"

### 45. Architect-original convention — `originates_at:` field
Resolves R2-2.

Replace the `cites: []` workaround with a semantic field:

```yaml
- id: A4
  claim: "..."
  originates_at: framing-stage   # architect-original; no cite or derived_from
```

Rules:
- Exactly one of `cites:`, `derived_from:`, or `originates_at:` must be present (`cites:` and `derived_from:` may both be present; `originates_at:` is mutually exclusive with the other two)
- `originates_at:` values: `spec`, `framing-stage`, `planning-stage`, `audit-stage`
- Structural check enforces presence

### 46. Canonical slug rule
Resolves R2-10.

Single canonical slugifier (applied in scripts + documented in templates):

```python
def slugify(heading_text):
    s = heading_text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)   # non-alphanumeric run → single dash
    s = s.strip("-")                      # strip leading/trailing dashes
    return s
```

`verify-cites.py` rules:
- Try exact match first
- Then try `slugify(anchor)` 
- Then try `slugify(text near anchor)` for approximated cites
- On miss, suggest closest match by string distance

### 47. Numbering coordination — architect pre-allocates ranges
Resolves R2-8.

Before dispatching N parallel appenders, architect:
- Reads escalations.md, computes next free E (`M`)
- Reserves a range PER appender: appender 1 = E`M`..E`M+9`, appender 2 = E`M+10`..E`M+19`, etc.
- Each dispatch prompt includes the appender's reserved range explicitly
- Appenders MUST use only their reserved range; halt-and-request if they need more

Documented in all dispatch templates.

### 48. Coverage check on pending — warn, don't block
Resolves R2-11.

`verify-coverage.py` behavior change:
- Runs on ALL adjudications (was: validated only)
- For `pending` adjudications: WARN (exit 2, non-blocking) if `affects_artifacts:` paths exist but are older than the adjudication
- For `validated` adjudications: FAIL (exit 1, blocking) if coverage missing

### 49. Planner-verifies-dag — codify the positive behavior
Resolves R2-7 / R2-12.

Planner-prompt template adds a required first step:

> BEFORE you start drafting your plan, verify dag.md's row for your phase against your understanding of what you'll consume/produce. If `consumes:` or `produces:` doesn't match what your plan needs, escalate via the halt-protocol before writing anything else.

Converts the round-2 lucky catch into a guaranteed check.

### 50. Architect-self-dogfooding
Resolves R2-1 generalized.

After any architect-written artifact mutation, run the relevant Structural pipeline:
- After `assumptions.md`: verify-cites, verify-coverage, verify-references, detect-duplicate-ids, verify-derived-from
- After `dag.md`: verify-dag, verify-references
- After any contract: verify-cites (contracts have referenceable anchors used elsewhere)

Stated as a discipline in skill.md's ORIENT step: "Re-run Structural on architect-mutated artifacts before declaring any stage-gate evaluation complete."

---

## Iteration-3 decisions (51-58) — reviewer-driven consolidation

Origin: a senior-skill-developer Opus reviewer (max-effort, separate session) read the full skill package and round-2 design notes. Their findings, where I agreed, are codified below. Where I disagreed, the original decision stands and the disagreement is noted.

### 51. Five named stages, not six
Round-2 had: Spec, Framing, Planning, Implementation, Audit, Close-out. Reviewer point: Audit isn't a distinct stage with its own gate — it's a step inside Close-out, with optional triggers from earlier stages. Six stages over-promises ceremony.

Decision: fold Audit into Close-out as a sub-step. Stages are now: **Spec / Framing / Planning / Implementation / Close-out**. Audit triggers (security-review, pr-review-toolkit, etc.) fire inside Close-out per the skill_requirements that earlier stages declared.

### 52. Per-dispatch escalation files (supersedes decision 47)
Round-2 decision 47 reserved E-number ranges per parallel appender. Reviewer point: that's a workaround. The root cause is shared write contention on `escalations.md`. Fix the root cause.

Decision: every subagent writes to its own file at `<work-dir>/escalations/<dispatch-id>.md`. Local numbering (E1, E2, ...) inside that file. Architect concatenates per-dispatch files on each ORIENT. No reserved ranges, no collisions, no "next free" reads.

Decision 47 is superseded. Templates updated; scripts updated to walk `escalations/` alongside the consolidated `escalations.md`.

### 53. Single `source:` field, tagged-union (supersedes the two-field shape in decision 44)
Round-2 decision 44 added top-level `derived_from:` alongside `cites:`. Decision 45 added `originates_at:` as a third top-level field. Reviewer point: three mutually-exclusive top-level fields is a tagged union pretending to be flat. Collapse them.

Decision: one `source:` field, exactly one form inside:

```yaml
source:
  cite: [{file, anchor}, ...]   # OR
  derived_from: [Ax, Ay]         # OR
  originates_at: framing-stage
```

`cite:` and `derived_from:` MAY coexist (a derived adjudication that also cites supporting facts). `originates_at:` is mutually exclusive with the other two — if you can cite something, you should.

Documented in `templates/adjudication-entry.md`. Decisions 44 and 45 are superseded by 53.

### 54. Subagent protocol — combined halt + surface (supersedes the two-file pattern)
Round-2 shipped `halt-protocol.md` and `assumption-surfacing.md` as two separate files appended verbatim to every dispatch. Reviewer point: every dispatch needs both, and they share concepts (escalation format, evidence discipline). Two files is duplication.

Decision: one file, `templates/subagent-protocol.md`, with two rules — HALT when blocked, SURFACE every assumption. Compressed ~50% from the combined originals. The deleted files (`halt-protocol.md`, `assumption-surfacing.md`) are gone, not stubbed.

### 55. Consolidated verifier — `verify-refs.py` with subcommands
Three Structural scripts (`verify-cites.py`, `verify-derived-from.py`, `verify-references.py`) all read the same adjudication blocks and prose. Reviewer point: duplicate parsing, duplicate path-walking, three exit codes to interpret instead of one.

Decision: merge into `scripts/verify-refs.py` with subcommands `cites`, `derived-from`, `references`, and `all`. `all` returns `max(child exit codes)` so one invocation gives the full Structural-class verdict on references. The three originals are deleted.

### 56. "When things go wrong" failure-mode branches
Reviewer point: the skill describes the golden path well but doesn't enumerate what to do when things deviate from it. Without explicit branches, the architect under load is likely to improvise.

Decision: skill.md adds a "When things go wrong" section covering four documented branches:
- **False-positive Haiku call** — dispute mechanism + Opus override; the dispute is logged so we can tune the prompt.
- **Partial planner failure** — some planners return clean, others halt; architect re-dispatches only the halted ones; gate doesn't open until all return.
- **Audit loop N=3** — after three audit→fix iterations without convergence, escalate to user with the findings and a recommendation rather than looping a fourth time.
- **Rubber-stamping detection** — if a reviewer returns "clean" on N consecutive cycles where other reviewers find issues, the architect down-weights that reviewer for the next dispatch and surfaces the pattern to user.

### 57. Harness-fit caveats — admit what the harness doesn't do
Reviewer point: the design assumes per-dispatch extended-thinking levels (Opus + high thinking, Opus + medium, etc.), but the Claude Code Agent tool doesn't currently expose thinking-level per dispatch. The skill mis-implies a knob it doesn't have.

Decision: skill.md adds a "Harness-fit caveats" section enumerating four limits:
- Per-dispatch model selection is supported; per-dispatch thinking-level is NOT — thinking is set at session level.
- Parallel agent dispatches are supported; cross-agent live monitoring is NOT — agents run to completion and return.
- Tool calls inside a single response are all-or-nothing — a failing Bash in a parallel batch can cancel the other dispatches in that response. Mitigation: `; :` exit-0 guards or split-batch.
- Haiku dispatches still cost roughly one Sonnet's worth of latency due to round-trip overhead; the cost win is in dollars and context, not wall-clock.

Skill text now says "use the most capable thinking available at session level" rather than prescribing thinking per dispatch.

### 58. Cost estimate baked into overkill detector
Reviewer point: the overkill detector scores 0–12 but doesn't give the user a dollar number. They're being asked to consent to ceremony with no idea of the bill.

Decision: skill.md's verdict line now includes a rough cost estimate: **$20–$100 typical run** (single-component features under 8 phases). Drops the abstract "≥6 strong fit" into actionable territory. User can decline ceremony if the spec doesn't justify the spend.

### 59. Overkill detector — qualitative heuristic primary, score supplementary
Origin: reviewer Section 3.6. The weighted 0–12 score is "a calculator pretending to be judgment."

Decision: primary gate is qualitative — *can the user describe the work in one paragraph and one component?* If yes, exit and recommend `superpowers:writing-plans` regardless of what the score says. The four-question score remains as a supplementary diagnostic that cannot override the qualitative gate. Cheaper to refuse a marginal run than to spend $20–$100 finding out it was overkill.

### 60. ORIENT context-budget discipline — read/lint/decide + lint output to file
Origin: reviewer Section 4.2. Every ORIENT cycle was emitting raw script output back into the architect's conversation. Over 25 cycles that's ~25× the lint output accumulated in context — ORIENT was undoing its own purpose.

Decision: ORIENT is now three phases — **read**, **lint**, **decide**. The lint phase redirects all script output to `<work-dir>/orient-latest.md` (overwritten each cycle). The architect reads only the summary file, not raw script output. Detail is one Read away when needed. This is the load-bearing fix for architect-side context preservation.

### 61. Cascade convergence guarantee — N=3 bound on cascade itself
Origin: reviewer Section 4.3. The cascade can loop indefinitely: three consumers re-dispatch, one refines its produced contract, restaling another consumer, etc.

Decision: bound the cascade at three iterations (mirroring decision 23's audit-loop bound). If three rounds of consumer re-dispatch don't quiesce, halt to user with three options: (a) pin all producer contracts at current versions and force consumers to live with them, (b) descope the offending field, (c) revisit Framing for the affected subgraph. Same discipline as audits — parallel N=3 escape hatches.

### 62. Spec-version pinning — ORIENT detects spec.md mutation
Origin: reviewer Section 4.4. Spec mutations are allowed (decision 22 forces resolution via spec-tightening) but cites to spec anchors silently break when the spec is rewritten.

Decision: ORIENT checks `spec.md`'s mtime each cycle. If changed since last ORIENT, all adjudications with a `cite:` to `spec.md` are marked `stale-spec` and require re-validation against the new content. No gate can open while any `stale-spec` adjudication remains. The architect cannot revise the spec for free — every revision pays for re-validation of dependent claims.

### 63. Atomic-write discipline — `.tmp` + rename for monitored files
Origin: reviewer Section 4.6. `status.md` mid-write, parallel appenders, architect concatenation — no atomicity discipline meant the architect could read torn state.

Decision: any file the architect monitors (`status.md`, `phases/Pn/plan.md`, escalation files) is written atomically: write `<path>.tmp`, then rename to `<path>`. Single-Write-call alternatives are acceptable (Claude Code's Write is effectively atomic for typical file sizes). Documented in `templates/subagent-protocol.md`. Streaming partial state to monitored files is a new anti-pattern.

The per-dispatch escalation files mechanism (decision 52) already eliminates the parallel-appender concurrency problem for escalations; this rule generalizes the principle to all monitored files.

### 64. Audit-N=3 user options — spec three explicit branches
Origin: reviewer Section 4.7. My decision 56 branch said "escalate to user" without specifying what the user actually does.

Decision: when audit loop hits N=3 without convergence, the user picks one of three options:
- **(a) accept-with-followup** — ship with remaining findings filed as v2 issues; each becomes a tracked `accepted-advisory` adjudication with `user_accepted_at:` timestamp
- **(b) descope** — user removes the contributing requirement from `spec.md`; cycle resumes against the descoped spec (triggers decision 62 stale-spec sweep)
- **(c) one more iteration** — user provides a new directive; architect re-dispatches with that direction (this is the user explicitly overriding the N=3 limit, recorded as such)

Never silently continue past N=3. Never silently accept findings. The user owns the decision.

### Supersession note — decisions 25–26 deferred

Round-2 decisions 25 (sanitize-learnings) and 26 (cross-project library promotion flow) were specified in detail but with 0 entries after 2 test runs and no evidence pattern reuse helps. Reviewer Section 3.3 recommended deferring wholesale. Decision: marked superseded; `skill.md` (line ~343) reflects the deferral with a single paragraph. The full decision text in this file stays for historical record but the design is not active. Re-evaluate after ~10 real runs produce empirical pattern data.

---

## Iteration-3 outcome summary

What changed:
- 14 new decisions (51–64) — 8 consolidations + 6 from the second-pass review of the reviewer's findings
- Stages reduced 6 → 5 (Audit folded into Close-out)
- Adjudication shape: 3 top-level source-fields → 1 tagged-union `source:` field
- Subagent protocol: 2 files → 1 file (~50% shorter)
- Reference verifiers: 3 scripts → 1 script with subcommands
- Escalations: shared file + reserved ranges → per-dispatch files
- New explicit failure-mode branches in skill.md
- New "Harness-fit caveats" section admitting what the harness can't do
- Overkill detector: qualitative gate primary + cost-range emit + score now supplementary
- ORIENT restructured into read/lint/decide; lint output redirected to file (architect-context preservation)
- Cascade capped at N=3 iterations matching audit discipline
- Spec-version pinning via mtime check + stale-spec sweep
- Atomic-write discipline added to subagent-protocol.md
- Audit-N=3 user options formally specified as (a) accept-with-followup / (b) descope / (c) one more iteration
- Decisions 25–26 (cross-project library) explicitly marked superseded; skill.md defers to v2

What got deleted, not stubbed:
- `templates/halt-protocol.md`
- `templates/assumption-surfacing.md`
- `scripts/verify-cites.py`
- `scripts/verify-derived-from.py`
- `scripts/verify-references.py`

Decisions 44, 45, and 47 are explicitly superseded by 52, 53.

Round-3 still pending: pick a different problem class (CLI tool, async event-driven service, or external-API integration); run with iterated skill; compare patterns.

---

## Iteration-4 decisions (65-72) — round-3 findings landed

Origin: round-3 on the `tasklog` test-bed (async/event-driven). 11 dispatches, ~$30 actual cost. Half-day's worth of test signal. Findings R3-0..R3-11; the substantive ones are codified below.

### 65. `$N` cost notation escapes (R3-0)
Skill body MUST use worded form ("ten cents", "twenty to one hundred dollars") for cost ranges, OR escape with backslash. The Skill tool's argument substitution interprets bare `$0`, `$1` etc. as positional argument references and eats them. On round-3 invocation the verification toolbox section displayed the spec path where the cost numbers should have been. Documented as a `Harness-fit caveat` in skill.md.

### 66. Architect MUST fill templates, not write artifacts from intuition (R3-3)
Skill.md Stage 2 (Framing) now explicitly directs each step at its template. The architect-under-context-pressure who writes dag.md from intuition produces YAML in body code blocks that `verify-dag.py` doesn't parse (because `verify-dag.py` requires YAML in frontmatter per dag-skeleton.md). The skill prose now says "fill `templates/dag-skeleton.md`" not "write dag.md," and explicitly names the YAML-in-frontmatter requirement. Same pattern for contract-skeleton.md, planner-prompt.md, etc. Architect anti-pattern added.

### 67. Architect materializes contract version bumps on disk (R3-8)
A real ownership gap surfaced in round-3: planners promise "lock C1 to v0.2" in their plans, but cannot rewrite the contract files themselves. The architect must walk every contract between planner returns and the Review Pipeline, absorbing each planner's promised deltas and bumping the YAML `version:` field. Without this step, edge reviewers chase phantom contracts (the contract on disk doesn't match the version planners claim to be working against). Added as an explicit Stage 3 architect step in skill.md; added as an anti-pattern.

### 68. Layered planner dispatch within DAG dependencies (R3-9)
Skill.md previously said "dispatch all planners in parallel." Round-3 surfaced the bootstrap-waste problem: a layer-N planner dispatched before its dependencies have returned reads framing-sketch contracts (v0.1) and re-plans against pre-lock state. Decision: planners dispatch in DAG-dependency layers. Layer 0 = phases with empty `consumes:`. Layer N = phases whose `depends_on` is fully covered by layers 0..N-1. Within a layer, dispatch in parallel (multiple Agent calls in one message — round-3 also surfaced that the harness only parallelizes within a single response, not across messages).

### 69. Edge reviewer must catch dispatch-laundered overrides (R3-6)
The architect can launder a spec-contradicting directive through a dispatch prompt without surfacing as a `revised`-status adjudication. Round-3: I put "in-process consumers" into a planner's dispatch prompt while the spec said "process-level isolation"; three of four reviewers caught it (A51 contradiction). Codified as: (i) skill.md anti-pattern, (ii) edge-reviewer-prompt.md ALWAYS-CHECK claim that the reviewer walks the architect's dispatch trail looking for unsurfaced overrides. This makes the countermeasure mechanical.

### 70. Architect MAY mutate `status:` / `resolved_by:` on close (R3-5)
The append-only escalation rule (decision 52) made gate-evaluation's simple grep for `status: open` always-non-zero because the grep didn't follow `resolved_by:` chains. Round-3 workaround was a one-time script-mutation of the skeptic file's status fields. Now formalized: the architect (and only the architect) MAY mutate `status:`, `resolved_by:`, `resolved_at:` on existing escalation entries when closing. The original `claim:` and `suggested_resolution:` are still immutable — those are audit history. Documented in `escalation-entry.md`.

### 71. `verify-refs.py source-form` check added (R3-7)
The assumption-sweep reviewer caught A14's intentional schema violation (both `derived_from: []` AND `originates_at:` present in the same `source:` block). The deterministic verifier didn't. This was an embarrassing gap — Judgment-class caught what Structural should have. Added a new subcommand `verify-refs.py source-form` that checks `source:` exclusivity: exactly one of cite / derived_from / originates_at, with `cite + derived_from` MAY coexist, but `originates_at` MUST be alone. Strict interpretation: presence-of-key counts even if the value is an empty list. Verified to catch A14.

### 72. Round-3 script fixes — verify-dag.py
Three round-3 findings landed in `verify-dag.py`:
- **R3-1:** script now writes its escalation to `escalations/architect-verify-dag-<timestamp>.md` (per-dispatch file per decision 52), not to the shared `escalations.md`.
- **R3-2:** `lands_at` field uses the named-stage vocabulary (`framing`) not the superseded T0-T5 form.
- **R3-4:** prose-mention regex relaxed from `(?:^|\s)({prefix}\d+)[\s:.\-,)]` to `\b({prefix}\d+)\b` so markdown bold (`**C3**`) and em-dash separators (`──C3──`) match.

---

## Iteration-4 outcome summary

What changed:
- 8 new decisions (65–72)
- Skill.md: cost-notation escaped, Framing steps reference templates explicitly, Stage-3 adds architect-materialization step, layered-dispatch rule, dispatch-laundering anti-pattern, R3 anti-patterns appended, harness-fit caveat for `$N` substitution
- `escalation-entry.md`: architect-on-close exception to append-only
- `edge-reviewer-prompt.md`: ALWAYS-CHECK claim for dispatch-laundered overrides
- `verify-refs.py`: new `source-form` subcommand; verified to catch round-3's A14
- `verify-dag.py`: per-dispatch escalation output, named-stage vocabulary, loosened prose regex

What is still untested:
- Decision 61 (cascade N=3 bound) — round-3 cascade converged in iteration 1; the bound has never actually fired
- Decision 62 (spec-version pinning) — validated for the unchanged-anchor case; the moved/renamed-anchor case still untested
- Decision 64 (audit N=3 user options) — no actual N=3 audit loop has been triggered

Round-4 plan: target the still-untested machinery deliberately. Probably a spec mutation that moves anchors AND a synthetic cascade that bumps producer contracts during consumer re-plan.

---

## Round-2 outcome summary

What changed in this iteration:
- 9 new decisions (42-50) addressing all 7 design-failure findings
- 1 new optional field on adjudications (`derived_from:`)
- 1 renamed convention (`cites: []` → `originates_at:`)
- 1 new Structural script (`verify-derived-from.py`)
- 1 script behavior change (`verify-coverage.py` runs on pending too)
- 1 dispatch-template addition (`next_free_E: <range>` reserved per appender)
- 1 planner-prompt addition (verify dag.md before drafting)
- 1 discipline rule (architect self-dogfoods Structural)

Cost of round-2: ~60 Opus dispatches across the habit-tracker run.
Yield: 16 findings, 9 of which are concrete design improvements.

Round-3 plan: pick a different problem class (CLI tool, async event-driven service, or external-API integration); run with iterated skill; compare patterns.

---

## Skill-package layout (distinct from work-dir)

The skill itself lives at `~/.claude/skills/plan-orchestrator/` and contains:

```
plan-orchestrator/
├── skill.md                  the skill body (to be written)
├── design-notes.md           this file — design log
├── templates/
│   └── halt-protocol.md      boilerplate every dispatch includes verbatim
└── scripts/                  (to be created)
    ├── verify-dag.sh         deterministic dag.md checker
    └── invalidate.py         field-level cascade engine
```

Per-run state lives separately in `~/.claude/plan-orchestrator-runs/<project>/<timestamp>/` (see decision 6).

---

## Open topics (in proposed order)

- [x] **6** — DAG manifest format, invalidation script ownership — closed (decisions 7, 8, 10, 11, 12)
- [x] **7** — Reviewer mechanism — closed (decisions 16, 17)
- [x] **7b** — Assumption Surfacing Protocol — closed (decisions 14, 15)
- [x] **8** — Long-running phase supervision — closed (decisions 18, 19)
- [x] **Tier-gating (cross-cutting, new)** — closed (decision 20)
- [x] **TODO + traceability (cross-cutting, new)** — closed (decision 21)
- [x] **9** — Audit phase classification — closed (decisions 22 + 23)
- [x] **10** — Sensitive-data discipline — closed (decision 25)
- [x] **11** — Architect blindspot mitigation — closed (decision 24; skeptic deferred to v2)
- [x] **12** — Persistent learning — closed (decision 26)
- [x] **13** — Viewer/visualizer — closed (decision 27; deferred to v2)
- [x] **14** — Sub-skill orchestration — closed (decisions 28 + composition-over-reinvention from earlier)
- [x] **15** — Cost threshold / overkill detector — closed (decision 29)
- [ ] **12** — Persistent learning across projects (the `learnings.md` flow + how it feeds future runs)
- [ ] **13** — Viewer/visualizer (terminal? web? what does the operator see while this runs?)
- [ ] **14** — Sub-skill orchestration (does this skill invoke other skills like brainstorming, writing-plans, security-review?)
- [ ] **15** — Cost threshold / "is this overkill" detector

---

## Gaps from the retrospective — status

- [x] Edit-applier between reviewer and original planners — closed by decision 31 (continuity of authority, not instance reuse)
- [x] Reviewer-reviews-reviewer — closed by decision 16 (4-layer pipeline: scripts → edge reviewers → assumption auditor → optional synthesizer; layers act as redundant checks)
- [x] Architect compaction recovery — closed by decision 30 (ORIENT step at every cycle)
- [x] Untested escalation protocol — first real run exercises it; dry-run mode for cheaper testing deferred to v2
- [ ] **n=1 evidence** — first real run *is* n=2 by definition (retrospective was n=1). Acknowledged as accepted risk for v1 ship; v2 plan requires deliberate test on a different problem shape.
- [x] Architect blindspot — closed by decisions 14, 20, 21, and 24 (skeptic in v1)
- [x] Single-reviewer SPOF — closed by decision 16 (layered, sharded reviewers)
- [x] Long-phase truncation (P4 case) — closed by decision 18 (heartbeat + continuation + verification)
- [x] Security as afterthought — closed by decisions 23 + 28 (audit-trigger mapping + lands_at routing)
- [x] Sensitive planning artifacts — closed by decisions 6 (work-dir outside repo) + 25 (learnings sanitization)
- [x] Untyped contracts — closed by decision 8 (sectioned-md with stable field anchors) + decision 7 (field-level cascade)
- [x] No persistent learning — closed by decision 26 (cross-project library with user-opt-in promotion)
- [x] Cost asymmetry on small work — closed by decision 29 (overkill detector at invocation)

---

## Next session, start here

1. Read this file top-to-bottom.
2. Resume at the first unchecked item in "Open topics."
3. If a decision in "Decisions captured" doesn't make sense anymore, flag it before continuing — don't silently override.
