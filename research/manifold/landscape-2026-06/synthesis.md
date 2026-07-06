---
status: complete
study: manifold-landscape-2026-06
type: synthesis
tags:
  - manifold
  - competitive-analysis
  - positioning
  - intent-drift
  - spec-driven-development
created: 2026-06-06
supersedes: synthesis-pass1.md
pass2: closed
---

# Manifold landscape synthesis (2026-06)

**Study complete.** Final merge of all five sessions (A–E). Supersedes the partial [`synthesis-pass1.md`](synthesis-pass1.md) draft (A + E only).

| Session | Topic |
|---|---|
| A | Spec-driven development / agent workflow |
| B | Enterprise ALM / traceability |
| C | Agent memory / context engineering |
| D | Orchestration / agent IDEs |
| E | Intent-drift discourse / validation |

**Scope:** 60+ tools, two model providers (Claude + ChatGPT dual-ran A and E; B/C/D Claude-only). Manifold is the reference — every "gap" column is measured against it.

**Index:** [`README.md`](README.md) · **Raw results:** [`results/`](results/)

---

## 1. Executive summary

Software projects lose their **"why"** faster than they lose their code. Requirements drift, docs decay into fiction, and AI agents amplify the gap by shipping correct-looking code fast without durable intent. This is no longer a vibes claim: it is named, measured, and worsening. Berkeley's MAST taxonomy (Cemri et al., arXiv:2503.13657) found 41–86.7% failure rates across 1,642 annotated multi-agent traces, with "disobey task specification" the single largest category. Arike et al. (arXiv:2505.02709) and the goal-drift literature put numbers on how agents wander from their objective over long horizons. The problem manifold targets is real.

**The core gap is consistent across all five sessions: no shipped tool combines a queryable layered intent *graph*, continuous *drift* detection, and a structured *"what's next"* query — together, in open source, agent-native.** The market is crowded at the **authoring** layer (Spec Kit, OpenSpec, BMAD, Kiro, Superpowers all converge on the same `constitution → spec → plan → tasks → implement` conveyor belt). It is rich at the **enterprise traceability** layer (DOORS, Polarion, Jama, Codebeamer own canonical truth + typed graph + baselines + verdicts, but are GUI-first, per-seat, $50–80/user/mo, and treat AI as a widget rather than a peer). It is converging on **file-based memory** as the agent-context primitive (AGENTS.md won the convention war at 60k+ repos; Anthropic explicitly bet on Markdown over vector RAG). And a fresh **validation** cluster is emerging (Roady, RealityCheck, Tricentis, drift-analyzer, Stonewall). But every one of these solves a *slice*. The slice nobody owns is **the read path that survives session resets** — the M3 (history of *why*) + M4 (drift) + M5 (compass) trifecta exposed over MCP.

**Strategic posture for manifold:**

- **Interoperate, don't compete, at the authoring layer.** Treat Spec Kit's pipeline as an upstream producer of graph nodes; treat OpenSpec's `ADDED/MODIFIED/REMOVED` delta syntax as an edge type. Manifold is the durable graph these tools feed, not a rival CLI.
- **Be the MCP intent-broker, not another orchestrator.** Session D is unambiguous: there are already 12+ orchestrators, every one of them consumes MCP, and not one holds a structured spec graph. Manifold's SQLite spec graph behind an MCP server is the missing context layer they are *built to consume*.
- **Own the vocabulary the discourse is talking around.** Lead with the operational nouns — `change_reason`, `rationale`, `drift-report`, `next-leaves` — and frame manifold as "ADRs that talk to your agent." Do not claim to have invented "intent drift" (three lineages already contest it).
- **Sit above, not against, the file-based ecosystem.** Compile manifold's graph down to a slim AGENTS.md so the project survives in tools that don't speak MCP, and offer ReqIF export as a cheap on-ramp to the enterprise world.

The idea is not novel — KAOS, traceability, and SDD all prefigure it. The **packaging for long-horizon, agent-orchestrated work** is the white space.

---

## 2. Cross-session findings

### What all five sessions independently agree on

1. **No tool ships `graph + drift + next-leaves` together.** Stated verbatim or in substance by A (both providers), B, C, D, and E. This is the load-bearing finding of Pass 1.
2. **M4 (drift) + M5 (compass) are the consistently unowned axes.** Authoring tools start work but don't sustain it; enterprise ALM models the graph but never reconciles it against live code; memory tools store facts or conventions, not the intent-vs-implementation gap.
3. **MCP is the integration surface; AGENTS.md is the convention layer.** Every commercial agent platform exposes MCP. The winning move is to *consume* AGENTS.md and *expose* over MCP, not to build a new IDE or CLI.
4. **Spec Kit, Kiro, and Augment (Intent/Cosmos) recur as the closest adjacents** in every relevant session — and each is missing exactly the graph + drift + rationale-history combination.
5. **The "why" survives nowhere.** None of the tools — not even the closest neighbors (Spec Kit, Roady, GCC, Zenn IDD) — persist a typed `change_reason` linking *why intent changed* to *whether code drifted*.

### Session-specific unique contributions

