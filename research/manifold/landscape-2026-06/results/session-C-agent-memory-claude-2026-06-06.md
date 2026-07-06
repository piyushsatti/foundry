---
status: frozen
study: manifold-landscape-2026-06
session: C
type: raw-result
provider: claude
date: 2026-06-06
synthesis: ../synthesis.md
---

# Session C — Agent Memory & Context Engineering: Landscape Scout

## TL;DR

- **No surveyed memory tool delivers manifold's "compass" layer in full.** Of 18 systems mapped, every one stores either (a) freeform conversational/code facts (mem0, Zep/Graphiti, Letta, Cognee, LangMem, MCP knowledge-graph servers) or (b) human-readable convention/instruction files (CLAUDE.md, AGENTS.md, .cursorrules, Cline Memory Bank, Factory Memory, Serena memories). Only **GitHub Spec Kit** and the **Git Context Controller (GCC)** arXiv prototype come close to typed, versioned project intent — and neither models a queryable intent graph with drift detection against code.
- **The discourse has converged on "context engineering" (Karpathy/Lütke, June 2025; Anthropic engineering blog, Sept 29 2025) as the dominant frame**, but practitioner pain has shifted from "context window too small" to "session amnesia + drift between what the spec says and what the code does." Anthropic's Sept 2025 memory tool is deliberately file-based — a Markdown-over-vector-RAG "opinionated bet" that validates manifold's premise that *structure beats similarity search* for project intent — but Anthropic's primitive stops at unstructured files.
- **Manifold's distinct surface area is the "WHY" graph + drift detection.** Codebase indexers (Sourcegraph, codebase-memory-mcp, Serena) know WHAT the code is; convention files know HOW the team writes it; mem0/Zep know WHO the user is and WHEN they said what. Nothing on the market answers *"what should we work on next, given the gap between intent and implementation?"* as a first-class structured query.

---

## Key Findings

