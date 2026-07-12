# Manifold human-comprehension redesign plan

**Status:** planned  
**Created:** 2026-06-15  
**Scope:** documentation, presentation surfaces, skill routing, evals, and validation for making Manifold easier for humans to understand without weakening its graph/API core.

---

## Executive summary

Manifold is structurally strong for agents: it has a durable SQLite intent graph, revision history, `next-leaves`, `spec-audit`, `drift-report`, trajectory preview/apply, MCP tools, and HTML/Markdown/JSON presentation surfaces.

The remaining product risk is human comprehension. Humans should not have to understand the internal graph, all MCP surfaces, or drift/status subtleties before they can answer basic questions:

| Human question | Desired first answer | Deeper surface |
|---|---|---|
| What is this project? | Short purpose, current state, links | Project graph, node list |
| Where are we? | Status brief with headline, timestamp, blockers, drift caveats | Full status brief JSON/HTML |
| What is blocked? | Risk/blocked list with evidence state | Drift report, blockers graph |
| What should happen next? | Ready frontier work, not priority ranking | `next-leaves`, delivery view |
| Can I trust this? | Violated, errored, unverified, satisfied counts | Verdict details, `spec-audit`, check evidence |
| What will change if we accept this? | Trajectory preview before mutation | Full trajectory leg list |

The redesign principle is **projection-first, graph-canonical**:

| Layer | Rule |
|---|---|
| Canonical truth | SQLite graph, revisions, verdict fields, target statuses |
| Agent contract | MCP JSON and structured view-models |
| Human presentation | HTML, Markdown, diagrams, mindmaps, summaries, URLs |
| Safety rule | Renderers format semantics; they do not invent semantics |

This plan builds on shipped Topic K human output. It does not replace the existing graph, MCP server, or status brief. It turns the research and critique into a phased execution contract.

---

## Evidence posture

All claims in this work should use evidence levels.

| Level | Meaning | Allowed language |
|---|---|---|
| High | Supported by local implementation/docs and external research or product precedent | "Manifold supports..." / "This design follows..." |
| Medium | Supported by external pattern precedent, but not yet validated on Manifold users | "This should improve..." |
| Low | Plausible product hypothesis | "We believe..." |
| Unknown | No current evidence | "Needs validation..." |

### Claims we can make now

| Claim | Evidence level | Basis |
|---|---:|---|
| Manifold has a canonical graph and human projections should not become truth | High | [`human-presentation.md`](human-presentation.md), [`glossary.md`](glossary.md) |
| Status and verdicts are independent axes | High | [`verdicts.md`](../../bundles/manifold/skills/manifold/references/verdicts.md), [`SKILL.md`](../../bundles/manifold/skills/manifold/SKILL.md) |
| Trajectory supports preview before graph mutation | High | [`trajectory.md`](../../bundles/manifold/skills/manifold/references/trajectory.md), [`glossary.md`](glossary.md) |
| Progressive disclosure is appropriate for Manifold's complexity | Medium | NN/g progressive disclosure, existing human-output research |
| Role-specific summaries should improve human comprehension | Medium | NN/g heuristics, Diataxis, Topic K research |
| Bounded diagrams can help; whole-graph diagrams are risky | Medium | Topic K human-output research, Mermaid edge-limit findings |
| Manifold has audit-friendly traceability primitives | Medium | Revision history, `change_reason`, verdicts, GitLab requirements precedent |

### Claims we cannot make yet

| Avoid | Replace with | Why |
|---|---|---|
| Manifold is compliance-ready | Manifold has audit-friendly traceability primitives | Real compliance needs controls, approvals, retention, auth/RBAC, domain standards |
| The redesign proves ROI | The redesign may reduce reorientation cost; validation required | No Manifold-specific ROI study yet |
| Status brief proves the project is healthy | Status brief summarizes current graph and evidence state | Unverified/errored/stale data must remain visible |
| `next-leaves` prioritizes work | `next-leaves` identifies graph-ready frontier work | No value/effort/roadmap priority field exists |
| Graph visualization makes the project understandable | Bounded projections can answer specific questions | Full-graph views can become hairballs |
| Onboarding time is reduced | Onboarding-time reduction is a validation target | Needs first-five-minutes testing |

