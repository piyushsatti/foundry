---
status: complete
study: manifold-landscape-2026-06
topic: manifold
type: study-index
tags:
  - manifold
  - competitive-analysis
  - landscape
  - intent-drift
  - spec-driven-development
  - agent-memory
  - orchestration
  - enterprise-alm
completed: 2026-06-06
pass2: closed
---

# Manifold landscape study (2026-06)

**Status: complete.** Competitive and discourse research mapping who else solves durable project intent, traceability, and agent-scale spec memory — and where manifold's gap is.

**Primary deliverable:** [`synthesis.md`](synthesis.md) — 60+ tools, five sessions (A–E), locked strategic posture.

Pass 2 (per-tool deep dives) is **closed indefinitely**. The synthesis is sufficient for positioning; [`06-pass2-deep-dive-template.md`](06-pass2-deep-dive-template.md) remains as an archived reference if integration work ever needs first-hand verification.

---

## Reading order

| Order | Document | Why read it |
|---|---|---|
| 1 | [`synthesis.md`](synthesis.md) | Executive summary, tool table, M-axis heatmap, locked decisions |
| 2 | [`results/README.md`](results/README.md) | Per-session calibration notes and provenance |
| 3 | Raw results in [`results/`](results/) | Primary sources when verifying a specific claim |
| 4 | [`00-MASTER-HANDOFF.md`](00-MASTER-HANDOFF.md) | M1–M7 axis definitions and original research charter |
| 5 | [`synthesis-pass1.md`](synthesis-pass1.md) | A+E calibration archive only — superseded |

---

## Document inventory

| File | Type | Status | Tags |
|---|---|---|---|
| [`README.md`](README.md) | study-index | current | meta |
| [`synthesis.md`](synthesis.md) | synthesis | **canonical** | positioning, tools, strategy |
| [`synthesis-pass1.md`](synthesis-pass1.md) | synthesis | archived | A+E draft |
| [`results/README.md`](results/README.md) | index | current | provenance, calibration |
| [`results/session-*.md`](results/) (7 files) | raw-results | frozen | sessions A–E |
| [`00-MASTER-HANDOFF.md`](00-MASTER-HANDOFF.md) | prompt-pack | historical | M1–M7, charter |
| [`01-session-A-sdd.md`](01-session-A-sdd.md) | session-prompt | historical | sdd, agent-workflow |
| [`02-session-B-alm.md`](02-session-B-alm.md) | session-prompt | historical | enterprise-alm |
| [`03-session-C-agent-memory.md`](03-session-C-agent-memory.md) | session-prompt | historical | agent-memory |
| [`04-session-D-orchestration.md`](04-session-D-orchestration.md) | session-prompt | historical | orchestration |
| [`05-session-E-drift-discourse.md`](05-session-E-drift-discourse.md) | session-prompt | historical | intent-drift |
| [`06-pass2-deep-dive-template.md`](06-pass2-deep-dive-template.md) | template | archived | pass2-closed |
| [`07-results-paste-template.md`](07-results-paste-template.md) | template | historical | collection |

**Naming convention:** `session-{ID}-{slug}-{provider}-YYYY-MM-DD.md` under `results/`.

---

## Load-bearing finding

No shipped tool combines a **queryable layered intent graph**, **continuous drift detection**, and a structured **`next-leaves` compass query** — together, in open source, agent-native. Stated independently by all five sessions.

**Locked posture** (detail in synthesis §8): interoperate with Spec Kit; MCP intent-broker not orchestrator; compile graph → AGENTS.md; ReqIF export; own `change_reason` / `rationale` / `drift-report` / `next-leaves`.

---

## Further reading

Curated primary sources cited in the synthesis. Read these to deepen understanding without re-running the study.

### Academic & field evidence

