# Red Team / Blue Team Analysis of the Claude Code Index Report
### An adversarial, evidence-graded review — verified against user experience, not just documentation (May 2026)

---

## 0. Method & how to read this

This is a falsification exercise, not a summary. I took each load-bearing claim in the original report and tried two things in sequence:

- **Blue Team** — steelman it. Find the strongest *independent* corroboration, ideally from people reporting real-world use (Reddit, DEV, Medium, X, GitHub issues, independent test harnesses), not just the docs that might have seeded the claim in the first place.
- **Red Team** — attack it. Look for sources that contradict it, version drift that has outdated it, single-source figures that don't replicate, and "true in the docs, false in practice" gaps.

Each claim ends with a **verdict** on this scale, and they're all collected in the verification table in §5:

| Symbol | Meaning |
|---|---|
| ✅ | **Confirmed** — official docs *and* user experience agree |
| 🟢 | **Confirmed with nuance** — true, but a caveat materially changes how you'd act on it |
| 🟡 | **Contested** — credible sources genuinely disagree; treat as unsettled |
| 🟠 | **Outdated** — was true; the product moved |
| 🔴 | **Likely incorrect** — the dominant evidence points the other way |
| ⚪ | **Unverified** — couldn't independently confirm; trust cautiously |

A note on epistemics: a large fraction of "Claude Code guide" content online is vendor/SEO material (claudefa.st, Morph, MintMCP, etc.). It's often *mechanically* accurate but tends to launder single observations into stated facts. Where a number appears in only one such source, I downgrade confidence regardless of how confidently it's phrased.

---

## 1. Blue Team — what survives scrutiny (and got *stronger*)

These are the claims I tried hardest to break and couldn't. Several are now better-supported than when the report was written.

### 1.1 "CLAUDE.md is context, not enforced configuration" — ✅ and now upgraded
This was the report's single most important framing claim, and it was originally presented as an inference. It is now **stated verbatim in the official docs**: Claude treats memory files as context, *not* enforced configuration, and to block an action regardless of what Claude decides you must use a PreToolUse hook instead. More importantly for your "user experience" ask, this is the **most-corroborated pain point in the entire ecosystem**. A widely-shared DEV write-up ("3 Hard Realities Nobody Talks About," ~1 month of heavy use) reports that memory instructions are routinely ignored — its author keeps "always respond in Japanese" at the top of his global CLAUDE.md and Claude *still* answers in English on the first prompt, and warns specifically that "when X, do Y" conditional rules in memory files "rarely work well." **Verdict: the report under-sold this.** It's not a soft caveat; it's the defining limitation of the whole instruction layer.

### 1.2 Keep CLAUDE.md lean (~under 200 lines; 80–120 sweet spot) — 🟢
Official guidance ("under 200 lines," longer files reduce adherence) is corroborated by independent practitioners, who report adherence "drops" past roughly 200 lines. The strongest *experiential* evidence: a documented real-world cleanup where a user's global CLAUDE.md went from **189 lines to 63 lines** by moving reference content into on-demand files, with the explicit claim that the bloated version was "loading 155 lines of dense reference content on every single session" for no benefit. **Nuance that matters:** the "200 lines" figure is frequently misapplied — the hard 200-line *truncation* applies to auto memory's `MEMORY.md`, whereas `CLAUDE.md` loads in full at any length and the 200 is a soft *quality* ceiling. The report got this distinction right; most blogs don't.

### 1.3 The Boris Cherny workflow quotes — ✅ verbatim
All checked against the primary Threads/X thread (dated Jan 2, 2026, as the report stated) and multiple mirrors. Confirmed accurate: running ~5 Claudes in parallel in the terminal numbered 1–5; another 5–10 on claude.ai/code; adding to CLAUDE.md whenever Claude does something wrong; starting most sessions in Plan mode then switching to auto-accept for a "1-shot"; a PostToolUse hook to format code; and notably *not* using `--dangerously-skip-permissions` (he pre-allows safe commands via `/permissions` checked into `.claude/settings.json`). One small temporal wrinkle: in that thread he said he used "Opus 4.5 with thinking for everything" — i.e., the quotes predate the Opus 4.6 effort system the report describes elsewhere. The quotes are real; just don't read them as describing the current effort UI.

