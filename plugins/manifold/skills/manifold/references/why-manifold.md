# Why manifold?

Intro for humans and agents: why this tool exists, what problem it inherits from the industry, and how it differs from tools that partially solve the same problem.

> **How this doc was written (2026-06-06):** Synthesized from manifold's design docs, the shipped v0.1.0 implementation, landscape research (`research/manifold/landscape-2026-06/synthesis.md`), and external validation. Use this as the canonical "why" story for the skill and README. Proper nouns: [`docs/manifold/glossary.md`](../../docs/manifold/glossary.md).

---

## The one-paragraph version

Software projects lose their **"why"** faster than they lose their code. Requirements drift, docs become fiction, and AI agents amplify the problem by shipping fast without durable intent. Manifold exists because the industry already knows this problem (KAOS, traceability, spec-driven development) but nothing agent-native gives you a **queryable, versioned graph of intent** with **typed revision discipline** (`change_reason`, `spec-audit`) and a **"what's next" API** for orchestrators. The idea isn't novel; the **packaging for long-horizon agent work** is.

**Positioning:** *ADRs that talk to your agent, version your intent, and produce a drift report when code diverges.* Shipped for projects with verdicts wired on realization nodes: graph + revisions + **`spec-audit`** (M3) + **`drift-report`** (M4 v1: violated + unverified rollup). v2 LLM rationale match (L17) is deferred.

---

## The problem (validated externally)

### Intent drift is not a bug

The field distinguishes two failures:

| Failure | Symptom | What catches it |
|---|---|---|
| **Bug** | Code fails its own spec | Tests, CI |
| **Intent drift** | Code passes tests but no longer matches *why* the work existed | Almost nothing by default |

