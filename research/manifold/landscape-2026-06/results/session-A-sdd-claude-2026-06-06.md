---
status: frozen
study: manifold-landscape-2026-06
session: A
type: raw-result
provider: claude
date: 2026-06-06
synthesis: ../synthesis.md
---

# Session A — Spec-Driven Development & Agent Workflow Tools: Landscape Scout

## TL;DR
- **Spec-driven development (SDD) is now a crowded category, but almost none of the tools sustain *queryable intent over months*** — most operate at the "spec at start of feature" layer (Spec Kit, OpenSpec, Kiro, BMAD, Superpowers, PRPs) rather than "long-lived project compass" (only Tessl and Augment Cosmos approach it, and both at significant cost or with vendor lock-in).
- **The closest adjacents to manifold's "next-leaves" / drift-detection thesis are Augment Cosmos (living specs + Context Engine), Tessl (specs as long-term memory + tests as guardrails), and OpenSpec (delta specs + `validate --strict`)** — but none ship a layered spec *graph* with a query API; they treat specs as folders of markdown.
- **Steal from the leaders, then fill the gap manifold owns:** steal Spec Kit's constitution → specify → plan → tasks → implement pipeline, steal OpenSpec's delta-spec syntax, steal Superpowers' workflow-as-skill enforcement, steal Tessl's MCP plumbing — but the *graph + drift + next-leaves API* is genuinely uncovered space.

---

## M-axis interpretation (please correct if wrong)
The columns M1–M7 are interpreted from their names, since the companion "master handoff axes" document was not provided:
- **M1_truth** = canonical source of truth for intent (is the spec, not the code, authoritative?)
- **M2_graph** = layered/linked spec graph structure (does it model spec→sub-spec→task→code as a graph, not just a folder?)
- **M3_history** = history/versioning of intent over time (git is necessary but not sufficient — does the tool *reason* over spec history?)
- **M4_drift** = drift detection between spec and code (does the tool detect divergence automatically?)
- **M5_compass** = ability to answer "what next" / navigation queries ("next-leaves" — given current state, what is the smallest open spec leaf?)
- **M6_verdict** = verification/acceptance verdicts against spec (test/lint/compliance gating tied to the spec)
- **M7_agent** = agent-native integration (MCP server, CLI for agents, slash commands, skills)

Ratings: **full / partial / none / n/a**. Verdicts are this scout's best read, not vendor self-claims.

---

## Tool Inventory

