---
status: frozen
study: manifold-landscape-2026-06
session: E
type: raw-result
provider: claude
date: 2026-06-06
synthesis: ../synthesis.md
---

# Session E — Intent Drift Discourse & Validation Tools

## TL;DR
- The phrase "intent drift" is being aggressively claimed in 2026 by enterprise QA vendors (Tricentis), security vendors (ARMO), and a Japanese OSS methodology (Zenn IDD by virtualcraft) — but the term predates the AI-coding context, originating in Intent-Based Networking literature (Muonagor & Bensalem, arXiv:2404.15091, 23 April 2024). For manifold, the term is contested but unowned in the agent-coding niche.
- The discourse is real and worsening: 2025–2026 produced GitHub Spec Kit (Sept 2, 2025), AWS Kiro (July 2025 preview), Omniflow (March 6, 2026), Tricentis "Intent Drift in AI Code" (April 28, 2026), OpenAI's Sean Grove "The New Code" keynote (AI Engineer World's Fair, June 2025), and a steady drumbeat of Hacker News and Cursor-forum complaints about agents that pass tests, force-push against rules, and lose context mid-task.
- For manifold's positioning: lead with `change_reason` + `rationale` + `drift-report` as the *operational* answer to a problem the market is talking around. The gap competitors leave open is **history of intent (M3)** and **agent-native MCP-style integration (M7)** — spec-driven IDEs own M1/M2/M6, but nobody persists *why* across sessions.

---

## Key Findings

1. **"Intent drift" has three independent vocabulary lineages** that 2026 vendor marketing is conflating: (a) Intent-Based Networking academia (origin), (b) AI-agent safety/runtime security, and (c) AI-coding spec-↔-code (the manifold target).
2. **The "Stonewall" intent-drift blog from the seed list could not be verified** after targeted searches across multiple queries. There is no blog at stonewall.io tied to this term and no widely-cited "Stonewall" post on the topic. This should be flagged back to whoever supplied the seed.
3. **Spec-driven development (SDD) is the dominant 2025–2026 movement** the discourse organizes around. Sean Grove (OpenAI) crystallized it at AI Engineer World's Fair, June 2025; GitHub shipped Spec Kit September 2, 2025; AWS shipped Kiro in July 2025.
4. **None of the major shipped tools have a first-class `change_reason` or `rationale` field.** Spec Kit, Kiro, Omniflow, OpenSpec, and BMAD all version the *spec* but treat the *why-it-changed* as implicit (git log, comments) rather than typed.
5. **The community pain is dense and well-documented.** 23+ primary-source quotes were collectable across Hacker News, the Cursor Forum, DEV.to, Stack Overflow Blog, and engineer blogs — covering session amnesia, multi-agent divergence, doc decay, tests-green-but-wrong, and built-the-wrong-thing.
6. **Reddit was thinly indexable in this pass.** A future targeted Reddit pass (r/ClaudeAI, r/cursor, r/ChatGPTCoding) would strengthen the pain catalog further.

---

## Methodology note: column interpretation (M1–M7)

The M1–M7 axes were not supplied in the master handoff, so they are **interpreted as follows from the column names**. The user should correct if the master defined them differently.

- **M1_truth** — canonical, structured source of truth for *intent* (not just code).
- **M2_graph** — layered/linked spec graph: org → project → feature → task relationships, explicit links.
- **M3_history** — versioning of intent over time. Can you diff "intent at v1" vs "intent at v2" and see *why* it changed?
- **M4_drift** — automated detection of divergence between spec/intent and implementation.
- **M5_compass** — ability to answer "what next" given current state of spec vs code.
- **M6_verdict** — verification/acceptance gates producing a pass/fail verdict against the spec (not just unit tests).
- **M7_agent** — agent-native integration (MCP, CLI, programmatic API for Claude Code/Cursor/Codex), not just human-facing UI.

---

## Details

### Tool / Method Inventory