Intent drift is "the lost why that diffs cannot reveal" — semantic divergence between original purpose and current implementation, often invisible until someone asks "wait, why is this here?" Sources: [Stonewall — Intent Drift](https://stonewall.dev/blog/intent-drift/), [Tricentis — Intent Drift in AI Code](https://www.tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots), [Zenn — What is Intent Drift?](https://zenn.dev/virtualcraft/articles/idd-02_what-is-intent-drift?locale=en).

### Requirement drift is structural, not a discipline problem

Teams with thorough documentation still drift because **requirements, design, and code live in separate systems with no live connection**. When one changes, the others don't follow. The PRD becomes historical fiction; reading the codebase to recover intent is expensive. Source: [Omniflow — The real cost of requirement drift](https://www.omniflowai.com/blog/the-real-cost-of-requirement-drift).

### AI agents make it worse, faster

Agents produce correct-looking code quickly, but **session context resets**. Without durable, structured intent outside the chat window, each session re-derives "why" from code snippets and ad-hoc prompts. Long-horizon work needs **external memory** — not just bigger context windows. Sources: [Anthropic — Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [Git Context Controller (arxiv)](https://arxiv.org/pdf/2508.00031).

### Spec-driven development names the direction — but not the longevity problem

The industry is moving toward **spec-as-source-of-truth** for AI-assisted builds ([Spec-Driven Development overview](https://medium.com/data-science-collective/spec-driven-development-when-intent-becomes-the-source-code-3af39f86b9d3), [GitHub Spec Kit](https://github.github.io/spec-kit/)). That solves *starting* work from intent. Manifold targets **sustaining** intent over months: revision history, drift surfacing, cross-project queries, orchestrator handoff.

---

## The metaphor: project compass

Manifold is a **compass**, not a task list, not a code generator, not a dispatch engine.

| Question | Compass answer |
|---|---|
| What is this project? | Root goals and layered breakdown |
| Where are we now? | Status and verdicts per spec node |
| Where do we go next? | `next-leaves` — unfinished frontier |
| Have spec revisions been explained? | **`spec-audit`** — M3 revision discipline |
| Does code still match why? | **`drift-report`** — M4 spec↔code (violated + unverified on realizations) |

A compass orients. Something else (orchestrator) walks. Something else (progress-tracker) reports steps taken.

---

## What the industry already built (and what manifold inherits)

### KAOS — the shape of the graph (1990s–2000s)

**KAOS** (Keep All Objectives Satisfied) is goal-oriented requirements engineering: decompose high-level goals into subgoals in an **AND/OR DAG**, link each goal to its rationale, operationalize to agents. Canonical references: [van Lamsweerde — Requirements Engineering (2009)](https://posomas.isse.de/Practices/aose.practice.req.goal_driven_requirements_elicitation.base/guidances/supportingmaterials/goal_driven_re_with_kaos_47BC83D3.html), [Darimont & van Lamsweerde — Formal refinement patterns (1996)](https://dl.acm.org/doi/10.1145/239098.239131).

Commercial KAOS tools (e.g. Objectiver) modeled this for human analysts. They did not target **MCP-queryable agent sessions** or **`next-leaves` for orchestrators**.

**Manifold inherits:** layered refinement, AND/OR DAG, rationale on nodes, cycle prohibition, coverage rules.  
**Manifold leaves behind:** full LTL semantics, built-in agent assignment (orchestrator's job).

### Enterprise traceability — the accountability layer

Tools like DOORS, Polarion, and similar ALM stacks enforce **requirements ↔ design ↔ test** links for regulated or large orgs. Heavy, expensive, not agent-native, not optimized for solo dev + Claude Code workflows.

**Manifold inherits:** the *idea* of traceability and revision audit.  
**Manifold differs:** SQLite, stdlib Python, MCP-first, single-operator scale.

### Spec Kit and SDD tooling — the agent-era spec workflow (2024–2026)

**[GitHub Spec Kit](https://github.github.io/spec-kit/)** is the closest mass-market sibling: constitution → specify → plan → tasks → implement, with markdown artifacts in the repo. It validates that **specifications should drive AI coding agents**.

| | Spec Kit | Manifold |
|---|---|---|
| **Canonical store** | Markdown files in git | SQLite DB |
| **Sweet spot** | Greenfield feature, one flow | Long-lived project, many sessions |
| **Structure** | Linear workflow artifacts | Layered goal graph (intent → … → realizations) |
| **Spec revision audit (M3)** | Re-run analyze / manual discipline | **`change_reason`** + **`spec-audit`** |
| **Spec↔code drift (M4)** | Validators (Roady, RealityCheck) | **`drift-report`** + per-node verdicts |
| **Orchestrator hook** | Task lists from `/speckit.tasks` | `next-leaves` API over graph |
| **Validation** | Checklists, analyze command | Per-node verdict engine (tests, LLM judge, etc.) |

**Use Spec Kit** when a one-shot feature kickoff in-repo is enough and you don't need manifold.  
**Use manifold** when the project outlives one feature. No automatic import bridge (Topic D deferred — L15).

### Agent memory — the unstructured layer

| Approach | Examples | Gap manifold fills |
|---|---|---|
| Static project rules | `CLAUDE.md`, `AGENTS.md` | No graph, no history, no spec-audit |
| Session notes | `NOTES.md`, GCC `.GCC/` | Unstructured; hard to query "what's next?" |
| RAG / memstore | MCP memory servers | Facts, not layered requirements with verdicts |

**Manifold is typed external memory for project intent** — queryable, versioned, not freeform prose. For session bootstrap without MCP, copy what you need into host instruction files (`CLAUDE.md`, `CODEX.md`, etc.) yourself; manifold does not auto-generate those files (Topic C deferred).

### Intent-broker (orchestrator role)

Orchestrators (Cursor, Codex, Factory, etc.) hold tickets and runtime state — not a spec graph. Manifold's MCP slot is the **intent-broker**: read `next_leaves` / `peek_project` before dispatch; write `transition_target` and verdicts back. Parallel worktrees share one `$MANIFOLD_DB`. The orchestrator skill (separate repo path) consumes this surface; manifold does not dispatch agents.

### Task / ticket tools — the execution layer

Linear, Jira, GitHub Issues track **work items**. They don't model **why the system must satisfy goal G**, how capability C refines intent I, or whether contract K drifted from its rationale.

**Manifold is not a ticket system.** Orchestrator may *create* tickets from `next-leaves`; manifold holds the spec they implement.

### Progress telemetry — the runtime layer

**progress-tracker** (this repo's MCP) answers "what are dispatched agents doing right now?" Manifold answers "what should the project become, and have we changed direction without saying so?"

---

## What manifold adds that the industry didn't combine

One package, agent-native:

1. **DB-canonical spec** — one source of truth; markdown is export, not working surface  
2. **Layered AND/OR graph** — KAOS-grounded, multi-parent, validated  
3. **Revision history** — every edit is a revision; **`change_reason` required** on content updates  
4. **Spec audit (M3)** — **`spec-audit`** surfaces unexplained revisions and rationale changes  
5. **Compass queries** — `next-leaves`, `target_status` for orchestrator handoff  
6. **Verdict engine** — automated_check, python_assertion, human_signoff, llm_judge  
7. **Three surfaces** — CLI (17 subcommands), MCP (38 tools), web UI — over one Python library  
8. **M4 drift report** — **`drift-report`** for spec↔code (Topic E v1 shipped; v2 LLM match deferred)  

The idea isn't novel. The **integration for long-horizon agent-orchestrated work** is.

### Three "intent drift" lineages (don't conflate)

| Lineage | Meaning |
|---|---|
| Intent-Based Networking | KPI degradation in telecom |
| Agent safety | Runtime goal change under adversarial pressure |
| **Spec↔code (manifold)** | Valid code, lost *why* — Stonewall/Tricentis discourse |

Lead with operational nouns (`change_reason`, `spec-audit`, `next-leaves`); cite IBN only for etymology.

---

## When to use manifold (and when not to)

### Use manifold when

- The project lives long enough that you might forget why something exists  
- Multiple agents or sessions touch the same spec over time  
- You need "what should we work on next?" from the spec graph, not from chat memory  
- You want to catch **unexplained spec revisions** before they compound (`spec-audit`)  
- You want **spec↔code drift** on realization nodes (`drift-report`)  
- An orchestrator will consume structured `next-leaves` and write verdicts back  

### Don't use manifold when

- You're doing a one-shot feature and Spec Kit's markdown workflow is enough  
- You only need task tracking (use Linear/issues) or agent telemetry (use progress-tracker)  
- You need enterprise ALM, sign-off chains, or multi-tenant requirements management  
- You want the spec to live in git as markdown first — use `manifold export` for archival, not as primary authoring if you prefer files  

---

## Further reading

| Doc | Contents |
|---|---|
| [`user-guide.md`](user-guide.md) | Install, CLI, MCP, daily workflows |
| [`architecture.md`](architecture.md) | Schema, MCP tools, KAOS lineage detail |
| [`../../packages/manifold/README.md`](../../packages/manifold/README.md) | Core library (for orchestrator imports) |
| [`../../docs/manifold/todo.md`](../../docs/manifold/todo.md) | Master checklist + roadmap decisions |
| [`docs/manifold/glossary.md`](../../docs/manifold/glossary.md) | Canonical proper nouns |
| [`docs/manifold/how-to-use.md`](../../docs/manifold/how-to-use.md) | Chat-first usage guide |

### External references cited above

- [Stonewall — Intent Drift](https://stonewall.dev/blog/intent-drift/)  
- [Omniflow — Requirement drift](https://www.omniflowai.com/blog/the-real-cost-of-requirement-drift)  
- [Tricentis — Intent drift in AI code](https://www.tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots)  
- [Anthropic — Context engineering for agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)  
- [GitHub Spec Kit](https://github.github.io/spec-kit/)  
- [Spec-Driven Development (Medium overview)](https://medium.com/data-science-collective/spec-driven-development-when-intent-becomes-the-source-code-3af39f86b9d3)  
- [KAOS tutorial (PDF)](https://www.cse.msu.edu/~cse870/Materials/GoalModeling/KaosTutorial-2007.pdf)  