| name | url | one_liner | canonical_store | drift_handling | agent_native | compass_queries | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **GitHub Spec Kit (`specify` CLI)** | https://github.com/github/spec-kit | Constitution → specify → clarify → plan → tasks → analyze → implement, agent-agnostic | markdown-in-git | manual (the `/speckit.analyze` command does cross-artifact consistency checks before `/implement`, but no continuous drift watcher) | yes (29+ agent integrations; slash commands or skills mode) | partial (tasks.md is ordered but not a queryable graph) | OSS (MIT) | one-shot feature → medium project | full | partial (constitution + spec + plan + tasks + checklist artifacts are linked by templates) | partial (git only; no semantic history) | partial (`/speckit.analyze` runs once, pre-implement) | partial (you can see the next unchecked task, but no API) | partial (checklists + analyze gate) | full (slash commands, skills mode, MCP support via agents) | No persistent compass query API; spec is per-feature branch (`001-feature-name`), not a project-level graph. Drift detection is one-shot, not continuous. | github.com/github/spec-kit (~108k stars, v0.9.1 Jun 2, 2026); github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/ |
| **BMAD-METHOD** | https://github.com/bmad-code-org/BMAD-METHOD | Multi-agent "agile team" (PM, Architect, SM, Dev, QA) producing PRDs, architecture docs, and sharded story files | markdown-in-git (`docs/specs/`) | manual (sharded story files reduce drift via tight scope; no automated detector) | yes (Claude Code native via skills/commands/hooks; works with Cursor, VS Code, Codex) | partial (Scrum Master agent picks next story from backlog — closest thing to "next-leaves" in this list) | OSS (free, no gated content) | long-lived project (greenfield, agile) | full | partial (PRD → epic → story sharding is hierarchical) | partial (git + named story files) | none (no spec↔code reconciliation) | partial (SM agent recommends next story to implement) | partial (QA agent role) | full (19+ agents, 50+ workflows; hooks into Claude Code skills/commands) | Spec graph is implicit in story file naming, not queryable. No drift detector. v6 framework is opinionated (heavy ceremony for small teams). | github.com/bmad-code-org/BMAD-METHOD (~48.6k stars, v6.8.0 May 25, 2026); dev.to/bspann/bmad-method-claude-code-how-i-actually-ship-projects-with-spec-driven-ai-development-1eei |
| **OpenSpec (Fission AI)** | https://github.com/Fission-AI/OpenSpec | Lightweight SDD with explicit **delta specs** (ADDED / MODIFIED / REMOVED) and three-phase state machine (proposal → apply → archive) | markdown-in-git (`openspec/specs/` + `openspec/changes/`) | partial (`openspec validate --strict` enforces GIVEN/WHEN/THEN coverage on each delta; no code↔spec drift check) | yes (20+ assistants via auto-generated slash commands) | partial (the change folder is the next-leaf, but no graph query) | OSS (MIT) | brownfield, incremental change | full | partial (delta specs link to base specs by capability) | partial (archive folder is history; no semantic diff query) | partial (validate catches missing scenarios, not implementation drift) | partial (next change in `openspec/changes/` is the obvious next leaf) | partial (`validate --strict`) | full (slash commands, skills, MCP-friendly) | Specs are per-capability folders, not a unified linked graph. Drift detection is structural (proposal completeness), not semantic. | github.com/Fission-AI/OpenSpec (~52.6k stars, v1.4.1 Jun 3, 2026); openspec.dev |
| **Amazon Kiro** | https://kiro.dev | VS Code-fork IDE that mandates a 3-doc spec (requirements.md / design.md / tasks.md) in EARS notation before code, plus event-driven **hooks** | hybrid (markdown in `.kiro/specs/`, IDE-managed) | partial (steering files + hooks can fire on save; spec is the unit of work) | yes (IDE and CLI; built on Bedrock, Claude Sonnet 4.5/Opus 4.7) | partial (tasks.md is an ordered checklist with "Start task" links) | freemium — revised tier (per InfoWorld 2026): free 50 vibe/0 spec requests, Pro $20/mo (225 vibe + 125 spec), Pro+ $40, Power $200; replaces Q Developer (EOL Apr 30, 2027) | one-shot feature → enterprise (AWS-native) | full | partial (spec / design / tasks / steering / hooks) | partial (git) | partial (hooks can detect file changes vs spec, but no semantic drift) | partial (sequential task execution) | partial (acceptance criteria embedded in requirements.md) | full (IDE + CLI + native MCP) | Lock-in to Bedrock + AWS auth; specs are per-feature, not a long-lived project graph. No cross-spec compass query. | aws.amazon.com/blogs/devops/amazon-q-developer-end-of-support-announcement/; kiro.dev; thenewstack.io/aws-kiro-testing-an-ai-ide-with-a-spec-driven-approach/ |
| **Amazon Q Developer CLI** | https://github.com/aws/amazon-q-developer-cli | Terminal agent with context hooks, slash commands, `q chat --resume` for persistent threads | unknown (chat history per working dir) | none | yes (CLI agent, MCP via `q mcp`) | no | freemium (50 free, $19/mo Pro) — **deprecated**: Q Developer IDE plugins EOL Apr 30, 2027; CLI rebranded as Kiro CLI | one-shot feature | none (intent lives in chat, not a spec artifact) | none | partial (resume restores conversation) | none | none | none | full (MCP, custom agents JSON schema with `mcpServers`/`allowedTools`/`resources`) | Not SDD at all by itself — but the agent JSON config (kiroqa example) shows how an agent can be pointed at a `requirements.md` as `resources`. Pure prompt/agent layer; spec is exogenous. | github.com/aws/amazon-q-developer-cli; aws.amazon.com/blogs/devops/amazon-q-developer-end-of-support-announcement/ |
| **Tessl Framework + Spec Registry** | https://tessl.io | Commercial spec-driven platform: specs as long-term memory in repo, vibe-spec or hand-authored, MCP-attached to any agent | hybrid (specs in repo + Tessl-hosted Spec Registry of 10,000+ external library specs) | partial → full claim (tests generated from spec act as guardrails; the registry prevents API hallucination drift) | yes (MCP server tools confirmed: search/install/auth against the Tessl registry) | partial (plans are produced before execution and updated as audit trail) | freemium (Spec Registry free; Free + Pro/Enterprise plan tiers; pivoted to "agent skills package manager" + governance/registry per tessl.io homepage Jun 2026) | long-lived project / enterprise | full | partial (spec has description + capabilities-with-tests + API sections; not a multi-level graph but multi-component) | partial (specs live in repo with code as long-term memory) | partial (tests bound to spec assertions catch behavioral drift) | partial (audit-trail plans, but no explicit "next-leaves" API) | full (spec-bound tests = regression gate) | full (MCP server, agent-agnostic) | Closest in *spirit* to manifold, but: not a graph; "compass" is the plan audit trail, not a structural query; commercial closed-source. | tessl.io/blog/announcing-tessls-products-to-unlock-the-power-of-agents/ (Sep 29, 2025); docs.tessl.io/reference/mcp-tools; tessl.io/enterprise/ |
| **Claude Code "Superpowers" plugin** | https://github.com/obra/superpowers | Skill library enforcing brainstorming → write-plan → execute-plan with hard gates and TDD red-green-refactor | markdown-in-git (`docs/superpowers/specs/` + `docs/superpowers/plans/`) | manual (review gates between tasks; no continuous drift check) | yes (Claude Code plugin via marketplace, also Codex/OpenCode with manual setup) | partial (plan checkbox state = recovery mechanism; no query API) | OSS (MIT) | one-shot feature → medium project | full (within a feature) | partial (design.md + plan.md + per-task checkboxes) | partial (git; plan-as-state log) | partial (spec-compliance review gate after each task) | partial (next unchecked plan item = next leaf) | partial (TDD enforcement + code review subagent) | full (skills, plan-mode intercept, subagent-driven dev) | Per-feature, per-branch discipline. Plan is the closest thing to a compass but it dies when the feature ships. No project-level graph. | github.com/obra/superpowers (~218.5k stars per ClaudePluginHub, v5.1.0 May 4, 2026; created by Jesse Vincent Oct 2025); blog.fsck.com/2026/03/09/superpowers-5/; builder.io/blog/claude-code-superpowers-plugin |
| **Agent OS (buildermethods)** | https://github.com/buildermethods/agent-os | Inject codebase standards + product mission into any agent; Plan-mode-aware spec shaping | markdown-in-git (`.agent-os/`) | manual | yes (works alongside Claude Code, Cursor, Antigravity, etc.) | no | OSS (MIT) | long-lived project (standards layer) | partial (standards are authoritative, spec less so) | partial (standards + product mission + per-spec folders) | partial (git) | none | none (no "next" notion) | partial (verification prompts in implementation phase) | full (`/inject-standards` bakes rules into subagents/skills) | Treats specs more like rules than a queryable intent graph. Closer to AGENTS.md++ than to manifold. | github.com/buildermethods/agent-os (~4.2k stars, Agent OS 3.0 Jan 20, 2026) |
| **PRP (Product Requirements Prompts) — Wirasm/PRPs-agentic-eng + coleam00/context-engineering-intro** | https://github.com/Wirasm/PRPs-agentic-eng; https://github.com/coleam00/context-engineering-intro | Template library: `/prp-prd` → `/prp-plan` → `/prp-implement`, with PRPs as "comprehensive implementation blueprints" for AI | markdown-in-git (`PRPs/`, `.claude/PRPs/`) | manual (validation commands per plan; Ralph loop with `--max-iterations`) | yes (Claude Code, Cursor, Windsurf, Gemini CLI compatible) | partial (PRD has Implementation Phases table; `/prp-plan` auto-selects next pending phase) | OSS | one-shot feature | full (within PRP scope) | partial (PRD → phase plans → implementations is hierarchical) | partial (archived plans) | none | partial (auto-selects next pending phase from PRD table — closest "next-leaves" behavior in OSS) | partial (validation commands) | full (slash commands, skills) | Templates only — no runtime drift watcher, no project-wide compass query, dies when the PRP archives. | github.com/Wirasm/PRPs-agentic-eng (~2.2k stars); github.com/coleam00/context-engineering-intro (~13.3k stars) |
| **Aider CONVENTIONS.md** | https://aider.chat/docs/usage/conventions.html | Single markdown file of project rules/preferences fed to aider via `--read CONVENTIONS.md` | markdown-in-git | none | yes (model-agnostic) | no | OSS | long-lived project (rules layer only) | none (rules, not specs) | none | partial (git) | none | none | none | full (model-agnostic CLI) | This is `AGENTS.md`-class context, **not** SDD. Listed for completeness because users conflate the two. Definitely not a spec graph. | aider.chat/docs/usage/conventions.html; github.com/Aider-AI/conventions |
| **Cursor Rules + Plan Mode** | https://cursor.com/docs | `.cursor/rules/*.mdc` (always/glob/intelligent/manual) + ephemeral Plan Mode | markdown-in-git (`.cursor/rules/`) | none (Plan Mode plans are markdown, not versioned specs; rules are advisory, not gating) | yes (Cursor-native; v2.1 removed custom modes/memory features) | no | freemium ($20–$200/mo personal; $40/user Teams) | one-shot feature | none (rules ≠ intent of truth) | partial (multiple .mdc files; no inter-file link semantics) | partial (git) | none (rules as suggestions; no enforcement) | none | none | full (Cursor agent) | Listed explicitly because the task said NOT to confuse rules with spec graphs — Cursor is the canonical example of a rules layer being mis-sold as SDD. | cursor.com/docs; augmentcode.com/guides/cursor-spec-driven-development |
| **Augment Cosmos (Intent, Context Engine, Experts)** | https://www.augmentcode.com | Cloud agent platform with **living specs**, tenant memory across sessions, Context Engine over 400k+ files, "Experts" registry | hybrid (specs in repo + platform-side tenant memory) | **automated** (the closest claim in the market: when an implementing agent alters an API response shape, the spec "reflected the change immediately, so downstream agents referenced the updated contract") | yes (Cosmos CLI, IDE, MCP) | partial (Coordinator agent breaks specs into tasks for Implementor + Verifier — closest org-scale "next-leaves") | enterprise ($200/dev/mo MAX plan; public preview May 4, 2026) | enterprise / long-lived multi-repo | full | partial (spec + tasks + tenant memory across repos; not a public graph API) | full claim (sessions are durable, replayable, auditable) | partial→full claim (bidirectional sync via Context Engine; no public drift API) | partial (Coordinator drives next-task selection) | full (Verifier expert; spec-bound checks) | full (MCP, multi-model, runs in customer perimeter) | Closest analog to manifold's "long-lived compass" — but vendor-locked, expensive, and the spec model is implicit in the platform rather than a queryable open graph. No public `next-leaves` API. | augmentcode.com/tools/best-spec-driven-development-tools; augmentcode.com/guides/living-specs-vs-static-specs; augmentcode.com/blog/cosmos-now-in-public-preview |
| **Codex CLI + AGENTS.md + Skills** | https://developers.openai.com/codex | OpenAI Codex CLI/IDE/Web with `AGENTS.md` instruction chain, `$plan` skill, subagent workflows, traces dashboard | markdown-in-git (`AGENTS.md`, `.agents/skills/`) | none (AGENTS.md is rules, not spec; plan is ephemeral) | yes (Codex CLI exposable as MCP server; integrates with OpenAI Agents SDK) | partial (`$plan` skill + traces; multi-agent handoff pattern with project-manager + designer + frontend/backend/tester roles, but no persistent spec graph) | freemium (ChatGPT Plus/Pro + API; AGENTS.md/skills are free OSS spec) | one-shot feature → orchestration | partial (AGENTS.md is instruction, not intent of truth) | partial (nested AGENTS.md files form a per-dir override chain) | partial (git; traces dashboard logs every prompt/tool/handoff) | none | partial (`$plan` produces ordered milestones; no "next-leaves" query) | partial (tester agent role in cookbook example) | full (MCP server, skills, subagents, OpenAI Agents SDK) | Codex's strength is *orchestration of agents*, not maintenance of a long-lived spec graph. AGENTS.md is now an Agentic AI Foundation–stewarded open standard (60k+ repos) — manifold should *consume* AGENTS.md, not compete with it. | developers.openai.com/codex/skills; developers.openai.com/codex/guides/agents-md; cookbook.openai.com/examples/codex/codex_mcp_agents_sdk/building_consistent_workflows_codex_cli_agents_sdk |