| Source | Link | Relevance |
|---|---|---|
| MAST multi-agent failure taxonomy | [arXiv:2503.13657](https://arxiv.org/abs/2503.13657) | 41–86.7% failure rates; "disobey task specification" top category |
| Goal drift in LLM agents | [arXiv:2505.02709](https://arxiv.org/abs/2505.02709) | Agent safety lineage of "drift" — disambiguate from spec↔code |
| Intent-Based Networking (etymology) | [arXiv:2404.15091](https://arxiv.org/abs/2404.15091) | Oldest "intent drift" lineage — cite for read-in signal |
| Git Context Controller | [arXiv:2508.00031](https://arxiv.org/abs/2508.00031) | Versioned agent context; closest research neighbor for revisions |
| Agent context field study | [arXiv:2602.20478](https://arxiv.org/pdf/2602.20478) | Outdated docs causing agent refactors to wire deprecated paths |

### Discourse & vocabulary

| Source | Link | Relevance |
|---|---|---|
| Stonewall — intent drift definition | [stonewall.dev/blog/intent-drift](https://stonewall.dev/blog/intent-drift/) | Cleanest spec↔code definition (May 2026); verified |
| Zenn IDD essay series | [zenn.dev/virtualcraft](https://zenn.dev/virtualcraft/articles/idd-07_idd-concept) | Closest philosophical ally — Why/What/How/Not structure |
| Martin Fowler — SDD tools | [martinfowler.com/.../sdd-3-tools](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html) | Kent Beck on spec-before-implement; culture-war context |
| Stack Overflow — black-box AI drift | [stackoverflow.blog/2026/04/23/...](https://stackoverflow.blog/2026/04/23/black-box-ai-drift-ai-tools-are-making-design-decisions-nobody-asked-for/) | "Built the wrong thing" pain quote |
| Tian Pan — long-conversation drift | [tianpan.co/blog/2026-05-04-...](https://tianpan.co/blog/2026-05-04-intent-drift-long-conversations-agent-goal-stale) | Correction acknowledged but not applied |

### Market anchors

| Source | Link | Relevance |
|---|---|---|
| GitHub Spec Kit | [github.com/github/spec-kit](https://github.com/github/spec-kit) | ~108k★ upstream producer manifold must interoperate with |
| OpenSpec | [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | Delta-spec syntax model for change edges |
| AGENTS.md standard | [agents.md](https://agents.md/) | Convention layer — manifold compiles down to this |
| ADR-tools | [github.com/npryce/adr-tools](https://github.com/npryce/adr-tools) | Honest ancestor — "ADRs that talk to your agent" |
| Tricentis intent drift | [tricentis.com/blog/intent-drift-...](https://www.tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots) | Commercial validation cluster framing |

### Community pain (HN)

- Session amnesia: [HN 44378022](https://news.ycombinator.com/item?id=44378022)
- SDD waterfall debate: search HN "Spec-Driven Development Waterfall Strikes Back"
- Enterprise ALM too heavy: [HN 46752826](https://news.ycombinator.com/item?id=46752826) (Show HN: Sara)

---

## Prompts for deepening understanding

Use these in a fresh external chat (web search on) when a specific question arises. **Not required** to close this study — optional follow-ups for product work later.

### 1. Spec Kit import path

> Map the exact file layout under `.specify/` in GitHub Spec Kit (latest release). For each artifact type (constitution, spec, plan, tasks), describe how it would become a node or edge in a layered intent graph. What is lost if you import once and never sync again? Cite repo paths and docs URLs.

### 2. Three-lineage vocabulary essay

> Write a 500-word glossary entry for "intent drift" covering three lineages: Intent-Based Networking (arXiv:2404.15091), agent safety/runtime goal drift (arXiv:2505.02709), and spec↔code drift (Stonewall, Tricentis, Zenn IDD). End with manifold's narrow definition and four operational nouns: `change_reason`, `rationale`, `drift-report`, `next-leaves`.

### 3. Roady vs manifold boundary

> Compare Roady (plan-of-record, `roady drift detect`, MCP-native) to a typed intent graph with rationale history. Where does Roady's task-and-plan model stop? What would `change_reason` on a revision edge add that Roady lacks? Primary sources only; mark unverified claims.

### 4. Enterprise on-ramp without GUI

> Explain ReqIF as an interchange format (Eclipse RMF). What would a solo-dev OSS tool need to export so Jama/Polarion teams could consume intent nodes? What ReqIF cannot represent that a graph-native store can?

### 5. Parallel agents shared-intent gap

> Given the coordinator + worktree pattern (Cursor, Codex, Factory, Devin), describe the failure mode when four agents compact independently. How would an MCP intent-broker change the architecture? Cite MAST (arXiv:2503.13657) and one practitioner quote.

### 6. Watchlist trigger check (quarterly)

> Re-scan GitHub issues/roadmaps for Spec Kit, Kiro, Augment Intent, Roady, and Graphiti. Has any shipped: `rationale`/`change_reason` fields, MCP spec server, Requirement entity types, or public next-task API? One paragraph per tool with URLs.

---

## Resume in a new chat

```
Read research/manifold/landscape-2026-06/README.md and synthesis.md.
This landscape study is complete. Help me apply §8 locked decisions to [specific task].
```

---

## Distillation (outside this folder)

When ready, distill findings into product docs and skill references — **not part of this study closure**:

- Manifold README / positioning copy ← synthesis §1, §3, §8
- `skills/manifold/references/why-manifold.md` ← vocabulary + AGENTS.md compile strategy
- Orchestrator design ← synthesis §4 Session D, §8 MCP intent-broker

Those live outside `research/` and are intentionally deferred until product work begins.