---

## Research foundation

### Local Manifold evidence

| Source | Supports | Design implication |
|---|---|---|
| [`human-presentation.md`](human-presentation.md) | Graph is authoritative; diagrams, mindmaps, HTML, chat summaries are projections | Keep one canonical graph and one view-model per surface |
| [`glossary.md`](glossary.md) | DB-canonical model, trajectory vocabulary, target status, verdict terms | Add human/API terminology crosswalk rather than renaming internals blindly |
| [`how-to-use.md`](how-to-use.md) | Chat-first compass questions and spec-audit vs drift-report split | First-run docs should start from questions, not commands |
| [`../../bundles/manifold/skills/manifold/references/verdicts.md`](../../bundles/manifold/skills/manifold/references/verdicts.md) | `violated`, `errored`, `unverified`, `satisfied`; `--repo`/`project_root`; layer and branch caveats | Risk views must show unknowns and broken checks, not only violations |
| [`../../bundles/manifold/skills/manifold/references/trajectory.md`](../../bundles/manifold/skills/manifold/references/trajectory.md) | `propose` and `show` are non-mutating; `accept` mutates; impact preview includes `next_leaves_after` | Human trajectory view must foreground mutation boundary |
| [`../../research/manifold/human-output-2026-06/synthesis.md`](../../research/manifold/human-output-2026-06/synthesis.md) | Deterministic `status-brief`, generated timestamps, JSON/HTML/Markdown parity, bounded diagrams | Start with one reliable brief and deepen via links |
| [`../../research/manifold/landscape-2026-06/synthesis.md`](../../research/manifold/landscape-2026-06/synthesis.md) | Market gap around graph + drift + compass + MCP; provenance caveats | Keep positioning calibrated and avoid overclaiming category ownership |
| [`todo.md`](todo.md) | Topic K shipped, risk-brief and full timelines deferred | Treat this redesign as the next validation/productization layer |

### External evidence and product precedents

| Source | Link | Supported principle | Limit |
|---|---|---|---|
| NN/g progressive disclosure | <https://www.nngroup.com/articles/progressive-disclosure/> | Show core answers first; defer advanced graph/API controls | Correct primary/secondary split still requires task analysis |
| NN/g usability heuristics | <https://www.nngroup.com/articles/ten-usability-heuristics/> | Status visibility, real-world language, recognition over recall, user control, error prevention | Heuristics do not prove Manifold-specific outcomes |
| Microsoft Guidelines for Human-AI Interaction | <https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/> | Calibrated trust, human control, AI failure handling, transparency | General HAI guidelines, not Manifold-specific validation |
| Diataxis | <https://diataxis.fr/> | Separate tutorial, how-to, reference, and explanation docs by user need | Documentation framework, not UI validation |
| Terraform `plan` | <https://developer.hashicorp.com/terraform/cli/commands/plan> | Preview proposed changes before applying them | Terraform state is more deterministic than spec intent |
| Terraform `apply` | <https://developer.hashicorp.com/terraform/cli/commands/apply> | Separate planning from execution with approval gates | Saved-plan semantics do not map one-to-one to Manifold trajectories |
| GitLab Requirements | <https://docs.gitlab.com/user/project/requirements/> | Long-lived requirements, satisfaction state, import/export, CI evidence | Does not make Manifold compliance-ready |

---

## Stakeholder matrix