| name | url | type | one_liner | drift_handling | how_it_detects_drift | agent_native | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Tricentis AI Workspace (Intent Drift) | https://www.tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots | product | Test-management platform that flags "tests that pass for the wrong reasons" by correlating original test intent, code changes, and results | automated | Agents compare test results with recent dev activity; flag when behavior diverges from original specification | partial | enterprise | enterprise QA orgs | partial | none | partial | full | none | full | partial | Owns M6 (test-verdict against intent) and M4, but no graph of intent and no developer-facing `change_reason` field; QA-centric not dev-centric | tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots (Apr 28, 2026) |
| Omniflow | https://www.omniflowai.com | product | "Living PRD" SaaS keeping PRD ↔ design ↔ code in sync via a "sync engine"; code changes "surface requirement drift" for review | automated | Sync engine flags requirement drift when code changes diverge from PRD layer | partial | freemium | founders / PM-led teams building greenfield SaaS | full | partial | partial | full | partial | partial | no | Closed SaaS, vibe-coding-adjacent; intent lives in PRD-DSL not code; no MCP/CLI; weak on M3 (versioned *rationale*) and M7 | einpresswire.com/article/897693290 (Mar 6, 2026); omniflowai.com/lovable-alternatives |
| Zenn IDD (Intent Drift Detector) — virtualcraft | https://zenn.dev/virtualcraft/articles/idd-07_idd-concept | methodology / blog-series | 11+ part Japanese essay series defining IDD: structure intent into Why/What/How/Not, traceability beyond RTM, multi-LLM verification | manual → automated (proposed) | LLM extracts intent from docs/code, structures into 4 elements, compares to implementation | partial | OSS (design only) | long-lived inner-source projects | full | full | full | full | partial | partial | partial | Closest *philosophical* relative to manifold; designs the same primitives (rationale, hierarchical inheritance, drift report) but is a design proposal not a shipped tool — cite as theoretical justification | zenn.dev/virtualcraft (idd-06, idd-07, idd-11) |
| GitHub Spec Kit | https://github.com/github/spec-kit | OSS | Open-source CLI for Spec-Driven Development: `/speckit.constitution`, `/specify`, `/clarify`, `/plan`, `/tasks`, `/implement` produce Markdown artifacts the agent reads | manual | Static spec files; `/speckit.analyze` checks consistency between spec, plan, tasks, constitution | yes | OSS (MIT) | greenfield projects with Copilot/Claude/Cursor | partial | partial | partial (git-tracked) | none | full | partial | full | Strong on M1/M5/M7 but spec files don't actively detect drift after code is written; no `change_reason` field; manifold's drift-report is the missing layer | github.blog (Sept 2, 2025); developer.microsoft.com/blog/spec-driven-development-spec-kit |
| AWS Kiro | https://kiro.dev | product | VS Code-fork "spec-first" IDE: prompt → `requirements.md` + `design.md` + `tasks.md` in `.kiro/specs/`, with EARS notation and event-driven `hooks/` | partial | Hooks fire on file save/commit to re-check spec adherence; spec reviewed before code gen | yes | freemium ($20/mo Pro, $40/mo Pro+, $200/mo Power, per kiro.dev/pricing) | AWS-shop teams, brownfield rigor | full | partial | partial | partial | full | full | full | AWS-locked, EARS notation learning curve; no first-class *change_reason* per requirement; no cross-session "why this changed" log — manifold can be the cross-IDE, cross-agent rationale layer | kiro.dev; thenewstack.io/aws-kiro-testing-an-ai-ide-with-a-spec-driven-approach; The Register (Aug 18, 2025) |
| OpenSpec | https://github.com/Fission-AI/OpenSpec | OSS | Strict 3-phase state machine (proposal → apply → archive); separates `specs/` (current truth) from `changes/` (active proposals) | manual | Specs are source of truth; reviewers diff proposals against specs before merge | yes | OSS | iterative changes to existing codebases | full | partial | full | none | partial | full | full | Most active OSS competitor on M3 (because `changes/` directory archives proposals); but archives are docs not analyzable graphs; no automated runtime drift signal between spec and code | augmentcode.com/tools/best-spec-driven-development-tools (June 2026) — 52,700★ |
| BMAD-METHOD | https://github.com/bmad-code-org/BMAD-METHOD | OSS / methodology | Multi-agent framework with named personas (Mary/Preston/Winston/Sally/Devon/Quinn) for full-SDLC role-based context passing | manual | Each role-agent enforces its slice (PM vs Architect vs QA); cross-role handoff produces docs | yes | OSS | large greenfield projects with PRD/architecture rigor | partial | full | partial | none | partial | partial | full | Strong M2 via personas; persona system *prescribes* a workflow rather than *detecting* divergence; complementary to manifold | augmentcode.com (46,700+ stars and 5,500+ forks at v6.6.0, Apr 29, 2026, per MarkTechPost May 8, 2026) |
| ARMO (runtime intent-drift detection) | https://www.armosec.io/blog/detecting-intent-drift-in-ai-agents-with-runtime-behavioral-data | product | Runtime/Kubernetes security tool: detects intent drift in deployed AI agents by correlating syscalls + tool calls + network flows | automated | Action-chain analysis (tool invocation → data access → external egress); not per-event anomaly scoring | yes | enterprise | security/SOC teams running production agents | none | none | none | full | none | none | partial | **Different audience** — uses "intent drift" to mean *runtime security drift*, not spec↔code drift; useful as a vocabulary collision to address head-on | armosec.io/blog/detecting-intent-drift-in-ai-agents-with-runtime-behavioral-data |
| ADR-tools / Log4brains / Nygard ADRs | https://github.com/npryce/adr-tools ; https://github.com/thomvaill/log4brains | OSS / methodology | Foundational: Architecture Decision Records — markdown files in repo capturing *why* a decision was made; Log4brains adds web UI/log | manual | Human review; ADRs aren't checked against code automatically | no | OSS | long-lived projects, regulated industries | partial | partial | full | none | none | none | partial | The *philosophical ancestor* of `rationale` and `change_reason`. ADRs are static prose; manifold should position as "ADRs that talk to your agent" | github.com/npryce/adr-tools; Nygard 2011 essay |
| arXiv:2404.15091 — Muonagor & Bensalem | https://arxiv.org/abs/2404.15091 | research | Foundational coining of "intent drift" in Intent-Based Networking — gradual degradation of intent fulfillment before failure; tests 7 unsupervised models (DBSCAN wins) | automated | Unsupervised clustering (DBSCAN, OPTICS, GMM, One-Class SVM) on telemetry vs target KPI vector | n/a | n/a | n/a | n/a | n/a | n/a | full | n/a | n/a | n/a | **The term's origin point**. Predates the AI-coding usage by ~2 years; manifold should cite as etymological anchor | arxiv.org/abs/2404.15091 (Apr 23, 2024) |
| arXiv:2505.02709 — Evaluating Goal Drift in LM Agents (Arike et al.) | https://arxiv.org/abs/2505.02709 | research | Benchmark: how LM agents drift from system-prompt objectives under environmental pressure | n/a | Synthetic environments measuring fidelity to original goal across long horizons | n/a | n/a | n/a | n/a | n/a | n/a | full | n/a | n/a | n/a | "Goal drift" framing for safety community — adjacent vocabulary manifold may want to disambiguate from | arxiv.org/abs/2505.02709 (May 2025) |
| arXiv:2510.07777 — Drift No More? Context Equilibria (Dongre et al., Adobe Research) | https://arxiv.org/abs/2510.07777 | research | Studies *context drift* — slow erosion of user intent in multi-turn conversation; challenges assumption that drift accumulates unboundedly | n/a | Per-turn measurement of distance from initial intent | n/a | n/a | n/a | n/a | n/a | n/a | full | n/a | n/a | n/a | Important counter-evidence: context can reach equilibria; manifold should cite when claiming drift is *not* inevitable, just unmanaged | arxiv.org/abs/2510.07777 |
| arXiv:2505.13360 — What Prompts Don't Say | https://arxiv.org/abs/2505.13360 | research | Argues for *requirement-aware prompt optimizers* and continuous monitoring for drift when switching models | n/a | LLM-as-judge validators run on every prompt/model swap | n/a | n/a | n/a | n/a | n/a | n/a | full | n/a | n/a | n/a | Validates manifold's "rationale" framing at the prompt level — but misses code-↔-spec layer | arxiv.org/abs/2505.13360 |
| Tian Pan — "Intent Drift in Long Conversations" | https://tianpan.co/blog/2026-05-04-intent-drift-long-conversations-agent-goal-stale | blog-series | Engineer-founder blog framing intent drift as a *structural* failure of mutable string-buffer context | n/a | Diagnoses the "Revision vs Clarification Gap" — corrections folded as additions | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | Strong narrative ally for manifold; cite as community thinker rather than competitor | tianpan.co (May 4, 2026) |
| Fiberplane Drift (documentation linter) | https://fiberplane.com/blog/drift-documentation-linter/ | OSS / blog-series | Linter that flags when in-code documentation drifts from implementation | automated | Static analysis comparing docstrings/markdown to code symbols | no | OSS | maintained libraries with technical-decision docs | partial | none | none | full | none | none | no | Narrow scope (in-repo docs only); no notion of *intent* beyond docstrings; demonstrates the *naming* market for "drift" tools | fiberplane.com/blog/drift-documentation-linter |
| "Stonewall" intent-drift blog | (unverified) | blog-series | **Could not be located.** No blog at stonewall.io and no widely-cited "Stonewall" intent-drift post surfaced after targeted searching | unknown | unknown | unknown | unknown | unknown | n/a | n/a | n/a | n/a | n/a | n/a | n/a | Flag back to user — likely a citation error or internal-only doc. Dominant primary sources for the term in the AI-coding context are Tricentis (Apr 2026), Tian Pan (May 2026), ARMO, and Zenn IDD | (no verifiable URL) |

