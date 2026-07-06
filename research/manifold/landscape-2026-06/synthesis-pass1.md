---
status: archived
study: manifold-landscape-2026-06
type: synthesis
tags: [A+E-calibration, archive]
superseded-by: synthesis.md
created: 2026-06-06
---

# Pass 1 synthesis — Sessions A + E (archive)

> **Superseded — see [`synthesis.md`](synthesis.md).** Full A–E merge is canonical. This file is the **frozen A+E calibration draft**; do not edit.

---

*Archive below — A+E calibration draft only. Do not edit; update `synthesis.md` instead.*

Merged findings from calibration runs: Session A + E (Claude + ChatGPT each).

---

## Executive summary

**The problem is real, named, and worsening.** Both session pairs agree: no shipped tool combines a **queryable layered intent graph**, **continuous drift detection**, and a **"what's next" API** for orchestrators. The market is crowded at the **authoring** layer (Spec Kit, OpenSpec, BMAD, Kiro, Superpowers) and emerging at the **validation** layer (Roady, RealityCheck, Tricentis, drift-analyzer). Manifold's gap is the **read path** — durable intent substrate that survives session resets and answers compass queries across months.

**Strategic posture:** Interoperate with Spec Kit (upstream node producer), don't compete. Own `change_reason` + `rationale` + `drift-report`. Ship as **MCP + AGENTS.md producer**, not another CLI/IDE.

---

## Calibration notes (provider comparison)