| Stakeholder | Primary question | Human need | Agent/API need | Evidence level | Main caveat |
|---|---|---|---|---:|---|
| Business stakeholder | Are we on track? | Headline, blockers, recent changes, stale warning | Stable status summary | Medium | ROI and decision-quality impact unproven |
| Engineering | What should I build next? | Ready work, blockers, rationale, verification state | `next-leaves`, verdicts, node details | High | Must not call frontier work priority |
| Product owner | What changed and what is at risk? | Status, deltas, decision points, roadmap context | Structured state, target changes | Medium | Decision-needed workflow is not fully modeled |
| AI orchestrator | What is safe to dispatch? | Minimal human summary | Canonical graph, JSON, revision IDs, verdicts | High | Humans need projections; agents need exact contracts |
| Docs steward | Where does each concept belong? | Clear IA, glossary, doc routing | Stable reference links | High | Current docs can mix tutorial/how-to/reference/explanation |
| Solo builder/new user | What do I do first? | Low-jargon first path and examples | Defaults and compact commands | Medium | Onboarding-time benefit needs testing |
| Enterprise/compliance | Can this support audit conversations? | Traceability, revisions, evidence, exports | Revision history, `change_reason`, verdict evidence | Medium/Low | Not compliance-ready without controls |
| Engineering manager | What is blocked across projects? | Portfolio/blocker rollup | Cross-project edges, portfolio report | Medium | Risk of becoming a second planning system |
| Investor/strategy | Is there a wedge? | Positioning, category map, evidence confidence | Not central | Low | Buyer urgency and market adoption unproven |
| Maintainer | Can we improve UX without scope explosion? | Tight contracts and deferred scope | One builder, multiple renderers | High | Too many views can fragment product semantics |
| Security/risk reviewer | Where can this lie? | Unknowns, stale data, check failures, LLM caveats | Explicit buckets and evidence | High | Summaries must not hide unverified/errored state |
| Designer/UX | How should humans parse this? | Progressive disclosure, plain language, bounded visuals | View-model semantics | High | Graph visuals must be scoped to questions |
| QA/verification | What is actually verified? | Violated/errored/unverified/satisfied details | Verdict mechanisms and evidence | High | `achieved` is not the same as `satisfied` |
| Support/customer success | How do we explain Manifold? | Simple answer paths and supportable examples | Stable docs and URLs | Medium/Low | Support needs real user confusion data |

---

## Design principles

| Principle | Rule | Enforcement |
|---|---|---|
| Graph-canonical | SQLite graph remains source of truth | Human surfaces render view-models only |
| JSON-first for agents | Agents consume MCP JSON, not HTML | Skill routing and evals |
| Human-first entry | First surfaces answer human questions, not internal architecture | `how-to-use.md`, status brief |
| Progressive disclosure | Show headline, status, risk, and links first; defer raw graph | Status/risk/delivery views |
| Explicit uncertainty | Show `generated_at`, stale warning, unverified and errored counts | View-model schema and tests |
| Two-axis truth | Explain `target_status` separately from verdict evidence | Glossary, risk view, evals |
| Preview before mutation | Multi-leg trajectory changes require preview before accept | Trajectory docs and skill evals |
| Bounded visuals | Diagrams answer specific questions and have hard caps | Presentation registry and docs |
| Claim discipline | Mark hypotheses and avoid compliance/ROI overclaims | Docs and evals |
| Smallest useful views | Each view answers one primary question | Phase gates |

---

## Target view system

| View | Primary question | Audience | Canonical input | Output surfaces | Priority |
|---|---|---|---|---|---:|
| Status brief | Where are we? | Everyone | Graph, targets, drift summary, recent changes | MCP JSON, HTML, Markdown | P0 |
| Risk brief | Can I trust this? | QA, security, leads | Verdict buckets, stale validation, status/verdict mismatches | MCP JSON, HTML, Markdown | P1 |
| Delivery view | What is ready next? | Engineers, orchestrators | `next-leaves`, blockers, verdicts, rationale | MCP JSON, HTML, Markdown | P1 |
| Trajectory preview | What will change? | Maintainers, product, agents | Draft trajectory legs and impact preview | MCP JSON, HTML, Markdown | P1 |
| Traceability projection | What evidence supports this requirement? | Compliance, QA, enterprise | revisions, rationale, parents, verdicts, external refs | JSON, Markdown/CSV later | P2 |

---

## Phase plan

### Phase 0: Research and decision document

**Goal:** Create the durable research/outcomes doc before product behavior changes.

