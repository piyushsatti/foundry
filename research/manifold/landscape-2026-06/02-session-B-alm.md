---
status: historical
study: manifold-landscape-2026-06
session: B
type: session-prompt
tags: [enterprise-alm, traceability, doors]
---

# Session B — Enterprise RE / ALM / traceability

**Paste this entire file into a new Claude or ChatGPT chat.** Enable web search / browsing if available.

---

## Your role

Landscape research scout for **requirements engineering, application lifecycle management, and traceability** tools — commercial and open source.

## Problem we care about

Requirements, design, and code live in separate systems. When one changes, others don't follow — the PRD becomes "historical fiction." We want to know what the **enterprise market** already sells to solve traceability, and whether any of it is becoming **agent-native**.

Our reference: **manifold** — SQLite spec graph, KAOS-inspired layers, drift-report, MCP. Solo-dev / agent-orchestrator scale, not enterprise ALM.

## Your task

1. Find **8–12 tools** (mix of legacy enterprise + modern cloud ALM).
2. Fill inventory table.
3. Community pulse — especially practitioner complaints about ALM vs agile AI workflows.
4. **3 implications for manifold** — what enterprise got right, what's overkill for agent era.

## Seed list (expand)

- IBM Engineering Requirements Management DOORS / DOORS Next
- Siemens Polarion ALM
- Jama Connect
- Visure Requirements
- Modern Requirements (Azure DevOps integration)
- Helix ALM / Perforce
- Codebeamer
- ReqIF ecosystem tools
- Open source: Doorstop, Sphinx-needs, traceability plugins
- Linear / Jira **requirements** features (if any traceability story)
- Notion/Confluence as PRD stores (adjacent)

Search: "requirements traceability AI", "ALM AI agents 2025", "ReqIF", "living requirements".

---

## Output format — Tool inventory

| name | url | one_liner | canonical_store | drift_handling | agent_native | compass_queries | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |

(Same column definitions as Session A — see 00-MASTER-HANDOFF.md)

**Extra column for this session (append):**
| regulated_industries | yes/no — medical, automotive, aerospace focus |

---

## Output format — Community pulse

Focus on:
- Do practitioners still use ALM or "just GitHub + markdown" in 2025–2026?
- Complaints about traceability overhead vs AI speed
- Any vendor claiming "AI requirements" or "intent drift detection"

Same structure as Session A (pain themes, trending phrases, notable threads).

---

## Session metadata

```
session: B
category: Enterprise ALM / traceability
researcher_model:
date:
sources_searched:
gaps_in_coverage:
```

---

## Do NOT

- Treat Jira/Linear as full RE tools unless they have requirements/traceability features worth noting
- Ignore pricing — note enterprise-only vs SMB if known

## DO

- Note whether tool has API/MCP/agent integration today or on roadmap
- Separate **requirements authoring** from **test traceability** from **release management**