| Signal | Claude | ChatGPT | Resolution |
|---|---|---|---|
| OSS long-tail | Superpowers, PRPs, Augment Cosmos, Fiberplane | Roady, RealityCheck, PAAD, drift-detect, ReqToCode | Merge — ChatGPT found drift validators Claude missed |
| Enterprise rows | Tricentis, Zenn IDD deep-dive | Qase, cleaner Kiro pricing | Use ChatGPT URLs for enterprise; Claude for discourse genealogy |
| Stonewall blog | Could not verify (search miss) | Cited as May 2026 popularizer | **Verified independently:** [stonewall.dev/blog/intent-drift](https://stonewall.dev/blog/intent-drift/) exists (May 20, 2026). Keep citation in `why-manifold.md`. |
| Terminology | Three lineages (IBN / agent safety / spec↔code) | Coinage vs popularization timeline | Adopt Claude's three-lineage frame; add Stonewall to line 3 popularizers |
| Pain catalog | 23+ HN/DEV/Stack Overflow quotes | 24 quotes incl. Reddit, GitHub issues | Combined catalog validates session amnesia, tests-green-but-wrong, doc decay |

**Provider pick for B/C/D:** Claude (long-tail discovery, hallucination flags). Use ChatGPT for citation hygiene on enterprise rows.

---

## Vocabulary decision

### Lead with "intent drift" — but define manifold's narrow sense

The term has **three lineages** conflated in 2026 marketing:

| Lineage | Origin | Meaning | Examples |
|---|---|---|---|
| **1. Intent-Based Networking** | Muonagor & Bensalem, [arXiv:2404.15091](https://arxiv.org/abs/2404.15091) (Apr 2024) | Gradual degradation of intent fulfillment in network telemetry | Etymological anchor — cite when claiming rigor |
| **2. Agent safety / runtime** | Arike et al. [2505.02709](https://arxiv.org/abs/2505.02709), ARMO, Zenity | Agent's runtime goal changing under adversarial pressure | Vocabulary collision — disambiguate in docs |
| **3. Spec↔code (manifold's lane)** | Tricentis (Apr 2026), [Stonewall](https://stonewall.dev/blog/intent-drift/) (May 2026), Zenn IDD, Tian Pan | Code passes tests but no longer matches *why* the work existed | **This is manifold's definition** |

**Manifold's operational nouns (USE):** `change_reason`, `rationale`, `drift-report`, `next-leaves`

**Avoid claiming:** invention of "intent drift"; ownership of "detection" alone (polluted by ARMO, ML drift vendors)

**Positioning sentence:**

> Everyone agrees intent drift is the problem. Manifold makes *why* a typed field — ADRs that talk to your agent, version your intent, and produce a drift report when code diverges.

### Related terms map

| Term | Who uses it | Manifold relationship |
|---|---|---|
| spec drift | Augment, Thoughtworks, Stonewall | Subset — code diverges from written spec; manifold also catches spec diverging from customer |
| requirement drift | Omniflow, PM tooling | Pre-code quality; manifold is post-authoring persistence |
| goal drift | Arike et al., safety community | Different audience — disambiguate |
| context engineering | Zenn IDD, Anthropic, Thoughtworks | Adjacent — manifold is typed context, not freeform |
| living PRD / living specs | Omniflow, Augment Cosmos, Stonewall | Commercial framing manifold competes with at narrative level |
| spec-driven development (SDD) | Spec Kit, Kiro, OpenSpec, Sean Grove keynote | **Complementary upstream** — manifold sustains what SDD starts |

---

## Unified tool inventory (deduplicated)

Ratings: **full / partial / none / n/a** on M1–M7 axes. Scores merge both providers where they agree; splits noted in `notes`.

| Tool | URL | Category | One-liner | Pricing | Sweet spot | M1 | M2 | M3 | M4 | M5 | M6 | M7 | Gap vs manifold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **GitHub Spec Kit** | [github.com/github/spec-kit](https://github.com/github/spec-kit) | OSS SDD | Constitution → specify → plan → tasks → implement; ~109k★ | OSS (MIT) | One-shot feature → medium project | full | partial | partial | partial | partial | partial | full | Per-feature markdown chain; no project graph; analyze is one-shot not continuous |
| **OpenSpec** | [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | OSS SDD | Delta specs (ADDED/MODIFIED/REMOVED); propose → apply → archive; ~53k★ | OSS (MIT) | Brownfield incremental change | full | partial | **full** | partial | partial | partial | full | Folders not graph; structural validation not semantic drift; no `change_reason` |
| **BMAD-METHOD** | [github.com/bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | OSS SDD | Multi-agent agile team; `bmad-help` recommends next workflow; ~49k★ | OSS | Long-lived greenfield | full | partial | partial | none | **full** | partial | full | Workflow files not queryable intent graph; no drift detector |
| **AWS Kiro** | [kiro.dev](https://kiro.dev) | Commercial IDE | Spec-first IDE: requirements/design/tasks in `.kiro/specs/`; hooks on save | Free / $20 / $40 / $200 mo | AWS-shop brownfield | full | partial | partial | partial | partial | partial | full | AWS-locked; per-feature specs; no cross-session rationale log |
| **Tessl** | [tessl.io](https://tessl.io) | Commercial platform | Spec registry + MCP; spec-bound tests; skills package manager | Freemium + enterprise | Enterprise / long-lived | full | partial | partial | partial→full | partial | **full** | **full** | Not a graph; compass = plan audit trail; closed-source |
| **Augment Cosmos** | [augmentcode.com](https://www.augmentcode.com) | Commercial platform | Living specs + Context Engine bidirectional sync; Coordinator agent | ~$200/dev/mo | Enterprise multi-repo | full | partial | full | partial→full | partial | full | full | Vendor-locked; no public next-leaves API; implicit spec model |
| **Superpowers** | [github.com/obra/superpowers](https://github.com/obra/superpowers) | OSS workflow | Brainstorm → plan → execute hard gates + TDD; ~218k★ | OSS (MIT) | One-shot feature | full | partial | partial | partial | partial | partial | full | Per-feature; plan dies when feature ships |
| **Roady** | [github.com (Roady)](https://github.com/search?q=roady+drift+detect+MCP&type=repositories) | OSS validator | MCP-native plan-of-record; `roady drift detect`; next-task flow | OSS | Long-lived project | full | full | full | **full** | **full** | partial | **full** | **Closest OSS adjacent.** Task-centric; weak on `change_reason` / rationale history |
| **RealityCheck** | [github.com (RealityCheck)](https://github.com/search?q=RealityCheck+SPEC.md+PLAN.md+drift&type=repositories) | OSS validator | SPEC.md + PLAN.md vs code verdicts (`DRIFT_DETECTED`) | OSS | One-shot feature slice | full | none | partial | **full** | none | **full** | partial | Point-in-time checker, not long-horizon compass |
| **PAAD** | [github.com (PAAD)](https://github.com/search?q=PAAD+pushback+alignment+agentic-review&type=repositories) | OSS skills | pushback / alignment / agentic-review guardrail skills | OSS | Long-lived project | partial | partial | partial | full | none | partial | full | Procedural guardrails, not durable intent memory |
| **drift-detect** | GitHub OSS | OSS scanner | Repo reality scan: plans/docs/GitHub vs code; LLM synthesis | OSS | Long-lived project | partial | partial | partial | full | partial | partial | partial | Episodic reconstructive, not persistent graph |
| **drift-analyzer** | GitHub OSS | OSS analyzer | Architectural erosion from AI code; passes tests, violates architecture | OSS | Long-lived project | none | partial | partial | full | none | full | partial | Structure not business intent |
| **Omniflow** | [omniflowai.com](https://www.omniflowai.com) | Commercial SaaS | Living PRD sync engine; requirement drift surfacing | Freemium | PM-led greenfield SaaS | full | partial | partial | full | partial | partial | no | Closed SaaS; PRD-DSL not code graph; no MCP |
| **Tricentis AI Workspace** | [tricentis.com/blog/intent-drift-ai-code](https://www.tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots) | Enterprise QA | Tests that pass for wrong reasons; intent vs code correlation | Enterprise | Enterprise QA orgs | partial | none | partial | **full** | none | **full** | partial | QA-centric not dev-centric; no intent graph |
| **Stonewall** | [stonewall.dev](https://stonewall.dev) | Commercial (waitlist) | Customer signal ↔ spec ↔ code provenance; intent drift detector | Unknown | PM/engineering alignment | partial | none | partial | full | none | partial | partial | Detector layer not durable spec graph |
| **Zenn IDD (virtualcraft)** | [zenn.dev/virtualcraft](https://zenn.dev/virtualcraft/articles/idd-07_idd-concept) | Methodology | Why/What/How/Not structure; 11+ part essay series | OSS (essays) | Inner-source projects | full | **full** | **full** | full | partial | partial | partial | Design proposal not shipped tool — cite as theoretical ally |
| **ADR-tools / Log4brains** | [github.com/npryce/adr-tools](https://github.com/npryce/adr-tools) | OSS methodology | Architecture Decision Records — capture *why* | OSS | Regulated / long-lived | partial | partial | **full** | none | none | none | partial | Static prose; manifold = "ADRs that talk to your agent" |
| **Agent OS** | [buildermethods.com/agent-os](https://buildermethods.com/agent-os) | OSS standards | Extract/inject coding standards into agent work | OSS | Standards layer | partial | partial | partial | none | none | none | partial | AGENTS.md++ not spec graph |
| **AGENTS.md** | [agents.md](https://agents.md) | Open format | Persistent agent instructions; 60k+ repos; AAIF-stewarded | OSS | Cross-agent conventions | partial | none | partial | none | none | none | partial | **Consume, don't compete** — manifold exports slim AGENTS.md from graph |
| **Claude Code / Cursor / Codex** | Various | Agent IDEs | Plan mode + rules/memory + MCP; session-scoped plans | Freemium | Daily agent coding | partial | none | partial | partial | partial | partial | **full** | File-based memory; no project compass graph |
| **ReqToCode** | [arxiv.org](https://arxiv.org/search/?query=ReqToCode+requirements+traceability) | Research | Compile-time requirement links in codebase | n/a | Research | full | full | full | full | partial | full | none | Research-stage; requirement-centric not compass platform |

**Category leaders not in Pass 2 shortlist:** Amazon Q Developer (deprecated → Kiro CLI), PRPs, Aider CONVENTIONS.md, Fiberplane Drift (docstring-only), ARMO (runtime security), Qase (enterprise traceability), R2Code (link recovery research).

---

## M-axis heatmap

Who owns which axis across the **top adjacents** (full = primary strength):

```
                    M1    M2    M3    M4    M5    M6    M7
                    truth graph hist  drift comp  verdict agent
─────────────────────────────────────────────────────────────
Manifold (target)   ●     ●     ●     ●     ●     ●     ●
GitHub Spec Kit     ●     ◐     ◐     ◐     ◐     ◐     ●
OpenSpec            ●     ◐     ●     ◐     ◐     ◐     ●
BMAD                ●     ◐     ◐     ○     ●     ◐     ●
Kiro                ●     ◐     ◐     ◐     ◐     ◐     ●
Tessl               ●     ◐     ◐     ◐     ◐     ●     ●
Augment Cosmos      ●     ◐     ●     ◐     ◐     ●     ●
Roady               ●     ●     ●     ●     ●     ◐     ●
RealityCheck        ●     ○     ◐     ●     ○     ●     ◐
Tricentis           ◐     ○     ◐     ●     ○     ●     ◐
Zenn IDD (design)   ●     ●     ●     ●     ◐     ◐     ◐
ADR-tools           ◐     ◐     ●     ○     ○     ○     ◐

● = full   ◐ = partial   ○ = none
```

**Blank columns in the market (manifold's moat):**

| Axis | Who comes closest | What's missing |
|---|---|---|
| **M2 + M5 together** | Roady (partial on both) | No KAOS-style layered AND/OR graph with multi-parent |
| **M3 + M4 together** | OpenSpec (M3), Roady/RealityCheck (M4) | No typed `change_reason` linking history to drift |
| **M5 as API** | BMAD `bmad-help`, Roady next-task | No `next-leaves` over cross-feature project graph |
| **M7 + M3** | Roady, Tessl | No rationale field + revision semantics |

**Core finding (both sessions):** No tool ships **graph + drift + next-leaves API** together in OSS.

---

## Category clustering

Three patterns dominate Pass 1:

### 1. Artifact conveyor belt (Session A)

Spec Kit, OpenSpec, BMAD, Kiro, Superpowers, PRPs — all converge on **constitution/standards → spec → plan → tasks → implement**. Strong at *starting* work from intent. Weak at *sustaining* intent over months.

**Manifold stance:** Treat as upstream producers. Spec Kit pipeline → graph nodes. OpenSpec delta syntax → edge types for changes.

### 2. Durable instruction layer (Session A)

AGENTS.md, CLAUDE.md, Cursor Rules, Agent OS, Aider CONVENTIONS — preserve **how we work**, not **why this feature exists**.

**Manifold stance:** Auto-generate slim AGENTS.md from graph for session-reset survival. Consume AGENTS.md standard, don't compete.

### 3. Drift validators (Session E)

Roady, RealityCheck, PAAD, drift-detect, drift-analyzer, Tricentis, Stonewall — detect divergence but lack **persistent rationale graph**.

**Manifold stance:** Differentiate by owning **why history (M3)**, not just alignment verdicts. `drift-report` as quotable artifact noun.

---

## Community pain (merged catalog)

Both sessions collected 40+ primary-source quotes. Top themes by frequency:

| Theme | Representative quote | Implication for manifold |
|---|---|---|
| **Session amnesia** | "Despite my best efforts… some of the nuance is lost and the implementation suffers" (HN) | External typed memory outside chat window |
| **Tests green, wrong thing** | "156/156 tests passed" while feature broken (HN) | `drift-report` + verdict engine beyond unit tests |
| **Doc/PRD decay** | "Outdated context documents caused agents to generate code that conflicted with recent refactors" (arXiv field study) | DB-canonical spec; markdown is export |
| **Multi-agent divergence** | "Four Claude Code sessions… four divergent agents" (DEV.to) | Single queryable graph all agents read |
| **Correction not applied** | "Acknowledges the correction and continues executing against the original interpretation" (Tian Pan) | `change_reason=correction` typed field |
| **Built wrong thing** | Kiro: "boat load of passing tests but zero useful code" (HN) | Compass queries before implement |
| **SDD = waterfall debate** | "Planning upfront helps agents because agents follow plans literally" (HN 45935763) | Position as *sustaining* not *starting* |

**Research validation:** Arike et al. (2025) and Saebo et al. (2026) quantify goal/intent drift in coding agents — academic anchor for product claims.

---

## Strategic implications (locked)

| Decision | Rationale | Source |
|---|---|---|
| Interoperate with Spec Kit, don't compete | ~109k★ incumbent; pipeline produces nodes manifold queries | Session A both |
| Own the read path (graph + drift + next-leaves) | Crowded at authoring; gap is continuous compass | Session A both |
| Lead with `change_reason` + `rationale` + `drift-report` | No competitor has typed why-field | Session E Claude |
| Ship MCP + AGENTS.md producer | Category settled on these two integration surfaces | Session A Claude |
| Frame as "ADRs that talk to your agent" | Legitimate lineage; inoculates against reinvented-wheel objection | Session E both |
| Avoid vibe-vs-SDD culture war | "Manifold works whichever way you code" | Session E Claude |
| Cite Muonagor & Bensalem (2024) for etymology | Three-lineage disambiguation looks informed | Session E Claude |

---

## Pass 2 shortlist (8 tools)

Ranked by adjacency to manifold's thesis and Pass 2 ROI:

| Priority | Tool | Why deep dive |
|---|---|---|
| **1** | **GitHub Spec Kit** | Incumbent to interoperate with; understand import path for graph nodes |
| **2** | **OpenSpec** | Strongest OSS on M3 (changes/ archive); delta syntax as edge types |
| **3** | **Roady** | Closest OSS on M4+M5+M7; understand task-vs-graph gap |
| **4** | **AWS Kiro** | Strongest commercial spec-first IDE; hooks model; AWS distribution |
| **5** | **Tessl** | Closest commercial on M6+M7; MCP + spec-bound tests |
| **6** | **Augment Cosmos** | Closest enterprise "living specs"; Context Engine bidirectional sync |
| **7** | **BMAD-METHOD** | Closest "what next" workflow (`bmad-help`); persona graph model |
| **8** | **RealityCheck** | Purest drift validator; understand verdict-only vs rationale gap |

**Run Pass 2 using:** [`06-pass2-deep-dive-template.md`](06-pass2-deep-dive-template.md) — one chat per tool or batch 3 per chat.

**Deferred to Session B/C or later:** Tricentis, Omniflow, Stonewall (commercial positioning), Qase (enterprise ALM), Zenn IDD (methodology essay, not tool).

---

## Action items

### Immediate (this repo)

- [x] Write this synthesis (`synthesis-pass1.md`)
- [ ] Run Sessions **B** (ALM/traceability), **C** (agent memory), **D** (orchestration) on Claude — prompts in `02-`, `03-`, `04-`
- [ ] Pass 2 deep dives on 8 shortlisted tools
- [ ] Final merge → `synthesis.md` after B/C/D complete
- [ ] Feed synthesis into manifold README redesign (parallel with v0.5 work in [`docs/README.md`](../../docs/README.md))

### `why-manifold.md` updates

- [ ] Add Stonewall to line 3 popularizers (verified May 2026)
- [ ] Add three-lineage vocabulary disambiguation section
- [ ] Add Roady, RealityCheck to competitor table (validation cluster)
- [ ] Strengthen "interoperate with Spec Kit" framing

### Positioning watchlist (triggers to reposition)

| Trigger | Response |
|---|---|
| GitHub Spec Kit adds `rationale.md` / `why.md` RFC | Reposition as layer that works *with* Spec Kit |
| Tricentis launches developer-facing (not QA) product | Lean harder into MCP + agent-native |
| Roady adds `change_reason` field | Direct OSS competitor — accelerate M3 differentiation |

---

## What's next

1. **You (Pi):** Run Sessions B + C + D in Claude (paste from `02-session-B-alm.md`, `03-session-C-agent-memory.md`, `04-session-D-orchestration.md`)
2. **Cursor:** Pass 2 deep dives on shortlist when B/C/D results are in (or start now on top 3: Spec Kit, OpenSpec, Roady)
3. **Parallel track:** Orchestrator design doc + manifold v0.1.1 per [`docs/README.md`](../../docs/README.md) — research informs README, doesn't block implementation

---

*Pass 1 calibration complete. Sessions A + E synthesized 2026-06-06.*