| Research topic | Questions |
|---|---|
| Human comprehension failure modes | Which Manifold concepts are exposed too early? |
| Evidence-backed design | Which recommendations are supported by UX/HCI/product precedent? |
| Stakeholder needs | Which users need human summaries vs agent contracts? |
| Claim discipline | Which claims are proven, plausible, or unsupported? |

| Todo | Output | Done |
|---|---|---|
| P0.1 Create this plan doc | `human-comprehension-redesign-plan.md` | [x] |
| P0.2 Add local evidence table | Traceable evidence anchors | [x] |
| P0.3 Add external evidence table | Research/product precedents | [x] |
| P0.4 Add evidence-rated stakeholder matrix | Role-specific needs | [x] |
| P0.5 Add claims to make/avoid | Claim discipline | [x] |
| P0.6 Link from docs index and presentation docs | Discoverability | [x] |
| P0.7 Track plan in `todo.md` | Execution visibility | [x] |

**Acceptance gate:** A future agent can implement the redesign from this doc without relying on chat memory.

### Phase 1: Terminology and information architecture

**Goal:** Make Manifold understandable without renaming canonical internals prematurely.

| Research topic | Questions |
|---|---|
| Vocabulary mismatch | Which terms are precise for agents but confusing for humans? |
| Alias strategy | Which human labels can sit above canonical API names? |
| Diataxis docs split | Which docs are tutorial, how-to, reference, or explanation? |
| Recognition over recall | What should be visible instead of remembered? |

| Canonical term | Human-facing label | Rule |
|---|---|---|
| `node` | spec item / requirement / project item | Keep API term; explain in glossary |
| `next-leaves` | ready next work | Never imply priority |
| `target_status` | planned/in-progress/done state | Explain separately from verdict |
| `verdict` | evidence check result | Use plain examples |
| `drift-report` | code/spec evidence report | Show caveats and buckets |
| `trajectory` | proposed change plan | Tie to preview/apply |
| `leg` | proposed change step | Advanced docs only |
| `spec-audit` | spec history audit | Distinguish from drift-report |

| Todo | Output |
|---|---|
| P1.1 Audit `how-to-use.md` for jargon-first explanations | IA gap list — done |
| P1.2 Audit `glossary.md` for human/API wording gaps | Crosswalk candidates — done |
| P1.3 Add human terms vs API terms table to glossary | Terminology contract — done |
| P1.4 Update first-run docs to start from questions, not commands | Better onboarding — done |
| P1.5 Add explicit `next-leaves` readiness caveat | Accuracy — done |
| P1.6 Add explicit status/verdict independence examples | Accuracy — done |
| P1.7 Add "Which doc should I read?" table | Navigation — done |

**Acceptance gate:** A new user can choose the right Manifold doc in under one minute.

### Phase 2: Default human status brief

**Goal:** Make "Where are we?" answerable from one trusted surface.

| Research topic | Questions |
|---|---|
| Status visibility | What must appear above the fold? |
| Trust calibration | How do timestamps, stale warnings, and unknowns appear? |
| View-model architecture | How do we prevent HTML from becoming truth? |
| Product precedent | What can be borrowed from status pages, project updates, and CI summaries? |

| Target field | Purpose |
|---|---|
| `generated_at` | Prevent stale authoritative-looking pages |
| `project_label` | Avoid raw IDs as primary human labels |
| `overall.headline` | One-sentence answer |
| `overall.status` | Small fixed vocabulary |
| `blocked[]` | Immediate risk visibility |
| `in_flight[]` | Current work |
| `shipped[]` | Progress evidence |
| `at_risk[]` | Drift, blockers, stale status |
| `changes_since[]` | Recent deltas |
| `drift_summary` | Link to deeper evidence |
| `unverified_count` | Prevent false confidence |
| `errored_count` | Prevent false confidence |
| `links` | Deep links to graph, drift, and spec audit |