| Session | Category | Unique contribution to the synthesis |
|---|---|---|
| **A** — SDD / agent workflow | The "artifact conveyor belt" framing; identification of Spec Kit as upstream node-producer; the steal-the-write-path / own-the-read-path split; academic drift anchors (Arike, Saebo) |
| **B** — Enterprise ALM / traceability | What enterprise got *right* (typed link semantics, immutable baselines, ReqIF interop) vs *wrong for the agent era* (per-seat, GUI-first, review-gate-as-unit-of-work); confirms no commercial tool ships real-time code↔req drift |
| **C** — Agent memory / context | The WHAT (code index) / HOW (conventions) / WHY (intent graph) trichotomy; AGENTS.md compile strategy; Anthropic's file-over-vector bet validates "structure beats similarity search"; GCC as research lineage for revisions |
| **D** — Orchestration / agent IDEs | "Who holds intent during parallel agent work" is sized and unowned; MAST + token-burn economics give the wedge urgency; manifold = intent-broker not orchestrator; worktree convergence |
| **E** — Drift discourse / validation | The three-lineage genealogy of "intent drift"; the operational-noun vocabulary decision; the OSS validation cluster (Roady, RealityCheck, drift-analyzer); ADRs as honest ancestor |

---

## 3. Vocabulary decision

### "Intent drift" has three lineages — claim none, but situate manifold in the third

The phrase is contested and 2026 vendor marketing conflates the three meanings:

