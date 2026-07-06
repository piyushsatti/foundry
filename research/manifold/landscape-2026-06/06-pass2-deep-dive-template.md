---
status: archived
study: manifold-landscape-2026-06
type: template
tags: [pass2-closed, deep-dive, verification]
pass2: closed
---

# Archived — per-tool deep dive template

**Pass 2 is closed indefinitely.** Kept as reference if product work requires first-hand verification of one competitor.

When needed: paste into external Claude/ChatGPT (web search on). Replace `[TOOL NAME]` and `[TOOL URL]`. Save as `results/adhoc-<tool>-YYYY-MM-DD.md`.

See also: prompts in [`README.md`](README.md) § "Prompts for deepening understanding".

---

## Deep dive: [TOOL NAME]

**URL:** [TOOL URL]  
**Chosen because:** [1 sentence from synthesis §9 shortlist]

### Context — what manifold is (for comparison)

Manifold = project compass. SQLite spec graph, layers (intent→realizations), revision history, `change_reason`, `drift-report`, `next-leaves`, verdict engine, MCP (29 tools). Long-lived multi-session agent work — not one-shot feature specs.

---

## Part 1 — Hands-on reconnaissance

Answer from docs + trial if you can sign up/clone:

1. **Hello world:** What's the smallest path to "project with spec that survives a second session"?
2. **Day 2 test:** After initial setup, where does intent live? File paths? DB? Tickets?
3. **Session reset test:** Close agent/chat, reopen — what must the user re-supply?
4. **Multi-feature test:** Second feature added — does spec structure scale or flatten?
5. **Export:** Can intent leave the platform (git markdown, API, dump)?

---

## Part 2 — Feature matrix

| Capability | Support (full/partial/none) | Evidence (URL or doc quote) |
|---|---|---|
| Single source of truth | | |
| Layered goals (intent→implementation) | | |
| Multi-parent / graph (not strict tree) | | |
| Rationale / "why" on spec items | | |
| Revision history | | |
| Change reason / audit semantics | | |
| Drift detection or analyze | | |
| Structured "what's next" | | |
| Verdict / validation hooks | | |
| Multi-project query | | |
| Git-friendly export | | |
| MCP or agent API | | |
| Human web UI | | |
| Pricing transparency | | |

---

## Part 3 — User sentiment (last 12 months)

### Positive (3)
| quote | url | date |

### Negative (3)
| quote | url | date |

### Common failure mode
One paragraph in users' own words, with citations.

---

## Part 4 — Verdict vs manifold

| Question | Answer |
|---|---|
| **Overlaps** — ideas manifold should steal | |
| **Gaps** — what manifold still uniquely fills | |
| **Integrate, replace, or ignore?** | integrate / replace / ignore / compete |
| **Best paired workflow** | e.g. "Use X for feature kickoff, manifold for longevity" |
| **Risk if we ignore this tool** | |

---

## Part 5 — Score (0–2 each, max 8)

| Axis | Score | Notes |
|---|---|---|
| Longevity (multi-month projects) | 0–2 | |
| Intent structure (graph/layers) | 0–2 | |
| Drift awareness | 0–2 | |
| Agent integration | 0–2 | |
| **Total** | /8 | |

---

## Metadata

```
study: adhoc-verification
tool:
researcher_model:
date:
hands_on: yes / docs-only
confidence: high / medium / low
```