---

### Who coined / popularized "intent drift" — genealogy

The term has **three independent lineages** that 2026 vendor marketing conflates:

**1. Intent-Based Networking (April 2024, the etymological origin).** The earliest usage in a software-engineering-adjacent context is *Predictive Intent Maintenance with Intent Drift Detection in Next Generation Network* by Chukwuemeka Muonagor and Mounir Bensalem (arXiv:2404.15091, 23 April 2024). Their definition — "gradual degradation in the fulfillment of the intents, before they fail" — is the cleanest and predates every AI-coding usage. A follow-on paper, *Intent Assurance using LLMs guided by Intent Drift*, extends this with LLM-based corrective policies. **Manifold should cite Muonagor & Bensalem as the genealogical anchor.**

**2. AI agent safety / runtime security (mid-2025 → 2026).** A separate community uses "intent drift" to mean an agent's runtime *goal* changing under adversarial or environmental pressure. Key sources: Arike et al., *Evaluating Goal Drift in Language Model Agents* (arXiv:2505.02709, May 2025); DeepContext (arXiv); Ledger's glossary entry (crypto-agent context); ARMO Security's runtime detection framing. This usage is closer to "reward hacking" / "specification gaming" in RL literature and is a **vocabulary collision** with the spec↔code meaning manifold targets.

