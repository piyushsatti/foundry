---
status: historical
study: manifold-landscape-2026-06
session: D
type: session-prompt
tags: [orchestration, agent-ides, mcp]
---

# Session D — Orchestration & agent IDEs

**Paste this entire file into a new Claude or ChatGPT chat.** Enable web search / browsing if available.

---

## Your role

Landscape scout for **multi-step agent orchestration** and **autonomous coding agent platforms** — tools that dispatch work, not just chat in one session.

## Problem we care about

When multiple agents work in parallel, who holds **project intent**? Orchestrators need a "what's next" surface and drift awareness. We map platforms that **run agents** and whether they **own the spec** or **consume an external spec**.

Our reference: **manifold** holds spec; **orchestrator** (future, this repo) will dispatch; **progress-tracker** holds runtime telemetry. Your job: what do commercial orchestrators do for spec/intent?

## Your task

1. Find **8–12 platforms** (Devin-class, IDE agents, framework orchestrators).
2. Fill inventory table.
3. Community pulse — multi-agent failures, "built wrong thing", oversight gaps.
4. **3 implications for manifold** — integration vs competition.

## Seed list (expand)

- Cognition Devin
- Factory.ai
- Cursor Cloud Agents / Background Agents
- OpenAI Codex (cloud agent)
- Windsurf Cascade / agents
- GitHub Copilot coding agent / workspace agent
- Amazon Q Developer agent modes
- LangGraph / LangSmith agent deployments
- Microsoft AutoGen / Agent Framework
- CrewAI
- SWE-agent / OpenHands / Aider multi-agent forks
- MetaGPT / ChatDev (research + OSS)
- Bolt.new / Lovable / v0 (spec→app, different angle)

Search: "autonomous coding agent 2025", "multi-agent software development", "AI agent orchestration production".

---

## Output format — Tool inventory

| name | url | one_liner | spec_ownership | orchestration_model | human_oversight | agent_native | compass_queries | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |

**Extra columns:**
- `spec_ownership`: internal / external / none / markdown-in-repo
- `orchestration_model`: single long-running agent / multi-agent DAG / human-in-loop tickets
- `human_oversight`: dashboard / PR-only / none documented

---

## Output format — Community pulse

Focus on:
- "Agent built the wrong thing" / misaligned requirements stories
- Trust vs autonomy debates
- Cost of multi-agent runs
- Whether users maintain a spec outside the orchestrator

---

## Session metadata

```
session: D
category: Orchestration / agent IDEs
researcher_model:
date:
sources_searched:
gaps_in_coverage:
```

---

## Do NOT

- Review IDEs without agent/autonomy story (plain VS Code)
- Assume marketing "autonomous" = structured spec management — verify

## DO

- Note if platform integrates Spec Kit, Linear, or custom PRD format
- Capture **session handoff** patterns if documented (like chronicler → orchestrator handoff)
