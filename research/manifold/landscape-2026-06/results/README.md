---
status: complete
study: manifold-landscape-2026-06
type: results-index
tags: [provenance, sessions, calibration]
---

# Pass 1 results — landscape research

Raw outputs from external research sessions. **Study complete.**

| Deliverable | Path |
|---|---|
| Final synthesis | [`../synthesis.md`](../synthesis.md) |
| Study index | [`../README.md`](../README.md) |
| A+E archive draft | [`../synthesis-pass1.md`](../synthesis-pass1.md) |

---

## Session A — SDD / agent workflow

| File | Provider | Model | Date | Rows |
|---|---|---|---|---|
| [`session-A-sdd-claude-2026-06-06.md`](session-A-sdd-claude-2026-06-06.md) | Claude | Sonnet 4.5 class | 2026-06-06 | 14 tools |
| [`session-A-sdd-chatgpt-2026-06-06.md`](session-A-sdd-chatgpt-2026-06-06.md) | ChatGPT | GPT-5.2 Thinking | 2026-06-06 | 11 tools |

**Calibration:** Claude found more OSS long-tail (Superpowers, PRPs, Augment Cosmos). ChatGPT had cleaner clustering and Amazon Q Developer. Both agree: no tool ships graph + drift + next-leaves API.

## Session B — Enterprise ALM / traceability

| File | Provider | Model | Date | Rows |
|---|---|---|---|---|
| [`session-B-alm-claude-2026-06-06.md`](session-B-alm-claude-2026-06-06.md) | Claude | Sonnet 4.5 | 2026-06-06 | 14 tools |

**Claude-only** (per provider pick for B/C/D). No ChatGPT dual-run.

**Key findings:**
- Enterprise ALM (DOORS, Polarion, Jama, Codebeamer, etc.) owns **M1/M2/M3/M6** for regulated industries (~$50–80/user/mo) but is GUI-first, not agent-native
- Only **Jama Connect** explicitly mentions MCP ("product context layer"); **Modern Requirements Copilot4DevOps** closest on chat-with-backlog
- OSS docs-as-code (**Doorstop, Sphinx-Needs, StrictDoc**) has graph/traceability but no MCP, no drift report, no compass
- **No commercial tool** ships real-time code↔requirements drift at manifold's `drift-report` level — confirms gap
- **Adopt from enterprise:** typed link semantics, baselines, ReqIF export as interop bridge
- **Skip for agent era:** review/approval UIs, per-seat licensing tooling, BIRT-style reporting

**Recovery note:** Original drop was `compass_artifact_wf-2770c4f7-...md`; accidentally deleted during migration cleanup (misidentified as Session A duplicate). Restored to `results/` 2026-06-06.

## Session C — Agent memory / context engineering

| File | Provider | Model | Date | Rows |
|---|---|---|---|---|
| [`session-C-agent-memory-claude-2026-06-06.md`](session-C-agent-memory-claude-2026-06-06.md) | Claude | Sonnet 4.5 | 2026-06-06 | 18 tools |

**Claude-only** (per provider pick for B/C/D). No ChatGPT dual-run.

**Key findings:**
- Two memory lineages don't talk: **conversational facts** (mem0, Zep/Graphiti, Letta, Cognee) vs **convention files** (CLAUDE.md, AGENTS.md, Cline Memory Bank)
- **AGENTS.md** won the convention war (60k+ repos, Linux Foundation AAIF Dec 2025); all convention files lack M3/M4/M5 for project intent
- **Spec Kit** + **Git Context Controller** (arXiv) closest to typed intent — still flat Markdown, no drift detection
- **Zero of 18 tools** ship drift detection between declared intent and current code
- **Manifold positioning:** typed WHY graph + drift layer **above** AGENTS.md (export/compile), not replacement; integrate don't compete with mem0/Zep for user facts
- **Adjacent (code graph, not intent):** Serena, codebase-memory-mcp — know WHAT code is, not WHY

## Session D — Orchestration / agent IDEs

| File | Provider | Model | Date | Rows |
|---|---|---|---|---|
| [`session-D-orchestration-claude-2026-06-06.md`](session-D-orchestration-claude-2026-06-06.md) | Claude | Sonnet-class | 2026-06-06 | 14 platforms |