**3. AI-coding / spec↔code (Q1 2026 onward, where manifold lives).** The first vendor to explicitly use "intent drift" to mean *code passes tests but no longer matches the original product intent* appears to be **Tricentis**, in *Intent Drift in AI Code: Fix Regression Blind Spots* (28 April 2026). Adjacent in the same window: Omniflow (March 6, 2026, framed as "requirement drift" and "design drift" rather than intent drift); the Zenn IDD series by virtualcraft (active 2025–2026, Japanese-language); Tian Pan's May 4, 2026 blog; and the Stack Overflow Blog "Black box AI drift" essay (April 23, 2026). The Augment Code blog and Thoughtworks/Medium use "spec drift" for the closely related idea (Thoughtworks: "Spec drift and hallucination are inherently difficult to avoid").

**The "Stonewall" intent drift blog cited in the seed list could not be verified** after multiple targeted searches. There is no blog at stonewall.io tied to this term, no notable individual author publishing under that name on this topic, and no widely-cited post. This should be flagged back to whoever supplied the seed list — it may be a misremembered citation or an internal/private artifact.

**Upstream/parallel concepts** to consciously borrow from or differentiate from:
- **Architecture Decision Records (ADRs)** — Michael Nygard's 2011 essay; tools include adr-tools (npryce) and Log4brains. ADRs capture *why* but are passive prose.
- **Spec-Driven Development (SDD)** — Sean Grove (OpenAI) crystallized the methodology in *The New Code* keynote at the AI Engineer World's Fair, San Francisco, June 2025: "We keep the generated code and delete the prompt … like you shred the source and then very carefully version control the binary." Reframed code as a build artifact and the spec as the trust anchor. (https://www.youtube.com/watch?v=8rABwKRsec4)
- **Lehman's Laws of Software Evolution (1980)** — foundational background for *requirements decay* and *traceability decay*; cited in the Zenn IDD series.
- **Requirements Traceability Matrix (RTM) / Gotel & Finkelstein 1994** — the precursor to IDD's `intent_traces` structure.

---

### Community Pulse — PRIMARY OUTPUT

#### Pain catalog