**Tools mentioned but marked "needs deep pass":** Specil (Show HN, March 2026, called itself "minimal" — single thread, low signal); Specific (YC F25, backend-as-spec, Oct 2025); spec-driver, lean-spec, fspec, MoAI-ADK, quint-code, MetaSpec, cc-sdd, SPEC-AGENTS.md, Vibe Kanban, Spec Kitty — surfaced in the awesome-spec-driven-development index but with insufficient documentation depth to fill a row honestly.

---

## Community Pulse (mid-2025 → June 2026)

### Pain themes (agents + specs)

- **"Specs only pay off if you actually engage with them — most teams won't."** OpenSpec maintainers concede this in their FAQ: *"If you're looking for a magic tool that plans everything for you without any effort on your part, this isn't it. Specs only work if you actually read them, think through them, and engage with them."* — openspec.dev (early 2026).
- **Context resets are the dominant pain.** The OpenSpec landing page frames it as the core thesis: *"Context doesn't disappear when a chat session ends or someone leaves the team."* — openspec.dev (Jan–Mar 2026). Echoed by Augment: *"Knowledge built up in one engineer's agent context reset when the session ended."* — awesomeagents.ai/reviews/review-augment-cosmos/ (May 2026).
- **SDD is "Waterfall in a costume" — and developers are arguing about it openly.** HN thread "Spec-Driven Development: The Waterfall Strikes Back" (id 45935763, Nov 12, 2025, 225 points, 191 comments). Top comment from user liampulles: *"Its not a surprise to me that this approach also helps AI coding agents to work more effectively, as in-depth planning is essentially moving the thinking upfront."* — news.ycombinator.com/item?id=45935763.
- **Kiro produces passing tests but missed intent — a recurring complaint.** HN (id 46540927, early 2026): *"It has spec driven development, which in my testing yesterday resulted in a boat load of passing tests but zero useful code. It first gathers requirements, which are all worded in strange language that somehow don't capture specific outcomes OR important implementation details."* — news.ycombinator.com/item?id=46540927.
- **Spec lifecycle is the unsolved question.** Martin Fowler quoting Kent Beck (Jan 8, 2026): *"The descriptions of Spec-Driven development that I have seen emphasize writing the whole specification before implementation. This encodes the (to me bizarre) assumption that you aren't going to learn anything during implementation that would change the specification."* — martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html.
- **Tooling sprawl is a real adoption blocker.** HN Show HN: Specil (id 46421151, ~March 2026): *"I think Spec-Driven Development is a way to work with AI agents like Claude Code, but the workflow still feels a bit unrefined. Existing tools are often too complex."* — submitter jtakahashi64, news.ycombinator.com/item?id=46421151.
- **Researchers are now putting numbers on intent drift.** Arike, Donoway, Bartsch & Hobbhahn (arxiv 2505.02709, May 2025, published AAAI/ACM AIES 2025) report that *"the best-performing agent (a scaffolded version of Claude 3.5 Sonnet) maintains nearly perfect goal adherence for more than 100,000 tokens in our most difficult evaluation setting, all evaluated models exhibit some degree of goal drift."* Saebo, Gibson, Crosse, Menon, Jang & Cruz (arxiv 2603.03456, Mar 3, 2026; Columbia / Georgia Tech / UC San Diego / MATS / SPAR) tested GPT-5 mini, Haiku 4.5, and Grok Code Fast 1 and found agents *"are more likely to violate their system prompt when its constraint opposes strongly-held values like security and privacy."* Independent confirmation that "manifold's drift detection" is solving a measured problem, not a vibes one.
- **"Spec drift" has crossed into vendor marketing language.** Kinde: *"Specification drift, or 'spec drift,' is what happens when the behavior of your code no longer matches its documentation or design specifications."* — kinde.com/learn/ai-for-software-engineering/ai-devops/spec-drift-the-hidden-problem-ai-can-help-fix/ (2026). Speakeasy ships drift webhooks for OpenAPI. Tricentis frames it as "intent drift" with human-review gates.
- **BMAD's quiet popularity is the under-discussed story.** HN (id 45156172, Sep 2025): *"Pretty surprised BMAD-method wasn't mentioned. For my money it's by far the best Claude Code compliment [sic]."* — news.ycombinator.com/item?id=45156172. BMAD is at ~48.6k stars and few benchmark articles include it.

