---
status: historical
study: manifold-landscape-2026-06
session: A
type: session-prompt
tags: [sdd, agent-workflow, spec-kit]
---

# Session A — Spec-driven development & agent workflow tools

**Paste this entire file into a new Claude or ChatGPT chat.** Enable web search / browsing if available.

---

## Your role

You are a landscape research scout. Map tools that use **specifications as the driver for AI-assisted software development** — not generic code completion.

## Problem we care about

Software projects lose their "why" faster than their code. AI agents ship fast but session context resets. We need tools that **sustain queryable intent over months**, not just generate a spec once and implement a feature.

Our reference tool (**manifold**) is a long-lived "project compass": layered spec graph, drift detection, `next-leaves` API. Your job is to find **alternatives and adjacents** in the spec-driven / agent-workflow space.

## Your task

1. Find **8–12 tools or projects** in this category (open source + commercial).
2. Fill one row per tool in the inventory table below.
3. Write a **community pulse** section (HN, Reddit, GitHub discussions, vendor blogs — last 12 months).
4. End with **3 implications for manifold** (what to steal, what gap remains).

## Seed list (expand beyond these)

- GitHub Spec Kit / `specify` CLI
- BMAD Method
- Claude Code superpowers (writing-plans, brainstorming, etc.)
- OpenSpec
- Tessl
- Amazon Kiro
- Amazon Q Developer spec workflows
- Aider / aider-desk conventions
- Cursor rules + plans
- Codex / OpenAI agent workflows with specs
- Agent OS / AGENTS.md patterns
- PRP (Product Requirements Prompt) templates
- Any "constitution → specify → plan → tasks → implement" pipeline

Search GitHub topics: `spec-driven-development`, `spec-driven`, `prd`, `ai-agents`.

---

## Output format — Tool inventory

Produce a markdown table with these columns:

| name | url | one_liner | canonical_store | drift_handling | agent_native | compass_queries | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |

**Column definitions:**
- `canonical_store`: markdown-in-git / DB / ticket-system / vector-memory / hybrid / unknown
- `drift_handling`: none / manual / automated / unknown
- `agent_native`: yes / partial / no
- `compass_queries`: yes / partial / no — can it structurally answer "what should we work on next?"
- `pricing`: free / OSS / freemium / enterprise / unknown
- `sweet_spot`: one-shot feature / long-lived project / enterprise / other
- `M1`–`M7`: full / partial / none / n/a (see master handoff axes)
- `gap_vs_manifold`: 1–2 sentences
- `sources`: comma-separated URLs with dates where possible

---

## Output format — Community pulse

### Pain themes (agents + specs)
5–10 bullets. Each bullet: **theme** + **quote or paraphrase** + **URL** + **approx date**.

### Trending phrases
List phrases people use (intent drift, spec-driven, context engineering, etc.) with 1 example link each.

### Notable threads (3–5)
| title | url | platform | date | summary |

---

## Output format — Session metadata

```
session: A
category: SDD / agent workflow
researcher_model: [your model name]
date: YYYY-MM-DD
sources_searched: [list queries and sites]
gaps_in_coverage: [what you couldn't find]
```

---

## Do NOT

- List Copilot/Cursor/ChatGPT as generic assistants without spec/intent angle
- Include tools with zero public documentation (mark "needs deep pass" instead)
- Confuse **task lists** (Jira/Linear) with **spec graphs**

## DO

- Note GitHub star count and last release date for OSS
- Distinguish "spec at start of feature" vs "spec maintained over project lifetime"
- Call out MCP support explicitly where it exists