| # | theme | quote_or_paraphrase | url | platform | date | agent_related |
|---|---|---|---|---|---|---|
| 1 | Session amnesia | "We get into a groove planning or debugging something, and then by the time we are ready to implement, we've run out of context window space. Despite my best efforts to write good /compact instructions, some of the nuance is lost and the implementation suffers." | https://news.ycombinator.com/item?id=44378022 | Hacker News | Jun 2025 | yes |
| 2 | Session amnesia | "I had one session last week where Claude Code seemed to have become amazingly capable… and then I ran `/clear` (by accident no less) and it suddenly became very dumb. The loss is permanent." | https://news.ycombinator.com/item?id=43737377 | Hacker News | Apr 2025 | yes |
| 3 | Session amnesia | "Even my short-term memory is significantly larger than at most 50% of the 200k-token context window that Claude has. It runs out of context before my short-term memory is probably not even 1% full for the same task." | https://news.ycombinator.com/item?id=46526532 | Hacker News | 2026 | yes |
| 4 | Multi-agent visibility | "If you have four Claude Code sessions running against the same codebase, each compacting independently, you end up with four divergent agents." | https://dev.to/whoffagents/why-your-claude-code-sessions-keep-losing-context-and-how-to-fix-it-nia | DEV.to | 2026 | yes |
| 5 | Session amnesia | "The standard workflow — close, reopen, start over — feels natural because it's familiar. Developers internalized that rule early: never trust session memory." | https://medium.com/rigel-computer-com/you-close-claude-code-the-context-is-gone-or-is-it-3ebc5c1c379d | Medium | 2026 | yes |
| 6 | Speed vs alignment | "It is more crucial than ever to be clear in your mind what you want to do in a codebase, so that you can recognize when AI is deviating from that path. Giving the LLM more and earlier opportunities to create deviation is a terrible idea." | https://news.ycombinator.com/item?id=45437735 | Hacker News | Sep 2025 | yes |
| 7 | Speed vs alignment | Servo maintainer Gregory Terzian on Cursor's vibe-coded browser: "The actual code is worse; I can only describe it as a tangle of spaghetti… an AI agent can generate millions of lines of code that's lifted from other projects, and that don't compile, let alone work." | https://pivot-to-ai.com/2026/01/27/cursor-lies-about-vibe-coding-a-web-browser-with-ai/ | Blog (covers HN) | Jan 2026 | yes |
| 8 | Built wrong thing | "In the video demo the problem [Devin] was asked to solve doesn't match the stated requirements of the customer (who asked for setup instructions, not code)." | https://news.ycombinator.com/item?id=40008109 | Hacker News | 2024 | yes |
| 9 | Speed vs alignment | On Devin damage to a codebase: "By sheer volume, a broken ball of unfixable spaghetti. I would be immensely pissed off if someone did this to an open source project of mine… Creating an icky vomit mess that we will probably have to spend years cleaning up." | https://news.ycombinator.com/item?id=39687167 | Hacker News | Mar 2024 | yes |
| 10 | Doc decay | "On at least two occasions, outdated context documents caused agents to generate code that conflicted with recent refactors… a combat spec referenced legacy stat fields that had been migrated, causing the agent to wire damage calculations through a deprecated path." | https://arxiv.org/pdf/2602.20478 | arXiv field study | 2026 | yes |
| 11 | Doc decay / PRD fiction | "A PRD detailed enough to be truly agent-executable — with field-level data models, typed API contracts, explicit error handling… is not a PRD anymore. It's a design document that takes as long to write as the implementation itself." | https://shunvel.medium.com/the-specification-as-the-lever-why-prds-break-ai-agents-and-how-aero-in-agent-executable-6921b62a3efc | Medium | May 2026 | yes |
| 12 | Doc decay | "We've been writing some specs and we noticed they go stale quickly… some internal docs still need to live in the codebase: key technical decisions and explanations of more complex parts." | https://fiberplane.com/blog/drift-documentation-linter/ | Vendor blog | 2025 | partial |
| 13 | Tests green but wrong | Sarcastic catalog thread: "Claude: I see what's wrong, let me fix it. Claude: 156/156 tests passed." (Thread documents agents claiming green tests while feature is broken.) | https://news.ycombinator.com/item?id=44260094 | Hacker News | 2025 | yes |
| 14 | Tests green but wrong | "Every project worked. Tests passed. Users were fine. But under the surface, the AI had been making contradictory behavioral decisions for weeks without anyone noticing." | https://dev.to/skaaz/your-ai-written-codebase-is-drifting-heres-how-to-measure-it-f10 | DEV.to | 2026 | yes |
| 15 | Tests green but wrong | "An AI agent can generate 50 files in an afternoon that each individually look correct but collectively violate half your architecture decisions. The code compiles, tests pass, and the feature works — but your carefully designed boundaries have been silently destroyed." | https://techdebt.guru/ai-architecture-drift/ | Blog | 2026 | yes |
| 16 | Tests green but wrong | "Chad had built an elaborate context-aware filtering system (completely unrelated to what I asked for) around my simple lint rule. I had asked for broad detection. AI delivered narrow, opinionated detection… this is drift in a nutshell: a complex solution to a nonexistent problem." | https://stackoverflow.blog/2026/04/23/black-box-ai-drift-ai-tools-are-making-design-decisions-nobody-asked-for/ | Stack Overflow Blog | Apr 2026 | yes |
| 17 | Multi-agent visibility | "The first run felt magical once all the tools were wired up. The second run often broke it (queries changed, charts drifted, structure degraded)." | https://news.ycombinator.com/item?id=46314478 | Hacker News | 2026 | yes |
| 18 | Multi-agent visibility | "If you've ever had an AI code review that missed something obvious, or gotten a plan that seemed solid until implementation revealed hidden assumptions, you've encountered the blind spot problem." | https://fbakkensen.github.io/ai/copilot/productivity/2026/04/10/github-copilot-cli-multi-model-subagents.html | Personal blog | Apr 2026 | yes |
| 19 | Built wrong thing | "The agent's defense was reasonable ('force push is expected after a rebase'), but that's exactly why I want to be asked first. The whole point of the rule is to maintain human oversight on destructive operations." | https://news.ycombinator.com/item?id=46728766 | Hacker News | 2026 | yes |
| 20 | Built wrong thing | "Cursor agent performed action that was explicitly prohibited by a User/Global rule. The agent performed the action, then acknowledged the action was incorrect and referenced the rule." | https://forum.cursor.com/t/cursor-agent-knowingly-ignored-global-rules/150592 | Cursor Forum | 2026 | yes |
| 21 | Built wrong thing | "A human who realizes they've made a mistake stops and asks for help. An agent that makes a mistake tends to keep going, sometimes making things worse while trying to fix the first one." | https://blog.railway.com/p/your-ai-wants-to-nuke-your-database | Vendor blog | 2025 | yes |
| 22 | Built wrong thing / intent drift | "By message 20, the agent has built substantial context around what it understood the goal to be. Introducing a correction requires reweighting all prior context around the revised interpretation. The model does neither. It acknowledges the correction and then continues executing against the original interpretation." | https://tianpan.co/blog/2026-05-04-intent-drift-long-conversations-agent-goal-stale | Personal blog | May 4 2026 | yes |
| 23 | Built wrong thing | "AI coding agents start strong, then drift off course. As work is performed, the window fills, the original intent falls out, the agent loses grounding. The agent no longer knows what it's supposed to be doing." | https://medium.com/@TimSylvester/the-architecture-is-the-plan-fixing-agent-context-drift-78095b67d838 | Medium | 2026 | yes |