**Claude-only** (per provider pick for B/C/D). No ChatGPT dual-run.

**Key findings:**
- Market bifurcated: **delivery platforms** (Devin, Factory, Cursor, Codex, Copilot) hold intent as prompt/ticket vs **framework runtimes** (LangGraph, MAF, CrewAI) hold no spec
- **Only Kiro + Augment Intent** own spec internally; everyone else uses AGENTS.md / Linear / chat prompt
- **MCP is table stakes** on all commercial platforms — manifold's integration path is the MCP slot, not competing with orchestrators
- Converging model: **coordinator + specialist subagents on git worktrees** — shared intent layer increasingly external
- **MAST taxonomy:** 41%–86.7% multi-agent failure rates; "disobey task specification" top category
- **Direct competitors:** Kiro (flat 3-doc spec), Augment Intent (living spec, proprietary); manifold differentiates on **M2 graph + M7 MCP-native spec exposure**
- **Orchestrator role for manifold:** intent-broker via MCP, not replacement orchestrator

## Session E — Drift discourse + validation

| File | Provider | Model | Date | Rows |
|---|---|---|---|---|
| [`session-E-drift-claude-2026-06-06.md`](session-E-drift-claude-2026-06-06.md) | Claude | Sonnet-class + subagent | 2026-06-06 | 15 tools/methods |
| [`session-E-drift-chatgpt-2026-06-06.md`](session-E-drift-chatgpt-2026-06-06.md) | ChatGPT | GPT-5.2 Thinking | 2026-06-06 | 12 tools |

**Calibration:**

| Signal | Claude | ChatGPT |
|---|---|---|
| **Unique finds** | Zenn IDD deep-dive, ADR-tools/Log4brains, Fiberplane Drift, arXiv lineage (2404.15091 et al.), 23+ pain quotes | Roady, RealityCheck, PAAD, drift-detect, drift-analyzer, ReqToCode, R2Code |
| **Stonewall blog** | Could **not** verify initially | Cites as May 2026 popularizer |
| **Terminology** | Three lineages (IBN / agent safety / spec↔code) | Coinage vs popularization timeline |
| **Agreement** | Problem real, worsening; no one owns `change_reason` + rationale history; lead with operational drift-report | Same; differentiate from validators by owning rationale not alignment |

**Stonewall resolution:** Independently verified at [stonewall.dev/blog/intent-drift](https://stonewall.dev/blog/intent-drift/) (May 20, 2026). Safe to cite in synthesis.

**Directional (ChatGPT-only, not repo-verified):** Roady, RealityCheck, PAAD, drift-detect, drift-analyzer — capability ratings from Session E; treat as hypotheses until primary-source read during product work.

**Closest OSS adjacents (merge both):** Roady (ChatGPT), Zenn IDD philosophy (Claude), RealityCheck, OpenSpec (M3 via changes/), Spec Kit, Kiro.

## Pass 1 progress

| Session | Claude | ChatGPT | Status |
|---|---|---|---|
| A — SDD / agent workflow | ✅ | ✅ | Complete |
| B — Enterprise ALM | ✅ | n/a | Complete |
| C — Agent memory | ✅ | n/a | Complete |
| D — Orchestration | ✅ | n/a | Complete |
| E — Drift discourse | ✅ | ✅ | Complete |

**All sessions merged** into [`../synthesis.md`](../synthesis.md). Study closed — see [`../README.md`](../README.md).

## Cross-session agreement (all five)

- No tool ships **graph + drift + next-leaves API** together
- **M4 (drift) + M5 (compass)** consistently unowned across SDD, ALM, memory, orchestration, and discourse sessions
- **MCP** is the integration surface; **AGENTS.md** is the convention layer manifold should compile to
- **Spec Kit + Kiro + Augment Intent** recur as closest adjacents; manifold differentiates on typed graph + MCP-native spec + drift-report

## Provider note

Sessions A and E were dual-run (Claude + ChatGPT) for calibration. Sessions B, C, D were Claude-only per provider pick documented in [`../synthesis-pass1.md`](../synthesis-pass1.md) calibration notes.
