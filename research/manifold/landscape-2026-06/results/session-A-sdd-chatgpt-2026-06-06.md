---
status: frozen
study: manifold-landscape-2026-06
session: A
type: raw-result
provider: chatgpt
date: 2026-06-06
synthesis: ../synthesis.md
---

# Session A Research Report on Spec-driven Development and Agent Workflow Tools

## Scope and scoring

I filtered for tools and projects that make **specification, plan, rules, or durable agent context** the organizing unit of work, rather than generic autocomplete. In practice, the category splits into three layers: **spec workflow kits** such as GitHub Spec Kit, OpenSpec, BMAD, and Kiro; **persistent instruction layers** such as Agent OS, AGENTS.md, Cursor Rules, Claude Code `CLAUDE.md`, and Codex `AGENTS.md`; and **context governance/control planes** such as Tessl, which focuses on versioning, evaluation, and distribution of agent skills and context. citeturn40view0turn8view0turn13view0turn16search4turn25view2turn27view3turn27view2turn34search10turn37search11turn39search1

For the manifold-style axes, I interpreted the user’s `M1` to `M7` as follows: `M1_truth` is whether the tool establishes a durable source of truth, `M2_graph` is whether intent is decomposed structurally rather than as flat docs, `M3_history` is whether past intent and changes remain legible over time, `M4_drift` is whether intent/code divergence is detected or managed, `M5_compass` is whether the tool can answer “what next?” structurally, `M6_verdict` is whether it can evaluate completeness or correctness against intent, and `M7_agent` is whether the workflow is deeply agent-native. These ratings are my synthesis from public docs, repo metadata, forum discussions, and vendor materials current to **2026-06-06**. citeturn40view0turn8view0turn13view0turn16search4turn25view2turn27view3turn34search1turn37search0turn39search3

## Tool inventory

