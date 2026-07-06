---
status: historical
study: manifold-landscape-2026-06
session: C
type: session-prompt
tags: [agent-memory, agents-md, context-engineering]
---

# Session C — Agent memory & context engineering

**Paste this entire file into a new Claude or ChatGPT chat.** Enable web search / browsing if available.

---

## Your role

Landscape scout for **persistent memory and context engineering** for AI coding agents — the layer that tries to solve "agent forgets everything when session ends."

## Problem we care about

Agents produce code fast but **session context resets**. CLAUDE.md and NOTES.md help but don't give structured, queryable project intent. We need to map **memory solutions** and assess: do they store **facts**, **conventions**, or **structured requirements**?

Our reference: **manifold** = typed external memory for **project intent** (graph + revisions + drift), not freeform RAG facts.

## Your task

1. Find **8–12 tools/projects** (OSS repos, MCP servers, commercial memory APIs).
2. Fill inventory table.
3. Community pulse on context engineering discourse (Anthropic blog, practitioner posts).
4. **3 implications for manifold** — overlap with memory layer vs distinct compass layer.

## Seed list (expand)

- Anthropic memory tool / Claude Projects memory
- Cursor rules, skills, AGENTS.md, .cursorrules
- mem0 / mem0ai
- Zep
- Graphiti / graph memory
- Cline memory patterns
- Git Context Controller (GCC) — arxiv + any implementations
- DeepCode "Code Memory" (arxiv)
- LangMem, LangGraph store
- Letta (formerly MemGPT)
- Custom MCP memory servers (search GitHub "mcp memory")
- memstore-style projects (blog posts)
- OpenAI Codex / ChatGPT project instructions
- Factory.ai / Devin "project context" claims

Search: "context engineering agents", "agentic memory coding", "MCP memory server", Anthropic engineering blog.

---

## Output format — Tool inventory

| name | url | one_liner | memory_type | canonical_store | retrieval_model | agent_native | compass_queries | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |

**Extra columns:**
- `memory_type`: vector-RAG / graph / file-based / hybrid / session-only
- `retrieval_model`: semantic search / keyword / structured query / manual

---

## Output format — Community pulse

Focus on:
- "Goldfish with a PhD" problem — session amnesia quotes
- CLAUDE.md scaling limits
- Context window vs external memory debates (2024–2026)
- Failed approaches people tried

---

## Session metadata

```
session: C
category: Agent memory / context
researcher_model:
date:
sources_searched:
gaps_in_coverage:
```

---

## Key distinction to enforce in every row

Ask: **Does this tool know WHY a feature exists, or only WHAT the codebase contains?**

- Codebase indexing (Cursor codebase, Sourcegraph Cody) → note as **adjacent**, mark `M2_graph` = n/a unless requirements graph exists
- Convention files (CLAUDE.md) → `M3_history` usually none