| Todo | Output |
|---|---|
| P2.1 Audit `packages/manifold/manifold/status_brief.py` against target fields | Gap list |
| P2.2 Audit HTML `/projects/<id>/brief` and MCP `peek_status_brief` | Surface parity list |
| P2.3 Document `status-brief.v1` view-model schema | Contract |
| P2.4 Ensure one builder feeds JSON, HTML, and Markdown | Projection safety |
| P2.5 Ensure violated, errored, unverified, satisfied are visible | Trust |
| P2.6 Ensure stale warning and generated timestamp are visible | Trust |
| P2.7 Add/refresh golden fixture tests | Regression safety |
| P2.8 Add example status brief to docs | Human comprehension |

**Acceptance gate:** A human can answer "where are we?" without reading raw node lists, and unknowns are not hidden.

### Phase 3: Risk and verification view

**Goal:** Make "Can I trust this?" answerable without conflating progress status and evidence.

| Research topic | Questions |
|---|---|
| Verification semantics | How should Manifold explain status vs verdict? |
| False confidence | Where might no violations be misread as all clear? |
| QA workflows | What does QA need from drift-report, spec-audit, and checks? |
| Human-AI safety | How should AI-generated summaries surface uncertainty? |

| Section | Contents |
|---|---|
| Critical mismatches | `violated` verdicts |
| Broken checks | `errored` verdicts |
| Unknowns | `unverified` realization nodes |
| Manual signoffs | `human_signoff` nodes |
| LLM judge caveats | Judge setup and failure modes |
| Status mismatch | Achieved but violated, or not achieved but satisfied |
| Next verification actions | Specific recommended follow-ups |

| Todo | Output |
|---|---|
| P3.1 Define `risk-brief.v1` view-model | Contract |
| P3.2 Add status/verdict independence examples | Docs |
| P3.3 Add "no violations is not all clear" language | Safety |
| P3.4 Group view by violated/errored/unverified/satisfied | Human scan |
| P3.5 Add tests for achieved-but-violated and satisfied-but-not-achieved cases | Regression safety |
| P3.6 Add evals preventing all-clear overclaims | Skill safety |
| P3.7 Add Markdown output suitable for PR/CI summaries | Workflow integration |

**Acceptance gate:** A user cannot miss material unknowns, broken checks, or status/evidence mismatches.

### Phase 4: Delivery and engineering view

**Goal:** Make "What should we work on next?" useful for engineers while preserving `next-leaves` semantics.

| Research topic | Questions |
|---|---|
| Frontier vs priority | How do we explain readiness without implying roadmap priority? |
| Engineering context | What details does an engineer need before dispatching work? |
| Agent handoff | What JSON must an orchestrator consume? |
| Blocker visibility | How do cross-project blockers affect readiness? |

| Field | Purpose |
|---|---|
| `ready_next[]` | `next-leaves` frontier |
| `excluded[]` | Why items are not ready |
| `blocked_by[]` | Local and cross-project blockers |
| `computed_verdict_status` | Optional repo-backed evidence |
| `stored_verdict_status` | Last persisted evidence |
| `rationale` | Why this node exists |
| `parents` | Context |
| `suggested_commands` | CLI/MCP next steps |

| Todo | Output |
|---|---|
| P4.1 Define delivery view-model | Contract |
| P4.2 Include `next-leaves` with plain-language readiness explanation | Human clarity |
| P4.3 Include excluded items and reasons | Debuggability |
| P4.4 Include cross-project blockers | Portfolio awareness |
| P4.5 Include verdict status when `project_root` is available | Evidence |
| P4.6 Add tests for blocked and excluded frontier nodes | Regression safety |
| P4.7 Add engineer workflow docs | How-to |
| P4.8 Add skill routing examples for "what should I build next?" | Agent behavior |

**Acceptance gate:** Engineers get exact work candidates with reasons, and the view never calls frontier work priority unless prioritization fields exist.

### Phase 5: Change proposal and trajectory human view

**Goal:** Make "What will change if we accept this?" clear before graph mutation.

| Research topic | Questions |
|---|---|
| Plan/apply trust | What Terraform-style concepts map cleanly to Manifold? |
| Preview safety | What must be visible before accepting a trajectory? |
| Human review | How should proposed graph changes be summarized? |
| User control | How does the user reject, defer, or partially accept safely? |