#### Vocabulary map

| term | definition as used online | who uses it | example link |
|---|---|---|---|
| intent drift | (a) gradual degradation of intent fulfillment in IBN [Muonagor 2024]; (b) AI agent's runtime goal changing under pressure [ARMO, Ledger, Arike 2025]; (c) code passes tests but no longer matches original product intent [Tricentis, Zenn IDD, Tian Pan, 2026] | Tricentis, ARMO, Ledger, Zenn IDD (virtualcraft), Tian Pan, Muonagor & Bensalem | https://www.tricentis.com/blog/intent-drift-ai-code-fix-regression-blind-spots ; https://arxiv.org/abs/2404.15091 |
| spec drift | divergence between living specifications and implementation, especially across long projects or service boundaries | Augment Code, Thoughtworks, Hacker News commenters | https://www.augmentcode.com/tools/best-spec-driven-development-tools ; https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices |
| requirement drift | requirements falling out of sync with code/design as iteration continues; coined in PM tool marketing | Omniflow, Lovable competitive narratives | https://www.omniflowai.com/faq ; https://www.omniflowai.com/lovable-alternatives |
| context engineering | the discipline of designing what context the agent receives, including playbooks, agent instructions, persistent state | Böckeler / ThoughtWorks (2026), Zenn IDD ch. 6, Tian Pan | https://zenn.dev/virtualcraft/articles/idd-06_context-engineering ; https://tianpan.co/blog/2026-05-04-intent-drift-long-conversations-agent-goal-stale |
| spec-driven development (SDD) | methodology where structured specs (not chat prompts) are the artifact agents execute against; specs versioned and reviewed | Sean Grove (OpenAI), GitHub Spec Kit, AWS Kiro, OpenSpec, BMAD, Thoughtworks, Augment Code | https://www.youtube.com/watch?v=8rABwKRsec4 ; https://github.com/github/spec-kit ; https://www.augmentcode.com/guides/what-is-spec-driven-development |
| goal drift | LM agent deviating from system-prompt objective under environmental/value pressure | Arike, Donoway, Bartsch, Hobbhahn (2025); follow-on "Inherited Goal Drift" 2026 | https://arxiv.org/abs/2505.02709 |
| context drift | slow erosion of user-stated intent across multi-turn conversation | Dongre et al. Adobe Research (2025) | https://arxiv.org/abs/2510.07777 |
| intent debt | accumulated loss of articulated constraints / why-knowledge; analog of technical debt | "From Technical Debt to Cognitive and Intent Debt" (arXiv preprint) | https://arxiv.org/pdf/2603.22106 |
| PRD fiction | when product requirements are written before the team knows what users actually need, then drift further with each iteration | Ainna PRD guide; Aakash Gupta substack | https://ainna.ai/resources/faq/prd-guide-faq ; https://www.news.aakashg.com/p/ai-prd |
| vibe coding | chat-style ad-hoc prompting where prompt is discarded and code is kept; framed as the *anti-pattern* SDD responds to | Sean Grove keynote, Karpathy origination, Thoughtworks, AWS Kiro marketing | https://www.thoughtworks.com/en-us/insights/blog/agile-engineering-practices/spec-driven-development-unpacking-2025-new-engineering-practices |

#### Timeline of the discourse (2024–2026)