| name | url | one_liner | canonical_store | drift_handling | agent_native | compass_queries | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| GitHub Spec Kit | [github.com/github/spec-kit](https://github.com/github/spec-kit) | OSS toolkit with `/speckit.constitution → specify → plan → tasks → implement`; 109k★, latest release **v0.0.77** on **2026-06-05**; supports 30+ coding agents; MCP not explicit in public docs reviewed | markdown-in-git | manual | yes | partial | OSS | one-shot feature | full | partial | partial | partial | partial | partial | full | Best-in-class front-door workflow and command surface, but it is still mostly a **feature-local artifact chain**. It does not expose a long-lived, queryable intent graph or a manifold-style `next-leaves` API. | repo/docs 2026-06-06, release 2026-06-05, GitHub blog 2025-09-02 citeturn40view0turn4view0turn7search7 |
| OpenSpec | [github.com/Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) | OSS, lightweight “source of truth spec” workflow with `propose/apply/sync/archive`, 53.2k★, latest **v1.4.1** on **2026-06-03**; supports many tools; public site explicitly says “No MCP” | markdown-in-git | manual | yes | partial | OSS | long-lived project | full | partial | partial | partial | partial | partial | full | Stronger than Spec Kit for **brownfield** and ongoing spec deltas, but it still centers on folders and change artifacts, not a layered spec graph with durable cross-feature navigation and query APIs. | repo/release 2026-06-06 and 2026-06-03, supported-tools docs 2026-06-06, site 2026-06-06, Thoughtworks Radar 2026-04-15 citeturn8view0turn9view0turn10search2turn10search5turn10search16 |
| BMAD Method | [github.com/bmad-code-org/bmad-method](https://github.com/bmad-code-org/bmad-method) | OSS framework with agents, PRD, architecture, epics/stories, sprint state, and `bmad-help` that recommends what to do next; 48.7k★, latest **v6.8.0** on **2026-05-25**; MCP not explicit in docs reviewed | markdown-in-git | manual | yes | yes | OSS | long-lived project | full | partial | partial | partial | full | partial | full | BMAD comes closest to a practical “project guide” because `bmad-help` inspects artifacts and suggests the next required workflow. The gap is that its state is still mainly **workflow files plus YAML**, not a semantic, queryable intent graph. | repo/release 2026-06-06 and 2026-05-25, docs 2026-06-06 citeturn12view0turn13view0turn11search0 |
| Kiro | [kiro.dev](https://kiro.dev/) | Commercial, spec-first IDE with **Specs**, **Steering**, **Hooks**, cloud/web agent, and Powers bundles that include MCP servers; pricing starts at Free, Pro $20, Pro+ $40, Power $200 | hybrid | partial | yes | partial | freemium | long-lived project | full | partial | partial | partial | partial | partial | full | Kiro is the strongest commercial embodiment of “specs as the unit of work,” but its persistence still lives in repo files, IDE state, and Kiro surfaces. It is not yet a standalone project compass with manifold-style structural queries across time. | product/docs/pricing 2026-06-06, specs 2026-05-05, steering/hooks 2026-02-18, first-project 2026-05-28, powers/web 2026-06-06 citeturn15search4turn16search4turn16search2turn16search0turn16search6turn18search0turn18search11turn18search17 |
| Tessl | [tessl.io](https://tessl.io/) | Agent enablement platform for versioned skills/context, registry distribution, evals, MCP integration, and optional spec-driven workflow tiles; offers free start plus enterprise motion | hybrid | automated | yes | partial | freemium | enterprise | partial | partial | full | full | none | full | full | Tessl is the closest thing here to **operationalizing agent memory and drift control**. The main gap is scope: it governs skills and context bundles very well, but it is not fundamentally a product intent graph or a “what should we build next?” engine. | home/docs 2026-06-06 and 2026-05-29, config docs 2026-05-29, Snyk partnership 2026-03-17 citeturn23view0turn24view0turn25view0turn25view2turn21search9turn15search15 |
| Agent OS | [buildermethods.com/agent-os](https://buildermethods.com/agent-os) | OSS system for discovering, indexing, and injecting coding standards into specs and agent work; 4.8k★, latest **Agent OS 3.0** on **2026-01-20**; MCP not explicit in docs reviewed | markdown-in-git | manual | partial | partial | OSS | long-lived project | partial | partial | partial | partial | partial | none | partial | Agent OS is excellent at **extracting durable conventions from a codebase** and feeding them back into plans. It is more “standard memory” than “project compass,” so it complements manifold more than it competes with it. | repo/release 2026-06-06 and 2026-01-20, site 2026-06-06 citeturn27view1turn28view0turn27view3 |
| AGENTS.md | [agents.md](https://agents.md/) | Open format for persistent agent instructions, used by 60k+ open-source projects; 22k★ on repo, **no GitHub releases published**; works across many agents | markdown-in-git | manual | partial | no | OSS | other | partial | none | partial | none | none | none | partial | AGENTS.md is becoming the common substrate for cross-agent project memory, but it is intentionally thin. It stores conventions and workflow hints, not decomposed intent, history semantics, or next-step reasoning. | site/repo 2026-06-06, GitHub blog 2025-11-19 citeturn27view2turn27view0turn29view0turn29view1turn26search6 |
| Cursor | [cursor.com/docs](https://cursor.com/docs) | Commercial agent IDE with **Plan Mode**, persistent **Rules**, **Subagents**, CLI rule/MCP support, and cloud/background agents; pricing includes a free Hobby tier and Pro from $20/mo | hybrid | manual | yes | partial | freemium | one-shot feature | partial | none | partial | partial | partial | partial | full | Cursor now has strong planning and persistent rules, but public workflow still centers on **session plans plus rules**, not a maintained project intent model that survives and answers months-later query flows structurally. | docs/pricing/blog/forum 2026-06-06 and 2026-01-09/2026-04-14 citeturn34search1turn34search10turn34search12turn34search17turn36search0turn33search4turn33search10 |
| Claude Code | [docs.anthropic.com/en/docs/claude-code/overview](https://docs.anthropic.com/en/docs/claude-code/overview) | Agentic coding tool with **plan mode**, `CLAUDE.md` memory, hooks, subagents, MCP tool hooks, and layered startup context; included in Pro/Max and enterprise offerings | hybrid | partial | yes | partial | unknown | long-lived project | partial | none | partial | partial | partial | partial | full | Claude Code is very strong on **plan gating, memory layering, and automation hooks**. The gap is that its durable memory is still file-based and conversational. It does not natively turn intent into a browsable, time-aware project compass. | docs/product/pricing 2026-06-06, help center 2026-05-18/19 citeturn37search2turn37search0turn33search3turn33search0turn37search12turn37search11turn38search2turn38search0turn38search12 |
| Codex | [developers.openai.com/codex](https://developers.openai.com/codex) | OpenAI coding agent with CLI, `AGENTS.md`, Skills, and MCP support in CLI and IDE; positioned as one agent across environments; changelog active through **June 2026** | hybrid | manual | yes | partial | unknown | one-shot feature | partial | none | partial | none | partial | partial | full | Codex has the right substrate pieces, especially `AGENTS.md`, Skills, and MCP, but public docs describe **instruction and capability plumbing**, not a maintained spec graph that can answer project-compass questions over time. | official docs/changelog 2026-06-06 and June 2026 citeturn39search19turn39search3turn39search1turn39search5turn39search7turn39search9turn39search15 |
| Amazon Q Developer | [docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/what-is.html](https://docs.aws.amazon.com/amazonq/latest/qdeveloper-ug/what-is.html) | Adjacent rather than first-class SDD platform: project rules, prompt library, workspace indexing, reviews, AWS-native workflow patterns; Free tier plus Pro; note that **Q CLI has become Kiro CLI** | hybrid | manual | yes | partial | freemium | enterprise | partial | none | partial | none | none | partial | full | Amazon Q Developer supports persistent rules and prompt reuse, but public docs expose a **context/rules layer**, not a maintained spec lifecycle. The spec-driven momentum in AWS has clearly shifted toward Kiro. | AWS docs and builder content 2025-10-25 to 2026-06-06 citeturn15search2turn15search8turn20search5turn20search2turn20search17turn20search20turn16search7turn20search1 |

## How the category is clustering

The strongest pattern is the **artifact conveyor belt**. GitHub Spec Kit, OpenSpec, BMAD, and Kiro all formalize a sequence like **requirements/specs -> technical plan/design -> tasks -> implementation**, often with agent commands or IDE flows wrapped around it. This is a big improvement over pure vibe coding, but most of these systems still store truth as markdown and YAML inside a repo, scoped to a feature or change, rather than as a graph of long-lived project intent. citeturn40view0turn8view0turn13view0turn16search4

The second pattern is the **durable instruction layer**. Agent OS, AGENTS.md, Cursor Rules, Claude Code `CLAUDE.md`, Amazon Q project rules, and Codex `AGENTS.md` all try to stop agents from forgetting local conventions, hooks, or workflows. That makes them important adjacencies for manifold, because they preserve “how we work” and “how this codebase behaves,” but they usually do not preserve the deeper “why,” feature lineage, or cross-feature dependency structure. citeturn27view3turn27view2turn34search10turn37search11turn20search5turn39search1

The third pattern is **agent context ops**. Tessl stands out here because it treats context and skills as software: versioned, distributed via registry, evaluated, security-scanned, and wired in through MCP. Kiro pushes in a similar direction with Powers that bundle steering, hooks, and MCP servers. This is the clearest signal that the market now sees “agent memory” as an operational surface, not just a prompt authoring problem. citeturn25view2turn25view0turn23view0turn15search15turn16search8turn18search17

What is still unusually rare is a genuine **compass**. BMAD comes closest because `bmad-help` inspects the project and recommends the next required workflow, and Kiro or Spec Kit can infer next actions within a current change. But none of the mainstream tools I found publicly expose something like a **layered spec graph + drift detection + queryable next-work API** across months, repos, and changing product intent. That remains the sharpest differentiation for manifold. citeturn13view0turn16search4turn40view0turn23view0

## Community pulse

### Pain themes

- **Session resets still destroy intent.** Tessl’s spec-driven docs frame the core problem bluntly: when you restart the session, “the agent has no easy way to regain context,” which they call an “intent-to-code chasm.” That is vendor language, but it matches what the broader market is building around. Approx. **2026-05**. citeturn24view0
- **Teams want planning gates before edits touch disk.** Claude Code explicitly recommends plan mode for work that should be reviewed before changes land, and Cursor’s docs market Plan Mode as generating a reviewable implementation plan first. Approx. **2026-06**. citeturn37search0turn34search1
- **Users still report agents that ignore instructions and start building anyway.** In Cursor’s forum, one recurring workaround is a “research / investigation / planning only” rule to keep the agent read-only. Approx. **2026-04**. citeturn33search10
- **The community is converging on the view that SDD is an approach, not a single package.** A Reddit thread in `r/ChatGPTCoding` argues that “spec driven development” should not be conflated with any one repo or tool. Approx. **2025-11**. citeturn7search2
- **Brownfield support is a fault line.** Thoughtworks Radar’s note on OpenSpec explicitly says many SDD frameworks are better suited to greenfield projects, while OpenSpec’s “spec deltas” are better for existing systems. Approx. **2026-04**. citeturn10search5
- **Framework complexity becomes its own adoption tax.** In the BMAD subreddit, maintainers and users acknowledge that “V6 is complicated” and that better docs are necessary just to know what is available. Approx. **2026-01**. citeturn11search12
- **Pricing and metering still cause backlash for long-running agents.** Kiro’s community thread complaining about pricing changes shows that agent workflows are judged not just on capability, but on how predictable and affordable they remain at spec-heavy usage levels. Approx. **2025-08**. citeturn18search5
- **After model quality improved, reviewability and governance moved to center stage.** Tessl’s messaging now says “the model’s solved, now comes the hard part,” meaning reviewability, skill measurement, and operational control. Approx. **2026-06**. citeturn23view0

### Trending phrases

- **spec-driven development**: GitHub Spec Kit and OpenSpec both use the phrase as the core framing for the workflow. Example: Spec Kit repo / GitHub blog. citeturn40view0turn7search7
- **vibe coding / vibecoding**: Kiro markets itself as the bridge from vibe coding to engineering rigor, and Tessl explicitly contrasts structured work with vibecoded output. Example: Kiro launch blog; Tessl docs. citeturn18search6turn24view0
- **plan mode**: now a standard phrase in Claude Code and Cursor for “think first, edit later.” Example: Claude Code common workflows; Cursor Plan Mode docs. citeturn37search0turn34search1
- **context engineering**: OpenSpec tags and adjacent tooling increasingly describe the problem as context engineering instead of prompt engineering. Example: OpenSpec repo topics. citeturn8view0
- **steering files**: Kiro’s steering files are becoming a recognized pattern for durable repo-specific behavior. Example: Kiro steering docs. citeturn16search2turn16search16
- **skills as code**: Tessl’s homepage literally says “Skills are the new code,” pushing skills into the software lifecycle. Example: Tessl homepage. citeturn23view0
- **AGENTS.md**: AGENTS.md has become the lowest-friction phrase for persistent coding-agent instructions. Example: agents.md site. citeturn27view2
- **MCP**: increasingly treated as the portable bridge between agent instructions and live tools/context. Example: Codex MCP docs; Kiro docs. citeturn39search7turn16search6
- **reviewability**: a newer phrase, mostly from enterprise-facing agent tooling, for making agent output governable. Example: Tessl homepage article. citeturn23view0
- **intent drift / drift**: still less standardized than the phrases above, but increasingly used in writeups comparing SDD approaches. Example: OpenSpec comparison article snippet connecting drift and specs. citeturn7search9

### Notable threads

| title | url | platform | date | summary |
|---|---|---|---|---|
| Spec-driven development for AI is a form of… | [reddit.com/r/ChatGPTCoding/comments/1o6j1yr/specdriven_development_for_ai_is_a_form_of](https://www.reddit.com/r/ChatGPTCoding/comments/1o6j1yr/specdriven_development_for_ai_is_a_form_of/) | Reddit | approx. 2025-11 | High-signal argument that SDD is a way of organizing agent work and maintaining intent, not simply a branded toolkit. citeturn7search2 |
| Agents ignoring instructions, deciding to go ahead and build on its own | [forum.cursor.com/t/agents-ignoring-instructions-deciding-to-go-ahead-and-build-on-its-own/157655](https://forum.cursor.com/t/agents-ignoring-instructions-deciding-to-go-ahead-and-build-on-its-own/157655) | Cursor forum | 2026-04-14 | Real-world evidence that persistent rules alone do not always constrain agents; users are writing explicit planning-only guardrails. citeturn33search10 |
| BMAD documentation | [reddit.com/r/BMAD_Method/comments/1psnjmo/bmad_documentation](https://www.reddit.com/r/BMAD_Method/comments/1psnjmo/bmad_documentation/) | Reddit | approx. 2026-01 | Maintainers acknowledge framework complexity and are prioritizing scenario-based docs, which suggests the workflow stack can become difficult to navigate at scale. citeturn11search12 |
| Amazon Kiro IDE, bait and switch on pricing? | [reddit.com/r/kiroIDE/comments/1mfvhja/amazon_kiro_ide_bait_and_switch_on_pricing](https://www.reddit.com/r/kiroIDE/comments/1mfvhja/amazon_kiro_ide_bait_and_switch_on_pricing/) | Reddit | approx. 2025-08 | Backlash focused on usage caps and pricing volatility, a reminder that enterprise-style process only sticks if cost mechanics are legible. citeturn18search5 |
| How to write a great AGENTS.md, lessons from over 2,500 repositories | [github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/) | GitHub Blog | 2025-11-19 | Important because it shows AGENTS.md has escaped niche status and is becoming part of mainstream coding-agent practice. citeturn26search6 |

## Implications for manifold

### Steal the guided workflow ergonomics

The best alternatives make it very easy to go from vague request to structured artifacts. Spec Kit’s command ladder, OpenSpec’s lightweight `propose/apply/sync/archive` flow, BMAD’s role-based workflows, and Kiro’s spec-first IDE all reduce friction for adoption. Manifold should consider stealing that **guided handoff UX**, especially the “ask clarifying questions, generate reviewable artifact, then progress to tasks” pattern, without giving up its longer-horizon compass model. citeturn40view0turn8view0turn13view0turn16search4

### Steal drift and context operations from Tessl and Kiro

Tessl’s strongest idea is that agent context is not just written, it is **versioned, evaluated, distributed, and regression-tested**. Kiro’s strongest complementary idea is packaging MCP servers, steering, and hooks into reusable Powers. If manifold wants to own durable intent over months, it should likely add stronger **intent observability**, **eval-backed drift checks**, and **portable context packages** that attach graph nodes to live tools and repos. citeturn25view2turn25view0turn23view0turn16search8turn18search17

### The biggest gap still remains open

None of the public tools I found fully combine: **durable source-of-truth intent**, **structural decomposition across the project**, **history over time**, **first-class drift handling**, and a **queryable “what next?” interface** that survives past a single feature or session. BMAD gets closest on “what next,” Tessl gets closest on drift/evals, and OpenSpec gets closest on long-lived brownfield spec maintenance. But the market still mostly stops at markdown artifacts, rule files, or context registries. That leaves real room for manifold if it can prove a superior **project-compass model** rather than yet another spec generator. citeturn13view0turn23view0turn10search5turn40view0turn8view0

## Open questions and limitations

I did **not** do a deep-pass inventory on smaller 2026 GitHub-topic entrants such as SpecPact, SDD Pilot, FSPEC, shipspec-style Claude plugins, or emerging “dark factory” repos. Several look relevant, but their public materials were thinner, more volatile, or closer to workflow plugins than durable project systems, so I left them out of the main inventory rather than overstate confidence. The GitHub topic pages do show clear recent experimentation in this direction. citeturn6search10turn6search14turn6search18

I also have stronger evidence for **vendor docs, repo metadata, and community forums** than for Hacker News specifically, because the captured high-signal discussion in this pass skewed toward GitHub, Reddit, and product forums. Relatedly, some commercial docs are JS-heavy and can shift quickly, so specific packaging or pricing details for tools like Cursor, Kiro, and Claude Code may evolve faster than the corresponding open-source repo metadata. citeturn36search0turn18search0turn38search2

## Session metadata

```yaml
session: A
category: SDD / agent workflow
researcher_model: GPT-5.2 Thinking
date: 2026-06-06
sources_searched:
  - "github/spec-kit repo, releases, GitHub blog on spec-driven development"
  - "Fission-AI/OpenSpec repo, supported-tools docs, openspec.dev, Thoughtworks Radar"
  - "BMAD Method docs, repo metadata, subreddit and release pages"
  - "Kiro product page, specs/steering/hooks docs, pricing, powers, web"
  - "Amazon Q Developer docs on pricing, project rules, prompt library, workspace context, builder content"
  - "Tessl homepage, docs on spec-driven development, configuration, changelog, Snyk partnership"
  - "Agent OS site and repo, AGENTS.md site and repo"
  - "Cursor docs for plan mode, rules, subagents, CLI, pricing, blog, forum"
  - "Anthropic Claude Code docs for plan mode, memory, hooks, subagents, pricing"
  - "OpenAI Codex docs for CLI, AGENTS.md, Skills, MCP, best practices, changelog"
  - "Community sources: Reddit, Cursor forum, GitHub blog, vendor blogs"
gaps_in_coverage:
  - "No deep-pass on smaller GitHub-topic SDD entrants such as SpecPact, FSPEC, SDD Pilot, and shipspec-style plugins"
  - "Limited Hacker News capture in this pass"
  - "Some commercial docs are JS-heavy and fast-moving, so packaging/pricing details may change"
```