1. **Two distinct memory lineages have emerged, and they don't talk to each other.** Conversational-memory tools (mem0, Zep, Letta, LangMem, Cognee) optimize for user-personalization benchmarks (LongMemEval, LoCoMo) — they store user preferences and chat episodes, not project intent. Coding-project memory tools (CLAUDE.md, AGENTS.md, Cline Memory Bank, Factory, Serena memories) store conventions and brief decisions in Markdown — they know HOW you code, not WHY each feature exists.
2. **AGENTS.md won the convention-file war.** Released by OpenAI in August 2025 and donated to the Linux Foundation's Agentic AI Foundation in December 2025, AGENTS.md has been "adopted by more than 60,000 open source projects and agent frameworks including Amp, Codex, Cursor, Devin, Factory, Gemini CLI, GitHub Copilot, Jules and VS Code" (Linux Foundation press release, Dec 9 2025). Claude Code keeps CLAUDE.md as a richer 3-layer alternative. But every commentator agrees: convention files break down at scale (>~2K tokens). They have **no M3 history**, **no M4 drift**, **no M5 compass**.
3. **Two arXiv prototypes target manifold's space directly but lack adoption.** Git Context Controller (arXiv:2508.00031, Aug 2025; v2 Oct 2025) treats agent context as a versioned filesystem with COMMIT/BRANCH/MERGE/CONTEXT ops — claims >80% SWE-Bench Verified. DeepCode "CodeMem" (arXiv:2512.07921, Dec 2025) is a stateful code-memory layer for paper→repo synthesis. Both have research-stage code only; neither models intent as a typed graph.
4. **Graph memory exists but is aimed at conversational facts.** Graphiti (Zep's open-source engine, ~27K stars as of June 6 2026, latest release v0.29.1 dated May 21 2026, MCP server in production at "hundreds of thousands of weekly users" per Zep) and the MCP knowledge-graph reference server both model entities+relations, but with *user-facing* entity types (people, preferences) — not requirements/acceptance-criteria/architectural-decision types.
5. **Anthropic explicitly endorsed file-based memory over vector RAG in Sept 2025.** Their context-engineering blog and the Memory Tool both treat Markdown files as the primitive. This is a tailwind for manifold's "structured external memory" thesis — but Anthropic's own primitive has no schema, no drift detection, and no graph layer.
6. **GitHub Spec Kit (Specify) is the closest commercial analogue to manifold.** ~108K stars (June 4 2026), latest stable v0.8.18 dated May 29 2026, MIT-licensed. It scaffolds spec → plan → tasks → implement Markdown artifacts plus a project `.specify/memory/constitution.md` of architectural principles. It stores *structured requirements* and is the only widely-adopted tool that reifies WHY-decisions as durable artifacts. But the artifacts are flat Markdown — there is no queryable graph, no drift detector, no revision diff between versions of intent.

---

## Tool Inventory

**Interpretation of M-axes (please correct if 00-MASTER-HANDOFF.md differs):**
- **M1_truth** = single canonical source-of-truth store for project intent?
- **M2_graph** = intent modeled as a typed graph (requirements ↔ features ↔ acceptance criteria ↔ code)?
- **M3_history** = revisions of intent versioned/diffable over time?
- **M4_drift** = does it detect when code drifts from declared intent?
- **M5_compass** = can it structurally answer "what should we work on next?"
- **M6_verdict** = does it produce verification/acceptance verdicts against intent?
- **M7_agent** = native MCP / API for agents?

| name | url | one_liner | memory_type | canonical_store | retrieval_model | agent_native | compass_queries | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Anthropic Memory Tool | https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool | Client-side file-based `/memories` directory Claude reads/writes across sessions | file-based | markdown-in-git (any client storage) | manual / file read | yes | no | free (beta) | long-lived project | partial | none | partial (via git) | none | none | none | yes (native tool) | Stores FACTS as files; agent decides schema. Knows WHAT it wrote down, not WHY a feature exists. No typed intent graph. | anthropic.com/news/context-management (Sep 29 2025); platform.claude.com/docs |
| Claude Code CLAUDE.md / Claude Projects | https://code.claude.com/docs/en/best-practices | 3-layer Markdown convention file (enterprise/project/user) auto-loaded by Claude Code | file-based | markdown-in-git | manual (file read) | yes | no | included in Claude plan | long-lived project | partial | none | partial (git) | none | none | none | yes | Stores CONVENTIONS. Anthropic's own docs warn: "If your CLAUDE.md is too long, Claude ignores half of it." Practitioners cap at 300–600 tokens. | code.claude.com/docs/en/best-practices; medium.com/@habib23me |
| AGENTS.md (OpenAI → Linux Foundation) | https://agents.md/ | Cross-tool open-standard Markdown file; "adopted by more than 60,000 open source projects" per LF | file-based | markdown-in-git | manual | yes | no | OSS / free | one-shot to long-lived | partial | none | partial (git) | none | none | none | yes (Codex, Cursor, Copilot, Windsurf, Amp, Devin, Aider, Jules, Factory, VS Code, Gemini CLI) | Stores CONVENTIONS by design — deliberately minimal. Knows WHAT to do, not WHY. 32 KiB cap in Codex. | linuxfoundation.org/press (Dec 9 2025); openai.com/index/agentic-ai-foundation; agents.md |
| Cursor Rules (.cursor/rules/*.mdc + legacy .cursorrules) | https://docs.cursor.com/context/rules | Per-glob, per-mode Markdown rule files with YAML frontmatter | file-based | markdown-in-git | structured (glob activation) | yes | no | included in Cursor | long-lived project | partial | none | partial (git) | none | none | none | yes (Cursor only) | Stores CONVENTIONS scoped by glob. Adds activation logic but no intent graph. Legacy .cursorrules deprecated 2025. | startupbricks.in (Jan 2026); cursor.com forum |
| Cline Memory Bank | https://docs.cline.bot/features/memory-bank | Community pattern: 6 Markdown files (projectbrief/productContext/activeContext/systemPatterns/techContext/progress.md) | file-based | markdown-in-git | manual (read all at session start) | yes | partial (progress.md acts as crude compass) | OSS / free | long-lived project | full (within its scope) | none | partial (git + activeContext) | none | partial (progress.md lists "what's left") | none | yes | Closest convention-file analogue to manifold's structure; uses a Mermaid-described hierarchy. Still flat Markdown — no typed graph, no drift between progress.md and the code. | docs.cline.bot; cline.bot/blog/memory-bank; github.com/nickbaumann98/cline_docs |
| mem0 (mem0ai/mem0) | https://github.com/mem0ai/mem0 | Vector-RAG memory layer w/ optional graph; LLM-extracted facts; ADD/UPDATE/DELETE/NOOP | vector-RAG (hybrid w/ graph add-on) | DB (vector store + optional graph) | semantic search | yes (SDK + MCP) | no | freemium ($19/mo+; OSS Apache-2.0) | conversational personalization | none (for project intent) | partial (graph add-on) | none | none | none | none | yes (MCP) | Stores conversational FACTS for user personalization. Does not know project WHY. **~57.4K GitHub stars** (Jun 2026); arxiv 2504.19413. LongMemEval 94.4 (vendor); 49.0% per Atlan third-party run. | github.com/mem0ai/mem0; mem0.ai (2026); atlan.com (2026); arxiv 2504.19413 |
| Zep / Graphiti | https://github.com/getzep/graphiti | Bi-temporal knowledge graph engine; valid_from/valid_to per edge | graph | DB (Neo4j/FalkorDB/Kuzu) | hybrid (graph traversal + vector + BM25) | yes (Graphiti MCP Server 1.0) | partial (temporal queries) | freemium ($125/mo+; Graphiti OSS Apache-2.0) | enterprise / temporal reasoning | partial | full (entity graph) | full (bi-temporal) | none | none | none | yes (native MCP) | Closest production graph-memory system. Entity types tuned to user/customer/team — not requirements/specs/acceptance-criteria. **~27K stars; latest v0.29.1 (May 21 2026); arxiv 2501.13956**. | github.com/getzep/graphiti; blog.getzep.com; help.getzep.com |
| Letta (formerly MemGPT) | https://github.com/letta-ai/letta | OS-inspired agent runtime with core/recall/archival memory tiers; Letta Code coding agent | hybrid (file + DB) | hybrid (Postgres + filesystem) | hybrid (structured + semantic) | yes (full runtime + MCP) | no | OSS Apache-2.0 + cloud | self-hosted stateful agents | partial | none (memory blocks, not typed graph) | partial (block versions) | none | none | none | yes | Stores agent's memory blocks plus filesystem; Letta claims Letta Code is #1 on Terminal-Bench. Memory blocks are unstructured strings. arxiv 2310.08560; ~23K stars; v0.16.8 (May 14 2026). | letta.com/blog; vectorize.io (2026); arxiv 2310.08560 |
| LangMem (langchain-ai/langmem) | https://github.com/langchain-ai/langmem | LangGraph-native memory SDK: semantic/episodic/procedural via BaseStore | hybrid | DB (BaseStore: vector / KV / Postgres) | semantic search | yes (LangGraph only) | no | OSS MIT | LangGraph apps | none | none | none | none | none | none | partial (LangGraph only, no MCP) | Stores conversational FACTS via LangGraph store. ~1.3K stars; last PyPI v0.0.29 (oct 2025); 59.82s p95 latency per Atlan — unusable interactively. | langchain-ai.github.io/langmem; atlan.com (2026) |
| Cognee (topoteretes/cognee) | https://github.com/topoteretes/cognee | Open-source memory engine: ECL (Extract/Cognify/Load) over vector+graph | hybrid (vector + graph) | DB (Neo4j/Memgraph + vector) | hybrid | yes (MCP + SDK) | no | OSS Apache-2.0 + Cognee Cloud | knowledge engine, on-prem | partial | full (ontology grounding) | partial | none | none | none | yes (MCP) | Stores cited FACTS + ontology. Closer to a typed graph than mem0/Zep, but ontologies are user-defined and aimed at documents, not engineering intent. ~16.6K stars; v1.0.1 (Apr 18 2026). | github.com/topoteretes/cognee; cognee.ai; memgraph.com |
| MCP Memory Server (modelcontextprotocol/servers/src/memory) | https://github.com/modelcontextprotocol/servers/tree/main/src/memory | Reference knowledge-graph MCP server: entities + relations + observations in JSONL | graph | JSONL-in-git | structured (search_nodes / open_nodes) | yes | no | OSS MIT | local persistent memory | partial | full (entities/relations) | partial (file-level) | none | none | none | yes (canonical MCP) | Reference impl every fork builds on (shaneholloman/mcp-knowledge-graph, n-r-w/knowledgegraph-mcp, MemoryMesh, memory-graph). Entity types user-defined — no project-intent schema. Parent monorepo ~76K stars. | github.com/modelcontextprotocol/servers; lobehub.com |
| Git Context Controller (GCC) — arXiv prototype | https://arxiv.org/abs/2508.00031 | Versioned filesystem for agent context: COMMIT / BRANCH / MERGE / CONTEXT ops | file-based (versioned) | markdown-in-git (`.GCC/` dir) | hierarchical retrieval + structured query | partial (prototype) | partial (branches encode alternate plans) | research / OSS prototype | long-horizon agents | full | partial | full (Git-style) | partial | partial | none | partial (implementation at github.com/faugustdev/git-context-controller) | Closest conceptual neighbor to manifold's revisions axis. Treats reasoning history as versioned tree; SWE-Bench Verified >80% claimed. But intent is still unstructured Markdown — no typed requirements graph. | arxiv.org/abs/2508.00031 (Aug 1 2025, v2 Oct 2025) |
| DeepCode "CodeMem" — arXiv prototype | https://arxiv.org/abs/2512.07921 | Stateful code memory for paper→repo synthesis (blueprint distillation + cross-file symbol tables) | hybrid (structured indexing + RAG) | DB (in-agent) | structured + RAG | partial (research) | no | research | scientific code repro | partial | partial (symbol tables + dep graph) | none | none | none | partial (PaperBench eval) | no | Stateful project memory for code synthesis, scoped to a single doc-to-repo task; not exposed as a memory service. arxiv 2512.07921 (Dec 2025); GitHub repo claimed at 15.7K via HuggingFace. | arxiv.org/abs/2512.07921; arxiv.org/html/2512.07921v1 |
| Factory.ai Droid Memory | https://docs.factory.ai/guides/power-user/memory-management | Two-tier (Personal + Org) auto-captured Markdown memories + AGENTS.md orchestration; repo overviews injected at session start | file-based (managed) | hybrid (markdown + indexed code overview) | manual + structured | yes | no | enterprise | enterprise teams | partial | none | partial | none | none | none | yes (proprietary) | Stores FACTS + CONVENTIONS auto-extracted from chat ("Always use snake_case for API endpoints"). Knows team preferences, not project intent. | docs.factory.ai; factory.ai/news/context-window-problem; sidbharath.com (2026) |
| Cognition Devin "Knowledge + Wiki" | https://devin.ai | Sandboxed agent with vector codebase snapshots, Devin Wiki auto-generated docs, learning across sessions | hybrid (vector + wiki) | DB + generated Markdown wiki | semantic + structured | yes (proprietary) | no | $20–enterprise | autonomous task execution | partial | partial (wiki structure) | partial | none | none | none | proprietary | Independent tests (Answer.AI) show ~15% success rate on real tasks. SitePoint (2025): "as of mid-2025, it does not maintain long-term memory across sessions...Think of it as a capable but amnesiac contractor." Wiki is generated docs, not declared intent. | analyticsvidhya.com (Apr 2025); datacamp.com (2025); sitepoint.com (2025) |
| OpenAI ChatGPT / Codex project memory | https://help.openai.com/en/articles/10169521 | "Saved memories" + "reference past chats" + project-only memory containers; AGENTS.md hierarchy in Codex CLI | hybrid | DB (proprietary) | semantic | yes (Codex reads AGENTS.md) | no | included in ChatGPT plans | personal / project containers | partial | none | partial | none | none | none | partial (no MCP server for the memory layer) | "Saved memories" are user-personal facts; project memory is opaque ("there's no memory list to browse like with saved memories" — Avi Hakhamanesh, 2026). Not engineered for project intent. | openai.com/index/memory-and-new-controls-for-chatgpt; help.openai.com; unite.ai (2026) |
| GitHub Spec Kit (Specify) | https://github.com/github/spec-kit | Spec-Driven Development CLI: scaffolds spec → plan → tasks → implement + `.specify/memory/constitution.md` | file-based (structured) | markdown-in-git | manual + slash-command driven | yes (via /speckit.* commands in 30+ agents) | partial (tasks.md acts as compass) | OSS MIT | spec-first projects | full (within scope) | none (flat Markdown) | full (git + tasks evolution) | none | partial | partial (tasks pass/fail) | yes (MCP-adjacent — `--approve-mcps` in v0.9.4) | **Closest commercial analogue to manifold's intent layer.** Stores STRUCTURED REQUIREMENTS as durable artifacts ("specifications as the source of truth that generates implementation"). But artifacts are flat Markdown — no typed graph, no drift detection between spec and code. **~108K stars; latest stable v0.8.18 (May 29 2026)**. | github.com/github/spec-kit; spec-driven.md |
| Serena (oraios/serena) | https://github.com/oraios/serena | MCP toolkit: LSP-based semantic code retrieval + simple Markdown memories | file-based + structured code index | markdown + LSP index | structured (symbol-level) + manual memory read | yes (MCP) | no | OSS MIT | symbol-aware coding | partial | partial (symbol graph from LSP) | partial | none | none | none | yes (MCP) | **ADJACENT** — codebase indexer that knows WHAT the code is at symbol level. Memories are flat Markdown; project README explicitly says "we received positive feedback from many users who tend to combine Serena's memory management system with their agent's internal system (e.g., AGENTS.md files)." M2_graph = n/a for *intent*; it's a code graph. ~25K stars; v1.5.3 (May 26 2026). | github.com/oraios/serena; oraios.github.io/serena |
| codebase-memory-mcp (DeusData) | https://github.com/DeusData/codebase-memory-mcp | High-performance LSP+tree-sitter codebase knowledge-graph MCP server (158 languages) | graph (code graph) | DB (local SQLite, persisted) | structured query | yes (MCP) | no | OSS | local code intelligence | none (for intent) | full (for *code*) | partial | none | none | none | yes | **ADJACENT** — knows WHAT (functions, call chains, routes) not WHY. Claims "Linux kernel (28M LOC) in 3 minutes" indexing. ~2.9–3K stars; v0.7.0 (May 30 2026). | github.com/DeusData/codebase-memory-mcp |

---

## Community Pulse: Context Engineering Discourse (2024–2026)

### Pain themes

**The "goldfish with a PhD" / session-amnesia theme**
- **"Like supervising a junior developer with short-term memory loss"** — Reddit r/ClaudeAI, cited by CleanAim (cleanaim.com/silent-wiring/problems/context-loss, 2026).
- **"Auto-compacting just obliterates important context"** — Twitter/X, cited by CleanAim, 2026.
- **"After 2-5 prompts it starts ignoring instructions"** — GitHub Issue #7777 (Claude Code), cited by CleanAim, 2026.
- **"Most developers build AI agents that forget everything the moment a session ends... You start from zero. Again."** — Rohit Kushwaha, Medium, May 2026.
- **"Your AI agent in session 50 should be better than your agent in session 1. But most agents start cold..."** — prociq, DEV Community, 2026.
- **"As of mid-2025, [Devin] does not maintain long-term memory across sessions, and its ability to reason about a codebase is bounded by what it can load into its context window during a given session. Think of it as a capable but amnesiac contractor who needs fresh onboarding every time."** — SitePoint, "Devin Aftermath: AI Engineers in Production," 2025.

**CLAUDE.md scaling limits**
- **"If your CLAUDE.md is too long, Claude ignores half of it because important rules get lost in the noise. Fix: Ruthlessly prune."** — Anthropic, "Best practices for Claude Code" (code.claude.com/docs/en/best-practices, 2026).
- **"A well-structured CLAUDE.md for a real project is usually 300 to 600 tokens. If yours is over 2,000 tokens, you are probably storing task state or documentation that does not belong there."** — Habib Mohammed, Medium, 2026.
- **"Users have observed a phenomenon described as 'fading memory.' This doesn't mean Claude is truly forgetting; rather, as the CLAUDE.md files grow larger and more monolithic, the model['s recall degrades]."** — Skywork.ai, 2025.
- **"Codex enforces a 32 KiB default size limit on AGENTS.md. Content beyond that limit is silently truncated."** — Morph, "AGENTS.md & SKILL.md: The Complete Guide (2026)."

**Context window vs external memory debate**
- **"+1 for 'context engineering' over 'prompt engineering'. People associate prompts with short task descriptions you'd give an LLM in your day-to-day use. When in every industrial-strength LLM app, context engineering is the delicate art and science of filling the context window..."** — Andrej Karpathy, X, June 25, 2025 (x.com/karpathy/status/1937902205765607626; 14K likes, 2.6K reposts, 530 replies).
- **"I really like the term 'context engineering' over prompt engineering. It describes the core skill better: the art of providing all the context for the task to be plausibly solvable by the LLM."** — Tobi Lütke, X, **June 18, 2025** (x.com/tobi/status/1935533422589399127) — the antecedent tweet, seven days before Karpathy's amplification.
- **"Studies on needle-in-a-haystack style benchmarking have uncovered the concept of context rot: as the number of tokens in the context window increases, the model's ability to accurately recall information from that context decreases."** — Anthropic Claude Cookbook, 2025.
- **"Treating context as a precious, finite resource will remain central to building reliable, effective agents."** — Anthropic Engineering, "Effective context engineering for AI agents," Sept 29, 2025.
- **"External memory: Agents will need durable, write-once-read-many memory to retain long-term project state, previous decisions, and user preferences across sessions."** — Factory.ai, "The Context Window Problem," 2025.

**Failed approaches**
- **"I've become disillusioned with automated context management tools like this, as it's nearly impossible to control. After a while, I always have to manually clean up the mess or correct inappropriate LLM notes."** — n-r-w, README of knowledgegraph-mcp, GitHub, 2026.
- **"After experimenting with AI tools like memory-bank, Spec Kit, and Boomerang Tasks, I found that simple .md files for project context and planning often work better."** — shinomontaz, DEV Community, 2026.
- **"Vector similarity has no concept of time. [...] the user said 'I prefer Python' in session 3. In session 47, they said 'Actually, I switched to TypeScript.' Both are embedded. Both exist in the vector store. A similarity search for 'preferred language' returns whichever is closer to the query embedding."** — db0.ai, "Why your AI agent forgets everything between sessions," 2026.
- **"LangMem p95 latency is 59.82 seconds per third-party benchmark. Use Mem0 or Zep for interactive agents."** — Atlan, 2026.
- **LOCOMO benchmark dispute (Zep vs mem0):** Zep originally claimed 84%, Mem0 corrected this to 58.44%, Zep counter-claimed 75.14%. Both vendors contest the other's methodology. Atlan, 2026.

### Trending phrases

- **"Context engineering"** — Karpathy/Lütke seed tweets, June 18 + June 25 2025; now Anthropic's house term as of Sept 29 2025.
- **"Just-in-time context retrieval"** — Anthropic Engineering, Sept 2025.
- **"Context rot"** — Chroma technical report cited by Anthropic Cookbook, 2025.
- **"Memory as documentation" vs "memory as database"** — DEV Community, imaginex, 2026.
- **"Goldfish with a PhD" / "amnesiac contractor"** — SitePoint on Devin, 2025.
- **"Spec-driven development" (SDD)** — GitHub Spec Kit; spec-driven.md.
- **"Memory bank"** — Cline community pattern, 2025.

### Notable threads

| title | url | platform | date | summary |
|---|---|---|---|---|
| "Effective context engineering for AI agents" | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | Anthropic Engineering Blog | Sept 29, 2025 | Canonical Anthropic statement: context is a finite resource; agents should use "just-in-time" retrieval and structured note-taking outside the context window. Introduces the Memory Tool. |
| "+1 for 'context engineering' over 'prompt engineering'" | https://x.com/karpathy/status/1937902205765607626 | X (Karpathy) | June 25, 2025 | 14K likes; widely cited as the rebrand moment. Built on Lütke's June 18 tweet. |
| "Memory Bank: How to Make Cline an AI Agent That Never Forgets" | https://cline.bot/blog/memory-bank-how-to-make-cline-an-ai-agent-that-never-forgets | Cline Blog | 2025 | Defines the 6-file Memory Bank pattern that became a community standard; uses Mermaid diagrams to define file hierarchy. |
| "Git Context Controller: Manage the Context of LLM-based Agents like Git" | https://arxiv.org/abs/2508.00031 | arXiv | Aug 1, 2025 (v2 Oct 2025) | Treats agent memory as a versioned filesystem. Claims >80% SWE-Bench Verified. Closest research analog to manifold's revisions axis. |
| "An update on recent Claude Code quality reports" | https://www.anthropic.com/engineering/april-23-postmortem | Anthropic Engineering Blog | April 2026 | Anthropic acknowledges that a single CLAUDE.md-style line about output length caused outsized intelligence regressions — direct evidence that flat instruction files are brittle at the production frontier. |
| "Why your AI agent forgets everything between sessions" | https://db0.ai/blog/why-agents-forget | db0.ai blog | 2026 | Walks through every memory architecture (DB → vector → graph → file) and why each fails on temporal/update questions. References LOCOMO benchmark and CoALA paper. |
| Linux Foundation Press Release on AGENTS.md | https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation | Linux Foundation | Dec 9, 2025 | Confirms AGENTS.md was released by OpenAI in August 2025, donated to LF in December 2025, "adopted by more than 60,000 open source projects." |

---

## 3 Implications for manifold

### 1. Manifold's "compass" layer is genuinely uncovered — the entire market codifies WHAT or HOW, not WHY-as-a-graph.

Every tool surveyed reduces to one of three things: a vector store of conversational facts (mem0/Zep/Letta/LangMem/Cognee/MCP-memory), a Markdown convention file (CLAUDE.md/AGENTS.md/.cursorrules/Cline Memory Bank/Factory/Serena memories), or a code index (Serena LSP, codebase-memory-mcp). The closest neighbors — **Spec Kit** and **Git Context Controller** — store structured intent as durable artifacts but stop at flat Markdown. Neither models intent as a *typed graph* with edges from requirements → features → acceptance criteria → code, and neither computes drift between the declared intent and the current repo state. **A query like "given the constitution, what's the highest-leverage next feature that's still un-implemented and un-tested?" has no first-class answer in any tool surveyed.** That's manifold's white space.

### 2. The market is converging on file-based memory as the primitive — manifold should be a structured *layer above* Markdown, not a replacement for it.

Anthropic's Sept 2025 "opinionated bet" was Markdown over vector RAG. AGENTS.md is winning the convention war (60,000+ repos per Linux Foundation, Dec 9 2025). Cline Memory Bank, Spec Kit, Factory, Serena all converged independently on Markdown-in-git as the canonical store. DEV Community has a popular post titled "AI Agent Memory Management - When Markdown Files Are All You Need?" with the answer "for most cases, yes." **Manifold should not fight this convergence — it should sit on top.** A manifold project should compile down to / cross-reference AGENTS.md so non-manifold tools can still bootstrap, while the typed graph + revisions + drift live in a separate `.manifold/` directory (similar to how Spec Kit uses `.specify/memory/`). This positions manifold as the "structured layer" that captures what flat Markdown loses, without forcing users to abandon the ecosystem.

### 3. Drift detection is the single feature no surveyed tool has — and it's where Anthropic's own postmortem language points.

Of the 18 entries in the inventory, **zero** ship drift detection between declared intent and current code. Graphiti tracks how facts change over time but not whether the codebase still satisfies them. Spec Kit produces a constitution.md that the agent re-reads, but doesn't flag when the implementation has diverged from the spec. Anthropic's April 2026 Claude Code postmortem is, in effect, a confession that even Anthropic cannot keep their own system prompt aligned with the model's behavior across releases — the gap between "what the spec says" and "what the code does" is precisely the manifold compass. Practitioners are already articulating the need: factory.ai/news/context-window-problem explicitly lists "durable, write-once-read-many memory to retain long-term project state, previous decisions" as the next missing layer. **Drift (M4) + Verdict (M6) + Compass (M5) is the trifecta that no one ships and that the discourse is asking for.** This is the most defensible position for manifold to stake out.

---

## Recommendations

1. **Position manifold as the typed intent + drift layer above AGENTS.md, not as a replacement.** Ship an exporter that compiles a manifold project to AGENTS.md + CLAUDE.md so manifold projects work in every agent on day one. Spec Kit's `.specify/memory/` pattern is precedent.
2. **Don't compete with mem0/Zep/Graphiti on conversational facts.** Their benchmarks (LongMemEval, LoCoMo) are not your benchmarks. If anything, integrate — let manifold's typed-intent nodes reference Zep entities for user-side facts.
3. **Stake the M4 (drift) + M5 (compass) + M6 (verdict) ground hard.** No surveyed tool — including GCC and Spec Kit — answers "what should we work on next given the intent-code gap?" as a structured query. This is the strongest moat.
4. **Ship a public benchmark that ISN'T LongMemEval.** Something like SpecDrift-Bench: given a project intent graph + a code snapshot, can the tool correctly identify which requirements are unsatisfied? Forces the discourse onto manifold's axes.
5. **Track Git Context Controller and DeepCode CodeMem closely.** Both are arXiv-stage but represent the closest research lineage to manifold's revisions axis. GCC's COMMIT/BRANCH/MERGE/CONTEXT vocabulary may be worth co-opting.

**Benchmarks that would change the recommendation:**
- If Spec Kit ships a typed graph + drift detector in the next 6 months → the "MIT-licensed, GitHub-distributed, 108K stars" channel becomes a serious competitor; manifold should pivot to deep integration rather than independent product.
- If Graphiti adds first-class "Requirement" and "AcceptanceCriterion" entity types and an MCP query for unsatisfied requirements → the graph-memory crowd has eaten the intent layer; manifold should pivot to focus on the drift/verdict axes only.
- If Anthropic's Memory Tool adds a schema/types primitive → file-based wins; manifold's edge collapses to drift detection alone.

---

## Caveats

- **GitHub star counts and release versions are point-in-time (June 6 2026)** and were corrected in a final enrichment pass: mem0 ~57.4K (not 47.6K), Graphiti ~27K with latest release v0.29.1 May 21 2026 (not v0.29.0 Apr 27), Spec Kit ~108K with latest stable v0.8.18 May 29 2026 (not v0.9.5). Treat all star counts as ±10%.
- **The M1–M7 axes are interpreted from column names alone.** A companion document (00-MASTER-HANDOFF.md) was referenced but not provided. The interpretation is explicit at the top of the inventory; please correct if the canonical definitions differ.
- **Vendor-published benchmark numbers (LongMemEval, LoCoMo) are contested.** Mem0 reports 94.4 on LongMemEval; Zep reports 71.2; an Atlan-cited third-party run showed mem0 at 49.0% and Zep at 63.8%. Both vendors dispute each other's methodology. None of these benchmarks measure coding-project intent — they measure conversational fact recall.
- **The Anthropic 2026 Agentic Coding Trends Report quote on "intent as infrastructure" was found in a secondary practitioner blog summary** (pathmode.io/blog/orchestration-era-needs-intent); the primary report URL was not directly verified in this session.
- **The LangMem p95 latency figure (59.82s) is from a single third-party benchmark cited by Atlan, 2026** — not independently replicated.
- **Two tools in the inventory (Devin's memory, OpenAI Codex/ChatGPT project memory) are proprietary closed systems** where the underlying architecture is partially speculative from public documentation.
- **Coverage gaps:** Sourcegraph Cody's context engine, Continue.dev's memory model, OpenMemory/mem0's MCP variant, Windsurf Cascade's memory layer, Hindsight, MemoryGraph, MemLayer, OMEGA, and Mastra Observational Memory all surfaced incidentally but were not deeply mapped. A second pass could add 4–6 more rows.

---

## Session Metadata

```
session: C
category: Agent memory / context
researcher_model: Claude (Anthropic) — research scout
date: 2026-06-06
sources_searched:
  - "Anthropic memory tool Claude context engineering 2025"
  - "mem0 vs Zep agent memory comparison 2025"
  - "Cline Memory Bank pattern"
  - "Letta MemGPT agent memory architecture 2025"
  - "Git Context Controller arxiv agent"
  - "AGENTS.md standard Cursor Codex specification"
  - "LangMem LangGraph store memory long-term"
  - "MCP memory server GitHub knowledge graph"
  - "DeepCode code memory arxiv repository"
  - "Graphiti Zep temporal knowledge graph MCP coding agent"
  - "context engineering Karpathy Shopify Tobi 2025"
  - "Cursor rules .cursorrules limitations scaling"
  - "Factory.ai Devin project context memory documentation"
  - "agent forgets session amnesia coding context reddit hacker news"
  - "CLAUDE.md scaling limits too long problems"
  - "Cognee memory agents knowledge graph open source"
  - "OpenAI ChatGPT memory project instructions persistent"
  - "Serena MCP coding agent semantic memory"
  - Subagent run for live GitHub star counts, Spec Kit details, and Anthropic quote on architectural intent
  - Enrichment pass for AGENTS.md provenance, mem0/Graphiti/Spec Kit star+release figures, Lütke tweet date
  - sites referenced: anthropic.com, claude.com, getzep.com, mem0.ai, letta.com, github.com (multiple repos), arxiv.org, langchain-ai.github.io, docs.factory.ai, devin.ai, cognee.ai, agents.md, cleanaim.com, db0.ai, oraios.github.io, linuxfoundation.org
gaps_in_coverage:
  - Sourcegraph Cody / Continue.dev / Windsurf Cascade memory layers not deeply surveyed
  - Anthropic 2026 Agentic Coding Trends Report primary URL not directly verified
  - Slack / Discord community pulse not searched directly — drew from web-indexed posts only
  - mem0's OpenMemory MCP variant not separately mapped
  - Emerging tools (Hindsight, MemoryGraph, MemLayer, OMEGA, Mastra Observational Memory) surfaced incidentally but not given inventory rows
  - No primary-source examples of manifold itself were located (referenced only as the task's reference tool)
```