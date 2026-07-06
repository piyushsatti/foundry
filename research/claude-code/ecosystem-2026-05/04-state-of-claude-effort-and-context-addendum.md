# Two New Sections for "The State of Claude — May 30, 2026 Update"

These two sections are drafted to slot directly into the existing report. Each leads with a bottom-line conclusion, distinguishes meaningful differences from cosmetic ones, separates Anthropic-self-reported claims from independently verified ones, and explicitly flags anything that could not be confirmed.

---

## Section 1: What the Modes Actually Represent (and the Speed→Intelligence Reframing)

**Bottom line:** The "faster → smarter" rename is real and documented — but it happened at the level of the *effort slider's labels in Claude Code*, not as a replacement of a separate "Fast/Balanced/Thorough" speed toggle. Anthropic's Claude Code changelog records that it "Renamed the /effort slider labels from 'Speed'/'Intelligence' to 'Faster'/'Smarter' for clarity." That is the clearest single piece of evidence that Anthropic deliberately reframed this control along a Faster↔Smarter axis. Fast Mode is a separate, orthogonal control that changes throughput (speed) only — not reasoning or quality. The user's recollection is essentially correct, with one correction: the dial that was reframed is the **effort control**, and the prior framing it replaced was the slider's own "Speed/Intelligence" labels, not a distinct speed-vs-quality model picker.

### The two controls, and how they compose
Claude now exposes two independent knobs that are easy to conflate:

1. **Effort** — controls how *hard* the model thinks: thinking depth, tool-call appetite, and response length. This is the "Faster ↔ Smarter" / "Low → Max" dial. It is a quality/intelligence control.
2. **Fast Mode** — controls how *fast* tokens are produced. Same model, same weights, same intelligence; only speed and price change. It is a latency control.

These compose freely: you can run any effort level in Fast Mode or in standard mode. Fast Mode is explicitly *not* an intelligence control. As described in Anthropic's positioning and reported by RoboRhythms (May 2026), Fast Mode "is the full model at 2.5x speed and three times cheaper than before, not a distilled 'lite' version" — "the full Opus 4.8 running in a high-speed configuration with identical intelligence, which means you are not trading quality for speed." In short: effort = how smart; Fast Mode = how fast. The rename pushed the *effort* dial's framing toward intelligence precisely because that is what it governs, while Fast Mode remains the explicit speed lever.

### What "effort" actually changes mechanically
Per Anthropic's effort documentation, effort is "a behavioral signal, not a strict token budget." It turns several knobs at once:
- **Thinking depth** — the adaptive thinking budget ceiling. At low, the model often skips thinking entirely; at max it can reason for thousands of tokens before producing any output. ("At lower effort levels, Claude will still think on sufficiently difficult problems, but it will think less than it would at higher effort levels for the same problem.")
- **Tool-call appetite** — at higher effort the model reads more files, runs more commands, and explores more before acting; at low it does the minimum.
- **Response length / verbosity** — higher effort produces longer, more detailed responses.
- Per the effort docs, lower effort levels "Combine multiple operations into fewer tool calls," "Make fewer tool calls," and "Proceed directly to action without preamble," while higher effort levels "Make more tool calls," "Explain the plan before taking action," and "Provide detailed summaries of changes."

Independent developer write-ups corroborate this: effort "changes how hard Claude thinks, how many tools it calls, and how long responses take." Setting effort to "high" produces exactly the same behavior as omitting the parameter entirely.