### 1.4 The 1M-token context window details — ✅
Official Claude Code docs confirm every specific the report made: 1M is supported on **Opus 4.6+ and Sonnet 4.6**; on **Max/Team/Enterprise, Opus auto-upgrades to 1M** with no config; **Sonnet's 1M is opt-in and consumes usage credits on every plan including Max**; disable with `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`. The GA event (March 13, 2026, standard pricing, no long-context premium) is confirmed by Anthropic's own announcement. *(Minor: some third-party posts claim Pro also gets the auto-upgrade; the official docs list only Max/Team/Enterprise. Trust the docs.)*

### 1.5 Sandboxing "reduces permission prompts by 84%" — ✅ (but see §3.1)
Verbatim from Anthropic's engineering blog. Repeated across many secondary sources. The number is real and first-party. The *interpretation* needs a caveat — handled in the Red Team section.

### 1.6 Auto memory mechanics — ✅
Official docs confirm auto memory requires **v2.1.59+**, is **on by default**, stores at `~/.claude/projects/<project>/memory/`, and loads the first 200 lines of `MEMORY.md` at startup. One source pins the ship date precisely to **Feb 26, 2026**. The report's framing that routing/instruction rules belong in CLAUDE.md (full load) rather than MEMORY.md (truncated) is sound.