### Trending phrases (with one example link each)

- **"spec-driven development" (SDD)** — github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/
- **"intent drift"** — tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots
- **"context engineering"** — github.com/coleam00/context-engineering-intro
- **"living specs" vs "static specs"** — augmentcode.com/guides/living-specs-vs-static-specs
- **"vibe coding" (pejorative)** — aws.amazon.com/blogs/devops/amazon-q-developer-end-of-support-announcement/
- **"vibe specs"** — tessl.io/blog/how-tessls-products-pioneer-spec-driven-development/
- **"delta specs" (ADDED / MODIFIED / REMOVED)** — openspec.dev
- **"constitution → specify → plan → tasks → implement" pipeline** — github.github.com/spec-kit/quickstart.html
- **"subagent-driven development"** — blog.fsck.com/2026/03/09/superpowers-5/
- **"executable specs" / "specs as source of truth"** — infoq.com/articles/spec-driven-development/
- **"agent OS / AGENTS.md"** — github.com/buildermethods/agent-os; AGENTS.md is stewarded by the Agentic AI Foundation (AAIF, a directed fund under the Linux Foundation; per LF press release Dec 9, 2025: *"adopted by more than 60,000 open source projects and agent frameworks including Amp, Codex, Cursor, Devin, Factory, Gemini CLI, GitHub Copilot, Jules and VS Code"*; originally released by OpenAI in August 2025).