### The exact label mapping (claude.ai/Cowork ↔ Claude Code/API)
| claude.ai / Cowork label | Claude Code / API level | Meaning (Anthropic's own wording where quoted) |
|---|---|---|
| Low | `low` | "Most efficient. Significant token savings with some capability reduction." |
| Medium | `medium` | "Balanced approach with moderate token savings." |
| High (default) | `high` | "High capability. Equivalent to not setting the parameter." Default on all surfaces for Opus 4.8. |
| Extra | `xhigh` | claude.ai "Extra" = Claude Code "xhigh" — confirmed verbatim in Anthropic's launch post: users can choose "extra" ("xhigh" in Claude Code). |
| Max | `max` | "For tasks requiring the absolute highest capability with no constraints on token spending." Session-only in Claude Code. |

The five canonical names (low/medium/high/xhigh/max) are standardized in the API docs and Claude Code. Anthropic has **not** published an exact slider-label table for the claude.ai consumer UI beyond "Extra" and "Max"; the consumer surface presents the same underlying dial with friendlier labels. Where a product shows a "Faster ↔ Smarter" style control, that is the same dial.

### The default shifted between releases (a meaningful change)
- **Opus 4.7** defaulted to **xhigh** in Claude Code (high on the API). The first time Opus 4.7 launched, Claude Code applied xhigh even if you had previously set another level.
- **Opus 4.8** defaults to **high** on *all* surfaces (claude.ai, API, Claude Code). When you first run Opus 4.8, Claude Code applies high even if you previously set a different level. Anthropic judges high the "best overall balance of quality and user experience," and says high effort on Opus 4.8 spends a similar number of tokens to Opus 4.7's default while performing better on coding.
- Anthropic recommends "extra" (xhigh) for difficult tasks and long-running asynchronous workflows, and explicitly raised Claude Code rate limits to accommodate the higher token usage of higher effort levels.

### "Ultracode" — a Claude Code setting, NOT an API effort level
This is a frequent point of confusion in third-party coverage. Per Anthropic's own model-config docs: "Ultracode is a Claude Code setting rather than a model effort level: it sends xhigh to the model and additionally has Claude orchestrate dynamic workflows for substantive tasks. It applies to the current session only." The effort docs reinforce this: "ultracode appears in Claude Code's effort menu, but it is not an additional API effort level. The values documented on this page are the complete set the API accepts." 

Mechanically, **ultracode = xhigh effort + standing permission for Claude Code to launch Dynamic Workflows** (parallel subagents + self-verification), granted through mid-conversation system messages. It was introduced in Claude Code v2.1.154+. It is set via `/effort ultracode` (or `"ultracode": true` through `--settings`/the Agent SDK) and is deliberately excluded from `effortLevel`, the `--effort` flag, and `CLAUDE_CODE_EFFORT_LEVEL`.

> **Conflict flag:** Some third-party blogs (notably MindStudio) describe Opus 4.8 as having five effort levels "Low, Medium, High, Max, and Ultra Code," and characterize "Ultra Code" as a specialized software-engineering effort preset configured via `budget_tokens`. This **contradicts Anthropic's primary docs**, which (a) list the five API levels as low/medium/high/xhigh/max, (b) state Opus 4.8 rejects `budget_tokens` entirely (adaptive thinking only), and (c) define ultracode as a session-only Claude Code orchestration toggle, not an API effort value. Trust the primary docs; treat the "Ultra Code as 5th effort level" framing as incorrect.

### Fast Mode framing and economics
Fast Mode on Opus 4.8 runs the same model at ~2.5x output speed for double the per-token rate: **$10/$50 per million input/output tokens** vs the standard $5/$25. Critically, it is ~3x cheaper than Fast Mode on previous Claude models. Per VentureBeat (May 28, 2026), Anthropic "slashed the price of running Opus 4.8 in fast mode … to $10 per million input tokens and $50 per million output tokens, down from $30/$150 for Opus 4.7" (Opus 4.7's Fast Mode was 6x standard rates). Toggle it with `/fast` in Claude Code, or `speed: "fast"` on the API (research preview; contact your account manager or join the waitlist). 

Practical caveats: advertised "up to 2.5x" is a ceiling, with real-world gains often in the 1.8x–2.4x range; switching Fast Mode on/off mid-session invalidates the prompt cache; and for Claude Code subscribers, Fast Mode tokens bill to a separate extra-usage pool with its own rate-limit pool (it falls back to standard speed when exhausted).

---

## Section 2: Context Management Across the Three Models

**Bottom line:** Context handling differs *meaningfully* across the three models on three axes — context-window size, long-context retrieval quality, and which context-management features are supported — while prompt caching, context editing, and the memory tool work largely the same way across all three. The single most consequential difference: **Opus 4.8 and Sonnet 4.6 have a 1M-token window; Haiku 4.5 is capped at 200K**, and on retrieval quality **Opus ≈ Sonnet at the high end, both far ahead of Haiku**, with Opus holding up best at the extreme (1M) edge.

### Context window sizes and max output (where they DIFFER)
| Model | Context window | Max output | Notes |
|---|---|---|---|
| Opus 4.8 | **1M tokens** on Claude API, Bedrock, Vertex AI; **200K on Microsoft Foundry** | **128K** | 1M by default; lowered 1,024-token min cacheable prompt |
| Sonnet 4.6 | **1M tokens** (now GA; was beta) | **64K** | 200K base, 1M generally available |
| Haiku 4.5 | **200K tokens** | **64K** | No 1M option |

This is the clearest meaningful difference: if a task regularly needs more than 200K tokens, you must use Opus or Sonnet — Haiku cannot do it. On the Message Batches API, Opus 4.8, Opus 4.7, Opus 4.6, and Sonnet 4.6 can produce up to 300K output tokens via the `output-300k-2026-03-24` beta header (well above the synchronous 128K/64K limits).

### The 1M-context beta → standard, and the (removed) pricing premium
The 1M window debuted as a **beta** on Opus 4.6 (February 2026, requiring an API header) and on Sonnet 4.5. It is now **standard at flat pricing** for the current lineup. Anthropic's pricing docs state: "Claude Mythos Preview, Claude Opus 4.8, Opus 4.7, Opus 4.6, and Sonnet 4.6 include the full 1M token context window at standard pricing."

Crucially, **the long-context premium was removed for the current models.** Historically, **Sonnet 4.5** on the 1M beta applied a **2× input / 1.5× output surcharge above 200K tokens**. That surcharge does **not** apply to Opus 4.8, Opus 4.7, Opus 4.6, or Sonnet 4.6 — they bill flat at $5/$25 (Opus) or $3/$15 (Sonnet) regardless of context length up to 1M. Haiku 4.5 (200K, no long-context tier) has no such surcharge. By contrast, competitor GPT-5.5 still applies a long-context surcharge above 272K input tokens — making Opus 4.8 the lower-cost option for frequent 272K+ contexts despite GPT-5.5's cheaper short-context output rate.

### Long-context retrieval quality (the biggest meaningful gap)
A large window is only useful if the model can actually use it across its full span. The data shows a stark hierarchy and an important historical wrinkle.

**The Opus 4.7 long-context regression (history that still matters):** On the 8-needle 1M MRCR v2 benchmark, Opus 4.6 scored **78.3%**, but Opus 4.7 collapsed to **32.2%** (256K: 91.9% → 59.2%). Anthropic's own Opus 4.7 system card acknowledged that Opus 4.6's 64k extended-thinking mode dominates 4.7 on long-context multi-needle retrieval. The practical takeaway from independent analysis (AllThings.how): "If precise ordinal retrieval from long documents is central to your workflow, Sonnet 4.6 or Opus 4.6 may still be the better fit" — i.e., many teams kept Opus 4.6 as a RAG/deep-research fallback through the 4.7 cycle.

**Opus 4.8 recovered long-context performance — but it is measured on GraphWalks, not MRCR.** Per the Opus 4.8 system card, GraphWalks BFS 1M F1 jumped to **68.1%** (from Opus 4.7's 40.3%), GraphWalks BFS 256K to **85.9%** (from 76.9%), and GraphWalks Parents 1M to **83.3%**. Anthropic's migration notes also cite "Better compaction handling and long-context quality. Long agentic traces stay on task with fewer derailments after compaction." 

> **Gap flag:** The Opus 4.8 system card does **not** publish an MRCR v2 score for Opus 4.8. Anthropic appears to have dropped MRCR for the 4.8 card. Per AllThings.how, "Anthropic's engineering lead on Claude Code, Boris Cherny, explained that MRCR is being phased out because it stacks distractors in ways that don't reflect real usage, and that GraphWalks is now the preferred long-context signal." Consequently, **a clean MRCR-to-MRCR Opus 4.6 → 4.7 → 4.8 comparison cannot be made from published numbers.** GraphWalks shows clear recovery; the equivalent MRCR recovery is inferred, not published.

**Sonnet 4.6 (verbatim from its system card, §2.16, Tables 2.16.A/B):**
- MRCR v2 8-needle: **90.3–90.6% at 256K**; **65.1–65.8% at 1M** (the <1M-token subset scores 71.3–77.8%, since some 1M problems exceed the public API limit).
- GraphWalks BFS 1M F1: **68.4% (64k) / 73.8% (max)**; GraphWalks Parents 1M: **71.1% (64k) / 86.4% (max)**.
- The card states (Fig. 2.16.2.A): "Claude Sonnet 4.6 is our best model for long context graph reasoning problems," and (Fig. 2.16.1.B) that it "is competitive with state-of-the-art Claude Opus 4.6 on long context … measured through OpenAI MRCR v2 8 needles." On GraphWalks specifically, Sonnet 4.6 actually edges Opus 4.6.

**Haiku 4.5:** No 1M long-context retrieval scores exist (it is 200K-capped). Independent developer analysis (Effloow) notes Haiku's limitation "isn't context length — it's reasoning depth on complex tasks within that context," and that on multi-file work, "context from earlier in the session degrades" faster than Sonnet 4.6, which "handles the cognitive load of a 20-file codebase edit more reliably."

> **Sourcing note:** All these long-context figures are **Anthropic self-reported** (internal evals; the 1M-token problems are explicitly "not reproducible via the public API" because they exceed its limits). Third-party leaderboards (LLM-Stats, Awesome Agents, Artificial Analysis) corroborate the *relative ordering* but list the underlying numbers as self-reported, not independently verified. The Sonnet 4.6 numbers above are verbatim from the official system card PDF; the Opus 4.8 GraphWalks numbers are transcribed by multiple independent readers of the Opus 4.8 card (DataCamp, DigitalApplied) — I could not open the official Opus 4.8 PDF directly to cite a page number.

### Context compaction / auto-compaction (DIFFERS by model)
There are two distinct compaction systems, and they diverge by model:

- **Claude Code auto-compact** (client-side, all models) — when a session approaches the context limit (~95% capacity / ~25% remaining), Claude Code summarizes the conversation and continues seamlessly; since v2.0.64 it is near-instant. `/compact` is the manual version (with optional preservation instructions); `/clear` wipes context entirely; `/context` shows current usage. Project-root CLAUDE.md survives compaction, but path-scoped rules, nested CLAUDE.md files, and older decisions can be summarized away — so durable rules belong in CLAUDE.md / CLAUDE.local.md, not in the conversation. Anthropic states Opus 4.8 has "fewer compactions, and better compaction recovery."
- **Server-side compaction (API, beta)** — enabled with the `compact-2026-01-12` beta header (`compact_20260112` strategy); it auto-summarizes older context when approaching the window limit. **This is where the models DIFFER:** server-side compaction is available in beta for **Opus 4.8, Mythos Preview, Opus 4.7, Opus 4.6, and Sonnet 4.6 — but NOT Haiku 4.5.** Haiku-based agents must use SDK/client-side compaction (e.g., the Agent SDK's `compaction_control`) instead. This is a concrete, meaningful capability gap for Haiku in long-running agentic use.

### Context editing and the memory tool (largely the SAME across all three)
- **Context editing** (beta header `context-management-2025-06-27`) provides **tool-result clearing** (`clear_tool_uses_20250919`) and **thinking-block clearing** (`clear_thinking_20251015`). Anthropic states context editing "is available on all supported Claude models" — so this works on Opus 4.8, Sonnet 4.6, and Haiku 4.5.
- **Memory tool** (`memory_20250818`) gives Claude a persistent `/memories` file directory across sessions, and pairs with context editing so Claude saves key information before tool results are cleared. It is broadly supported (Sonnet 4.5/4, Haiku 4.5, Opus 4.1/4 and current models).
- Anthropic's internal evals report that combining the memory tool with context editing improved agentic-search performance **39% over baseline** (context editing alone: 29%) and cut token consumption **84%** in a 100-turn web-search evaluation. These are Anthropic self-reported, not independently benchmarked.

### Prompt caching and cache TTL (mostly SAME; one model-specific difference)
- Caching multipliers are identical across models: **5-minute cache write = 1.25× input, 1-hour cache write = 2× input, cache read = 0.10× input** (the ~90% read discount). Reading a live cache also refreshes its TTL.
- **Yes, a 1-hour cache option exists** (`"ttl": "1h"` / `"ttl": 3600`), supported across Anthropic, Bedrock, and Vertex.
- **The TTL change that caused cost blowouts:** around **March 6–7, 2026**, Anthropic silently reverted the *default* prompt-cache TTL from 1 hour back to 5 minutes. This is documented in GitHub issue #46829 (anthropics/claude-code) by Sean Swanson, who analyzed **119,866 API calls (Jan 11 – Apr 11, 2026)** and found the reversion "caused a 20–32% increase in cache creation costs" plus a spike in quota consumption for subscription users; the data showed a 1-hour default introduced ~Feb 1 and reverted ~Mar 7. With 5m TTL, any pause longer than 5 minutes expires the cached context, forcing an expensive re-write (the write rate is ~12.5× the read rate) — disproportionately punishing for Claude Code's long, high-context sessions.
- **Anthropic's position:** Per The Register (Apr 13, 2026), Jarred Sumner (Bun creator, now at Anthropic) said the 5-minute change actually made Claude Code cheaper because "a meaningful share of Claude Code's requests are one-shot calls where the cached context is used once and not revisited," and that "the Claude Code client determines the cache TTL automatically and there are no plans for a global setting." (Subagent-heavy sessions, which interact quickly, benefit from the cheaper 5m write cost.)
- **Model-specific difference:** the minimum cacheable prompt length is **1,024 tokens for Opus 4.8, Sonnet 4.6, and Sonnet 4.5** (per Anthropic's prompt-caching docs), versus **4,096 tokens for Mythos Preview, Opus 4.7, Opus 4.6, and Opus 4.5**. This means Opus 4.8 lowered its minimum from 4,096 (on 4.6/4.7) to 1,024 — short prompts that couldn't cache on Opus 4.7 now cache with no code change. *(Flag: Anthropic's caching docs do not separately list Haiku 4.5's minimum in the table reviewed; treat Haiku's exact minimum as unconfirmed, with secondary sources citing 4,096.)*

### Adaptive vs extended thinking, and context budgeting (DIFFERS by model)
- **Opus 4.8 uses adaptive thinking ONLY.** Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) returns a 400 error; `budget_tokens` is rejected. Effort is the recommended (and only) control for thinking depth. The model decides per turn whether and how much to think.
- **Sonnet 4.6 and Haiku 4.5 support extended thinking** (with `budget_tokens`). Haiku 4.5 was the *first* Haiku model to support extended thinking; it is **disabled by default** and must be enabled explicitly (Anthropic recommends enabling it for complex coding/reasoning). Both also support adaptive thinking / effort.
- **Context-budgeting effect:** thinking tokens count toward the context window and are billed as output. But the API **automatically strips previous turns' thinking blocks** from the context for subsequent turns, preserving capacity for actual conversation. With adaptive thinking the model varies allocation per request, so thinking-token usage is less predictable than a fixed `budget_tokens`. Note that extended thinking reduces prompt-caching efficiency — a real consideration on Haiku 4.5, where Anthropic explicitly warns "extended thinking impacts prompt caching efficiency."

### Context-awareness training intervention (DIFFERS / partially unconfirmed)
"Context awareness" is the trained capability that lets a model track its remaining context budget ("token budget") across a long session, pacing itself to make incremental progress and avoid quitting early ("agentic laziness"). Per Anthropic's prompting docs: "Claude 4.6 and Claude 4.5 models feature context awareness, enabling the model to track its remaining context window … throughout a conversation." The context-windows docs explicitly name **Sonnet 4.6, Sonnet 4.5, and Haiku 4.5** as having this feature, and the Haiku 4.5 release notes describe "Token budget tracking … real-time updates on remaining context capacity after each tool call" and "Multi-context-window workflows."

> **Flag:** The materials reviewed confirm context awareness for **Sonnet 4.6 and Haiku 4.5** explicitly. Anthropic's docs frame it as a "4.6 and 4.5 generation" feature, which logically includes Opus, but the reviewed docs did not *restate it by name for Opus 4.8 specifically.* Treat Opus 4.8 context awareness as highly likely but not explicitly reconfirmed in the 4.8 materials.

### Mid-task system messages (NEW with Opus 4.8 — a context-management primitive)
The Messages API now accepts `role: "system"` entries *inside the messages array* (not just the top-level `system` parameter), placed immediately after a user turn. This lets a harness update instructions mid-task — change permissions, token budgets, or environment context — **without breaking the prompt cache or faking a user turn.** Its relevance to context management: in long agentic runs you can steer the model mid-flight while continuing to pay cached-input rates on everything before the change, avoiding a full system-prompt re-send (which would invalidate the cache). This API primitive is what underpins Claude Code's ultracode: the "standing permission" for Claude to launch Dynamic Workflows is granted via these mid-conversation system messages. It is opt-in and backward compatible — existing code is unaffected.

### Quick differentiation summary
| Capability | Opus 4.8 | Sonnet 4.6 | Haiku 4.5 |
|---|---|---|---|
| Context window | 1M (200K on Foundry) | 1M (GA) | **200K** |
| Max output | 128K | 64K | 64K |
| 1M long-context surcharge | None (flat) | None (flat) | N/A (no 1M) |
| Long-context retrieval | Best at the 1M edge (GraphWalks BFS 1M F1 **68.1%**) | Strong (BFS 1M F1 **68.4–73.8%**; MRCR 1M ~65%) | 200K-limited; degrades fastest |
| Server-side compaction (beta) | Yes | Yes | **No** |
| Context editing / memory tool | Yes | Yes | Yes |
| Thinking | **Adaptive only** (budget_tokens rejected) | Extended + adaptive | Extended (1st Haiku) + adaptive |
| Min cacheable prompt | 1,024 | 1,024 | 4,096 (unconfirmed in primary table) |
| Context awareness | Family feature (not restated for 4.8 — flag) | Yes | Yes |
| Mid-task system messages | **Yes (new)** | API-wide | API-wide |

---

## Recommendations (for integrating these sections)

1. **Frame the rename precisely.** State plainly that the reframing is at the effort slider's labels ("Speed"/"Intelligence" → "Faster"/"Smarter," per the Claude Code changelog), and keep Fast Mode in a clearly separate box as the speed-only lever. Avoid implying a "Fast/Thorough" model picker was replaced — that's not what happened.

2. **Lead the context section with the Haiku 200K cliff and the Opus-vs-Sonnet retrieval story**, since those are the two differences that actually change model selection. Tie this back to the existing decision matrix: Haiku is disqualified above 200K; for genuine 1M-token retrieval, prefer Opus 4.8 (best at the edge) or Sonnet 4.6 (near-parity, far cheaper).

3. **Add a callout box on the MRCR gap.** Because Anthropic dropped MRCR from the Opus 4.8 card, explicitly tell readers that long-context recovery for 4.8 is demonstrated on GraphWalks, and that RAG teams who relied on MRCR-style ordinal retrieval should A/B test 4.8 against Sonnet 4.6 / Opus 4.6 on their own data before migrating.

4. **Add a caching-cost warning.** Flag the March 2026 5-minute-default TTL reversion and the lack of a global user setting; recommend explicitly setting `"ttl": "1h"` for agent pipelines with multi-minute gaps, and note Opus 4.8's lowered 1,024-token cache minimum as a small win.

5. **Benchmarks/thresholds that would change these recommendations:** (a) if Anthropic republishes an MRCR v2 score for Opus 4.8, replace the inferred recovery language with the hard number; (b) if Haiku gains server-side compaction or a >200K window, revisit the Haiku disqualification; (c) if the 1M flat-pricing changes, re-run the Opus-vs-GPT-5.5 long-context cost comparison.

## Caveats
- **Self-reported vs verified:** Essentially all long-context and honesty/alignment numbers originate from Anthropic's own system cards and internal evals; the 1M-token results are explicitly not reproducible on the public API. Third parties corroborate ordering, not absolute values.
- **Opus 4.8 system card not directly opened:** Opus 4.8 GraphWalks figures (68.1% / 85.9% / 83.3%) are transcribed by multiple independent readers (DataCamp, DigitalApplied), not quoted from the PDF with a page number. Sonnet 4.6 figures are verbatim from the official §2.16 tables.
- **Unconfirmed items explicitly flagged above:** (1) Opus 4.8 MRCR v2 score is unpublished; (2) Opus 4.8 context awareness is not restated by name in the 4.8 materials; (3) Haiku 4.5's exact minimum cacheable prompt length is not in the primary caching-docs table reviewed.
- **Contradiction to ignore:** The "Ultra Code as a 5th Opus 4.8 effort level configured via budget_tokens" framing (MindStudio and similar) conflicts with Anthropic's primary docs and should not be used; ultracode is a session-only Claude Code orchestration setting, and Opus 4.8 rejects budget_tokens entirely.
- **Fast Mode** is a research preview; "up to 2.5x" is a ceiling, and toggling it mid-session invalidates the prompt cache.