### 1.7 `ultrathink` reintroduced in v2.1.68 — ✅
Confirmed exactly: v2.1.68 (March 4, 2026) brought back `ultrathink` as a high/max-effort trigger keyword, and the official docs confirm the keyword adds an in-context instruction for deeper reasoning on that turn while plain phrases like "think hard" are treated as ordinary text. (The report's claim that only the keyword "does something" is correct.)

### 1.8 Plan-mode-first + verification loops as the top habits — ✅
This is the rare case where the *creator's* practice, the *official* best-practices guidance, and *community* consensus all align: plan before non-trivial work; pour effort into the plan; give Claude a check it can run (tests/build/screenshot). Nothing contradicts it.

### 1.9 Settings scope cascade & "managed can't be overridden" — 🟢
The five-layer scope order (managed → CLI flags → local → project → user) and the absolute supremacy of managed settings are confirmed repeatedly, including official docs. The nuance is in §3.3 — the cascade is right, but how *deny* interacts with it is where the report stumbled.

### 1.10 Skill descriptions drive triggering; gerund naming; test across models — ✅ (direction), 🟡 (the numbers — §3.2)
The qualitative claims are confirmed by the official skill-authoring docs (gerund names, test with every model you'll use, Haiku may need more detail than Opus). The *quantitative* activation claims are where the trouble is.

---

## 2. Blue Team bonus — claims the report hedged that turned out *more* certain

- **"Context rot" / big window ≠ better.** The report flagged this as a caveat; a user write-up titled, in effect, *why I shrank my context window back to 200K* validates it concretely: on a 1M window the ~95% auto-compact threshold means compaction doesn't fire until ~950K tokens — "way past the point where quality has degraded" — so he forced a 70% threshold to compact at ~140K instead. Real behavior confirms the theory.
- **"Use hooks for hard guarantees."** Now explicitly endorsed by the official memory docs (quoted in §1.1). This elevates the report's hooks-as-enforcement point from "nice idea" to "documented escape hatch from the unreliability of instructions."

---

## 3. Red Team — what's contested, outdated, or probably wrong

This is the part worth your attention.

### 3.1 The sandbox is *not* a hard boundary — and the report's framing is too reassuring — 🟢→⚠️
The 84% number is real, but Anthropic's **own newer post** ("How we contain Claude across products") quietly undercuts the optimistic reading: telemetry showed users approve **~93% of permission prompts** (i.e., the prompt model is "security theatre" once fatigue sets in), and Anthropic calls the sandbox-plus-Auto-Mode approach **"fallible."** Independent security writing adds that the native sandbox ships with an **unsandboxed-command escape hatch**, that **Auto Mode is a research preview** (launched ~March 12, 2026) rather than a settled feature, and that for hard enforcement you should treat external isolation (VM/container/managed policy) as the *primary* boundary. **Action:** keep the report's sandbox section, but reframe it as "reduces friction and contains casual mistakes," not "makes autonomy safe." For credential-bearing machines, the honest answer is devcontainer/VM.

> ⚠️ **Two different "84%"s — do not conflate.** Anthropic's 84% = *reduction in permission prompts*. A separate, unrelated figure circulating in security writing is an **84% prompt-injection success rate** across 314 payloads embedded in READMEs/comments/dependency metadata (third-party research). Same number, opposite meaning. The report didn't make this error, but it's an easy one to make when skimming sources.

### 3.2 Skill activation "20% → 50%, examples → 90%" — 🟡 weakly sourced, partly contradicted
The report's optimism here traces to a **single GitHub gist** whose own numbers are internally incoherent (it jumps "20% → 50%" and then, separately, "72% → 90%" — not a clean curve). The more rigorous evidence cuts against the rosy reading: an independent practitioner built a **200+ prompt test harness** and found that description quality alone plateaus around **50% — a coin flip** — and that reliably hitting **~80–84%** required a **forced-evaluation hook**, not better prose or examples. The official skill-creator's optimization loop also concedes the core problem: Claude "rarely triggers Skills for short, simple requests." **So:** the *direction* (descriptions matter, Claude under-triggers) is solid; the implied "write good examples and you're at 90%" is not supported. The real reliability lever is a **hook that forces explicit skill evaluation** — which, neatly, is the same "use hooks for guarantees" lesson from §1.1.

### 3.3 "A user's local *allow* overrides a project *deny*" — 🔴 likely incorrect as stated; recommendation still stands
This was the report's stated "security gotcha," and the sources genuinely **disagree**:
- One vendor guide (claudefa.st) says local scope (priority 3) beats project scope (priority 4), so a **local allow overrides a project deny**. This is presumably where the report got it.
- But **multiple other sources, including practitioner security guides**, state the opposite and stronger rule: *deny is evaluated first across the merged ruleset*, so "a deny rule cannot be overridden by any allow rule anywhere," and "if a tool is denied at any level, no lower level can allow it."

The dominant reading — and the one consistent with the documented `deny → ask → allow, first-match-wins` evaluation — is that **deny generally wins regardless of scope**, which makes the report's stated mechanism wrong. **However**, the report's *practical advice* — put security-critical denies in managed settings — survives on stronger grounds: managed settings genuinely can't be overridden or removed by a user, and (see next) file-level protection is unreliable anyway. **Action:** correct the *reason*, keep the *recommendation*, and flag the scope-vs-rule-type precedence as an unsettled point to verify against your installed version with `/permissions`.

### 3.4 Effort defaults ("high on Team/Enterprise/API, medium elsewhere") — 🟠 outdated
This was a moving target during exactly the window the report covers. v2.1.68 (March 4, 2026) **switched Opus 4.6 to medium-effort default** for Max/Team to cut latency — then Anthropic **reversed it on April 7** after users said they'd rather default to higher intelligence (documented in Anthropic's own April 23 post-mortem). Current official docs now state: **default effort is high on Opus 4.6, Opus 4.8, and Sonnet 4.6, and xhigh on Opus 4.7.** The report's mapping is stale. (That post-mortem is also useful context for *why* this section was shaky: there were genuine, acknowledged Claude Code quality bugs at the intersection of context management and extended thinking in March–April 2026, fixed ~April 20 in v2.1.116.)

### 3.5 The model lineup has moved past the report — 🟠
The report treats **Opus 4.6** as the newest model and cites the string `claude-opus-4-6`. Since then, **Opus 4.7** (flagship, default xhigh) and **Opus 4.8** (now the newest; requires Claude Code v2.1.154+) have shipped; current pinning strings referenced by admins are `claude-opus-4-7` / `claude-sonnet-4-6` / `claude-haiku-4-5-20251001`. The report's *mechanics* are unaffected, but any hard-coded model string in it should be re-checked before use.

### 3.6 The auto-compaction threshold — 🟡 and the "override can only lower" claim is 🔴
The report hedged "~83–95%," which was wise, because the wild numbers really do conflict: an Anthropic GitHub issue refers to a **"hardcoded 95%"** threshold; another user reports compaction firing at **~76% used**; a vendor source states **~83.5%**. The cleanest explanation (from the more technical write-ups) is that the percentage is computed against *usable* space after a **reserved output buffer that was recently cut from ~45K to ~33K tokens** (undocumented in the changelog), which is exactly why a single flat "%" misleads. **The harder problem:** the report claimed `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` "can only lower, not raise" the threshold — but a documented example sets it to **90 to trigger *later* than the ~83.5% default**, and the variable is described as accepting 1–100 and directly controlling the trigger point. So that specific claim is **likely wrong**; the override appears to move the threshold in *both* directions.

### 3.7 `.env` / secret protection — ⚠️ a real-world gap the report omitted
The report implicitly trusts permission denies to protect secrets. The Register reproduced (on v2.1.12, Jan 2026) that Claude Code **read a `.env` file despite `.claudeignore` and `.gitignore` entries** and despite the "respect .gitignore" config flag — and noted Claude itself *incorrectly* told a user `.claudeignore` would block reads. Two things follow: (a) `.claudeignore`/`.gitignore` are **not** reliable enforcement — the supported mechanism is `permissions.deny: ["Read(./.env)", ...]` (which officially replaced the deprecated `ignorePatterns`); and (b) even the supported mechanism should be treated as defense-in-depth, not a guarantee, given the prompt-injection exfiltration risk. This strengthens, rather than contradicts, the report's "use hooks/managed settings for hard guarantees" thesis — but the report should have surfaced the gap explicitly.

### 3.8 "Agent tool replaced Task tool in v2.1.63" — ⚪ unverified
I couldn't cleanly confirm this rename. Current permission documentation and managed-settings tooling **still reference `Task(AgentName)`** for controlling which subagents Claude can spawn (with built-ins Explore, Plan, Verify). It's plausible the internal tool was renamed while the permission-rule syntax kept the `Task(...)` spelling, but treat the specific "v2.1.63 / Agent replaced Task" detail as unconfirmed.

### 3.9 Import depth "4 hops (some say 5)" — 🟡 lean toward 5
A community how-to states recursive imports are supported to a **maximum depth of 5**. The report's hedge was appropriate; if you need a working number, assume 5 and don't architect anything that relies on it.

---

## 4. Net assessment

The report's **architecture is sound and, in its most important claim, prophetic** — "instructions are context, not config; use hooks for guarantees" is now official text and the dominant lived experience of users. Its **conceptual model** (lean CLAUDE.md → offload to rules/skills/subagents; plan-then-verify; managed settings for enforcement) matches both the creator's workflow and independent practitioners.

Where it's weakest is **precision on fast-moving numbers and one precedence mechanism**:
- The **deny-override** rationale (§3.3) is probably backwards, though the advice it supports is fine.
- The **auto-compact "can only lower"** detail (§3.6) is probably wrong.
- **Effort defaults and the model lineup** (§3.4, §3.5) have already drifted.
- The **skill-activation percentages** (§3.2) and **buffer/threshold figures** (§3.6) rest on thin or single-vendor sourcing.
- The **sandbox** (§3.1) and **`.env`** (§3.7) sections are too trusting of the safety story.

None of these break the report's usefulness as an *index*. They're exactly the class of detail you'd expect to rot fastest, which is itself the lesson: **anything with a version number or a percentage in this ecosystem should be re-verified at use time** with `/status`, `/permissions`, `/context`, and `claude --version`.

---

## 5. Verification table

| # | Claim in the report | Verdict | Evidence basis | Note / correction |
|---|---|---|---|---|
| 1 | CLAUDE.md/memory is context, not enforced config; use PreToolUse hooks for guarantees | ✅ | Official docs **+** heavy user reports | Now explicit in docs; understated as a "caveat" — it's *the* core limitation |
| 2 | Keep CLAUDE.md lean (<200 lines; 80–120 ideal) | 🟢 | Official + practitioner + real 189→63-line cleanup | 200-line *truncation* is MEMORY.md; CLAUDE.md's 200 is a soft quality ceiling |
| 3 | Boris Cherny workflow quotes (5 parallel Claudes, plan-first, add-to-CLAUDE.md, PostToolUse format hook, no `--dangerously-skip-permissions`) | ✅ | Primary thread (Jan 2 2026) + mirrors | Quotes predate Opus 4.6 effort UI ("Opus 4.5 with thinking") |
| 4 | 1M window: Opus 4.6+/Sonnet 4.6; Max/Team/Ent auto-upgrade Opus; Sonnet opt-in/credits; `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`; GA Mar 13 no premium | ✅ | Official Claude Code docs + Anthropic announcement | Pro is *not* in the auto-upgrade list despite some blogs |
| 5 | Sandboxing reduces permission prompts 84% | ✅ (number) / 🟢 (meaning) | Anthropic engineering blog | Anthropic now calls the approach "fallible"; users approve ~93% of prompts; escape hatch exists |
| 6 | Auto memory: v2.1.59+, default on, `~/.claude/projects/<p>/memory/`, 200-line MEMORY.md load | ✅ | Official docs + ship-date report (Feb 26 2026) | — |
| 7 | `ultrathink` reintroduced v2.1.68 | ✅ | Changelog + official docs | March 4 2026 |
| 8 | Plan-mode-first + verification loops are top habits | ✅ | Creator + official + community | — |
| 9 | Scope cascade managed→CLI→local→project→user; managed can't be overridden | 🟢 | Official + multiple guides | True for scope; deny interaction is the problem (#13) |
| 10 | Skill descriptions drive triggering; gerund naming; test across models | ✅ | Official skill-authoring docs | Qualitative claims solid |
| 11 | Sandbox is a safety win enabling autonomy | 🟢→⚠️ | Anthropic "how we contain Claude" | Friction-reducer, not a hard boundary; use VM/container for real isolation |
| 12 | Skill activation 20%→50%, examples→90% | 🟡 | Single gist (incoherent) vs 200+ prompt test | Descriptions plateau ~50%; ~84% needs a forced-eval *hook* |
| 13 | Project deny overridable by a local allow | 🔴 | Sources conflict; dominant reading says deny wins anywhere | Mechanism likely wrong; "put denies in managed" advice still correct |
| 14 | Effort default high on Team/Ent/API, medium elsewhere | 🟠 | v2.1.68 → reversed Apr 7; Apr 23 post-mortem; current docs | Now high on 4.6/4.8/Sonnet 4.6, xhigh on 4.7 |
| 15 | Opus 4.6 is newest; string `claude-opus-4-6` | 🟠 | Newer model announcements/admin docs | Opus 4.7 then 4.8 shipped; re-check any pinned string |
| 16 | Auto-compact ~83–95% | 🟡 | GitHub issue (95%) vs 76% vs 83.5% reports | Varies because % is of usable space after a ~33K (was ~45K) buffer |
| 17 | `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` can only lower the threshold | 🔴 | Documented example raises it to 90 | Appears to move threshold both ways (1–100) |
| 18 | Secrets protected via permission denies (`.env`) | ⚠️ | The Register reproduction (v2.1.12) | `.claudeignore`/`.gitignore` unreliable; use `permissions.deny: Read(./.env)`; treat as defense-in-depth |
| 19 | Agent tool replaced Task tool in v2.1.63 | ⚪ | Docs still reference `Task(AgentName)` | Rename detail unconfirmed |
| 20 | Import depth 4 (maybe 5) | 🟡 | Community how-to says 5 | Assume 5; don't depend on it |
| 21 | "Context rot": big window ≠ better | ✅ | User who shrank window back to 200K | Reinforced, not weakened |

---

## 6. If you act on one thing

The pattern across every 🔴/🟠/🟡 above is the same: **the durable conceptual claims held; the version-stamped and percentage-stamped claims rotted within weeks.** So the practical upgrade to the report isn't a content change — it's a *discipline*: treat the inventory as stable and re-verify anything numeric or version-specific at the moment of use. The tools to do that are already in the report (`/status`, `/permissions`, `/context`, `/memory`, `claude --version`); they should arguably be promoted from "debugging aids" to "the first thing you run in any new install."
