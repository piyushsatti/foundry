# Claude Code: Index & Inventory of Features, Mechanics, and Community-Verified Best Practices (May 2026)

## TL;DR
- This is a complete inventory of the Claude Code application's configuration and context surface — settings layers, Agent Skills, CLAUDE.md memory files, auto memory, context management, prompt engineering, hooks, and sandbox — with each item tagged by how widely used it is.
- The single highest-leverage area is **context engineering via CLAUDE.md** plus disciplined context management (/clear, /compact, subagents); the community consensus is "keep CLAUDE.md lean (<200 lines, ideally 80–120), put it in the right scope, and offload everything else to skills, rules, and subagents."
- Most facts are stable, but several are version-dependent as of May 2026 (auto memory v2.1.59+, 1M-token context window for Opus 4.6+/Sonnet 4.6, the effort system replacing thinking budgets, `ultrathink` re-added v2.1.68); these are flagged inline.

## Key Findings
- Claude Code has **two distinct configuration systems**: JSON `settings.*` files ("what Claude is allowed to do") and Markdown `CLAUDE.md`/memory files ("what Claude should know"). Confusing them is the most common setup mistake.
- Settings follow a strict precedence cascade (Managed > CLI flags > Local > Project > User); arrays merge/concatenate, scalars override by highest scope.
- CLAUDE.md is **context, not enforced configuration** — it is injected as a user message and Claude "tries" to follow it. For hard guarantees you must use hooks or permission rules.
- Skills, subagents, and `.claude/rules/` exist specifically to keep CLAUDE.md and live context lean — they load on demand rather than every session.
- The community has converged on a "Research → Plan → Execute → Review → Ship" workflow, with plan mode + verification loops as the two highest-impact habits.

---

## A) SETTINGS LAYERS

**The settings cascade (precedence, highest → lowest)** — *core/heavily used*
Official order: **Managed policy > Command-line flags > Local project (`.claude/settings.local.json`) > Project (`.claude/settings.json`) > User (`~/.claude/settings.json`)**. Higher scopes override lower for the same scalar key; arrays (like permission rules) merge/concatenate across all layers. Some docs phrase it as a "5-layer" system by splitting managed into its own tier.

- **User / global — `~/.claude/settings.json`** — *core*. Personal defaults across all projects (preferred model, status line, global allow rules). Never committed.
- **Project (shared) — `.claude/settings.json`** — *core*. Team standards, committed to git. Permission allowlists, hooks, model/effort floor, MCP servers.
- **Local project — `.claude/settings.local.json`** — *common*. Personal per-project overrides; auto-gitignored by Claude Code. Highest of the file layers.
- **Managed/enterprise** — *niche (enterprise)*. Locations: macOS `/Library/Application Support/ClaudeCode/managed-settings.json`, Linux `/etc/claude-code/managed-settings.json` (and `managed-settings.d/` drop-ins, v2.1.83+), Windows `C:\ProgramData\ClaudeCode\managed-settings.json`. Cannot be overridden by user/project. Within the managed tier precedence is server-managed > MDM/OS policy > file-based > Windows HKCU registry.
- **CLI / env overrides** — *common*. `claude --model`, `--settings <file-or-json>`, `--setting-sources user|project|local`. Admin policy and CLI flags are always loaded and cannot be excluded by `--setting-sources`. A shell-exported env var (e.g. `ANTHROPIC_MODEL`) beats the same key in settings.json's `env` object.