### Notable threads (3–5)

| title | url | platform | date | summary |
|---|---|---|---|---|
| Spec-Driven Development: The Waterfall Strikes Back | https://news.ycombinator.com/item?id=45935763 | Hacker News | Nov 12, 2025 | 225-point debate on whether SDD is rebranded waterfall. Consensus: planning upfront helps agents specifically because agents follow plans literally — a useful inversion of the "waterfall = bad" reflex. |
| Verified Spec-Driven Development (VSDD) | https://news.ycombinator.com/item?id=47197595 | Hacker News | early 2026 | Argues for spawning N parallel agent implementations against the same spec and picking the best. Reframes specs as the substrate for *agent fleets*, not single agents. Quote: *"You can now spin up five agents to implement five different versions of the thing you're building and simply pick the best one."* |
| Show HN: Specil – A minimal and helpful tool for Spec-Driven Development | https://news.ycombinator.com/item?id=46421151 | Hacker News | ~Mar 2026 | Reaction to Spec Kit/Kiro being "too complex" — points to a market opening for thin/composable SDD tools. |
| AWS Kiro spec-driven thread ("passing tests, zero useful code") | https://news.ycombinator.com/item?id=46540927 | Hacker News | early 2026 | Skeptical hands-on review of Kiro. Useful counterweight to vendor narrative. |
| BMAD+Spec-kit interop discussion | https://github.com/github/spec-kit/discussions/415 | GitHub Discussions | late 2025 | *"BMAD and the multi-agent-squad seem to be going the more prescriptive low/no-code path. spec-kit and specpulse seem to want to be a bit closer to the implementation and less opinionated."* The category is already self-segmenting into "prescriptive multi-agent" vs "thin spec scaffolding." |