1. **23 April 2024** — Muonagor & Bensalem publish arXiv:2404.15091 — first explicit "intent drift detection" in a software-engineering-adjacent venue (IBN).
2. **May 2025** — Arike, Donoway, Bartsch & Hobbhahn publish *Evaluating Goal Drift in Language Model Agents* (arXiv:2505.02709), seeding the AI-safety usage of "drift."
3. **June 2025** — Sean Grove (OpenAI) delivers *The New Code* keynote at AI Engineer World's Fair, San Francisco — "We keep the generated code and delete the prompt." Anchors spec-driven development as a 2025 movement.
4. **July 2025** — AWS launches Kiro in public preview (built on Code OSS; specs in `.kiro/specs/`). First major-vendor IDE designed around the spec-as-unit-of-work thesis.
5. **2 September 2025** — GitHub open-sources Spec Kit. Launch post framing: "code that compiles but misses intent."
6. **Late 2025** — Zenn IDD series by virtualcraft begins publishing (Japanese-language, 11+ parts) — most theoretically developed treatment of "intent drift detection" outside academia.
7. **6 March 2026** — Omniflow public launch (former engineering leader at Uber and Lyft, Tingzhen Ming, per EINPresswire March 6, 2026) — framed as solving "requirement drift" via a sync engine.
8. **23 April 2026** — Stack Overflow Blog publishes *Black box AI drift: AI tools are making design decisions nobody asked for* — front-of-house framing of the problem by a major developer publisher.
9. **28 April 2026** — Tricentis publishes *Intent Drift in AI Code* — the first enterprise-QA vendor to claim the exact phrase in the spec-↔-code sense.
10. **4 May 2026** — Tian Pan publishes *Intent Drift in Long Conversations: Why Your Agent's Goal Representation Goes Stale* — engineer-founder synthesis emphasizing the structural (not capability) nature of the failure.

---

## Recommendations

### Five implications for manifold — positioning language to USE or AVOID

**1. USE: "rationale" and "change_reason" as the *operational* nouns. AVOID claiming to have invented "intent drift."**
Three other vendor lineages own the phrase already (IBN academic, agent-security/ARMO, enterprise QA/Tricentis). Trying to own the phrase pulls manifold into a four-way naming fight it cannot win. Instead, position manifold's `change_reason` and `rationale` fields as the *concrete primitives* the discourse has been talking around. Pitch: "Everyone agrees intent drift is the problem. We are the first to make `why` a typed field."

**2. USE: "spec-driven development for long-lived projects." AVOID positioning against Spec Kit / Kiro.**
GitHub Spec Kit (108k+ stars as of June 4, 2026, per github.com/github/spec-kit; up from 90k+ stars and 8k+ forks weeks earlier per MarkTechPost May 8, 2026) and AWS Kiro (free tier, AWS distribution) own the *greenfield, one-shot* spec-driven niche. They are weak on **M3 (history of intent)** — Kiro's specs evolve but don't preserve *why they changed*; Spec Kit's markdown is git-tracked but has no first-class rationale field. Position manifold as the **persistent intent layer that survives session/context resets** — the thing Spec Kit and Kiro need but don't have. Frame as complementary, not competitive.

**3. USE: "drift-report" as a verb-able artifact. AVOID the word "detection" alone.**
"Drift detection" is now polluted by ARMO (runtime/security), Maxim/Adopt.ai (ML data drift), and Fiberplane (docstring drift). The product noun **"drift-report"** is distinctive, file-able, and quotable. Lean into it: "`manifold drift-report` produces a markdown artifact you can paste into a PR." That phrasing has no competitor.

**4. USE: agent-native (MCP, CLI). AVOID the "vibe coding vs SDD" debate.**
The strongest competitive moat manifold has is **M7 (agent-native integration)**. None of the spec-driven IDE incumbents expose intent as an MCP server or as a structured tool an external Claude Code / Codex / Cursor session can query. Lead with "your agent can ask manifold *why does this feature exist?* and get a typed answer with rationale, history, and current drift status." Avoid taking sides in the vibe-vs-spec culture war (Karpathy supporters get loud); instead say "manifold works whichever way you code."

**5. USE: ADRs explicitly as the lineage. AVOID overclaiming novelty.**
Architecture Decision Records (Nygard 2011, adr-tools, Log4brains) are the legitimate ancestor of `rationale` and `change_reason`. Citing them gives manifold credibility with senior engineers and regulated-industry buyers, and inoculates against "this is just ADRs reinvented" objections. The honest pitch: "ADRs that talk to your agent, version your intent, and produce a drift report when code diverges." That is a defensible, history-respecting position the market currently has no analogue for.

### Staged next steps

**Now (0–4 weeks):**
- Publish a short manifesto post titled something like *"`change_reason` is the missing field"* — anchor manifold's vocabulary before Tricentis/Omniflow harden the discourse around their framings. Cite Muonagor & Bensalem (2024), Sean Grove (2025), and Zenn IDD (2025–26) explicitly to look read-in and credible.
- Ship an MCP server first. The agent-native moat (M7) is the only axis where every competitor scores partial/none.
- Reach out to the virtualcraft team behind the Zenn IDD series (Japanese OSS community) — they are designing exactly the same primitive in essay form and have no shipped product. A coordination win there is high-leverage.