**Most-tuned settings keys:**
- **`permissions` (allow / ask / deny arrays + `defaultMode`, `additionalDirectories`, `disableBypassPermissionsMode`)** — *core/heavily used*. Rules evaluated deny → ask → allow, first match wins. Format `Tool` or `Tool(specifier)`, e.g. `Bash(npm run test:*)`, `Read(./.env)`, `WebFetch(domain:example.com)`. `defaultMode` values: `default`, `acceptEdits`, `plan`, `bypassPermissions`. **Security gotcha:** deny rules in project settings can be overridden by a user's local file — security-critical denies must live in managed settings.
- **`model`** — *core*. e.g. `claude-opus-4-6`, `claude-sonnet-4-6`, `claude-haiku-4-5-20251001`. `availableModels` restricts the `/model` picker.
- **`env`** — *common*. Injects env vars into every Bash call and hook (plain strings only; deep-merged across scopes).
- **`hooks`** — *common*. Lifecycle automation (see §G). Arrays concatenate across scopes.
- **`mcpServers`** — *common*. External tool integrations (note: MCP/Cowork are out of strict scope, but MCP is configured here).
- **`sandbox`** — *common/growing* (see §H).
- **`autoMemoryEnabled` / `autoMemoryDirectory`** — *common* (v2.1.59+).
- **`claudeMdExcludes`** — *niche* (monorepo hygiene).
- **`attribution`** (replaces deprecated `includeCoAuthoredBy`) — *common*. Set to empty strings to strip Co-Authored-By from commits/PRs.
- **`cleanupPeriodDays`, `apiKeyHelper`, `apiBaseUrl`, `forceLoginMethod`, `forceLoginOrgUUID`** — *niche/enterprise*.

**Community conventions** — *core knowledge*:
- Add `"$schema": "https://json.schemastore.org/claude-code-settings.json"` for editor autocomplete/validation.
- Pin **model + effort at the project layer** so the whole team gets consistent output; let individuals raise (not lower) via local.
- Secrets never go in `.claude/settings.json` (committed) — use `.local.json` or shell env.
- Debug with `/status` (shows which sources loaded), `/permissions` (active rules), and `/config`. Most settings hot-reload; a few are read once at startup. Claude Code keeps the 5 most recent timestamped config backups.
- Some UI prefs live in `~/.claude.json`, not settings.json (adding them to settings.json throws a schema error).

---

## B) SKILLS (Agent Skills)

**What they are** — *common, rapidly growing*. Skills are folders containing a `SKILL.md` (YAML frontmatter + Markdown body), optionally with bundled `scripts/`, `references/`, `assets/`, `templates/`. They follow the open **Agent Skills standard** (agentskills.io) and work across Claude.ai, the API, and other tools. In Claude Code, custom slash commands have effectively merged into skills — `.claude/commands/*.md` still work, but `.claude/skills/<name>/SKILL.md` is the recommended path; if a command and skill share a name, the skill wins.

**Directory / scope** — *common*:
- Project: `.claude/skills/` (shared via git; loaded from start dir up to repo root).
- User: `~/.claude/skills/` (all projects).
- Plugin skills: `<name>:<skill>` namespace, bundled with plugins.
- Precedence on name clash: enterprise > personal > project (plugins never clash). Live edits to `SKILL.md` apply within the session; a brand-new top-level skills dir needs a restart.

**Progressive disclosure (the core mechanic)** — *core concept*:
1. At startup only `name` + `description` of every skill load into the system prompt (cheap).
2. `SKILL.md` body loads only when the skill is triggered.
3. Bundled files load only when Claude reads them; scripts execute without their source entering context (only output costs tokens).

**Frontmatter fields** — *common*:
- `name` (lowercase, hyphens, numbers only; gerund form recommended, e.g. `processing-pdfs`).
- `description` (**the single most important field**, up to ~1024 chars) — must state *what it does* AND *when to use it*, with explicit trigger phrases ("Use when…", "even if the user doesn't explicitly say X").
- Optional: `context: fork` (run in isolated subagent, returns only final result), `agent:` (Explore/Plan/custom), `allowed-tools`/`disallowed-tools` (CLI only), `disable-model-invocation: true` (hide from auto-trigger; / only), `argument-hint`, glob path-limits, `model`.

**Design best practices (official + community)** — *core knowledge*:
- **One skill, one job.** Avoid "mega-skills" — they have lower activation accuracy and composability.
- **The description determines whether the skill fires.** Claude *undertriggers* — include concrete keywords/contexts. Community testing reportedly moved activation from ~20% to ~50% with optimized descriptions, and higher still with examples.
- Keep `SKILL.md` body **under 500 lines**; push depth into `references/` loaded on demand (use Read-tool pointers, not `@` imports — `@` only works in CLAUDE.md).
- Prefer **scripts for deterministic work** ("voodoo constants" discouraged, forward-slash paths, list required packages).
- A **"Gotchas"/common-mistakes section** is the highest-value content; iterate it from real failures.
- Add context Claude *doesn't already have* — don't restate general coding knowledge.
- Test across every model you'll use it with (Haiku may need more detail than Opus).
- **Security:** treat installing third-party skills like installing software (they can run bash/scripts, fetch external URLs, exfiltrate data). Audit bundled files.
- Bundled skills shipping in the CLI include `/code-review`, `/batch`, `/debug`, `/loop`, `/simplify`, `/claude-api` (prompt-based, not fixed logic). Large community libraries exist (e.g. `anthropics/skills`, plus big third-party marketplaces).