| Lineage | Origin | Meaning | Manifold's stance |
|---|---|---|---|
| **1. Intent-Based Networking** | Muonagor & Bensalem, [arXiv:2404.15091](https://arxiv.org/abs/2404.15091) (23 Apr 2024) — "gradual degradation in the fulfillment of the intents, before they fail" | Network telemetry drifting from target KPIs | **Cite as the etymological anchor** — it predates the AI-coding usage by ~2 years and signals manifold is read-in. |
| **2. Agent safety / runtime** | Arike et al. [arXiv:2505.02709](https://arxiv.org/abs/2505.02709) (May 2025); ARMO; Zenity | An agent's *runtime* goal changing under adversarial/environmental pressure | **Disambiguate explicitly** — this is a vocabulary collision, closer to reward-hacking, and a different audience (SOC/security). |
| **3. Spec↔code (manifold's lane)** | Tricentis (28 Apr 2026); [Stonewall](https://stonewall.dev/blog/intent-drift/) (20 May 2026, **independently verified**); Zenn IDD; Tian Pan (4 May 2026) | Code passes tests but no longer matches *why* the work existed | **This is manifold's narrow sense.** |

> **Verification note.** Session E (Claude) could **not** verify the Stonewall blog initially; Session E (ChatGPT) cited it as the May-2026 popularizer. **Independently verified:** [stonewall.dev/blog/intent-drift](https://stonewall.dev/blog/intent-drift/) (May 20, 2026). Its definition — intent drift as "the distance between what a customer or PM asked for and what an engineer, or an engineer's AI, actually builds," distinguished from bugs, scope creep, model drift, and spec drift — is the cleanest in the corpus. ChatGPT-only finds (Roady, RealityCheck, PAAD) are **directional** — capability ratings from Session E, not primary-source verified in this study.

### Manifold's narrow definition

> **Intent drift (manifold's sense):** code that is valid, test-green, and even review-approved, yet no longer matches the preserved *why*. It is the lost why that diffs cannot reveal.

### Operational nouns — USE these, not the contested category label

| Noun | Role | Why it wins |
|---|---|---|
| `change_reason` | Typed field on every revision | No surveyed tool has a first-class why-it-changed field; git log and comments are the status quo |
| `rationale` | Why a node exists | The ADR lineage made explicit and queryable |
| `drift-report` | A file-able, quotable artifact (`manifold drift-report` → markdown you paste into a PR) | "Drift detection" alone is polluted (ARMO runtime, ML data drift, Fiberplane docstrings); the *report noun* is distinctive |
| `next-leaves` | The compass query — smallest open frontier nodes given current state | The structured answer to "what's next?" that no orchestrator holds internally |

**Positioning sentence (locked):**
> Everyone agrees intent drift is the problem. Manifold makes *why* a typed field — ADRs that talk to your agent, version your intent, and produce a drift report when code diverges.

### AGENTS.md compile strategy (from Session C)

The market has converged on **file-based memory as the primitive**: Anthropic's Sept 2025 "opinionated bet" was Markdown over vector RAG; AGENTS.md is at 60,000+ repos (Linux Foundation AAIF, Dec 9 2025); Cline Memory Bank, Spec Kit's `.specify/memory/`, Factory, and Serena all independently landed on Markdown-in-git. Manifold should **not fight this** — it should **compile down to a slim AGENTS.md** (and CLAUDE.md) from the graph, exactly as Spec Kit uses `.specify/memory/`. The typed graph, revisions, and drift live in a separate `.manifold/` store; the compiled AGENTS.md is the lowest-common-denominator export so non-MCP tools bootstrap the same context on session start. Positioning: manifold is the **structured layer above AGENTS.md**, capturing what flat Markdown loses without forcing users off the standard.

---

## 4. Market map by category

### SDD / agent workflow (Session A)

The category has crowded fast and converged hard. GitHub Spec Kit (~108k★, MIT), OpenSpec (~53k★, MIT), BMAD-METHOD (~49k★), AWS Kiro (commercial IDE), Superpowers (~218k★ per ClaudePluginHub), and the PRP template family all formalize the same conveyor belt: a constitution / standards layer, a high-level spec, a plan, an ordered task list, and an implement step with some verification gate. This is a genuine improvement over vibe coding — planning upfront helps agents *because* agents follow plans literally (the inversion at the heart of the "Spec-Driven Development: The Waterfall Strikes Back" HN thread, 225 points).

But almost none of these sustain **queryable intent over months**. Spec Kit's `/speckit.analyze` runs *once*, pre-implement; its specs live on per-feature branches (`001-feature-name`), not a project graph. OpenSpec's `validate --strict` checks structural completeness, not semantic drift. BMAD's `bmad-help` is the closest thing to a compass — it inspects artifacts and recommends the next workflow — but its state is workflow files plus YAML, not a typed graph. The only tools approaching "long-lived project compass" are commercial and closed: **Tessl** (specs as long-term memory, spec-bound tests as guardrails, MCP-native, but pivoting to a skills/registry play and treating the "compass" as a plan audit trail) and **Augment Cosmos/Intent** (living specs + a Context Engine over 400k+ files, the strongest bidirectional-sync story in the market — but vendor-locked at ~$200/dev/mo and with no public `next-leaves` API). Manifold's edge here is structural: a layered graph + drift + compass API that *interoperates* with Spec Kit's write path rather than re-implementing it.

### Enterprise RE / ALM / traceability (Session B)

This is the layer that already solved canonical truth, typed graphs, baselines, and verdicts — for regulated industries, at enterprise prices. IBM DOORS / DOORS Next (Jazz/OSLC backbone, token pricing ~$30k+/yr for 10 seats), Siemens Polarion (LiveDocs, built-in ReqIF, Copilot in the 2512 release), Jama Connect (branded "Live Traceability," and notably the *only* tool advertising an MCP "product context layer" and explicit "Spec-Driven Development" framing), Codebeamer (PTC, ~$79/user/mo), and Modern Requirements4DevOps + Copilot4DevOps (chat-with-backlog inside Azure DevOps) all own M1/M2/M3/M6 brilliantly. Every one of them shipped an "AI requirements assistant" in 2024–2025 — but those features do quality-scoring against INCOSE/EARS rules and test-case generation, **not** continuous code↔requirement drift detection. None ships that out of the box.

The OSS docs-as-code wing — Doorstop (YAML-per-requirement, git-versioned, used in Space ROS), Sphinx-Needs (typed needs graph from RST), and StrictDoc (`.sdoc` + web UI, presented at ESA's 2025 SW Product Assurance workshop) — gives the open world a genuine spec graph with traceability. But it is build-time only, single-owner CLI-shaped, has no MCP, no agent interface, and no drift report. ReqIF (Eclipse RMF / formalmind Studio) is the lowest-common-denominator interchange format every commercial tool speaks; it is XML/SpecObject-centric, not graph-native, but **manifold should ship ReqIF export as a cheap interop bridge** to the enterprise world. The practitioner verdict is bimodal and quotable: regulated teams still buy DOORS because regulators trust its baselines, while everyone else flees to "GitHub + markdown" — leaving an unserved middle that is exactly manifold's solo-dev / agent-orchestrator scale.

### Agent memory / context engineering (Session C)

Of 18 systems mapped, every one stores either **conversational facts** (mem0 ~57k★, Zep/Graphiti ~27k★ with a bi-temporal graph, Letta, LangMem, Cognee, the reference MCP knowledge-graph server) or **convention files** (CLAUDE.md, AGENTS.md, Cursor Rules, Cline Memory Bank, Factory Memory, Serena memories). The first lineage optimizes for user-personalization benchmarks (LongMemEval, LoCoMo) — it knows WHO the user is and WHEN they said what. The second knows HOW the team writes code. Neither knows WHY each feature exists, as a graph.

Two signals matter most. First, **Anthropic explicitly endorsed file-based memory over vector RAG** (Sept 29 2025) — a tailwind for manifold's "structure beats similarity search" thesis, though Anthropic's own primitive stops at unstructured files with no schema, no history semantics, no drift. Second, the closest neighbors — **GitHub Spec Kit** (structured requirements as durable artifacts) and the **Git Context Controller** arXiv prototype (arXiv:2508.00031; treats agent context as a versioned filesystem with COMMIT/BRANCH/MERGE/CONTEXT ops, claims >80% SWE-Bench Verified) — reify *some* structured intent but stop at flat Markdown, with no typed requirements→features→acceptance-criteria→code graph and no drift detector. **Zero of the 18 tools** compute drift between declared intent and current code. Adjacents like Serena and codebase-memory-mcp are code graphs (WHAT), not intent graphs (WHY). The whitespace is unambiguous, and Anthropic's own April-2026 Claude Code postmortem — a single instruction-file line causing outsized regressions — is in effect a confession that flat instruction files are brittle at the frontier.

### Orchestration / agent IDEs (Session D)

The orchestrator market has bifurcated: **delivery platforms** (Devin/Devin Desktop, Factory.ai Droids, Cursor Cloud Agents, OpenAI Codex, GitHub Copilot cloud agent, Replit) hold intent as an internal prompt + a Linear/Jira/GitHub ticket; **framework runtimes** (LangGraph/LangSmith, Microsoft Agent Framework, CrewAI, OpenHands) hold no spec at all and expect you to bring one. Of 12+ platforms, **only Kiro and Augment Intent treat the spec as a first-class, system-versioned artifact** — and Kiro's is a flat 3-document set (requirements/design/tasks), not a graph, not exposed over MCP, and locked to a Code-OSS fork; Augment's living spec is tied to a proprietary Context Engine.

Three structural facts make this manifold's strongest wedge. **MCP is table stakes** — every commercial platform exposes it (Copilot enables the GitHub MCP server by default; Codex CLI *is* an MCP server; Cursor has a 40-tool ceiling), so manifold's integration path is the MCP slot, identical across platforms. The orchestration model has **converged on "coordinator + specialist subagents on git worktrees"** (Factory, Cursor `/multitask`, Codex, Devin Desktop, Augment Intent) — which pushes the intent-holding layer *external* to any single agent and creates a shared-intent gap when worktrees diverge. And the economics are urgent: the Stanford Digital Economy Lab measured agentic tasks at ~1000× the token cost of code chat, Augment measured an 8.5× multiplier from un-isolated multi-agent context, and Carlini's 16-agent compiler experiment showed all 16 agents converging on the same bug for lack of shared knowledge. Manifold's future "orchestrator" component should **not** try to be the orchestrator — it should be the intent-broker every orchestrator reads from before each tool call.

### Drift discourse / validation (Session E)

This is the youngest and fastest-moving cluster, and the one closest to manifold's product surface. A wave of OSS validators landed in 2026: **Roady** (file-based, git-versioned, MCP-native plan-of-record with `roady drift detect` and a next-task flow — the **closest OSS adjacent to manifold today**, scoring well on M2/M4/M5/M7 but task-and-plan-centric with no rationale ledger), **RealityCheck** (parses `SPEC.md` + `PLAN.md`, indexes code symbols, emits `DRIFT_DETECTED`/`VIOLATION` verdicts — a sharp point-in-time checker, not a long-horizon compass), **drift-analyzer** (static architectural-erosion detection for code that passes tests but violates architecture), **drift-detect** (episodic repo reality scans), and **PAAD** (pushback/alignment/agentic-review guardrail skills). On the commercial side, **Tricentis** reframes regression blind spots as intent drift (QA-centric, "tests that pass for the wrong reasons"), **Omniflow** sells a "living PRD" sync engine, and **Stonewall** pitches customer-signal↔spec↔code provenance detection. The honest ancestor of it all is **ADRs** (Nygard 2011, adr-tools, Log4brains) — static prose capturing *why*; manifold's pitch is "ADRs that talk to your agent." The **Zenn IDD** essay series (virtualcraft) is the closest *philosophical* relative — it designs the same primitives (Why/What/How/Not structure, rationale, hierarchical inheritance, drift report) but is a design proposal, not a shipped tool. Across the whole cluster, validators check a slice of spec/plan/test/code fit; **none persists the preserved reason across months** — decision lineage, rejected alternatives, change reasons — which is exactly where `change_reason` + `rationale` + `drift-report` are uniquely powerful.

---

## 5. Unified tool table

Deduplicated to the ~25 most relevant tools across all five sessions (tools appearing in multiple sessions, e.g. Spec Kit and Kiro, are merged into one row with a combined assessment). Ratings: **● full / ◐ partial / ○ none**. Verdicts are this synthesis's read, not vendor self-claims.

### SDD / agent workflow

| Tool | URL | One-liner | M1 | M2 | M3 | M4 | M5 | M6 | M7 | Gap vs manifold |
|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| **GitHub Spec Kit** | [github.com/github/spec-kit](https://github.com/github/spec-kit) | Constitution→specify→plan→tasks→implement; ~108k★, MIT | ● | ◐ | ◐ | ◐ | ◐ | ◐ | ● | Per-feature markdown chain; `analyze` runs once not continuously; no project graph |
| **OpenSpec** | [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | Delta specs (ADDED/MODIFIED/REMOVED); propose→apply→archive; ~53k★ | ● | ◐ | ● | ◐ | ◐ | ◐ | ● | Folders not graph; structural validation not semantic drift; no `change_reason` |
| **BMAD-METHOD** | [github.com/bmad-code-org/BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD) | Multi-agent agile team; `bmad-help` recommends next workflow; ~49k★ | ● | ◐ | ◐ | ○ | ● | ◐ | ● | Workflow files + YAML, not a queryable intent graph; no drift detector |
| **AWS Kiro** | [kiro.dev](https://kiro.dev) | Spec-first IDE: requirements/design/tasks in `.kiro/specs/`; hooks on save | ● | ◐ | ◐ | ◐ | ◐ | ◐ | ● | Flat 3-doc spec not a graph; AWS-locked; spec not exposed over MCP; no rationale log |
| **Tessl** | [tessl.io](https://tessl.io) | Spec registry + MCP; spec-bound tests as guardrails | ● | ◐ | ◐ | ◐ | ◐ | ● | ● | Not a graph; "compass" = plan audit trail; closed-source; registry pivot |
| **Superpowers** | [github.com/obra/superpowers](https://github.com/obra/superpowers) | Brainstorm→plan→execute hard gates + TDD; Claude Code plugin | ● | ◐ | ◐ | ◐ | ◐ | ◐ | ● | Per-feature, per-branch; plan dies when the feature ships |

### Enterprise ALM / traceability

| Tool | URL | One-liner | M1 | M2 | M3 | M4 | M5 | M6 | M7 | Gap vs manifold |
|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| **Jama Connect** | [jamasoftware.com](https://www.jamasoftware.com/platform/jama-connect/) | "Live Traceability" RM + test mgmt; MCP "product context layer" | ● | ● | ● | ◐ | ◐ | ● | ◐ | Enterprise-priced; assumes humans + large teams; no real-time code↔spec drift |
| **IBM DOORS / DOORS Next** | [ibm.com](https://www.ibm.com/products/requirements-management) | Systems-engineering RM workhorse; Jazz/OSLC; AI assistants | ● | ● | ● | ○ | ◐ | ● | ◐ | Heavyweight, server-install, expensive; agents are widget consumers, not peers |
| **Siemens Polarion** | [siemens.com](https://polarion.plm.automation.siemens.com/) | Unified ALM + LiveDocs + ReqIF; Polarion Copilot | ● | ● | ● | ○ | ◐ | ● | ◐ | AI is on top, not the substrate; no MCP; steep learning curve |
| **Doorstop** | [github.com/doorstop-dev/doorstop](https://github.com/doorstop-dev/doorstop) | YAML-per-requirement, git-versioned RM; CLI + Python API | ● | ◐ | ● | ○ | ○ | ◐ | ○ | No drift detection, no compass, no agent layer; non-dev-hostile UX |
| **StrictDoc** | [github.com/strictdoc-project/strictdoc](https://github.com/strictdoc-project/strictdoc) | Plain-text `.sdoc` + web UI; cross-doc trace links; ReqIF | ● | ● | ● | ○ | ◐ | ◐ | ○ | Closest OSS spec-graph peer, but Python-process-bound, no MCP, no drift report |
| **ReqIF ecosystem** (Eclipse RMF) | [eclipse.dev/rmf](https://eclipse.dev/rmf/) | OMG ReqIF reference impl + editors; tool-to-tool exchange format | n/a | ● | ◐ | n/a | n/a | n/a | ○ | A format, not a tool — manifold should ship ReqIF export as enterprise on-ramp |

### Agent memory / context engineering

| Tool | URL | One-liner | M1 | M2 | M3 | M4 | M5 | M6 | M7 | Gap vs manifold |
|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| **AGENTS.md** | [agents.md](https://agents.md/) | Cross-tool open instruction standard; 60k+ repos; AAIF-stewarded | ◐ | ○ | ◐ | ○ | ○ | ○ | ◐ | Conventions by design; **consume, don't compete** — manifold exports slim AGENTS.md |
| **Claude Code CLAUDE.md / Memory Tool** | [code.claude.com](https://code.claude.com/docs/en/best-practices) | 3-layer Markdown conventions + file-based `/memories` | ◐ | ○ | ◐ | ○ | ○ | ○ | ● | Stores conventions/facts; "ignores half if too long"; no typed intent graph |
| **mem0** | [github.com/mem0ai/mem0](https://github.com/mem0ai/mem0) | Vector-RAG memory w/ optional graph; ~57k★ | ○ | ◐ | ○ | ○ | ○ | ○ | ● | Conversational facts for personalization; doesn't know project WHY |
| **Zep / Graphiti** | [github.com/getzep/graphiti](https://github.com/getzep/graphiti) | Bi-temporal knowledge graph; ~27k★; MCP server | ◐ | ● | ● | ○ | ○ | ○ | ● | Entity types tuned to user/customer, not requirements/acceptance-criteria |
| **Git Context Controller** (arXiv) | [arxiv.org/abs/2508.00031](https://arxiv.org/abs/2508.00031) | Versioned filesystem for agent context: COMMIT/BRANCH/MERGE | ● | ◐ | ● | ◐ | ◐ | ○ | ◐ | Closest research neighbor for revisions; intent still unstructured Markdown |
| **Serena** | [github.com/oraios/serena](https://github.com/oraios/serena) | LSP-based semantic code retrieval + Markdown memories; MCP | ◐ | ◐ | ◐ | ○ | ○ | ○ | ● | Code graph (WHAT), not intent graph (WHY); memories are flat Markdown |

### Orchestration / agent IDEs

| Tool | URL | One-liner | M1 | M2 | M3 | M4 | M5 | M6 | M7 | Gap vs manifold |
|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| **Augment Intent / Cosmos** | [augmentcode.com](https://www.augmentcode.com) | Living specs + Context Engine; coordinator/specialist/verifier | ● | ◐ | ● | ◐ | ◐ | ● | ● | **Most direct competitor**; vendor-locked, no public `next-leaves` API, implicit spec model |
| **Cursor / Codex / Copilot** (agent IDEs) | [cursor.com](https://cursor.com) · [openai.com/codex](https://openai.com/codex) | Parallel cloud agents on worktrees; MCP slots; plan mode | ◐ | ○ | ◐ | ○ | ◐ | ◐ | ● | Intent = prompt + worktree; zero spec graph; the perfect MCP consumers |
| **Factory.ai** | [factory.ai](https://factory.ai) | Coordinator droid dispatches specialist droids over MCP | ○ | ○ | ◐ | ○ | ◐ | ◐ | ● | Spec lives in Linear/Jira; decomposition but no structured intent store |
| **LangGraph + LangSmith** | [langchain.com/langgraph](https://www.langchain.com/langgraph) | OSS orchestration runtime + durable execution + tracing | ○ | ○ | ● | ◐ | ○ | ◐ | ● | Pure plumbing — integration partner; manifold could ship as a spec-graph node type |

### Drift / validation

| Tool | URL | One-liner | M1 | M2 | M3 | M4 | M5 | M6 | M7 | Gap vs manifold |
|---|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| **Roady** | [github.com (roady)](https://github.com/search?q=roady+drift+detect+MCP&type=repositories) | File-based, git-versioned, MCP-native plan-of-record; `roady drift detect` | ● | ● | ● | ● | ● | ◐ | ● | **Closest OSS adjacent.** Task-and-plan-centric; no rationale fields / `change_reason` |
| **RealityCheck** | [github.com (RealityCheck)](https://github.com/search?q=RealityCheck+SPEC.md+PLAN.md+drift&type=repositories) | SPEC.md + PLAN.md vs code symbols; emits `DRIFT_DETECTED` | ● | ○ | ◐ | ● | ○ | ● | ◐ | Point-in-time checker for a feature slice, not a long-horizon compass |
| **Tricentis AI Workspace** | [tricentis.com](https://www.tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots) | Flags "tests that pass for the wrong reasons" | ◐ | ○ | ◐ | ● | ○ | ● | ◐ | QA-centric not dev-centric; no intent graph; no developer-facing `change_reason` |
| **Omniflow** | [omniflowai.com](https://www.omniflowai.com) | "Living PRD" sync engine surfacing requirement drift | ● | ◐ | ◐ | ● | ◐ | ◐ | ○ | Closed SaaS; PRD-DSL not code graph; no MCP/CLI |
| **Stonewall** | [stonewall.dev/blog/intent-drift](https://stonewall.dev/blog/intent-drift/) | Customer-signal↔spec↔code provenance; intent-drift detector | ◐ | ○ | ◐ | ● | ○ | ◐ | ◐ | Detector layer, not a durable layered spec graph with native traversal |
| **Zenn IDD** (virtualcraft) | [zenn.dev/virtualcraft](https://zenn.dev/virtualcraft/articles/idd-07_idd-concept) | Why/What/How/Not intent structure; 11+ part essay series | ● | ● | ● | ● | ◐ | ◐ | ◐ | Design proposal, not a shipped tool — cite as theoretical ally |
| **ADR-tools / Log4brains** | [github.com/npryce/adr-tools](https://github.com/npryce/adr-tools) | Architecture Decision Records — capture *why* in markdown | ◐ | ◐ | ● | ○ | ○ | ○ | ◐ | Static prose; manifold = "ADRs that talk to your agent" |

> **Provenance flags:** Roady, RealityCheck, drift-analyzer, drift-detect, and PAAD were surfaced by Session E (ChatGPT) — capability ratings are **directional** (not primary-source repo-verified in this study). Stonewall is verified (above). Enterprise pricing in Session B is analyst-estimate, not vendor list.

---

## 6. M-axis heatmap

Top 12 adjacents + manifold's target row. **●** = full · **◐** = partial · **○** = none.

```
                        M1    M2    M3    M4    M5    M6    M7
                        truth graph hist  drift comp  verd  agent
────────────────────────────────────────────────────────────────
Manifold (target)        ●     ●     ●     ●     ●     ●     ●
Roady                    ●     ●     ●     ●     ●     ◐     ●
Augment Intent/Cosmos    ●     ◐     ●     ◐     ◐     ●     ●
GitHub Spec Kit          ●     ◐     ◐     ◐     ◐     ◐     ●
OpenSpec                 ●     ◐     ●     ◐     ◐     ◐     ●
AWS Kiro                 ●     ◐     ◐     ◐     ◐     ◐     ●
Tessl                    ●     ◐     ◐     ◐     ◐     ●     ●
BMAD-METHOD              ●     ◐     ◐     ○     ●     ◐     ●
Jama Connect             ●     ●     ●     ◐     ◐     ●     ◐
Zenn IDD (design only)   ●     ●     ●     ●     ◐     ◐     ◐
RealityCheck             ●     ○     ◐     ●     ○     ●     ◐
Tricentis                ◐     ○     ◐     ●     ○     ●     ◐
ADR-tools                ◐     ◐     ●     ○     ○     ○     ◐
────────────────────────────────────────────────────────────────
```

**Reading the map.** Manifold is the only target row that is full across all seven axes — and the claim is credible precisely because the strongest competitors each have a *different* hole:

| Combination | Who comes closest | What's still missing |
|---|---|---|
| **M2 + M5** (graph + compass) | Roady (full on both) | No KAOS-style AND/OR layered graph with multi-parent refinement |
| **M3 + M4** (history + drift) | OpenSpec (M3), Roady/RealityCheck (M4) | No typed `change_reason` linking *why intent changed* to *whether code drifted* |
| **M5 as an API** | BMAD `bmad-help`, Roady next-task | No `next-leaves` over a cross-feature project graph |
| **M7 + M3** (agent-native + history) | Roady, Tessl | No rationale field + revision semantics together |

**Core finding, restated:** no tool ships **graph + drift + next-leaves** together in OSS. Roady gets closest and is the one to watch.

---

## 7. Community pain synthesis

Both dual-run sessions plus the Claude-only B/C/D collected 60+ primary-source quotes. Deduplicated to the eight highest-frequency themes, one quote each:

1. **Session amnesia.** "We get into a groove planning or debugging something, and then by the time we are ready to implement, we've run out of context window space. Despite my best efforts to write good `/compact` instructions, some of the nuance is lost and the implementation suffers." — Hacker News ([id 44378022](https://news.ycombinator.com/item?id=44378022), Jun 2025)

2. **Tests green but wrong.** "Every project worked. Tests passed. Users were fine. But under the surface, the AI had been making contradictory behavioral decisions for weeks without anyone noticing." — DEV.to ([skaaz, 2026](https://dev.to/skaaz/your-ai-written-codebase-is-drifting-heres-how-to-measure-it-f10))

3. **Doc / PRD decay.** "On at least two occasions, outdated context documents caused agents to generate code that conflicted with recent refactors… a combat spec referenced legacy stat fields that had been migrated, causing the agent to wire damage calculations through a deprecated path." — arXiv field study ([2602.20478](https://arxiv.org/pdf/2602.20478), 2026)

4. **Multi-agent divergence.** "If you have four Claude Code sessions running against the same codebase, each compacting independently, you end up with four divergent agents." — DEV.to (whoffagents, 2026)

5. **Correction acknowledged but not applied.** "By message 20, the agent has built substantial context around what it understood the goal to be… It acknowledges the correction and then continues executing against the original interpretation." — Tian Pan ([2026-05-04](https://tianpan.co/blog/2026-05-04-intent-drift-long-conversations-agent-goal-stale))

6. **Built the wrong thing.** "Chad had built an elaborate context-aware filtering system (completely unrelated to what I asked for) around my simple lint rule… this is drift in a nutshell: a complex solution to a nonexistent problem." — Stack Overflow Blog ([Apr 23 2026](https://stackoverflow.blog/2026/04/23/black-box-ai-drift-ai-tools-are-making-design-decisions-nobody-asked-for/))

7. **SDD = waterfall / the spec-lifecycle question.** "The descriptions of Spec-Driven development that I have seen emphasize writing the whole specification before implementation. This encodes the (to me bizarre) assumption that you aren't going to learn anything during implementation that would change the specification." — Kent Beck, quoted by Martin Fowler ([Jan 8 2026](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html))

8. **Enterprise ALM too heavy for modern dev.** "Expensive, heavy tools like DOORS that don't fit modern dev workflows; JIRA-based workarounds that slow everything down and integrate poorly with code… your requirements are too important to be locked in proprietary systems." — Show HN: Sara ([id 46752826](https://news.ycombinator.com/item?id=46752826), ~Feb 2026)

**Academic validation:** Arike et al. (arXiv:2505.02709, 2025) and the Berkeley MAST taxonomy (arXiv:2503.13657 — 41–86.7% failure across 1,642 traces, "disobey task specification" top category) give the product claims a numbers-backed anchor, not a vibes one.

---

## 8. Strategic implications for manifold

Locked decisions carried forward from Pass 1 and extended with B/C/D findings:

| Decision | Rationale | Source |
|---|---|---|
| **Interoperate with Spec Kit, don't compete** | ~108k★ incumbent; its pipeline produces nodes manifold queries; OpenSpec delta syntax becomes manifold edge types | A (both) |
| **Own the read path** (graph + drift + next-leaves) | Market is crowded at authoring; the unowned gap is the continuous compass over months | A (both), C, D, E |
| **Be the MCP intent-broker, not an orchestrator** | 12+ orchestrators exist, all consume MCP, none hold a structured spec graph; manifold serves all parallel agents via one MCP server | D |
| **Compile to AGENTS.md** | File-based memory won the convention war (60k+ repos); export a slim AGENTS.md so non-MCP tools bootstrap the same context | C |
| **Ship ReqIF export** | Lowest-common-denominator interop into the enterprise ALM world; cheap on-ramp, no GUI required | B |
| **Adopt typed link semantics + immutable baselines** | What DOORS/Polarion/Jama got right; what makes impact analysis possible 18 months later | B |
| **Lead with `change_reason` + `rationale` + `drift-report`** | No competitor has a typed why-it-changed field; the `drift-report` noun is uncontested | E |
| **Frame as "ADRs that talk to your agent"** | Honest lineage (Nygard 2011); inoculates against "reinvented wheel" objections; credible with senior/regulated buyers | E (both) |
| **Don't compete with mem0/Zep on conversational facts** | Different benchmarks (LongMemEval/LoCoMo), different audience; optionally integrate for user-side memory | C |
| **Avoid the vibe-vs-SDD culture war** | "Manifold works whichever way you code"; don't pick a side that loses half the market | E |
| **Cite Muonagor & Bensalem (2024) for etymology** | Three-lineage disambiguation signals manifold is read-in, not naive | E |
| **Do NOT build a CLI-only IDE, an autonomous agent, or a model** | The most crowded, best-funded parts of the market; no moat there | A, D |

---

## 9. Integration reference shortlist

Eight tools ranked by adjacency to manifold's thesis — **reference list for future product work**, not an open research phase. (Tessl deferred to watchlist: closed-source, registry pivot.)

| # | Tool | Why it matters |
|---|---|---|
| **1** | **GitHub Spec Kit** | ~108k★ incumbent — map `.specify/` artifacts → graph nodes; OpenSpec `ADDED/MODIFIED/REMOVED` → edge types |
| **2** | **OpenSpec** | Strongest OSS on M3 (`changes/` archive); model for change-edge semantics and `change_reason` capture |
| **3** | **Roady** | Closest OSS adjacent (M2/M4/M5/M7); boundary study vs typed intent graph + rationale ledger |
| **4** | **AWS Kiro** | Strongest commercial spec-first IDE; hooks model, EARS notation, flat 3-doc vs graph |
| **5** | **Augment Intent / Cosmos** | Most direct competitor (living specs + bidirectional sync); no public `next-leaves` API |
| **6** | **BMAD-METHOD** | Closest "what next" via `bmad-help`; foil for queryable compass over project graph |
| **7** | **RealityCheck** | Purest drift validator (SPEC.md+PLAN.md→`DRIFT_DETECTED`); verdict-only vs rationale-history gap |
| **8** | **StrictDoc** | Inspectable OSS spec-graph peer; typed cross-doc links + ReqIF for enterprise on-ramp (Jama = commercial MCP reference on watchlist) |

See [`README.md`](README.md) § "Prompts for deepening understanding" for copy-paste follow-up prompts. Archived template: [`06-pass2-deep-dive-template.md`](06-pass2-deep-dive-template.md).

---

## 10. Watchlist / reposition triggers

| Trigger | Response |
|---|---|
| **GitHub Spec Kit adds a `rationale.md` / `why.md` first-class concept** (plausible given roadmap velocity) | Reposition immediately from "tool" to "layer that works *with* Spec Kit"; watch the spec-kit issue tracker for any RFC mentioning "rationale," "change_reason," or "why." |
| **Kiro ships an MCP "spec server"** exposing its specs to *other* agents (Cursor, Devin, Codex) | The M7 differentiation collapses to UX/indexing depth — publish a Kiro-compatible spec-import adapter and reposition as "open layer underneath Kiro." |
| **Augment open-sources Intent's living-spec API** | Build an Intent-importer; compete on graph richness (KAOS layers) and the `next-leaves` API rather than on the spec-ownership concept. |
| **Roady adds a `change_reason` field** | Direct OSS competitor on manifold's core differentiator — accelerate the M3 rationale-history work and the `drift-report` artifact. |
| **Graphiti adds first-class `Requirement`/`AcceptanceCriterion` entity types + an unsatisfied-requirements query** | The graph-memory crowd has eaten the intent layer — pivot manifold's emphasis to the drift/verdict axes. |
| **Tricentis launches a developer-facing (not QA) intent-drift product** | The framing competition intensifies — lean harder into the MCP/agent-native angle and the `drift-report` noun. |
| **Anthropic's Memory Tool adds a schema/types primitive** | File-based memory wins outright — manifold's edge narrows to drift detection; double down on M4. |
| **MAST-style multi-agent failure rates drop below ~10% via better base models** for two consecutive quarters | The "shared intent" wedge weakens — pivot toward the more boring but defensible spec-version-control niche. |
| **Tessl reopens as an open spec graph** | Re-evaluate shortlist; today closed and registry-focused. |

---

## 11. Sources index

All seven raw result files (provenance — do not delete):

| Session | File |
|---|---|
| A — SDD (Claude) | [`results/session-A-sdd-claude-2026-06-06.md`](results/session-A-sdd-claude-2026-06-06.md) |
| A — SDD (ChatGPT) | [`results/session-A-sdd-chatgpt-2026-06-06.md`](results/session-A-sdd-chatgpt-2026-06-06.md) |
| B — Enterprise ALM (Claude) | [`results/session-B-alm-claude-2026-06-06.md`](results/session-B-alm-claude-2026-06-06.md) |
| C — Agent memory (Claude) | [`results/session-C-agent-memory-claude-2026-06-06.md`](results/session-C-agent-memory-claude-2026-06-06.md) |
| D — Orchestration (Claude) | [`results/session-D-orchestration-claude-2026-06-06.md`](results/session-D-orchestration-claude-2026-06-06.md) |
| E — Drift discourse (Claude) | [`results/session-E-drift-claude-2026-06-06.md`](results/session-E-drift-claude-2026-06-06.md) |
| E — Drift discourse (ChatGPT) | [`results/session-E-drift-chatgpt-2026-06-06.md`](results/session-E-drift-chatgpt-2026-06-06.md) |

Supporting context: [`README.md`](README.md) (study index, further reading, deepening prompts) · [`00-MASTER-HANDOFF.md`](00-MASTER-HANDOFF.md) (M1–M7 axis definitions) · [`results/README.md`](results/README.md) (cross-session calibration) · [`synthesis-pass1.md`](synthesis-pass1.md) (A+E archive).

---

## 12. Study closure

This landscape analysis is **complete**. Sessions A–E merged 2026-06-06. Per-tool deep dives (formerly "Pass 2") are **closed indefinitely** — the synthesis above is the deliverable.

If product work later requires first-hand verification of one tool (e.g. Spec Kit import mapping), use the archived template [`06-pass2-deep-dive-template.md`](06-pass2-deep-dive-template.md) or the prompts in [`README.md`](README.md). Save any ad-hoc output as `results/adhoc-<tool>-YYYY-MM-DD.md` — not a continuation of this study phase.

**Distillation** into product README, skill references, and orchestrator design is intentionally outside `research/` and tracked separately.

---

*Landscape study complete — 2026-06-06. Supersedes `synthesis-pass1.md`.*