(Direct Reddit threads on r/ClaudeAI, r/ChatGPTCoding, r/aws specifically about OpenSpec/Spec Kit/Kiro were referenced in secondary coverage but not retrievable as primary URLs within this scout's budget — flagged as a coverage gap below.)

---

## Three implications for manifold

### 1. Steal the **constitution → spec → plan → tasks → implement** pipeline as the *write path*, but keep manifold's spec graph as the *read path*

Every serious tool in this list — Spec Kit, BMAD, OpenSpec, Kiro, Superpowers, PRPs — has converged on roughly the same authoring workflow (constitution/standards → high-level spec → plan → tasks → implement, with a verification step). Don't reinvent it. The *queryable spec graph + `next-leaves` API + drift detection* is what nobody else has. Treat Spec Kit's pipeline as the upstream producer of nodes in your graph and OpenSpec's delta-spec syntax (ADDED/MODIFIED/REMOVED) as your edge type for "what changed against the canonical spec." That makes manifold immediately interoperable with the ~108k-star incumbent rather than competing with it.

### 2. The genuine gap is **continuous drift + cross-feature compass**, not authoring

Of the 12 tools surveyed, only **Augment Cosmos** (closed-source, $200/dev/mo MAX plan, May 2026 preview) and **Tessl** (closed-source, MCP, tests-as-spec-guardrails) attempt continuous spec↔code reconciliation, and even they don't expose a project-level graph query API. Spec Kit's `/speckit.analyze` runs once before implement. OpenSpec's `validate --strict` checks structural completeness, not behavioral drift. Kiro's hooks are file-event triggers, not semantic comparators. **A `next-leaves` API that says "given current code + current spec graph, here are the 3 smallest open leaves" is genuinely uncovered space in OSS** — and the published research on goal/intent drift in coding agents (Arike et al. 2025; Saebo et al. 2026) means there's now an academic vocabulary to anchor the value prop.

### 3. Ship as an **MCP server + AGENTS.md producer**, not as a CLI or IDE

The category has already settled on two integration surfaces: (a) MCP server (Tessl, Codex, Kiro, Cursor, Claude Code all expose or consume), (b) `AGENTS.md` / `CLAUDE.md` / `.cursor/rules` markdown files that agents auto-load on session start. Spec Kit alone ships 29+ agent integrations because it commits to *both*. Manifold should expose its spec graph and `next-leaves` API as an MCP server (so any agent can ask "what's next?" mid-session) and auto-generate a slim `AGENTS.md` from the graph (so the same context survives session resets in tools that don't speak MCP). **Do not build a CLI or IDE** — that's the most crowded part of the market (Kiro, Cursor, Antigravity, Cosmos, Aider, Codex, Claude Code, Continue, Cline) and offers no compass-query moat.

---

## Session metadata

```
session: A
category: SDD / agent workflow
researcher_model: Claude (Sonnet 4.5 class, June 2026)
date: 2026-06-06
sources_searched:
  - web_search: "GitHub Spec Kit specify CLI spec-driven development"
  - web_search: "BMAD Method agent spec-driven"
  - web_search: "OpenSpec AI spec-driven development tool"
  - web_search: "Tessl AI spec-driven software development platform"
  - web_search: "Amazon Kiro AWS spec-driven IDE"
  - web_search: "Amazon Q Developer spec workflow CLI"
  - web_search: "Claude Code superpowers writing-plans brainstorming skill"
  - web_search: "AGENTS.md Agent OS spec-driven standard"
  - web_search: "PRP product requirements prompt template AI coding"
  - web_search: "aider conventions file CONVENTIONS.md spec"
  - web_search: "Cursor rules .cursorrules plans spec drift"
  - web_search: "'spec-driven development' hacker news 2026"
  - web_search: "'spec-driven' reddit AI coding agents 2026"
  - web_search: "spec drift detection AI code documentation"
  - web_search: "'intent drift' AI agent coding context engineering"
  - web_search: "OpenAI Codex agent spec plan workflow CLI"
  - web_search: "'spec-driven-development' github topic 2026"
  - web_search: "Augment Cosmos spec-driven living spec"
  - subagent: stars + last release + community quotes for 7 OSS tools + Tessl pricing/MCP/announcement
  - enricher pass: confirmed paper authors, Kiro revised pricing, Superpowers star count, AGENTS.md stewardship
  - sites referenced: github.com, github.blog, news.ycombinator.com, kiro.dev, kinde.com, tessl.io,
    openspec.dev, openspec.pro, aider.chat, augmentcode.com, awesomeagents.ai,
    developers.openai.com, claude.com, cursor.com, infoq.com, martinfowler.com, arxiv.org,
    dev.to, medium.com, hashrocket.com, builder.io, blog.fsck.com, marktechpost.com, faros.ai,
    alexcloudstar.com, knightli.com, openaitoolshub.org, chatforest.com, thenewstack.io,
    repost.aws, aws.amazon.com, claudepluginhub.com, infoworld.com, linuxfoundation.org
gaps_in_coverage:
  - Direct Reddit thread URLs (r/ClaudeAI, r/ChatGPTCoding, r/aws) for Kiro/OpenSpec/Spec Kit
    could not be retrieved as primary sources within budget — secondary coverage referenced them
    but URLs were not surfaced.
  - Specil, Specific (YC F25), spec-driver, lean-spec, fspec, MoAI-ADK, quint-code, MetaSpec,
    cc-sdd, Vibe Kanban, Spec Kitty — surfaced in the awesome-spec-driven-development index but
    with insufficient documentation depth to fill a row honestly. Marked "needs deep pass".
  - Tessl's exact pricing tier numbers (Pro / Enterprise dollar amounts) are not public —
    only "Free Plans" + "Professional Plans" structure is confirmed.
  - Direct quotes from agent-os, PRPs-agentic-eng, context-engineering-intro communities
    (HN/Reddit) in the last 12 months were not surfaced — those tools' community footprints
    are smaller and discussion happens on Twitter/X and Discord which were not searched.
  - M-axis interpretations are this scout's best read from the column names; the companion
    master-handoff-axes document was not provided and the user is explicitly invited to correct.
```