---

## C) CONTEXT ENGINEERING via CLAUDE.md (most important area)

**What CLAUDE.md is** — *core/heavily used*. Markdown instruction files Claude reads at the **start of every session**, injected as a user message after the system prompt. Critical nuance: it is **context, not enforced config** — "Claude reads it and tries to follow it, but there's no guarantee of strict compliance." For hard guarantees, use hooks/permissions.

**Locations & load order (broadest → most specific)** — *core*:

| Scope | Location | Shared with |
|---|---|---|
| Managed policy | macOS `/Library/Application Support/ClaudeCode/CLAUDE.md`; Linux `/etc/claude-code/CLAUDE.md`; Windows `C:\Program Files\ClaudeCode\CLAUDE.md` (or `claudeMd` key in managed-settings.json) | All org users; cannot be excluded |
| User | `~/.claude/CLAUDE.md` | You, all projects |
| Project | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Team via git |
| Local | `./CLAUDE.local.md` (gitignore it) | You, this project |

**Loading mechanics** — *core*:
- Claude **walks up** the directory tree from the working dir, loading every `CLAUDE.md`/`CLAUDE.local.md` it finds **in full** at launch. Order: filesystem root → working dir (closer files read last); within a directory, `.local.md` is appended after `CLAUDE.md`.
- **Subdirectory CLAUDE.md files are lazy-loaded** — only pulled in when Claude reads a file in that subdirectory (good for monorepos).
- All files are **concatenated, not overridden**. Cross-layer conflicts → "Claude may pick one arbitrarily." Only guaranteed precedence is `.local.md` after `CLAUDE.md` within the same directory. **So: avoid conflicts; don't rely on precedence.**
- No restart needed after editing — changes apply on the next turn.
- Block-level HTML comments (`<!-- ... -->`) are stripped before injection (free maintainer notes).

**Imports / `@`-references** — *common*:
- `@path/to/file` pulls in other files (README, package.json, docs). Relative paths resolve from the importing file. Recursive up to **4 hops** (some sources say 5). **Imports do NOT save context** — content expands inline at launch.
- Pattern for cross-tool repos: `CLAUDE.md` containing `@AGENTS.md` (Claude reads CLAUDE.md, not AGENTS.md). `/init` also reads `.cursorrules`/`.windsurfrules`.
- First-time external imports trigger an approval dialog.

**What belongs in CLAUDE.md** — *core knowledge*: build/test commands, code style/conventions, project architecture/layout, naming conventions, "always do X" rules, and things Claude "couldn't know unless told." Add an entry when Claude repeats a mistake, a review catches something it should've known, you retype the same correction, or a new teammate would need it.

**What should NOT go in it** — *core knowledge*: secrets/credentials/PII; generic advice ("write good code," "be a senior engineer," "think step by step"); anything Claude can infer from code; long duplicated docs (reference them instead); multi-step procedures or path-specific rules (→ skills or `.claude/rules/`); static plans (→ issue trackers/commands).

