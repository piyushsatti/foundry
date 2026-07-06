---
status: historical
study: manifold-landscape-2026-06
type: prompt-pack
tags: [manifold, research-charter, M-axis]
completed: 2026-06-06
---

# Manifold landscape research — master handoff

> **Historical.** Pass 1 (sessions A–E) is complete. Final output: [`synthesis.md`](synthesis.md). Study index: [`README.md`](README.md). Pass 2 closed indefinitely.

**You (Pi) ran this** by opening parallel chats (Claude + ChatGPT), pasting one session prompt per chat, collecting outputs, and synthesizing in Cursor.

**We are NOT building manifold here.** We are mapping who else solves "projects lose their why faster than their code" in the agent era.

---

## Problem charter (every session gets this context)

> Software projects lose their **"why"** faster than they lose their code. Requirements drift, docs become fiction, and AI agents amplify the problem by shipping fast without durable intent. The industry knows this problem (KAOS, traceability, spec-driven development) but few tools combine: **queryable versioned intent**, **explicit drift detection**, and a **"what's next" API** for orchestrators.

**Manifold** (our tool) is a "project compass" — layered spec graph in SQLite, `next-leaves`, `drift-report`, MCP for agents. See repo: `skills/manifold/references/why-manifold.md`.

**Research question:** Who else solves intent longevity, traceability, and agent-scale spec memory — commercially, in open source, and in community discourse?

---

## Pass 1 — run these 5 sessions in parallel

| Session | File to paste | Target |
|---|---|---|
| **A** | [01-session-A-sdd.md](01-session-A-sdd.md) | Spec-driven dev / agent workflow tools |
| **B** | [02-session-B-alm.md](02-session-B-alm.md) | Enterprise RE / ALM / traceability |
| **C** | [03-session-C-agent-memory.md](03-session-C-agent-memory.md) | Agent memory / context engineering |
| **D** | [04-session-D-orchestration.md](04-session-D-orchestration.md) | Orchestration + agent IDEs |
| **E** | [05-session-E-drift-discourse.md](05-session-E-drift-discourse.md) | Intent drift discourse + validation tools |

Each session should produce:
1. **Tool inventory table** (8–12 rows)
2. **Community pulse** (5–10 bullets with links)
3. **Session metadata** (date, model used, sources searched)

---

## Pass 2 — closed

Per-tool deep dives are **closed indefinitely**. The synthesis is the deliverable. If product work ever needs first-hand verification of one tool, use the archived [06-pass2-deep-dive-template.md](06-pass2-deep-dive-template.md) or prompts in [README.md](README.md).

---

## How to paste results back into Cursor

Use [07-results-paste-template.md](07-results-paste-template.md). Copy the filled template once per session into the Cursor chat.

---

## Manifold comparison axes (use in every row)

Rate each tool **full / partial / none / n/a** on:

1. **Single source of truth** — one canonical spec store (not scattered files)
2. **Layered graph** — intent→implementation structure, not flat docs
3. **Revision history** — versioned edits with change semantics
4. **Drift detection** — explicit spec↔reality divergence handling
5. **Compass queries** — structured "what's next?"
6. **Verdict engine** — automated validation of spec satisfaction
7. **Agent-native** — MCP, API, or CLI designed for agents

Also fill operational fields: `canonical_store`, `pricing`, `sweet_spot`, `gap_vs_manifold`.

---

## Rules for researchers

- Prefer sources from **2024–2026**. Mark older tools as "legacy" if still relevant.
- Every claim needs a **URL**. Mark unverified as `unverified`.
- Do **not** produce generic "top 10 AI coding assistants" lists unless mapped to intent/drift.
- Include **open source** (GitHub stars, last commit) and **commercial** (pricing page if public).
- Quote community sentiment **verbatim** where possible, with link.

---

## Timeline

| When | What |
|---|---|
| Day 1 | Launch sessions A–E (A+E dual-run on Claude + ChatGPT optional; see `research/README.md`) |
| Day 2 | Paste into Cursor → synthesis → pick top 5–8 |
| Done | [`synthesis.md`](synthesis.md) — study complete |
| Closed | Pass 2 per-tool deep dives (see [README.md](README.md)) |