| Section | Purpose |
|---|---|
| Target brief | Desired to-be state |
| Proposed changes | Human-readable leg list |
| Impact preview | Nodes touched, status changes, next leaves after |
| Risk flags | Dangerous or broad changes |
| Review checklist | What user should inspect |
| Accept/reject path | Clear next action |
| Partial accept caveat | Preview may differ if only a subset is accepted |

| Todo | Output |
|---|---|
| P5.1 Audit current `trajectory show` output | Gap list |
| P5.2 Define human trajectory preview format | Contract |
| P5.3 Make non-mutating propose/show and mutating accept prominent | Trust |
| P5.4 Add before/after summary for target statuses | Reviewability |
| P5.5 Show `next_leaves_after` with caveat | Accuracy |
| P5.6 Add partial-accept warning | Accuracy |
| P5.7 Add evals for no mutation before accept | Safety |
| P5.8 Add docs comparing to Terraform `plan`/`apply` | Mental model |

**Acceptance gate:** A human can review trajectory impact without inspecting raw JSON, and assistants never apply a multi-leg trajectory without preview.

### Phase 6: Compliance and traceability projection

**Goal:** Support audit-friendly workflows without claiming full compliance readiness.

| Research topic | Questions |
|---|---|
| Traceability | Which Manifold fields support lineage and evidence? |
| Compliance limits | What is missing for regulated use? |
| Export | What lightweight formats help reviewers? |
| Permissions | What auth/access gaps block compliance claims? |

| Section | Purpose |
|---|---|
| Spec item | Human-readable node |
| Rationale | Why it exists |
| Change history | Revisions and `change_reason` |
| Parent/child links | Trace |
| Evidence/verdict | Verification state |
| External refs | Jira, Linear, GitHub, ReqIF future |
| Gaps | Missing evidence or signoff |
| Export | JSON, Markdown, CSV, ReqIF later |

| Todo | Output |
|---|---|
| P6.1 Define "audit-friendly, not compliance-ready" language | Claim discipline |
| P6.2 Identify schema fields needed for traceability export | Gap list |
| P6.3 Add traceability projection spec | Contract |
| P6.4 Add export format proposal | Future implementation |
| P6.5 Add missing controls list: auth, RBAC, signatures, retention, approvals | Compliance caveats |
| P6.6 Add GitLab Requirements and ALM references | Evidence |
| P6.7 Add tests for revision/change_reason visibility | Regression safety |
| P6.8 Add "how to hand this to a reviewer" docs | Human workflow |

**Acceptance gate:** The projection helps audit conversations while explicitly documenting missing compliance controls.

### Phase 7: Skill routing, evals, and agent safety

**Goal:** Make agents use the new human surfaces correctly and avoid unsafe summaries.

| User asks | Route |
|---|---|
| What is this project? | Status brief plus project summary |
| Where are we? | Status brief |
| What is blocked? | Risk brief or delivery view |
| What should I build next? | Delivery view / `next-leaves` |
| Does code match spec? | Drift report / risk brief |
| What changed? | Status brief `changes_since` |
| Can I trust this? | Risk brief |
| Show me the plan before applying | Trajectory preview |
| Is this compliant? | Traceability projection plus caveats |

| Todo | Output |
|---|---|
| P7.1 Update `bundles/manifold/skills/manifold/SKILL.md` routing table | Skill behavior |
| P7.2 Add human summary + URL + caveats response pattern | Chat safety |
| P7.3 Add eval for status/verdict distinction | Eval |
| P7.4 Add eval for unverified/errored not all-clear | Eval |
| P7.5 Add eval for `next-leaves` not priority | Eval |
| P7.6 Add eval for trajectory preview before accept | Eval |
| P7.7 Add eval for compliance caveat | Eval |
| P7.8 Add eval for JSON-first agent consumption | Eval |
| P7.9 Run skill manifest validation | Verification |
| P7.10 Update skill docs links to new plan | Discoverability |