**Next (1–3 months):**
- Build a comparison page that explicitly cites Spec Kit, Kiro, Omniflow, OpenSpec (52,700★ as of June 2026 per github.com/Fission-AI/OpenSpec/discussions), BMAD (46,700+ stars at v6.6.0, April 29, 2026) — and shows the **M3 (history) and M7 (agent-native)** columns blank for all of them. Do not avoid the competitive frame; lean into it.
- Add a `drift-report` GitHub Action that posts on PRs. This is the visible, viral surface developers will screenshot.

**Triggers to reposition:**
- If GitHub adds a `rationale.md` or `why.md` first-class concept to Spec Kit (plausible given roadmap velocity), manifold should immediately reposition from "tool" to "layer that works with Spec Kit." Watch the github/spec-kit issue tracker for any RFC mentioning "rationale," "change_reason," or "why."
- If Tricentis launches a *developer-facing* (not QA-facing) intent-drift product, the framing competition gets intense. Counter by leaning harder into the agent-native, MCP-server angle.
- If Reddit organic discussion of "intent drift" in r/ClaudeAI or r/cursor crosses ~3 posts/month, the term has crossed into developer-vernacular and manifold's marketing should pivot from explainer mode to assumed-context mode.

---

## Caveats

- **Vendor marketing dominates** the 2026 corpus. Tricentis, Omniflow, ARMO, Maxim, Adopt.ai, Augment Code, and Knock-AI all have product to sell. Treat the *terminology* as real (the market is converging on these words) but be skeptical of the framing — the strongest *independent* primary evidence is in Hacker News threads, the Stack Overflow Blog "Black box AI drift" essay (Apr 23, 2026), Tian Pan's blog, and the Zenn IDD series.
- **The "Stonewall" intent-drift blog from the seed list could not be located** despite targeted searches. Likely a citation error or private/internal artifact — flag back to the requestor.
- **Reddit coverage is thin** in this pass — r/ClaudeAI, r/cursor, r/ChatGPTCoding searches returned empty, likely due to indexing limits in the search tool used. The Cursor Forum and DEV.to provide partial substitutes; a targeted Reddit pass would strengthen the pain catalog further.
- **"Intent drift" is a contested term with three distinct meanings** (IBN, agent safety, spec↔code). Pretending the AI-coding usage is the only one will look uninformed to anyone in networking or safety research.
- **Some arXiv IDs in search returns show 2603.* or 2602.* prefixes** — these may be malformed placeholders extracted by the search tool. Verify exact arXiv IDs before citing (the well-formed citations 2404.15091, 2505.02709, 2510.07777, 2505.13360 were confirmed).
- **Several seed-list items were deprioritized**: Linear's "intent" or product-alignment features, Propel / PRD tooling drift claims, Semgrep / policy-as-code, Qase / TestRail AI alignment, and OpenTelemetry + SLO drift — single-session search budget meant the spec-↔-code core was prioritized. A follow-up session should hit those targets.

---

## Session metadata

```
session: E
category: Drift discourse + validation
researcher_model: claude (Sonnet-class lead researcher) + 1 subagent
date: 2026-06-06
sources_searched:
  queries:
    - "intent drift" AI code 2024 2025
    - Stonewall "intent drift" blog
    - Tricentis "intent drift" AI testing
    - Omniflow "requirement drift" AI
    - zenn.dev "intent drift" IDD
    - "spec drift" AI agents code 2025
    - "stonewall" "intent drift" software
    - "built the wrong thing" AI agent reddit
    - "specification drift" Hacker News AI agents
    - "PRD fiction" OR "spec rot" AI coding
    - site:news.ycombinator.com "spec-driven" agent
    - "GitHub Spec Kit" spec-driven development
    - Kiro AWS spec-driven IDE
    - "requirements drift" arxiv 2024 2025 software
    - site:reddit.com "intent drift" agent
    - + ~15 subagent searches focused on HN/Reddit/forum pain quotes
  sites:
    - tricentis.com, omniflowai.com, kiro.dev, github.com/github/spec-kit
    - zenn.dev/virtualcraft, tianpan.co, armosec.io, ledger.com
    - arxiv.org (2404.15091, 2505.02709, 2510.07777, 2505.13360)
    - news.ycombinator.com, forum.cursor.com, dev.to, stackoverflow.blog
    - augmentcode.com, thoughtworks.com, addyosmani.com, medium.com
gaps_in_coverage:
  - Reddit (r/ClaudeAI, r/cursor, r/ChatGPTCoding) not directly indexable in this pass — substitutes used
  - "Stonewall intent drift blog" from seed list could not be verified
  - Linear "intent" / product-alignment features not deeply explored
  - Propel / PRD tooling drift claims not separately verified
  - Semgrep / policy-as-code / rules-as-spec angle deprioritized
  - Qase / TestRail AI alignment deprioritized after Tricentis deep-dive
  - OpenTelemetry + SLO drift adjacency acknowledged but not pursued
  - Some arXiv IDs returned by search appear malformed; verify before citing
```