**Lean / token-budget consensus** — *core*:
- Official: **target under 200 lines**; longer files "consume more context and reduce adherence." (CLAUDE.md loads in full regardless of length, unlike auto memory.)
- Community sweet spots: 80–120 lines (high-signal limit), 20–80 for small repos; "point, don't dump." A widely cited heuristic: models reliably follow ~150–200 instructions and Claude Code's own system prompt eats ~50 of those slots.
- **Boris Cherny (Claude Code's creator) confirmed his team's approach in a January 2, 2026 X/Threads thread:** "Our team shares a single CLAUDE.md for the Claude Code repo. We check it into git, and the whole team contributes multiple times a week. Anytime we see Claude do something incorrectly we add it to the CLAUDE.md, so Claude knows not to do it next time." His file is cited at ~2,500 tokens / ~100 lines.
- Test signals: if Claude ignores a rule, the file is probably too long; if it asks something already answered, the phrasing is ambiguous. **Treat CLAUDE.md like code — prune it regularly.** Emphasis ("IMPORTANT", "YOU MUST") improves adherence. Put most important rules near the top.

**`.claude/rules/` (modular instructions)** — *common, growing*:
- Topic files in `.claude/rules/` (and `~/.claude/rules/` for user-level). Rules **without** `paths:` frontmatter load every session at `.claude/CLAUDE.md` priority; rules **with** `paths:` glob frontmatter load only when Claude touches matching files — the key tool for keeping context lean. Supports symlinks for sharing across projects. The community pattern: "root CLAUDE.md becomes the index; deep/topic-specific content lives in `.claude/rules/`."

---

## D) MEMORY

**Two complementary systems, both loaded every session** — *core*:
1. **CLAUDE.md** (you write; instructions/rules; loaded in full) — covered in §C.
2. **Auto memory** (Claude writes; learnings/patterns) — *common, newer*. Requires **v2.1.59+**, on by default.

**Auto memory mechanics** — *common*:
- Storage: `~/.claude/projects/<project>/memory/` (per git repo; shared across worktrees; machine-local, not synced/committed). Configurable via `autoMemoryDirectory`.
- Contains a `MEMORY.md` index plus topic files (`debugging.md`, etc.). **Only the first 200 lines / 25 KB of `MEMORY.md` load at session start**; topic files load on demand. (This 200-line limit applies only to MEMORY.md, not CLAUDE.md.)
- Claude decides what's worth saving (build commands, debugging insights, preferences). Toggle via `/memory`, `autoMemoryEnabled: false`, or `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`. Subagents can keep their own auto memory.
- Community caution: routing/instruction rules belong in CLAUDE.md (loads in full), not MEMORY.md (truncated at 200 lines).

**Key commands/shortcuts** — *core*:
- **`/init`** — generates a starter CLAUDE.md by analyzing the codebase (suggests improvements if one exists); reads AGENTS.md/.cursorrules. `CLAUDE_CODE_NEW_INIT=1` enables an interactive multi-phase flow (also sets up skills/hooks).
- **`/memory`** — lists all loaded CLAUDE.md/CLAUDE.local.md/rules files, toggles auto memory, opens files to edit. **Primary debugging tool** when a rule isn't being followed (if a file isn't listed, Claude can't see it).
- **`#` shortcut** — type `# <text>` to quickly add a memory; Claude saves preference-type items to auto memory, or you can ask it to add to CLAUDE.md.
- **`--add-dir`** + `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` — load CLAUDE.md from extra directories (monorepos).
- Debug aids: `InstructionsLoaded` hook logs exactly which instruction files loaded.

**Community practice**: "spending one hour on a solid CLAUDE.md saves countless hours"; maintain a per-task notes directory and point CLAUDE.md at it; commit project CLAUDE.md for team compounding value.

---

## E) CONTEXT MANAGEMENT

**Context window size (verified, current)** — *core; version-dependent*:
- **Default baseline is 200,000 tokens.** A **1,000,000-token window** is supported by **Opus 4.6+ and Sonnet 4.6** in Claude Code. Per Anthropic's GA announcement (March 13, 2026), the 1M window became generally available for Opus 4.6 and Sonnet 4.6 **with no long-context premium** (the prior beta charged 2× input / 1.5× output above 200K tokens). On Max/Team/Enterprise, **Opus is automatically upgraded to 1M** (no config); **Sonnet's 1M is opt-in and requires usage credits on every plan** (including Max, except usage-based Enterprise). Disable via `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`. (Note: `opusplan`'s Opus plan phase runs at standard 200K. claude.ai chat uses a 500K window — don't conflate with Code's 1M.) Verify live with `/context` (shows `Xk/1000k` if 1M active).
- Why it matters: performance degrades as context fills ("context rot" / "lost in the middle") even with a huge window. Retrieval quality at extreme length is model-dependent — on the 8-needle 1M MRCR v2 retrieval test, Anthropic reports Opus 4.6 scores ~76–78% (vs. 18.5% for Sonnet 4.5), described as "the highest among frontier models at that context length." Context remains the fundamental constraint.

**`/clear` vs `/compact`** — *core/heavily used*:
- **`/clear`** — hard reset; wipes conversation history entirely (CLAUDE.md still reloads; file edits remain). Use between unrelated tasks or when context is "poisoned." Community ritual: before clearing, write a 3–5 line brief (goal, constraints, what you learned, what to avoid) to seed the new session.
- **`/compact [instructions]`** — summarizes history and replaces it with the summary (e.g. ~70K → ~4K tokens). Use `/compact Focus on the API changes` to steer. Use when continuity matters.
- **Auto-compaction** — fires automatically as you approach the limit (clears older tool outputs first, then summarizes). **Anthropic does not officially publish the exact threshold**; community/reverse-engineered sources conflict (~83% vs ~95%). `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` (integer 1–100) exists but community reports it can only *lower*, not raise, the default threshold.

**What survives compaction (official)** — *core*:
- **Re-injected from disk:** project-root CLAUDE.md, unscoped rules, auto memory. Invoked skill bodies re-injected (capped 5K tokens/skill, 25K total).
- **Lost until re-triggered:** path-scoped (`paths:`) rules, nested subdirectory CLAUDE.md, conversation-only instructions. → If a rule must persist, drop `paths:` or move it to root CLAUDE.md.

**Community techniques** — *core knowledge*:
- **Compact proactively at ~60–70%**, not at the auto-trigger — the model summarizes better while context is still clean; auto-compact runs in a degraded state.
- **`/clear` between tasks** is the most-repeated single tip.
- **Smaller tasks > bigger window**: if you keep hitting compaction before finishing, break the work down.
- **Delegate to subagents** for research/exploration — they run in separate context windows and return only summaries (see below).
- **`/context`** — visual breakdown of context usage (system prompt, tools, memory, skills, messages, free space, autocompact buffer) with optimization tips; check it periodically in long sessions.
- **`/rewind`** / Esc-Esc — roll back to a checkpoint (code and/or conversation); "Summarize from here / up to here."
- **`/btw`** — ask an ephemeral side question that never enters conversation history.
- Add a "Compact Instructions" section to CLAUDE.md to control what survives.

**Subagents (context isolation)** — *common, heavily endorsed*:
- Isolated Claude instances (`.claude/agents/*.md`: YAML frontmatter = config, body = system prompt; user `~/.claude/agents/` or project `.claude/agents/`). Each gets its own context window, tools, permissions, optional model; returns only a summary to the parent. Invoked via the **Agent tool** (replaced the Task tool in v2.1.63). Built-ins: **Explore** and **Plan** (read-only; skip CLAUDE.md/git status to stay lean) and general-purpose.
- Best practices: one task per subagent; give full context upfront (they can't ask follow-ups); specify structured output; use for noisy/bounded/summarizable work (codebase exploration, verification, parallel edits); `model: haiku` for cheap search; `isolation: worktree` to avoid parallel-edit collisions. Avoid for tightly-coupled sequential work or same-file edits.
- Related (mostly out of core but adjacent): **Agent Teams** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, v2.1.32+) for peer-to-peer multi-session coordination; git **worktrees** for parallel sessions.

---

## F) PROMPT ENGINEERING for Claude Code

**Plan mode** — *core/heavily used*. `Shift+Tab` cycles modes (default → acceptEdits → plan; with `--enable-auto-mode`, adds → auto). Claude reads/proposes a plan but makes **no edits until approved**. The most-cited rule: **plan before any non-trivial task (3+ files/steps)**; pour effort into the plan so Claude can one-shot implementation; if something goes sideways mid-execution, **stop and re-plan** rather than course-correct. Typical flow: plan mode → refine → switch to auto-accept → execute. Power pattern: have one Claude draft a plan, a second review it "as a staff engineer," iterate with "address all notes, don't implement yet."

**Thinking / effort** — *core; version-dependent*:
- v2 uses an **effort system**: `/effort` with levels low / medium / high / max (and `auto`); default high on Team/Enterprise/API, medium elsewhere. Also `xhigh` for hardest Opus tasks. Set permanently via `/model` effort selection.
- **`ultrathink`** keyword — re-introduced **v2.1.68**; parsed as a max/high-effort trigger (`think < think hard/megathink < think harder/ultrathink` was the v1 budget ladder). More reliable than natural-language "think deeply." `/t` toggles thinking-keyword detection. Costs 2–5× more tokens — reserve for hard architecture/debugging. (Note: these keywords only do something in Claude Code, not the web app or raw API.)

**Other widely-agreed patterns** — *core knowledge*:
- **Be specific and verifiable**: "Use 2-space indentation," "run `npm test` before committing," exact file paths — not "format properly."
- **Spec-driven**: write `spec.md`, then "read spec.md and implement it exactly"; explicit phases ("Phase 1: explore; Phase 2: plan; Phase 3: execute one file at a time").
- **Verification is the highest-leverage practice** (per the Claude Code team's own best-practices guidance): "Give Claude a check it can run: tests, a build, a screenshot to compare. It's the difference between a session you watch and one you walk away from." TDD-style red→green loops give unambiguous feedback Claude can iterate against.
- **Interview-first** for ambiguous tasks: "ask me questions before implementing."
- **`@`** to attach files/dirs; **`!`** for inline bash; images via path.
- **Commit before sessions** (`git checkout .` undoes mistakes in 1s); review `git diff HEAD` after.
- **Self-improvement loop**: after any correction, update CLAUDE.md / a `lessons.md`.

---

## G) HOOKS (brief)

*Common, power-user.* User-defined shell commands, HTTP endpoints, or LLM prompts that fire at lifecycle events. Configured under the `hooks` key in settings files (project `.claude/settings.json` most common; also user-level; also agent/skill frontmatter). Arrays for the same event concatenate across scopes.

- **Events (~12–17 total):** `PreToolUse` (can block/modify before a tool runs — the enforcement hook; exit code 2 = block; can modify tool input since v2.0.10), `PostToolUse` (validate/format after — can't undo), `UserPromptSubmit`, `Stop`/`StopFailure` (exit 2 forces Claude to keep working), `SessionStart`/`SessionEnd`, `SubagentStart`/`SubagentStop`, `Notification`, `PermissionRequest`, `Setup`, `Elicitation`/`ElicitationResult`, `InstructionsLoaded`.
- **Handler types:** command (shell — most common), http (POST JSON), prompt (single-turn LLM), agent (subagent verification).
- **Common uses:** auto-format/lint after edits (Prettier/ESLint/Black), block edits to `.env`/secrets/lockfiles, block dangerous bash (`rm -rf`), run tests, route notifications (Slack/desktop), git automation, log skill/subagent usage. Hooks fire for subagent actions too (gates apply recursively).
- **Why they matter:** hooks are **deterministic** — they turn advisory CLAUDE.md rules into enforced gates. Use `$CLAUDE_PROJECT_DIR`/absolute paths; keep handlers fast (each runs synchronously).

---

## H) SANDBOX (brief)

*Common, growing; some pieces beta/research-preview.* OS-level isolation for the Bash tool, reducing permission prompts while increasing safety. Per Anthropic's engineering post *Making Claude Code more secure and autonomous*: "In our internal usage, we've found that sandboxing safely reduces permission prompts by 84%." Two boundaries that must work together:
- **Filesystem isolation** — Claude can only read/modify allowed directories (can't touch `~/.ssh`, `~/.bashrc`, settings files — which the sandbox auto-protects from writes).
- **Network isolation** — outbound traffic routes through a local allowlist proxy; new domains prompt; child processes inherit restrictions.

- **Enable:** `/sandbox`; or `sandbox.enabled: true` in settings (disabled by default). Tech: macOS **Seatbelt**, Linux **bubblewrap**, WSL2 supported (WSL1 and native Windows are not).
- **Two modes:** auto-allow (bash auto-approved inside the sandbox; out-of-bounds falls back to permission prompts) vs. regular-permissions (still approve each command, but denied ops fail fast). `autoAllowBashIfSandboxed`.
- **Config:** `sandbox.filesystem`, `sandbox.network` (allow/deny domains, `allowManagedDomainsOnly`), `allowUnixSockets`, `excludedCommands`/`allowUnsandboxedCommands` (run git/docker outside), proxy ports.
- **Caveats:** there's a documented escape hatch — Claude is trained to retry failed commands with `dangerouslyDisableSandbox: true`; `enableWeakerNestedSandbox` weakens isolation for Docker; the proxy makes allow decisions from client-supplied hostnames (domain-fronting risk). For hard enforcement, enterprises pair it with managed policy / containers. Adjacent: **Docker Sandboxes** (microVM isolation, Jan 2026) and Claude Code on the web (cloud sandbox).

---

## I) GENERAL COMMUNITY BEST PRACTICES (synthesis)

*The convergent consensus across X, Reddit, GitHub, blogs, and the Anthropic team:*

1. **Context is the scarce resource — engineer it, don't fill it.** "Context engineering has replaced prompt engineering" as the leverage point. Keep CLAUDE.md lean, offload to skills/rules/subagents, `/clear` between tasks, compact proactively.
2. **Plan before you execute.** The most expensive mistake is letting Claude code before agreeing on what to build (0.8^20 ≈ 1% chance of getting a 20-decision feature fully right unguided; Anthropic's internal testing found unguided attempts succeed ~33% of the time). Plan mode collapses ambiguity.
3. **Give Claude a way to verify itself.** Tests/linters/build/browser checks — the single highest-impact habit per the Claude Code team.
4. **Treat CLAUDE.md as a living, team-owned, git-committed document.** Update it the moment Claude makes a repeatable mistake (Boris Cherny: "Anytime we see Claude do something incorrectly we add it to the CLAUDE.md"). Layer it (org/managed → user → project → subdir).
5. **Build your setup over time, not upfront.** Recommended staging: basic CLAUDE.md + a few commands → add hooks/skills when a need is proven → subagents for multi-context → MCP only if truly required.
6. **Use the right primitive for the job:** CLAUDE.md = always-on context; `.claude/rules/` = path-scoped context; skills = on-demand reusable workflows; subagents = isolated/parallel tasks; hooks = deterministic enforcement; settings = permissions/behavior.
7. **Run parallel/async.** Power users run multiple sessions at once. Boris Cherny describes his own setup: "I run 5 Claudes in parallel in my terminal. I number my tabs 1-5 … I also run 5-10 Claudes on claude.ai, in parallel with my local Claudes." Pair parallel local sessions with git worktrees so edits don't collide; treat Claude as an async engineer (kick off a task, minimize the terminal, return to review).
8. **Model/effort discipline:** match model and effort to task (Haiku/low for trivial, Opus/high/ultrathink for architecture & gnarly debugging) — overusing max effort wastes tokens.
9. **Safety reflexes:** commit before sessions; deny secrets in managed/project settings; review diffs; sandbox or container for autonomy.
10. **Common mistakes to avoid:** bloated CLAUDE.md (rules get ignored); putting security denies in project (not managed) settings; one long session for many features; waiting for auto-compact; over-delegating trivial tasks to subagents; mega-skills with vague descriptions; relying on CLAUDE.md for hard guarantees instead of hooks.

## Caveats
- **Version sensitivity (May 2026):** auto memory needs v2.1.59+; Agent tool replaced Task tool in v2.1.63; `ultrathink` re-added v2.1.68; managed-settings.d drop-ins v2.1.83+; HTTP hooks/PreToolUse input-modification are recent; the 1M context window depends on model (Opus 4.6+/Sonnet 4.6) and plan, and went GA (no premium) on March 13, 2026. Confirm against `claude --version`.
- **Conflicting/unofficial figures:** the exact auto-compaction percentage is **not officially published** — community estimates range ~83–95% and appear to vary by version; `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` reportedly only lowers the threshold. Import depth is cited as both 4 and 5 hops. Treat these as approximate.
- **Many "guides" are vendor/SEO content** (claudefa.st/ClaudeFast Kit, Blink, Morph, Verdent, etc.) and sometimes promote products; their mechanics largely match official docs but treat specific numbers cautiously. Official precedence facts come from code.claude.com/docs.
- **Scope:** this index deliberately excludes Cowork, Projects, the desktop app, the API/SDK harness, and MCP server internals except where they are configured *within* Claude Code settings.
- **Next step:** this is the inventory; phasing (which features to adopt in what order) is a separate deliverable.