**Acceptance gate:** Agent behavior matches routing, and evals reject dangerous overclaims.

### Phase 8: UX validation and dogfood

**Goal:** Prove or disprove the human-comprehension claims before making stronger product claims.

| Research topic | Questions |
|---|---|
| First-five-minutes test | Can a new user understand Manifold quickly? |
| Task comprehension | Can users answer real questions faster and more accurately? |
| Role fit | Which views help which stakeholders? |
| Dogfood metrics | Does this reduce reorientation cost in Foundry work? |

| Validation task | Success metric |
|---|---|
| What is this project? | Correct answer in under 2 minutes |
| Where are we? | Correct status and top risk in under 2 minutes |
| What is blocked? | Correct blocker identified |
| What should happen next? | User distinguishes ready frontier from priority |
| Can we trust this? | User notices unverified/errored caveats |
| What will this trajectory change? | User identifies mutation boundary |

| Todo | Output |
|---|---|
| P8.1 Create first-five-minutes test script | Validation protocol |
| P8.2 Create before/after task set | Comparison |
| P8.3 Dogfood on `ai-foundry` Manifold project | Real use |
| P8.4 Record time-to-answer and wrong-answer rate | Metrics |
| P8.5 Record points of confusion | UX backlog |
| P8.6 Update confidence levels in this plan | Evidence update |
| P8.7 Decide which low-confidence claims can be upgraded | Product claims |
| P8.8 Add follow-up todos to `todo.md` | Roadmap |

**Acceptance gate:** Confidence levels are updated based on observed evidence, not assumed benefit.

---

## Recommended ordering

| Order | Phase | Why |
|---:|---|---|
| 1 | Phase 0 | Captures research and prevents undocumented drift |
| 2 | Phase 1 | Fixes language before surfaces multiply |
| 3 | Phase 2 | Highest user value: "Where are we?" |
| 4 | Phase 3 | Prevents false confidence |
| 5 | Phase 4 | Improves engineer and agent workflows |
| 6 | Phase 5 | Makes graph mutation safer |
| 7 | Phase 7 | Teaches agents to use surfaces correctly |
| 8 | Phase 8 | Validates claims |
| 9 | Phase 6 | Useful, but avoid compliance overreach until basics are clear |

---

## Risks and controls

| Risk | Control |
|---|---|
| Human views become second source of truth | One builder returns dict; renderers only format |
| Simplified language loses precision | Glossary crosswalk preserves canonical terms |
| Status brief hides unknowns | Always show stale, unverified, and errored indicators |
| `next-leaves` mistaken for priority | Human label = ready next work; add caveat |
| Compliance claims overreach | Use audit-friendly primitives; list missing controls |
| Diagram hairball | Hard cap graph projections; no full-graph Mermaid |
| Agent scrapes HTML | MCP/JSON view-models are canonical |
| Scope explosion | Each view answers one primary question |
| User trust exceeds evidence | Add generated timestamps, stale warnings, uncertainty labels |
| Evals only test routing | Add comprehension and overclaim-prevention evals |

---

## Definition of done

| Area | Done means |
|---|---|
| Documentation | This research-backed plan is linked from Manifold docs |
| Language | Human/API terminology split is documented |
| Status | One default status brief answers "where are we?" with caveats |
| Risk | Unknown/errored/unverified states are impossible to miss |
| Delivery | Engineers can see ready frontier work without priority confusion |
| Trajectory | Humans can preview before mutation |
| Agents | Skill routing uses JSON views and avoids overclaims |
| Validation | Dogfood/usability results update confidence levels |

---

## First execution slice

The smallest useful slice is documentation-only:

| Step | Work | State |
|---:|---|---|
| 1 | Create this plan doc | Done |
| 2 | Link it from `docs/manifold/README.md` | Done |
| 3 | Link it from `docs/manifold/human-presentation.md` | Done |
| 4 | Track it in `docs/manifold/todo.md` | Done |
| 5 | Review before product/code changes | Done via subagent review |

After this slice, implementation should start at Phase 1 and proceed through the acceptance gates above.
