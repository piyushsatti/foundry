---
status: historical
study: manifold-landscape-2026-06
session: E
type: session-prompt
tags: [intent-drift, validation, discourse]
---

# Session E — Intent drift discourse & validation tools

**Paste this entire file into a new Claude or ChatGPT chat.** Enable web search / browsing if available.

---

## Your role

Landscape scout focused on **intent drift**, **requirement drift**, and **spec↔code validation** — the problem discourse and tools that explicitly name it (2024–2026).

## Problem we care about

**Intent drift** ≠ bug. Code passes tests but no longer matches why the feature existed. Diffs don't reveal lost "why." We want the **vocabulary**, **vendor narratives**, and **tools** attacking this — plus raw community evidence the problem is real and worsening with AI agents.

Our reference: **manifold** `drift-report`, `change_reason`, `rationale` fields.

## Your task

1. Find **8–12 entries** — can be **tools**, **products**, **research papers**, or **named methodologies** (not all must be software).
2. Heavy emphasis on **community pulse** (this session owns the best pain-evidence collection).
3. Map **who coined or popularized "intent drift"** in AI context (2024–2026).
4. **5 implications for manifold** — positioning language to use or avoid.

## Seed list (expand)

- Stonewall "intent drift" blog
- Tricentis intent drift / AI code articles
- Omniflow requirement drift
- Zenn IDD (Intent Drift Detection) series
- Propel / PRD tooling with drift claims
- Semgrep / rules-as-spec / policy-as-code angles
- Qase, TestRail AI alignment features
- Linear "intent" or product alignment features
- Architecture decision records (ADR) tools — Nygard, Log4brains, adr-tools
- OpenTelemetry + SLO drift (adjacent)
- Academic: requirements drift, traceability decay, Lehman laws + AI
- arxiv: "intent drift", "specification drift", "requirements evolution" 2023–2026

Search HN/Reddit: "intent drift", "requirements drift", "spec drift AI", "built the wrong thing agent".

---

## Output format — Tool/method inventory

| name | url | type | one_liner | drift_handling | how_it_detects_drift | agent_native | pricing | sweet_spot | M1_truth | M2_graph | M3_history | M4_drift | M5_compass | M6_verdict | M7_agent | gap_vs_manifold | sources |

**Extra column:**
- `type`: product / OSS / methodology / research / blog-series

---

## Output format — Community pulse (PRIMARY OUTPUT FOR THIS SESSION)

### Pain catalog (aim for 15+ distinct themes)

| # | theme | quote_or_paraphrase | url | platform | date | agent_related |

Group themes into:
- **Session amnesia** (agent forgets context)
- **Speed vs alignment** (ships fast, wrong thing)
- **Doc decay** (PRD fiction)
- **Test green but wrong** (intent drift)
- **Multi-agent visibility** (can't see what subagents did)
- **Other**

### Vocabulary map

| term | definition as used online | who uses it | example link |
|---|---|---|---|
| intent drift | | | |
| spec drift | | | |
| requirement drift | | | |
| context engineering | | | |
| spec-driven development | | | |

### Timeline (optional)

5–8 dated milestones in this discourse (blog posts, major launches, HN front page).

---

## Session metadata

```
session: E
category: Drift discourse + validation
researcher_model:
date:
sources_searched:
gaps_in_coverage:
```

---

## Special instruction

This session's community pulse is **shared evidence** for the final report's "problem validation" section. Prioritize **primary sources with URLs** over synthesis without citations.
